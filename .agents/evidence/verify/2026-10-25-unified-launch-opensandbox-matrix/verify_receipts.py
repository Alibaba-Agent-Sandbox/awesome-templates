"""Recheck the preserved 2026-10-25 matrix against this repository checkout."""
import hashlib
import json
from pathlib import Path

import yaml


directory = Path(__file__).resolve().parent
root = directory.parents[3]
catalog = yaml.safe_load((root / "awesome-templates.yaml").read_text())
expected = {row["name"]: root / row["path"] for row in catalog["templates"]}
receipts = [json.loads(path.read_text()) for path in sorted(directory.glob("public-launch-*.json"))]
assert len(receipts) == len(expected) == 46
assert {row["template"] for row in receipts} == set(expected)
calls = 0
smokes = 0
for receipt in receipts:
    name = receipt["template"]
    manifest_file = expected[name] / "template.yaml"
    manifest = yaml.safe_load(manifest_file.read_text())
    assert receipt["result"] == "PASS", name
    assert receipt["provider"] == "opensandbox" and receipt["endpoint_mode"] == "direct", name
    assert receipt["manifest_sha256"] == hashlib.sha256(manifest_file.read_bytes()).hexdigest(), name
    cases = [case for case in receipt["checks"] if isinstance(case, dict)]
    assert len(cases) == len(manifest["smoke"]), name
    for index, case in enumerate(cases):
        assert case["smoke"] == index and case["command"] == manifest["smoke"][index]["command"], name
        assert set(case["consumers"]) == {"cli", "python", "host-http"}, name
        assert case["has_expected_result"] == ("expect" in manifest["smoke"][index]), name
        calls += len(case["consumers"])
    smokes += len(cases)
    for check in ["unchanged source launched by installed CLI", "service authentication rejects wrong token",
                  "runtime source identity", "SDK exec and file round trip"]:
        assert check in receipt["checks"], (name, check)
    cleanup = receipt["cleanup"]
    assert cleanup["sandbox"] == cleanup["prepared_artifacts"] == "confirmed absent", name
    assert all(cleanup[key] == 0 for key in ["retained_artifact_count", "uncertain_count", "artifact_cleanup_failures"]), name
    packages = receipt["installed_packages"]
    assert packages["distribution"] == "source", name
    assert packages["cli"]["source_ref"] == "ea28f207c8a0016cf798f5a355e3c363c7c936f4", name
    assert packages["python_client"]["source_ref"] == packages["python_server"]["source_ref"] == "ff073167f8993a5c580c78cccccd5779db1f5836", name
    assert packages["provider_source_ref"] == "ebfb1c1554a567585e337f2e68cb3d449d5414b1", name
    assert packages["template_source_ref"] == "1d2953e16eec96da6c9c8a0a631220e2933c2aaf", name
assert (smokes, calls) == (73, 219)
summary = json.loads((directory / "verification.json").read_text())
assert (summary["result"], summary["cases"], summary["smoke_definitions"], summary["consumer_calls"]) == ("PASS", 46, 73, 219)
print("PASS: 46 receipts, 46 manifest hashes, 73 smoke definitions, 219 consumer calls; exact provenance and independent cleanup verified")
