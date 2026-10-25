"""Read-only cloud authorization planning and shared owned ACR cleanup.

Current cloud acceptance runs through public-template-launch.yml and
public_launch_e2e.py. This module never launches an old pinned deployment path.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import uuid
import yaml

def save(path: Path, data: dict, *, private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    if private:
        temporary.chmod(0o600)
    temporary.replace(path)

def select(text: str) -> list[str]:
    root = Path(__file__).resolve().parents[1]
    catalog = yaml.safe_load((root / "awesome-templates.yaml").read_text())
    available = {item["path"] for item in catalog["templates"] if item.get("kind", "source") == "source"}
    names = sorted(available) if text == "all" else text.split(",")
    if not names or len(set(names)) != len(names) or any(name not in available for name in names):
        raise ValueError("select unique current source template names or all")
    return names


def authorization(env: dict[str, str]) -> tuple[bool, list[str]]:
    names = select(env.get("REVIEW_TEMPLATES", "python-hello"))
    head = env.get("REVIEW_HEAD", "")
    enabled = (env.get("REVIEW_ENABLE") == "approved" and
               re.fullmatch(r"[0-9a-f]{40}", head) is not None and
               env.get("REVIEW_APPROVED_SHA") == head and
               env.get("REVIEW_SAME_REPOSITORY") == "true")
    return enabled, names

def plan() -> int:
    enabled, names = authorization(dict(os.environ))
    save(Path("canonical-authorization.json"), {"result": "AUTHORIZED" if enabled else "BLOCKED",
        "cloud_executed": False, "entry_point": "public-template-launch.yml", "reason": "exact-head opt-in accepted" if enabled else
        "default disabled, unapproved workflow head or fork; no cloud acceptance",
        "templates": names})
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        stream.write("enabled=" + str(enabled).lower() + "\n")
        stream.write("templates=" + json.dumps(names) + "\n")
    print("AUTHORIZED reviewed head; use public-template-launch for cloud execution" if enabled else "BLOCKED: no cloud execution authorized", flush=True)
    return 0

def registry(method: str, path: str) -> None:
    """Official ACR 2016-06-07 ROA DeleteImage/DeleteRepo/GetRepo paths."""
    headers = {"Accept": "application/json", "Content-Type": "application/json",
        "Date": format_datetime(datetime.now(timezone.utc), usegmt=True),
        "x-acs-signature-method": "HMAC-SHA1", "x-acs-signature-nonce": str(uuid.uuid4()),
        "x-acs-signature-version": "1.0", "x-acs-version": "2016-06-07"}
    canonical = "".join(k + ":" + headers[k] + "\n" for k in sorted(headers) if k.startswith("x-acs-"))
    signed = method + "\napplication/json\n\napplication/json\n" + headers["Date"] + "\n" + canonical + path
    signature = base64.b64encode(hmac.new(os.environ["ALICLOUD_ACCESS_KEY_SECRET"].encode(), signed.encode(), hashlib.sha1).digest()).decode()
    headers["Authorization"] = "acs " + os.environ["ALICLOUD_ACCESS_KEY_ID"] + ":" + signature
    request = urllib.request.Request("https://cr.cn-hangzhou.aliyuncs.com" + path, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FileNotFoundError("owned registry object absent") from None
        raise RuntimeError("ACR API HTTP " + str(exc.code)) from None

def delete_absent(path: str) -> None:
    try:
        registry("DELETE", path)
    except FileNotFoundError:
        pass
    for attempt in range(15):
        try:
            registry("GET", path)
        except FileNotFoundError:
            return
        time.sleep(2)
    raise RuntimeError("owned registry deletion not confirmed")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["plan"])
    parser.parse_args()
    return plan()


if __name__ == "__main__":
    raise SystemExit(main())
