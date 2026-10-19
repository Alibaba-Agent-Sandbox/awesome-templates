#!/usr/bin/env python3
"""Materialize this catalog's Dockerfile profile as explicit platform steps.

No Docker execution, cloud calls or directory upload occurs here. Only explicit
COPY inputs are embedded. Unsupported Docker instructions fail closed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
from string import Template
import zlib

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
BASE = "fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>"
BASE_PATH = "/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/.fce2b"


def instructions(text: str) -> list[tuple[str, str]]:
    lines = iter(text.splitlines())
    result = []
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Z]+)\s+(.*)$", line)
        if not match:
            raise ValueError("unsupported Dockerfile syntax")
        kind, value = match.groups()
        while value.endswith("\\"):
            value = value[:-1] + " " + next(lines).lstrip()
        heredoc = re.search(r"<<\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", value)
        if heredoc:
            for body in lines:
                value += "\n" + body
                if body == heredoc[2]:
                    break
            else:
                raise ValueError("unterminated Dockerfile heredoc")
        result.append((kind, value))
    return result


def _copy(source: Path, value: str, workdir: str, source_commit: str | None = None) -> tuple[str, dict[str, str]]:
    words = shlex.split(value)
    owner = None
    if words and words[0].startswith("--chown="):
        owner = words.pop(0).split("=", 1)[1]
    if len(words) < 2 or any(word.startswith("--") for word in words):
        raise ValueError("COPY supports only explicit paths and --chown")
    destination = Path(words[-1])
    if not destination.is_absolute():
        destination = Path(workdir) / destination
    sources = words[:-1]
    directory = len(sources) > 1 or words[-1].endswith("/") or words[-1] in {".", "./"}
    files = []
    fetched = []
    hashes = {}
    for item in sources:
        if any(char in item for char in "*?["):
            raise ValueError("COPY globs are unsupported except the injected server wheel")
        path = source / item
        if not path.exists() or path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError("COPY input is missing, symlinked or outside the template")
        paths = sorted(path.rglob("*")) if path.is_dir() else [path]
        for entry in paths:
            if entry.is_symlink():
                raise ValueError("symlinked COPY input is unsupported")
            if not entry.is_file():
                continue
            if entry.name == ".env" or entry.name.startswith(".env.") or entry.suffix in {".key", ".pem"}:
                raise ValueError("refusing a secret-named COPY input")
            data = entry.read_bytes()
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("COPY input exceeds the 2 MiB per-file step limit")
            target = (destination / entry.relative_to(path) if path.is_dir() else
                      destination / entry.name if directory else destination)
            digest = hashlib.sha256(data).hexdigest()
            mode = entry.stat().st_mode & 0o777
            relative = str(entry.relative_to(source))
            can_fetch = False
            if source_commit:
                remote_path = source.name + "/" + relative
                previous = subprocess.run(["git", "show", source_commit + ":" + remote_path],
                                          cwd=source, capture_output=True)
                can_fetch = previous.returncode == 0 and previous.stdout == data
            if can_fetch:
                fetched.append([str(target), remote_path, digest, mode])
            else:
                files.append([str(target), base64.b64encode(data).decode(), mode])
            hashes[relative] = digest
    packed = base64.b64encode(zlib.compress(json.dumps(files).encode(), 9)).decode()
    fetch = ""
    if fetched:
        fetch = ("cache=Path('/tmp/abx-step-source-" + str(source_commit) + ".tar.gz')\n"
            "if not cache.exists():\n"
            " for attempt in range(4):\n"
            "  try:\n"
            "   request=urllib.request.Request('https://codeload.github.com/Alibaba-Agent-Sandbox/awesome-templates/tar.gz/"
            + str(source_commit) + "',headers={'User-Agent':'AgentSandbox-Template'})\n"
            "   archive=urllib.request.urlopen(request,timeout=90).read(33554433)\n"
            "   if len(archive)>33554432: raise RuntimeError('source archive exceeds 32 MiB')\n"
            "   cache.write_bytes(archive);break\n"
            "  except (urllib.error.URLError,TimeoutError):\n"
            "   if attempt==3: raise RuntimeError('pinned source archive download failed') from None\n"
            "   time.sleep(2**attempt)\n"
            "archive=tarfile.open(cache,mode='r:gz')\n"
            "for name,relative,digest,mode in " + repr(fetched) + ":\n"
            " data=archive.extractfile('awesome-templates-" + str(source_commit) + "/'+relative).read(2097153)\n"
            " if len(data)>2097152 or hashlib.sha256(data).hexdigest()!=digest: raise RuntimeError('immutable COPY integrity mismatch')\n"
            " files.append([name,base64.b64encode(data).decode(),mode])\n"
            "archive.close()\n")
    code = ("import base64,json,os,pwd,grp,zlib,urllib.request,urllib.error,hashlib,tarfile,time\nfrom pathlib import Path\n"
            "files=json.loads(zlib.decompress(base64.b64decode(" + repr(packed) + ")))\n" + fetch +
            "for name,data,mode in files:\n"
            " p=Path(name); p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(base64.b64decode(data)); p.chmod(mode)\n")
    if owner:
        if not re.fullmatch(r"[a-z_][a-z0-9_-]*:[a-z_][a-z0-9_-]*", owner):
            raise ValueError("COPY owner must be an explicit user:group")
        user, group = owner.split(":")
        code += f" os.chown(p,pwd.getpwnam({user!r}).pw_uid,grp.getgrnam({group!r}).gr_gid)\n"
    return "python3 -c " + shlex.quote(code), hashes


def compact_run(command: str) -> str:
    if len(command.encode()) < 1024:
        return command
    packed = base64.b64encode(zlib.compress(command.encode(), 9)).decode()
    code = ("import base64,zlib,os;os.execv('/bin/sh',['sh','-c',"
            "zlib.decompress(base64.b64decode(" + repr(packed) + ")).decode()])")
    compact = "python3 -c " + shlex.quote(code)
    return compact if len(compact.encode()) < len(command.encode()) else command


def prepare(source: Path, *, region: str = "cn-hangzhou", tag: str = "v0.0.49",
            server_commit: str | None = None, source_commit: str | None = None,
            base_path: str | None = None, _inline: bool = True) -> tuple[dict, dict]:
    if not re.fullmatch(r"[a-z]+-[a-z]+(?:-\d+)?", region) or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("use an explicit Alibaba region and versioned base tag")
    if server_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", server_commit):
        raise ValueError("server source must be an immutable 40-character commit")
    source = source.resolve()
    if source_commit is None and source.parent == ROOT:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True)
        source_commit = head.stdout.strip() if head.returncode == 0 else None
    if source_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be an immutable 40-character commit")
    data = yaml.safe_load((source / "template.yaml").read_text())
    if base_path is None and tag != "v0.0.49":
        raise ValueError("an unverified base tag requires an explicit verified --base-path")
    build_env = {"PATH": base_path or BASE_PATH}
    # Express executes steps as user by default; Docker's build profile installs
    # dependencies as root and explicitly returns to USER user for the runtime.
    steps = [{"type": "USER", "args": ["root"]}]
    copied = {}
    workdir = "/"
    seen_from = False
    dockerfile = (source / "Dockerfile").read_text()
    def run_step(command: str) -> dict:
        # Native ENV configures the resulting runtime but did not affect RUN's
        # npm/PATH in the real platform probe. Recreate Docker build state explicitly.
        exports = "".join("export " + shlex.quote(key + "=" + val) + "\n" for key, val in build_env.items())
        directory = shlex.quote(workdir)
        return {"type": "RUN", "args": [exports + "mkdir -p " + directory + " || exit $?\ncd " + directory + " || exit $?\n" + command]}
    for kind, value in instructions(dockerfile):
        if kind == "FROM":
            if seen_from or value != BASE:
                raise ValueError("only the single-stage catalog Alibaba base profile is supported")
            seen_from = True
        elif kind == "COPY":
            if value == "*.whl /tmp/":
                continue  # Local source-wheel injection has no remote COPY context.
            command, hashes = _copy(source, value, workdir, None if _inline else source_commit)
            copied.update(hashes)
            steps.append(run_step(command))
        elif kind == "RUN":
            if "if ls /tmp/*.whl" in value:
                match = re.fullmatch(r"if ls /tmp/\*\.whl.*?; then\s+.*?else\s+(.*?)\s*;\s*fi(.*)", value, re.S)
                if not match:
                    raise ValueError("unknown server-wheel fallback; review it before generating steps")
                value = match[1] + match[2]
                if server_commit:
                    value, count = re.subn(r"(?<=python-sdk/archive/)[0-9a-f]{40}(?=\.tar\.gz)", server_commit, value)
                    if count != 1:
                        raise ValueError("expected one pinned server-source fallback")
            steps.append(run_step(value))
        elif kind == "WORKDIR":
            if not value.startswith("/"):
                raise ValueError("WORKDIR must be absolute")
            workdir = value
            steps.append({"type": kind, "args": [value]})
        elif kind == "ENV":
            pairs = []
            updates = {}
            for item in shlex.split(value):
                if "=" not in item:
                    raise ValueError("ENV requires explicit key=value declarations")
                key, val = item.split("=", 1)
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                    raise ValueError("invalid ENV name")
                try:
                    val = Template(val).substitute(build_env)
                except (KeyError, ValueError):
                    raise ValueError("ENV references an unverified base variable") from None
                pairs.extend([key, val])
                updates[key] = val
            build_env.update(updates)
            steps.append({"type": kind, "args": pairs})
        elif kind == "USER":
            steps.append({"type": kind, "args": [value]})
        elif kind == "EXPOSE":
            continue  # Manifest ports and platform commands remain authoritative.
        else:
            raise ValueError(f"unsupported Docker instruction: {kind}")
    if not seen_from or not steps or steps[-1] != {"type": "USER", "args": ["user"]}:
        raise ValueError("the catalog profile must end with USER user")
    if not _inline and source_commit:
        steps.insert(len(steps) - 1, {"type": "RUN", "args": ["rm -f /tmp/abx-step-source-" + source_commit + ".tar.gz"]})
    for step in steps:
        if step["type"] == "RUN":
            step["args"] = [compact_run(step["args"][0])]
    wire_bytes = len(json.dumps(steps, ensure_ascii=False).encode())
    if wire_bytes > 15000:
        if _inline and source_commit:
            return prepare(source, region=region, tag=tag, server_commit=server_commit,
                           source_commit=source_commit, base_path=base_path, _inline=False)
        raise ValueError("compressed steps exceed the provider's 16 KiB limit; use an immutable source archive or Dockerfile mode")
    data["base"] = BASE.replace("<region>", region).replace("<tag>", tag)
    data["build"] = {"mode": "steps", "steps": steps}
    provenance = {"schema_version": 1, "template": source.name,
                  "materializer_sha256": MATERIALIZER_SHA256,
                  "template_version": str(data["version"]), "build_mode": "steps",
                  "base_image": data["base"], "server_commit_override": server_commit,
                  "verified_base_path": base_path or BASE_PATH,
                  "copy_source_commit": None if _inline else source_commit,
                  "steps_json_bytes": wire_bytes,
                  "inputs_sha256": {"Dockerfile": hashlib.sha256(dockerfile.encode()).hexdigest(),
                                    "template.yaml": hashlib.sha256((source / "template.yaml").read_bytes()).hexdigest(),
                                    **copied}}
    manifest = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if len(manifest.encode()) > 8 * 1024 * 1024:
        raise ValueError("generated step manifest exceeds the 8 MiB local safety limit")
    provenance["generated_manifest_sha256"] = hashlib.sha256(manifest.encode()).hexdigest()
    return data, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New standalone staging directory")
    parser.add_argument("--region", default="cn-hangzhou")
    parser.add_argument("--base-tag", default="v0.0.49")
    parser.add_argument("--base-path", help="Verified PATH when using a different base-image tag")
    parser.add_argument("--server-commit")
    parser.add_argument("--source-commit", help="Immutable public source; unchanged COPY files are fetched and hash-checked")
    args = parser.parse_args()
    data, provenance = prepare(args.template, region=args.region, tag=args.base_tag,
                               server_commit=args.server_commit, source_commit=args.source_commit,
                               base_path=args.base_path)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "template.yaml").write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    (args.output / "steps-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Prepared {args.template.name}: {len(data['build']['steps'])} explicit steps; no cloud call")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
