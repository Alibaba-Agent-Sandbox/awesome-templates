#!/usr/bin/env python3
"""Unit tests for the template checker and the Express harness."""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import check_template
import express_e2e
import image_size_report
from test_template_application import ApplicationContractTest  # noqa: F401 — discovered by unittest

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
    def test_native_no_ask_flag_is_not_a_credential_but_secret_prefix_remains_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"commands.py"
            for literal,rejected in [("--no-ask-user",False),("sk-"+"synthetic-example",True),("ghp_"+"synthetic-example",True)]:
                with self.subTest(literal=literal):
                    path.write_text("value="+repr(literal)+"\n")
                    violations=[];check_template._check_commands(path,violations)
                    self.assertEqual(any(v.code=="secrets" for v in violations),rejected)

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
            self.assertFalse(check_template._evidence_passes(dest,"alicloud-express"))
            self.assertEqual(legacy.read_bytes(),original)
    def test_fc_resource_profile_rejects_actual_ocr_ratio_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            for cpu, memory, valid in [(2,1024,False),(1,1024,True),(2,2048,True),(1,4160,False),(1,1025,False)]:
                with self.subTest(cpu=cpu,memory=memory):
                    data=check_template.yaml.safe_load((dest/"template.yaml").read_text())
                    data["resources"]={"cpu":cpu,"memory":memory}
                    (dest/"template.yaml").write_text(check_template.yaml.safe_dump(data))
                    errors=[v for v in check_template.check_directory(dest) if v.code=="yaml-resources"]
                    self.assertEqual(not errors,valid)

    def test_provider_preparation_hint_cannot_certify_a_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "_skeleton"
            shutil.copytree(SKELETON, dest)
            index = {"templates": [{"name": "_skeleton", "path": "_skeleton", "status": "experimental",
                "providers": {"alicloud-express": "provider-preparation-required"}}]}
            (root / "awesome-templates.yaml").write_text(check_template.yaml.safe_dump(index))
            path = dest / "README.md"
            path.write_text(path.read_text() +
                "\n## Verified\n\n| Provider | Date | Level |\n|---|---|---|\n| alicloud-express | 2026-10-19 | L2 |\n")
            violations = check_template.check_directory(dest)
            self.assertTrue(any(v.code == "verified-evidence" for v in violations))
            self.assertFalse(check_template._evidence_passes(dest, "alicloud-express"))

    def test_catalog_retired_compatibility_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "example"
            shutil.copytree(SKELETON, dest)
            metadata = check_template.yaml.safe_load((dest / "template.yaml").read_text())
            metadata["name"] = "example"
            (dest / "template.yaml").write_text(check_template.yaml.safe_dump(metadata))
            for key in ("capabilities", "tested_on", "providers"):
                with self.subTest(key=key):
                    row = {"name": "example", "path": "example", "status": "experimental", key: []}
                    (root / "awesome-templates.yaml").write_text(check_template.yaml.safe_dump({"schema_version": 2, "templates": [row]}))
                    self.assertIn("index-workflow", {item.code for item in check_template.check_directory(dest)})

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

    def test_consumer_readme_does_not_require_engineering_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            for filename, headings in (
                ("README.md", ("Verified", "Historical verification", "Secondary development")),
                ("README.zh-CN.md", ("已验证", "历史验收", "二次开发")),
            ):
                readme = dest / filename
                text = readme.read_text(encoding="utf-8")
                for heading in headings:
                    text = re.sub(r"(?ms)^## " + re.escape(heading) + r"\n.*?(?=^## |\Z)", "", text)
                readme.write_text(text, encoding="utf-8")
            self.assertEqual(check_template.check_directory(dest), [])
            self.assertFalse(check_template._evidence_passes(dest, "alicloud-express"))

    def test_skeleton_conforms(self) -> None:
        violations = check_template.check_directory(SKELETON)
        self.assertEqual([str(item) for item in violations], [])

    def test_verified_provider_needs_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            readme = dest / "README.md"
            text = readme.read_text(encoding="utf-8")
            text += "\n## Verified\n\n| Provider | Date | Level | Evidence |\n|---|---|---|---|\n| alicloud-express | 2026-10-15 | L2 | evidence/express-2026-10-15.json |\n"
            readme.write_text(text, encoding="utf-8")
            zh = dest / "README.zh-CN.md"
            zh_text = zh.read_text(encoding="utf-8")
            zh_text += "\n## 已验证\n\n| Provider | Date | Level | Evidence |\n|---|---|---|---|\n| alicloud-express | 2026-10-15 | L2 | evidence/express-2026-10-15.json |\n"
            zh.write_text(zh_text, encoding="utf-8")
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
            self.assertIn("verified-evidence", codes)

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

    def test_all_rejects_missing_spec_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            metadata = dest / "template.yaml"
            data = check_template.yaml.safe_load(metadata.read_text(encoding="utf-8"))
            data.pop("spec_version", None)
            metadata.write_text(check_template.yaml.safe_dump(data), encoding="utf-8")
            self.assertEqual(check_template.main(["--all", "--root", tmp]), 1)

    def test_public_server_package_pin_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            path = dest / "Dockerfile"
            text = path.read_text()
            self.assertIn('agent-sandbox-server==0.4.0a6', text)
            self.assertEqual(check_template.check_directory(dest), [])
            path.write_text(text.replace('agent-sandbox-server==0.4.0a6', 'agent-sandbox-server'))
            self.assertIn('server-package-pin', {item.code for item in check_template.check_directory(dest)})

    def test_retired_server_archive_is_not_a_public_package_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "_skeleton"
            shutil.copytree(SKELETON, dest)
            path = dest / "Dockerfile"
            path.write_text(path.read_text().replace('agent-sandbox-server==0.4.0a6', 'agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/' + 'a'*40 + '.tar.gz#subdirectory=server-sdk'))
            self.assertIn('server-package-pin', {item.code for item in check_template.check_directory(dest)})

    def test_declared_profile_requires_same_published_server_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / '_skeleton'
            shutil.copytree(SKELETON, dest)
            metadata = dest / 'template.yaml'
            data = check_template.yaml.safe_load(metadata.read_text())
            data['build_profiles'] = {'portable': {'dockerfile': 'Dockerfile.portable', 'context': '.'}}
            metadata.write_text(check_template.yaml.safe_dump(data))
            profile = dest / 'Dockerfile.portable'
            original = (dest / 'Dockerfile').read_text()
            profile.write_text(original)
            self.assertEqual(check_template.check_directory(dest), [])
            for pin in ['agent-sandbox-server', 'agent-sandbox-server==0.4.0a1',
                        'agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/' + 'a'*40 + '.tar.gz#subdirectory=server-sdk']:
                profile.write_text(original.replace('agent-sandbox-server==0.4.0a6', pin))
                self.assertIn('server-package-pin', {v.code for v in check_template.check_directory(dest)})

    def test_hash_enforced_local_lock_requires_every_pin_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"_skeleton";shutil.copytree(SKELETON,dest)
            path=dest/"requirements.lock";digest="a"*64
            base=(dest/"Dockerfile").read_text()
            copied="COPY requirements.lock /tmp/requirements.lock\n"
            install="RUN python3 -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock\n"
            for content,extra,accepted in [
                ("example==1.2.3 --hash=sha256:"+digest+"\n","",True),
                ("example==1.2.3 --hash=sha256:"+digest+"\nother>=1 --hash=sha256:"+digest+"\n","",False),
                ("example==1.2.3\n","",False),
                ("--extra-index-url https://example.invalid\nexample==1.2.3 --hash=sha256:"+digest+"\n","",False),
                ("example==1.2.3 --hash=sha256:"+digest+"\n"," unpinned-package",False),
            ]:
                with self.subTest(content=content,extra=extra):
                    path.write_text(content)
                    (dest/"Dockerfile").write_text(base+copied+install.rstrip()+extra+"\n")
                    codes={v.code for v in check_template.check_directory(dest)}
                    self.assertEqual("pinned-version" not in codes,accepted)
            path.write_text("example==1.2.3 --hash=sha256:"+digest+"\n")
            for malformed in [install.replace("--require-hashes ",""), install.replace("/tmp/requirements.lock","/tmp/other.lock")]:
                (dest/"Dockerfile").write_text(base+copied+malformed)
                self.assertIn("pinned-version",{v.code for v in check_template.check_directory(dest)})

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


class MonitorTest(unittest.TestCase):
    def test_progress_resets_idle_timeout(self) -> None:
        script = "import time\nfor _ in range(10):\n    print('tick', flush=True)\n    time.sleep(0.2)\n"
        proc = express_e2e.run_monitored(
            [sys.executable, "-c", script],
            idle_timeout=0.5,
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
                env=env,
            )
            self.assertEqual(proc.returncode, 124, proc.stderr)
            self.assertIn("no process output progress", proc.stderr)
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



class ImageBuildContextTest(unittest.TestCase):
    def test_actual_contexts_preserve_heredocs_and_public_package_install(self) -> None:
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
            environment = {"RUNNER_TEMP": folder, "GITHUB_ENV": str(runner / "environment")}
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
                    self.assertFalse(list(context.glob("*.whl")))
                    self.assertIn(b'pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"', materialized)


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
