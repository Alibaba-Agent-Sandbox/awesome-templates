#!/usr/bin/env python3
"""Unit tests for the template checker and the Express harness."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import check_template
import express_e2e
from express_e2e import Proc

ROOT = Path(__file__).resolve().parents[1]
SKELETON = ROOT / "_skeleton"


class CheckerTest(unittest.TestCase):
    def test_skeleton_conforms(self) -> None:
        violations = check_template.check_directory(SKELETON)
        self.assertEqual([str(item) for item in violations], [])

    def test_verified_provider_needs_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            readme = dest / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = text.replace(
                "No provider has a passing run recorded for this template.",
                "| Provider | Date | Level | Evidence |\n|---|---|---|---|\n| alicloud-express | 2026-10-15 | L2 | evidence/express-2026-10-15.json |",
            )
            readme.write_text(text, encoding="utf-8")
            zh = dest / "README.zh-CN.md"
            zh_text = zh.read_text(encoding="utf-8")
            zh_text = zh_text.replace(
                "尚未记录任何通过的提供方测试。",
                "| Provider | Date | Level | Evidence |\n|---|---|---|---|\n| alicloud-express | 2026-10-15 | L2 | evidence/express-2026-10-15.json |",
            )
            zh.write_text(zh_text, encoding="utf-8")
            yaml_path = dest / "template.yaml"
            yaml_text = yaml_path.read_text(encoding="utf-8").replace("tested_on: []", "tested_on: [alicloud-express]")
            yaml_path.write_text(yaml_text, encoding="utf-8")
            codes = {item.code for item in check_template.check_directory(dest)}
            self.assertIn("verified-evidence", codes)

            evidence = dest / "evidence"
            evidence.mkdir()
            evidence.joinpath("express-2026-10-15.json").write_text(
                json.dumps(
                    {
                        "provider": "alicloud-express",
                        "date": "2026-10-15",
                        "template": "_skeleton",
                        "template_version": "1.0.0",
                        "sdk_version": "0.3.0",
                        "passed": True,
                        "commands": [
                            {"name": "hello", "via": "cli", "ok": True, "duration_s": 0.1},
                            {"name": "hello", "via": "sdk", "ok": True, "duration_s": 0.2},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            codes = {item.code for item in check_template.check_directory(dest)}
            self.assertNotIn("verified-evidence", codes)

    def test_dockerfile_cmd_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            dockerfile = dest / "Dockerfile"
            dockerfile.write_text(dockerfile.read_text(encoding="utf-8") + 'CMD ["python3", "commands.py"]\n', encoding="utf-8")
            codes = {item.code for item in check_template.check_directory(dest)}
            self.assertIn("dockerfile-cmd", codes)

    def test_all_legacy_does_not_fail(self) -> None:
        code = check_template.main(["--all", "--root", str(ROOT)])
        self.assertEqual(code, 0)


class HarnessTest(unittest.TestCase):
    def test_plan_uses_yaml_smoke(self) -> None:
        code = express_e2e.main([str(SKELETON), "--plan"])
        self.assertEqual(code, 0)

    def test_blocker_skips_evidence_and_still_cleans_known_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "python-hello"
            dest.mkdir()
            (dest / "template.yaml").write_text(
                "name: python-hello\nversion: '1.0.0'\nbase: python:3.12-slim\n",
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def runner(args: list[str], timeout: float) -> Proc:
                del timeout
                calls.append(args)
                if "deploy" in args:
                    return Proc(1, "", "BuildModeError: base must be a mapping")
                return Proc(0, "", "")

            options = express_e2e.build_options(
                [str(dest), "--command", "hello", "--arg", "name=E2E", "--expect", "Hello, E2E!"]
            )
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_: "Hello, E2E!")
            self.assertEqual(code, 2)
            self.assertFalse((dest / "evidence").exists())
            self.assertTrue(any("deploy" in args for args in calls))
            self.assertFalse(any(args[:1] == ["kill"] for args in calls))

    def test_pass_writes_evidence_and_deletes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "python-hello"
            shutil.copytree(ROOT / "python-hello", dest)
            shutil.rmtree(dest / "evidence", ignore_errors=True)
            calls: list[list[str]] = []

            def runner(args: list[str], timeout: float) -> Proc:
                del timeout
                calls.append(list(args))
                if "deploy" in args:
                    return Proc(0, json.dumps({"TemplateID": "tmpl-spec", "Status": "ready"}), "")
                if "create" in args:
                    return Proc(0, json.dumps({"ID": "sb-spec"}), "")
                if "run" in args:
                    return Proc(0, json.dumps({"result": "Hello, E2E!"}), "")
                return Proc(0, "", "")

            options = express_e2e.build_options(
                [
                    str(dest),
                    "--command",
                    "hello",
                    "--arg",
                    "name=E2E",
                    "--expect",
                    "Hello, E2E!",
                    "--start-cmd",
                    "agent-sandbox-server serve --port 9000 --commands /app/commands.py",
                    "--ready-cmd",
                    "agent-sandbox-server healthcheck --port 9000",
                ]
            )
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_args: "Hello, E2E!")
            self.assertEqual(code, 0)
            evidence = list((dest / "evidence").glob("express-*.json"))
            self.assertEqual(len(evidence), 1)
            payload = json.loads(evidence[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["provider"], "alicloud-express")
            self.assertTrue(payload["passed"])
            self.assertNotIn("tmpl-spec", evidence[0].read_text(encoding="utf-8"))
            self.assertNotIn("sb-spec", evidence[0].read_text(encoding="utf-8"))
            self.assertTrue(any(args[:2] == ["kill", "sb-spec"] for args in calls))
            self.assertTrue(any(args[:3] == ["template", "delete", "tmpl-spec"] for args in calls))

    def test_sdk_blocker_still_deletes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "python-hello"
            shutil.copytree(ROOT / "python-hello", dest)
            shutil.rmtree(dest / "evidence", ignore_errors=True)
            calls: list[list[str]] = []

            def runner(args: list[str], timeout: float) -> Proc:
                del timeout
                calls.append(list(args))
                if "deploy" in args:
                    return Proc(0, json.dumps({"TemplateID": "tmpl-spec", "Status": "ready"}), "")
                if "create" in args:
                    return Proc(0, json.dumps({"ID": "sb-spec"}), "")
                if "run" in args:
                    return Proc(0, json.dumps({"result": "Hello, E2E!"}), "")
                return Proc(0, "", "")

            def sdk(*_args: object) -> str:
                raise RuntimeError("protocol error: promised 12 bytes in enveloped message")

            options = express_e2e.build_options(
                [str(dest), "--command", "hello", "--arg", "name=E2E", "--expect", "Hello, E2E!"]
            )
            code = express_e2e.execute(options, runner=runner, sdk=sdk)
            self.assertEqual(code, 2)
            self.assertFalse((dest / "evidence").exists())
            self.assertTrue(any(args[:1] == ["kill"] for args in calls))
            self.assertTrue(any("delete" in args for args in calls))


if __name__ == "__main__":
    unittest.main()
