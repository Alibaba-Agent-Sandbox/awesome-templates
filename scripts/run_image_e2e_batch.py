#!/usr/bin/env python3
"""Run missing current-source Express image acceptance in isolated bounded workers.

Uses an already successful exact-source image-export workflow. Credentials stay
in the operator environment and each child runs the canonical one-image harness.
No raw logs, ownership IDs or registry references enter the progress JSON.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys

from ci_image_archive import github
from run_ci_image_e2e import check_image_cli
from select_image_templates import ROOT, catalog_names
from source_image_acceptance import audit


def selection(root: Path, requested: str | None, rerun: bool) -> list[str]:
    names = catalog_names(root)
    if requested is not None:
        selected = [name.strip() for name in requested.split(',')]
        if not selected or any(name not in names for name in selected) or len(set(selected)) != len(selected):
            raise ValueError('templates must be unique comma-separated catalog names')
        names = selected
    if not rerun:
        complete = {row['template'] for row in audit(root)['templates'] if row['express_image_http']}
        names = [name for name in names if name not in complete]
    return sorted(names, key=lambda name: (name != 'python-hello', name))


def exported_artifacts(run_id: int, names: list[str]) -> tuple[str, dict[str, int]]:
    workflow = github('/actions/runs/' + str(run_id))
    if workflow.get('event') != 'workflow_dispatch' or workflow.get('status') != 'completed' or workflow.get('conclusion') != 'success':
        raise ValueError('a completed successful explicit exact-source export is required')
    head = workflow['head_sha']
    artifacts = []
    for page in range(1, 21):
        batch = github(f'/actions/runs/{run_id}/artifacts?per_page=100&page={page}')['artifacts']
        artifacts.extend(batch)
        if len(batch) < 100:
            break
    result = {}
    for name in names:
        matches = [item for item in artifacts if item['name'] == 'image-' + name + '-' + head and not item.get('expired')]
        if len(matches) != 1:
            raise ValueError('missing or ambiguous unexpired exact-source export for ' + name)
        result[name] = matches[0]['id']
    return head, result


def worker(source: Path, artifact_id: int, crane: Path, private_root: Path) -> dict:
    private = private_root / source.name
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    before = set((source / 'evidence').glob('*.json'))
    with (private / 'private-worker-console.log').open('w') as output:
        response = subprocess.run([sys.executable, str(ROOT / 'scripts/run_ci_image_e2e.py'),
            str(source), '--artifact-id', str(artifact_id), '--crane', str(crane),
            '--private-root', str(private)], stdout=output, stderr=output)
    added = sorted(set((source / 'evidence').glob('*.json')) - before)
    reports = []
    for path in added:
        value = json.loads(path.read_text())
        if value.get('verification_type') == 'ci-image-backed-external-http':
            reports.append(value)
    runtime_started = any(report.get('runtime_attempted') for report in reports)
    unresolved = not reports
    for path in private.glob('abx-ci-image-*/registry-intent.json'):
        intent = json.loads(path.read_text())
        if intent.get('push_attempted') and intent.get('cleanup_verified') is not True:
            unresolved = True
    if runtime_started and any(report.get('cleanup_verified') is not True for report in reports):
        unresolved = True
    for path in private.glob('abx-ci-image-*/platform-intent.json'):
        if json.loads(path.read_text()).get('template_cleanup_verified') is not True:
            unresolved = True
    passed = response.returncode == 0 and any(report.get('passed') is True and
        report.get('cleanup_verified') is True and report.get('registry_cleanup_verified') is True
        and report.get('http_acceptance', {}).get('passed') is True for report in reports)
    return {'template': source.name, 'passed': passed, 'exit_code': response.returncode,
            'unresolved_owned_cleanup': unresolved,
            'receipts': [str(path.relative_to(ROOT)) for path in added],
            'http_acceptance': [report.get('http_acceptance', {}) for report in reports]}


def execute(names, artifacts, operation, workers, save):
    """Stop new writes after uncertain cleanup; finish existing owned workers."""
    pending = iter(names)
    active = {}
    rows = []
    stopped = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for _ in range(workers):
            name = next(pending, None)
            if name:
                active[pool.submit(operation, name, artifacts[name])] = name
        while active:
            completed, _ = concurrent.futures.wait(active, return_when=concurrent.futures.FIRST_COMPLETED)
            # Inspect every completed result before scheduling any follow-up.
            for future in completed:
                name = active.pop(future)
                try:
                    row = future.result()
                except Exception as exc:
                    row = {'template': name, 'passed': False, 'unresolved_owned_cleanup': True,
                           'error_type': type(exc).__name__}
                rows.append(row)
                stopped = stopped or row['unresolved_owned_cleanup']
                print(name + ': ' + ('PASS' if row['passed'] else 'FAIL') +
                      '; cleanup uncertainty=' + str(row['unresolved_owned_cleanup']), flush=True)
            save(rows, stopped)
            while not stopped and len(active) < workers:
                name = next(pending, None)
                if name is None:
                    break
                active[pool.submit(operation, name, artifacts[name])] = name
    return rows, stopped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workflow-run', type=int, required=True)
    parser.add_argument('--crane', type=Path, required=True)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--templates', help='Explicit comma-separated names; default selects missing current image HTTP')
    parser.add_argument('--rerun', action='store_true', help='Explicitly include already qualified sources')
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    private = args.private_root.resolve()
    if private.is_relative_to(ROOT):
        parser.error('private recovery/log/archive staging must stay outside the checkout')
    names = selection(ROOT, args.templates, args.rerun)
    check_image_cli()
    head, artifacts = exported_artifacts(args.workflow_run, names)
    report = {'workflow_run': args.workflow_run, 'source_head_commit': head, 'selected': names,
              'workers': args.workers, 'results': [], 'complete': False}

    def save(rows, stopped):
        report.update(results=rows, stopped_for_owned_cleanup=stopped,
                      complete=len(rows) == len(names) and all(row['passed'] for row in rows) and not stopped)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')

    save([], False)
    rows, stopped = execute(names, artifacts, lambda name, artifact: worker(ROOT / name, artifact,
        args.crane.resolve(), private), args.workers, save)
    save(rows, stopped)
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
