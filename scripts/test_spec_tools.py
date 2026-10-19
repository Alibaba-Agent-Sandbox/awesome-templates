#!/usr/bin/env python3
"""Unit tests for the template checker and the Express harness."""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

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
    def test_same_day_versioned_receipts_are_immutable_and_require_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"_skeleton";shutil.copytree(SKELETON,dest)
            metadata=check_template.yaml.safe_load((dest/"template.yaml").read_text());version=str(metadata["version"])
            evidence=dest/"evidence";evidence.mkdir(exist_ok=True)
            old={"provider":"alicloud-express","template":"_skeleton","template_version":"0.0.1","passed":True,"cleanup_verified":True,
                 "commands":[{"ok":True,"via":"cli"},{"ok":True,"via":"sdk"}]}
            legacy=evidence/"express-2026-10-19.json";legacy.write_text(json.dumps(old));original=legacy.read_bytes()
            self.assertFalse(check_template._evidence_passes(dest,"alicloud-express"))
            current=dict(old,template_version=version,cleanup_verified=False)
            dated=evidence/"express-2026-10-19T180000Z.json";dated.write_text(json.dumps(current))
            self.assertFalse(check_template._evidence_passes(dest,"alicloud-express"))
            current["cleanup_verified"]=True;dated.write_text(json.dumps(current))
            self.assertTrue(check_template._evidence_passes(dest,"alicloud-express"))
            self.assertEqual(legacy.read_bytes(),original)

    def test_provider_preparation_hint_cannot_certify_a_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "_skeleton"
            shutil.copytree(SKELETON, dest)
            index = {"templates": [{"name": "_skeleton", "path": "_skeleton", "status": "experimental",
                "providers": {"alicloud-express": "provider-preparation-required"}}]}
            (root / "awesome-templates.yaml").write_text(check_template.yaml.safe_dump(index))
            path = dest / "README.md"
            path.write_text(re.sub(r"(?ms)^## Verified\n.*?(?=^## |\Z)",
                "## Verified\n\n| Provider | Date | Level |\n|---|---|---|\n| alicloud-express | 2026-10-19 | L2 |\n\n",
                path.read_text()))
            violations = check_template.check_directory(dest)
            self.assertTrue(any(v.code == "verified-evidence" for v in violations))
            self.assertFalse(check_template._evidence_passes(dest, "alicloud-express"))

    def test_catalog_capabilities_match_template_ignoring_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "example"
            shutil.copytree(SKELETON, dest)
            metadata = check_template.yaml.safe_load((dest / "template.yaml").read_text())
            metadata["name"] = "example"
            metadata["capabilities"] = ["shell", "files", "ports"]
            (dest / "template.yaml").write_text(check_template.yaml.safe_dump(metadata))
            for capabilities, rejected in ((["ports", "files", "shell"], False),
                                             (["ports"], True), ({"ports": True}, True)):
                with self.subTest(capabilities=capabilities):
                    (root / "awesome-templates.yaml").write_text(check_template.yaml.safe_dump({
                        "templates": [{"name": "example", "path": "example", "status": "experimental",
                                       "capabilities": capabilities}]}))
                    violations = check_template.check_directory(dest)
                    self.assertEqual(any(item.code == "index-capabilities" for item in violations), rejected)

    def test_http_section_requires_request_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            for filename, heading in (
                ("README.md", "Quick start (HTTP POST)"),
                ("README.zh-CN.md", "快速开始（HTTP POST）"),
            ):
                with self.subTest(filename=filename):
                    readme = dest / filename
                    original = readme.read_text(encoding="utf-8")
                    sections = check_template._sections(original)
                    readme.write_text(original.replace(sections[heading], "HTTP is available.\n\n"), encoding="utf-8")
                    violations = check_template.check_directory(dest)
                    self.assertTrue(any(v.code == "readme-http" and filename in v.message for v in violations))
                    readme.write_text(original, encoding="utf-8")

    def test_skeleton_conforms(self) -> None:
        violations = check_template.check_directory(SKELETON)
        self.assertEqual([str(item) for item in violations], [])

    def test_verified_provider_needs_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            readme = dest / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = re.sub(r"(?ms)^## Verified\n.*?(?=^## |\Z)",
                "## Verified\n\n| Provider | Date | Level | Evidence |\n|---|---|---|---|\n| alicloud-express | 2026-10-15 | L2 | evidence/express-2026-10-15.json |\n\n", text)
            readme.write_text(text, encoding="utf-8")
            zh = dest / "README.zh-CN.md"
            zh_text = zh.read_text(encoding="utf-8")
            zh_text = re.sub(r"(?ms)^## 已验证\n.*?(?=^## |\Z)",
                "## 已验证\n\n| Provider | Date | Level | Evidence |\n|---|---|---|---|\n| alicloud-express | 2026-10-15 | L2 | evidence/express-2026-10-15.json |\n\n", zh_text)
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
                        "template_version": str(check_template.yaml.safe_load((dest / "template.yaml").read_text())["version"]),
                        "sdk_version": "0.3.0",
                        "passed": True,
                        "cleanup_verified": True,
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

            evidence_file = evidence / "express-2026-10-15.json"
            original = json.loads(evidence_file.read_text(encoding="utf-8"))
            for field, value in (("template", "another-template"), ("template_version", "0.9.0")):
                with self.subTest(field=field):
                    evidence_file.write_text(json.dumps({**original, field: value}), encoding="utf-8")
                    codes = {item.code for item in check_template.check_directory(dest)}
                    self.assertIn("verified-evidence", codes)
            evidence_file.write_text(json.dumps(original), encoding="utf-8")

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
                if "--official-api" in args:
                    return Proc(0, "[]", "")
                if "deploy" in args:
                    return Proc(1, "", "BuildModeError: base must be a mapping")
                return Proc(0, "", "")

            options = express_e2e.build_options(
                [str(dest), "--command", "hello", "--arg", "name=E2E", "--expect", "Hello, E2E!"]
            )
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_: "Hello, E2E!", verify=lambda *_: True)
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
                if "--official-api" in args:
                    return Proc(0, "[]", "")
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
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_args: "Hello, E2E!", verify=lambda *_: True)
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
                if "--official-api" in args:
                    return Proc(0, "[]", "")
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
            code = express_e2e.execute(options, runner=runner, sdk=sdk, verify=lambda *_: True)
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
                if "--official-api" in args:
                    return Proc(0, "[]", "")
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
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_args: "Hello, E2E!", verify=lambda *_: True)
            self.assertEqual(code, 0)
            self.assertEqual(sum(1 for args in calls if "deploy" in args), 3)
            deploy_call = next(args for args in calls if "deploy" in args)
            self.assertIn("--verbose", deploy_call)
            self.assertIn("--timeout", deploy_call)

    def test_build_failure_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "python-hello"
            dest.mkdir()
            (dest / "template.yaml").write_text("name: python-hello\nversion: '1.0.0'\n", encoding="utf-8")
            calls: list[list[str]] = []

            def runner(args: list[str], timeout: float) -> Proc:
                del timeout
                calls.append(list(args))
                if "--official-api" in args:
                    return Proc(0, "[]", "")
                return Proc(1, "", "Docker build failed (exit 1)")

            options = express_e2e.build_options(
                [str(dest), "--command", "hello", "--push-retries", "2"]
            )
            code = express_e2e.execute(options, runner=runner, sdk=lambda *_args: "Hello, E2E!", verify=lambda *_: True)
            self.assertEqual(code, 1)
            self.assertEqual(sum("deploy" in args for args in calls), 1)


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


