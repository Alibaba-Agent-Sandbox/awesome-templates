#!/usr/bin/env python3
"""Audit current catalog step receipts, without creating cloud resources."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from select_image_templates import ROOT, catalog_names


def inspect_runtime(source: Path, receipt: dict) -> tuple[bool, str]:
    """Require current source, genuine steps and independent resource absence."""
    manifest = yaml.safe_load((source / "template.yaml").read_text())
    proof = receipt.get("build_provenance") or {}
    if (receipt.get("build_mode") or proof.get("build_mode")) != "steps":
        return False, "different build mode"
    if receipt.get("provider") != "alicloud-express":
        return False, "different provider"
    if receipt.get("passed") is not True or receipt.get("cleanup_verified") is not True:
        return False, "run or independent cleanup did not pass"
    if proof.get("asset_transport") == "oss":
        cache = receipt.get("asset_cache") or {}
        if cache.get("cleanup_verified") is not True or cache.get("private_acl_verified") is not True:
            return False, "private asset-cache ownership/cleanup did not pass"
    version = receipt.get("template_version") or proof.get("template_version")
    if str(version) != str(manifest["version"]):
        return False, "historical template version"
    hashes = proof.get("inputs_sha256") or {}
    if not hashes.get("Dockerfile") or not hashes.get("commands.py"):
        return False, "missing runtime provenance"
    for name, expected in hashes.items():
        # Qualification and README-only changes alter manifest bytes. Exact
        # version plus every recorded build/runtime file still must match.
        if name == "template.yaml":
            continue
        path = source / name
        if not path.resolve().is_relative_to(source.resolve()) or not path.is_file():
            return False, "missing or invalid input"
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            return False, "runtime input changed"
    return True, "current-version step runtime and independent cleanup verified"


def inspect_receipt(source: Path, receipt: dict) -> tuple[bool, str]:
    """A version, image receipt or deletion acknowledgement alone cannot pass."""
    valid, reason = inspect_runtime(source, receipt)
    if not valid:
        return valid, reason
    manifest = yaml.safe_load((source / "template.yaml").read_text())
    required = {(smoke["command"], via, json.dumps(smoke.get("args", {}), sort_keys=True))
                for smoke in manifest.get("smoke", []) for via in ("cli", "sdk")}
    observed = {(item.get("name"), item.get("via"), json.dumps(item.get("args", {}), sort_keys=True))
                for item in (receipt.get("commands") or [])
                if isinstance(item, dict) and item.get("ok") is True}
    if not required or not required.issubset(observed):
        return False, "missing successful CLI/SDK smoke calls"
    return valid, reason


def inspect_http_receipt(source: Path, receipt: dict) -> tuple[bool, str]:
    """Accept only the unchanged full controller, never image or smoke scope."""
    valid, reason = inspect_runtime(source, receipt)
    if not valid:
        return valid, reason
    counts = receipt.get("http_acceptance") or receipt
    if not isinstance(counts, dict):
        return False, "missing full HTTP controller result"
    if (counts.get("exit_code", counts.get("http_exit_code")) != 0
            or type(counts.get("pass_count")) is not int or counts["pass_count"] <= 0
            or type(counts.get("fail_count")) is not int or counts["fail_count"] != 0):
        return False, "full HTTP controller did not pass"
    controller = source / "e2e_test.py"
    if not controller.is_file() or counts.get("controller_sha256") != hashlib.sha256(controller.read_bytes()).hexdigest():
        return False, "HTTP controller changed or lacks provenance"
    return True, "full current HTTP controller passed; model skips retain their scope"


def audit(root: Path = ROOT, *, require_http: bool = False) -> dict:
    rows = []
    for name in catalog_names(root):
        source = root / name
        manifest = yaml.safe_load((source / "template.yaml").read_text())
        accepted = []
        http = []
        for path in sorted((source / "evidence").glob("*.json")):
            try:
                receipt = json.loads(path.read_text())
            except (ValueError, OSError):
                continue
            if isinstance(receipt, dict) and inspect_receipt(source, receipt)[0]:
                accepted.append(str(path.relative_to(root)))
            if isinstance(receipt, dict) and inspect_http_receipt(source, receipt)[0]:
                http.append(str(path.relative_to(root)))
        rows.append({"template": name, "version": str(manifest["version"]),
                     "steps": "PASS" if accepted else "MISSING", "receipts": accepted,
                     "http": "PASS" if http else "MISSING", "http_receipts": http})
    passed = sum(row["steps"] == "PASS" for row in rows)
    http_passed = sum(row["http"] == "PASS" for row in rows)
    return {"scope": "current-version Express platform-step runtime acceptance; not model or Docker acceptance",
            "passed": passed, "http_passed": http_passed, "require_http": require_http,
            "total": len(rows), "complete": passed == len(rows) and (not require_http or http_passed == len(rows)), "templates": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-http", action="store_true", help="Also require the complete current external HTTP controller for every profile")
    args = parser.parse_args()
    result = audit(require_http=args.require_http)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(text)
    else:
        print(text, end="")
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
