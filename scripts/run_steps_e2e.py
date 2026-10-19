#!/usr/bin/env python3
"""Run real Express step acceptance serially, retaining sanitized per-attempt receipts.

Credentials come from the environment. ABX selects the verified CLI command.
Private harness journals/logs remain outside the checkout. This does not run L3.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time
import uuid

import yaml

import express_e2e
from prepare_steps import ROOT, prepare
from select_image_templates import catalog_names


def run_one(name: str, args: argparse.Namespace) -> dict:
    source = ROOT / name
    started = time.monotonic()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    stage = Path(tempfile.mkdtemp(prefix="abx-step-stage-"))
    stage.chmod(0o700)
    result = {"template": name, "provider": "alicloud-express", "build_mode": "steps",
              "attempt": stamp, "result": "FAIL", "passed": False, "model_acceptance": "NOT_RUN"}
    try:
        manifest, proof = prepare(source, region=args.region, tag=args.base_tag, server_commit=args.server_commit)
        (stage / "template.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
        (stage / "steps-provenance.json").write_text(json.dumps(proof, indent=2) + "\n")
        result["build_provenance"] = proof
        options = express_e2e.build_options([str(stage), "--build", "steps", "--alias",
            f"e2e-steps-{name}-{uuid.uuid4().hex[:8]}", "--timeout", str(args.timeout),
            "--idle-timeout", str(args.timeout), "--wall-timeout", str(args.timeout + 180),
            "--push-retries", "0"])
        with (stage / "private-harness.log").open("x") as output, redirect_stdout(output), redirect_stderr(output):
            status = express_e2e.execute(options)
        result["exit_code"] = status
        if status == 0:
            receipts = list((stage / "evidence").glob("express-*.json"))
            if len(receipts) != 1:
                raise RuntimeError("missing unique successful step receipt")
            receipt = json.loads(receipts[0].read_text())
            if receipt.get("cleanup_verified") is not True or receipt.get("build_mode") != "steps":
                raise RuntimeError("step receipt lacks required cleanup/build-mode evidence")
            target = source / "evidence" / receipts[0].name
            target.parent.mkdir(exist_ok=True)
            if target.exists():
                target = target.with_name("steps-" + stamp + ".json")
            # Exclusive creation preserves every historical receipt.
            with target.open("x") as stream:
                json.dump(receipt, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            result.update(result="PASS", passed=True, cleanup_verified=True,
                          receipt=str(target.relative_to(ROOT)), command_calls=len(receipt["commands"]))
        else:
            result["reason"] = "canonical step harness failed; private diagnostics/journal retained"
            result["result"] = "BLOCKED" if status == 2 else "FAIL"
    except Exception as exc:
        result["reason"] = type(exc).__name__ + "; private staging retained"
    result["duration_s"] = round(time.monotonic() - started, 3)
    evidence = source / "evidence"
    evidence.mkdir(exist_ok=True)
    path = evidence / ("verification-steps-" + stamp + ".json")
    with path.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"{name}: {result['result']} ({result['duration_s']}s); {path.relative_to(ROOT)}", flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--region", default="cn-hangzhou")
    parser.add_argument("--base-tag", default="v0.0.49")
    parser.add_argument("--server-commit", help="Optional immutable source override, recorded separately")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    names = catalog_names()
    selected = names if args.all else args.templates
    if not selected or len(set(selected)) != len(selected) or any(name not in names for name in selected):
        parser.error("select unique catalog names or --all")
    results = [run_one(name, args) for name in selected]
    return int(any(not row["passed"] for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
