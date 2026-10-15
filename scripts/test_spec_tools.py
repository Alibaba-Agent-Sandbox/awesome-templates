#!/usr/bin/env python3
"""Unit tests for the template checker and the Express harness."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

import check_template
import express_e2e
import image_size_report
from express_e2e import Proc

ROOT = Path(__file__).resolve().parents[1]
SKELETON = ROOT / "_skeleton"


def _process_dead(pid: int) -> bool:
    stat = Path(f"/proc/{pid}/stat")
    if not stat.exists():
        return True
    try:
        text = stat.read_text(encoding="utf-8")
    except OSError:
        return True
    state = text.rsplit(")", 1)[-1].split()[0]
    return state == "Z"


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

    def test_git_archive_pin_is_enough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            dockerfile = dest / "Dockerfile"
            text = dockerfile.read_text(encoding="utf-8")
            self.assertRegex(text, check_template.SERVER_GIT_ARCHIVE)
            self.assertEqual([str(item) for item in check_template.check_directory(dest)], [])

            short = text.replace(
                "35da216a300f1e2e84254a1cf4b4a7ea98681505",
                "35da216",
            )
            dockerfile.write_text(short, encoding="utf-8")
            codes = {item.code for item in check_template.check_directory(dest)}
            self.assertIn("pinned-version", codes)

    def test_pypi_pin_is_enough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            dockerfile = dest / "Dockerfile"
            text = dockerfile.read_text(encoding="utf-8")
            text = text.replace(
                '"agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk"',
                '"agent-sandbox-server==0.3.0"',
            )
            dockerfile.write_text(text, encoding="utf-8")
            self.assertEqual([str(item) for item in check_template.check_directory(dest)], [])

    def test_comment_only_pin_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            dest.joinpath("Dockerfile").write_text(
                "FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>\n"
                "# agent-sandbox-server==0.3.0\n"
                "RUN pip install --no-cache-dir requests\n"
                "WORKDIR /home/user/app\n"
                "COPY --chown=user:user commands.py .\n"
                "USER user\n",
                encoding="utf-8",
            )
            codes = {item.code for item in check_template.check_directory(dest)}
            self.assertIn("pinned-version", codes)

    def test_readme_client_package_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            readme = dest / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace("agent-sandbox-client", "the-sdk"),
                encoding="utf-8",
            )
            codes = {item.code for item in check_template.check_directory(dest)}
            self.assertIn("readme-client", codes)

            readme.write_text(
                SKELETON.joinpath("README.md").read_text(encoding="utf-8")
                + "\npython3 -m pip install agent-sandbox\n",
                encoding="utf-8",
            )
            messages = [item.message for item in check_template.check_directory(dest) if item.code == "readme-client"]
            self.assertTrue(any("unrelated" in message for message in messages))

            replaced = SKELETON.joinpath("README.md").read_text(encoding="utf-8")
            readme.write_text(replaced, encoding="utf-8")
            codes = {item.code for item in check_template.check_directory(dest)}
            self.assertNotIn("readme-client", codes)


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
            self.assertEqual(sum(1 for args in calls if "deploy" in args), 1)

    def test_stalled_push_retries_then_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "python-hello"
            shutil.copytree(ROOT / "python-hello", dest)
            shutil.rmtree(dest / "evidence", ignore_errors=True)
            calls: list[list[str]] = []

            def runner(args: list[str], timeout: float) -> Proc:
                del timeout
                calls.append(list(args))
                if "deploy" in args:
                    attempt = sum(1 for item in calls if "deploy" in item)
                    if attempt < 3:
                        return Proc(124, "", "no ACR push progress for 180s. Stopped process group 1.")
                    return Proc(0, json.dumps({"TemplateID": "tmpl-retry", "Status": "ready"}), "")
                if "create" in args:
                    return Proc(0, json.dumps({"ID": "sb-retry"}), "")
                if "run" in args:
                    return Proc(0, json.dumps({"result": "Hello, E2E!"}), "")
                return Proc(0, "", "")

            options = express_e2e.build_options(
                [str(dest), "--command", "hello", "--arg", "name=E2E", "--expect", "Hello, E2E!", "--push-retries", "2"]
            )
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_args: "Hello, E2E!")
            self.assertEqual(code, 0)
            self.assertEqual(sum(1 for args in calls if "deploy" in args), 3)
            self.assertIn("--verbose", calls[0])
            self.assertIn("--timeout", calls[0])

    def test_build_failure_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "python-hello"
            dest.mkdir()
            (dest / "template.yaml").write_text("name: python-hello\nversion: '1.0.0'\n", encoding="utf-8")
            calls: list[list[str]] = []

            def runner(args: list[str], timeout: float) -> Proc:
                del timeout
                calls.append(list(args))
                return Proc(1, "", "Docker build failed (exit 1)")

            options = express_e2e.build_options(
                [str(dest), "--command", "hello", "--push-retries", "2"]
            )
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_args: "Hello, E2E!")
            self.assertEqual(code, 1)
            self.assertEqual(len(calls), 1)


class MonitorTest(unittest.TestCase):
    def test_progress_resets_idle_timeout(self) -> None:
        script = "import time\nfor _ in range(4):\n    print('tick', flush=True)\n    time.sleep(0.2)\n"
        proc = express_e2e.run_monitored(
            [sys.executable, "-c", script],
            idle_timeout=1.5,
            wall_timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("tick", proc.stdout)

    def test_idle_timeout_kills_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "child"
            flag = Path(tmp) / "flag"
            script = (
                "import os, time, pathlib\n"
                "flag = pathlib.Path(os.environ['FLAG'])\n"
                "pid = os.fork()\n"
                "if pid == 0:\n"
                "    while True:\n"
                "        flag.write_text('alive')\n"
                "        time.sleep(0.1)\n"
                "pathlib.Path(os.environ['PIDFILE']).write_text(str(pid))\n"
                "time.sleep(30)\n"
            )
            env = os.environ.copy()
            env["FLAG"] = str(flag)
            env["PIDFILE"] = str(pidfile)
            proc = express_e2e.run_monitored(
                [sys.executable, "-c", script],
                idle_timeout=1.0,
                wall_timeout=10,
                marker="e2e-monitor-test",
                env=env,
            )
            self.assertEqual(proc.returncode, 124, proc.stderr)
            self.assertIn("no ACR push progress", proc.stderr)
            self.assertTrue(pidfile.is_file())
            child = int(pidfile.read_text(encoding="utf-8"))
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and not _process_dead(child):
                time.sleep(0.05)
            self.assertTrue(_process_dead(child), f"child {child} still alive")

    def test_wall_timeout_while_output_continues(self) -> None:
        script = "import time\nwhile True:\n    print('tick', flush=True)\n    time.sleep(0.05)\n"
        proc = express_e2e.run_monitored(
            [sys.executable, "-c", script],
            idle_timeout=5,
            wall_timeout=0.8,
        )
        self.assertEqual(proc.returncode, 124, proc.stderr)
        self.assertIn("wall clock", proc.stderr)

    def test_push_lock_is_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "push.lock"
            order: list[str] = []
            started = threading.Event()

            def hold() -> None:
                with express_e2e.acr_push_lock(path):
                    started.set()
                    order.append("a-in")
                    time.sleep(0.3)
                    order.append("a-out")

            thread = threading.Thread(target=hold)
            thread.start()
            self.assertTrue(started.wait(3))
            with express_e2e.acr_push_lock(path):
                order.append("b-in")
            thread.join(timeout=5)
            self.assertEqual(order, ["a-in", "a-out", "b-in"])


class ImageReportTest(unittest.TestCase):
    def test_render_lists_layers_and_guidance(self) -> None:
        text = image_size_report.render(
            [
                {"Size": "16.9kB", "CreatedBy": "COPY commands.py . # buildkit"},
                {"Size": "592MB", "CreatedBy": "RUN pip install --no-cache-dir something && npm install -g tool@1"},
                {"Size": "606MB", "CreatedBy": "COPY / / # buildkit"},
                {"Size": "0B", "CreatedBy": "ENV PATH=/usr/bin"},
            ],
            image="example:local",
            total_bytes=1_230_000_000,
            shared_with_base=2,
            base_layers=2,
            base_image="base:v0.0.49",
        )
        self.assertIn("592MB", text)
        self.assertIn("606MB", text)
        self.assertIn("shared with base:v0.0.49: 2 of 2", text)
        self.assertIn("commands.py", text)
        self.assertIn("--no-cache-dir", text)


if __name__ == "__main__":
    unittest.main()