class ImageBuildContextTest(unittest.TestCase):
    def test_actual_template_contexts_preserve_heredocs_and_sdk_install(self) -> None:
        """Exercise the real context step; no Docker process is mocked or invoked."""
        import contextlib
        import io

        workflow = check_template.yaml.safe_load((ROOT / ".github/workflows/image-build.yml").read_text())
        job = workflow["jobs"]["image-build"]
        step = next(item for item in job["steps"] if item.get("name") == "Prepare the standalone template context")
        code = step["run"].split("python - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        templates = sorted(item["path"] for item in check_template.yaml.safe_load((ROOT / "awesome-templates.yaml").read_text())["templates"])
        self.assertEqual(job["strategy"]["matrix"]["template"], "${{ fromJSON(needs.plan.outputs.templates) }}")
        catalog = check_template.yaml.safe_load((ROOT / "awesome-templates.yaml").read_text())["templates"]
        self.assertEqual(set(templates), {item["path"] for item in catalog})
        with tempfile.TemporaryDirectory() as folder:
            runner = Path(folder)
            wheel_dir = runner / "server-wheel"
            wheel_dir.mkdir()
            # The prepare step only copies this opaque fixture; it never claims
            # that these bytes are an installed or executable server wheel.
            wheel = wheel_dir / "agent_sandbox_server-0.3.0-py3-none-any.whl"
            wheel.write_bytes(b"context-copy fixture, not an installable package")
            environment = {"RUNNER_TEMP": folder, "GITHUB_ENV": str(runner / "environment"),
                           "SERVER_SDK_SHA": "e2cb27e24fde0a67112f82b8d44af463445a5d1a"}
            for name in templates:
                with self.subTest(template=name), patch.dict(os.environ, {**environment, "TEMPLATE": str(ROOT / name)}):
                    with contextlib.redirect_stdout(io.StringIO()):
                        exec(compile(code, "image-build.yml::prepare", "exec"), {})
                    context = runner / ("image-context-" + name)
                    materialized = (context / "Dockerfile").read_bytes()
                    original = (ROOT / name / "Dockerfile").read_bytes()
                    self.assertEqual(materialized.replace(
                        b"FROM fc-e2b-registry.cn-hangzhou.cr.aliyuncs.com/runtime/base:v0.0.49",
                        b"FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>"), original)
                    self.assertEqual((context / wheel.name).read_bytes(), wheel.read_bytes())


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
    import test_express_cleanup
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
        unittest.defaultTestLoader.loadTestsFromModule(test_express_cleanup),
    ])
    raise SystemExit(not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful())
