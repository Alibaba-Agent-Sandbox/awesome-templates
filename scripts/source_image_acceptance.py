"""Audit current-source image runtime receipts, separately for each backend.

This performs no cloud operations and never turns missing proof into a pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import yaml

from ci_image import context_sha256, server_commit, validate_proof
from select_image_templates import ROOT, catalog_names
from opensandbox_template_e2e import PINS


def fixture_complete(name, receipt):
    fixture = receipt.get("test_configuration") or {}
    if name == "openclaw":
        return fixture.get("gateway_lifecycle_required") is True and fixture.get("generated_test_token") is True
    if name == "osworld":
        return fixture.get("desktop_lifecycle_required") is True
    if name == "cursor-agent":
        return fixture.get("native_authentication_error_path_required") is True and fixture.get("synthetic_invalid_vendor_credential") is True
    if name == "devin":
        return fixture.get("native_authentication_error_path_required") is True and fixture.get("credential_absence_required") is True
    return True


def http_complete(source, receipt):
    http = receipt.get("http_acceptance") or {}
    if any(type(http.get(key)) is not int or http[key] < 0 for key in ["pass_count", "fail_count", "skip_count"]):
        return False
    if not (http.get("passed") is True and http.get("exit_code") == 0
            and http.get("pass_count", 0) > 0 and http.get("fail_count", 0) == 0
            and http.get("verifier_sha256") == hashlib.sha256((source / "e2e_test.py").read_bytes()).hexdigest()):
        return False
    if source.name in {"cursor-agent", "devin", "osworld", "chrome"} and http.get("skip_count") != 0:
        return False
    if source.name in {"cursor-agent", "devin"} and http["pass_count"] < 16:
        return False
    if source.name == "osworld" and http["pass_count"] < 18:
        return False
    return fixture_complete(source.name, receipt)


def inspect_express(source, receipt):
    if not (receipt.get("provider") == "alicloud-express" and receipt.get("build_mode") == "image"
            and receipt.get("passed") is True and receipt.get("cleanup_verified") is True
            and receipt.get("registry_cleanup_verified") is True):
        return False, False
    proof = receipt.get("image_provenance") or {}
    # Only validate public proof shape/content. No live tag or API request is made.
    try:
        validate_proof(source, proof, "registry.cn-hangzhou.aliyuncs.com/acceptance/e2e-ci-image-0123456789abcdef:review")
    except (ValueError, TypeError, KeyError):
        return False, False
    if proof.get("tag_digest_verified_after_runtime") is not True:
        return False, False
    return True, http_complete(source, receipt)


def inspect_opensandbox(source, receipt, root):
    manifest = yaml.safe_load((source / "template.yaml").read_text())
    if not (receipt.get("provider") == "opensandbox" and receipt.get("build_mode") == "image"
            and receipt.get("template") == source.name and receipt.get("template_version") == str(manifest["version"])
            and receipt.get("verification_type") == "source-image-native-opensandbox-docker-http"
            and receipt.get("passed") is True and receipt.get("cleanup_verified") is True
            and receipt.get("workflow_job_conclusion") == "success"
            and receipt.get("pins") == PINS
            and (receipt.get("test_configuration") or {}).get("model_credentials_injected") is False
            and re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("source_commit", "")))
            and str(receipt.get("workflow_run_id", "")).isdigit()
            and receipt.get("context_sha256") == context_sha256(source)
            and receipt.get("server_sdk_commit") == server_commit(source)
            and receipt.get("controller_sha256") == hashlib.sha256((root / "scripts/opensandbox_template_e2e.py").read_bytes()).hexdigest()):
        return False
    cleanup = receipt.get("cleanup_observations") or {}
    identity = receipt.get("execution_identity") or {}
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str((receipt.get("images") or {}).get("template_image_id", ""))):
        return False
    if not (cleanup.get("sdk_not_found") is True and cleanup.get("owned_docker_containers_absent") is True
            and cleanup.get("errors") == [] and identity.get("probe_exit_code") == 0
            and type(identity.get("uid")) is int and identity["uid"] > 0):
        return False
    checks = set(receipt.get("checks") or [])
    commands = receipt.get('commands') or []
    for index, smoke in enumerate(manifest.get('smoke') or []):
        args_hash = hashlib.sha256(json.dumps(smoke.get('args', {}), sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        for via in ['cli', 'sdk']:
            if not any(item.get('index') == index and item.get('name') == smoke['command']
                       and item.get('via') == via and item.get('ok') is True
                       and item.get('args_sha256') == args_hash for item in commands if isinstance(item, dict)):
                return False
    if not manifest.get('smoke'):
        return False
    required = {"independent Docker identity matches exact built image", "actual runtime command bytes match source",
                "SDK real shell Python program", "SDK file write/read", "SDK file removal readback",
                "complete current external HTTP controller", "independent SDK and Docker absence",
                "owned provider engine stopped and reaped", "owned original server process stopped"}
    return required.issubset(checks) and http_complete(source, receipt)


def audit(root=ROOT):
    rows = []
    for name in catalog_names(root):
        source = root / name
        row = {"template": name, "version": str(yaml.safe_load((source / "template.yaml").read_text())["version"]),
               "express_image_runtime": [], "express_image_http": [], "opensandbox_native_http": []}
        for path in sorted((source / "evidence").glob("*.json")):
            try:
                receipt = json.loads(path.read_text())
                if not isinstance(receipt, dict):
                    continue
                native, http = inspect_express(source, receipt)
                if native:
                    row["express_image_runtime"].append(str(path.relative_to(root)))
                if http:
                    row["express_image_http"].append(str(path.relative_to(root)))
                if inspect_opensandbox(source, receipt, root):
                    row["opensandbox_native_http"].append(str(path.relative_to(root)))
            except (ValueError, OSError, KeyError, TypeError):
                continue
        rows.append(row)
    columns = ["express_image_runtime", "express_image_http", "opensandbox_native_http"]
    counts = {key: sum(bool(row[key]) for row in rows) for key in columns}
    return {"scope": "current-source image native/API/HTTP qualification, not model or generic native code capability",
            "total": len(rows), **counts, "complete": all(count == len(rows) for count in counts.values()), "templates": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(text)
    else:
        print(text, end="")
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
