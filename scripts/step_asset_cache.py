"""Temporary private OSS transport for verified public build archives.

Operator credentials remain local. The private execution recipe receives only
short-lived read URLs for this run's immutable public artifacts. Neither signed
URLs nor resource identifiers are returned by public_proof().
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import tempfile
import time
import urllib.request
from urllib.parse import urlsplit


try:
    from .step_assets import reviewed_muse_native, reviewed_asset_limit, reviewed_cursor_native, reviewed_devin_native, reviewed_download_headers
except ImportError:
    from step_assets import reviewed_muse_native, reviewed_asset_limit, reviewed_cursor_native, reviewed_devin_native, reviewed_download_headers


@contextmanager
def upload_slot():
    """Bound controller disk use across independent uniquely owned cloud runs."""
    with Path("/tmp/abx-step-asset-upload.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def verify_compressed_input(path: Path, item: dict) -> dict:
    """Rehash unchanged original bytes without allocating a full raw disk copy."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > reviewed_asset_limit(item):
        raise ValueError("invalid bounded local compressed public input")
    digest = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    size = 0
    deadline = time.monotonic() + 900
    with gzip.open(path, "rb") as source:
        while block := source.read(1024 * 1024):
            size += len(block)
            if size > item["size"] or size > reviewed_asset_limit(item) or time.monotonic() > deadline:
                raise RuntimeError("bounded compressed original input exceeded")
            digest.update(block)
            md5.update(block)
    if size != item["size"] or digest.hexdigest() != item["sha256"]:
        raise RuntimeError("compressed original input size/SHA256 mismatch")
    return {"size": size, "md5": base64.b64encode(md5.digest()).decode()}


class AssetCache:
    def __init__(self, region: str):
        if not re.fullmatch(r"[a-z]+-[a-z]+(?:-\d+)?", region):
            raise ValueError("an explicit Alibaba region is required")
        import oss2
        self.sdk = oss2
        self.architecture = platform.machine()
        self.directory = Path(tempfile.mkdtemp(prefix="abx-private-step-cache-"))
        self.directory.chmod(0o700)
        self.name = "abx-step-assets-" + secrets.token_hex(12)
        endpoint = "https://oss-" + region + ".aliyuncs.com"
        auth = oss2.Auth(os.environ["ALICLOUD_ACCESS_KEY_ID"], os.environ["ALICLOUD_ACCESS_KEY_SECRET"])
        self.bucket = oss2.Bucket(auth, endpoint, self.name, connect_timeout=60)
        self.keys = []
        self.urls = {}
        self.created = False
        self.creation_attempted = False
        self.preflight_absent = False
        self.cleanup_verified = False
        self.archives = []
        self.private_acl_verified = False
        self.save()

    def save(self):
        path = self.directory / "intent.json"
        descriptor = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"bucket": self.name, "keys": self.keys, "created": self.created,
                       "creation_attempted": self.creation_attempted,
                       "preflight_absent": self.preflight_absent,
                       "cleanup_verified": self.cleanup_verified}, stream)

    def prepare(self, assets: dict) -> dict:
        allowed = {"github.com", "codeload.github.com", "static.rust-lang.org", "go.dev", "files.pythonhosted.org", "cdn.playwright.dev", "nodejs.org"}
        for item in assets[self.architecture]:
            url = urlsplit(item["url"])
            muse_native = reviewed_muse_native(item)
            official_origin = muse_native or reviewed_cursor_native(item) or reviewed_devin_native(item) or url.hostname in allowed or item["url"] == "https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.1.0.bundle"
            if url.scheme != "https" or not official_origin or url.username or url.password or (url.query and not muse_native) or url.fragment:
                raise ValueError("only fixed official public archive origins may enter the private cache")
            if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                raise ValueError("an exact archive SHA256 is required")
        # A prior exact-name absence readback prevents adopting an existing bucket.
        try:
            self.bucket.get_bucket_acl()
        except self.sdk.exceptions.NoSuchBucket:
            self.preflight_absent = True
        else:
            raise RuntimeError("refusing an existing asset-cache bucket")
        self.creation_attempted = True
        self.save()
        self.bucket.create_bucket(self.sdk.BUCKET_ACL_PRIVATE)
        self.created = True
        self.save()
        if self.bucket.get_bucket_acl().acl != "private":
            raise RuntimeError("private asset-cache ACL was not independently verified")
        self.private_acl_verified = True
        for item in assets[self.architecture]:
            with upload_slot():
                compressed_directory = os.environ.get("ABX_STEP_LOCAL_GZIP_DIR")
                compressed = Path(compressed_directory) / (item["sha256"] + ".gz") if compressed_directory else None
                if reviewed_muse_native(item) and compressed is not None and compressed.is_file():
                    observed = verify_compressed_input(compressed, item)
                    key = "owned/" + item["sha256"]
                    self.keys.append(key)
                    self.save()
                    # OSS verifies Content-MD5 against the complete decoded byte stream;
                    # the original installer rechecks its published SHA256 at the target.
                    with gzip.open(compressed, "rb") as decoded:
                        self.bucket.put_object(key, self.sdk.SizedFileAdapter(decoded, observed["size"]), headers={
                            "x-oss-object-acl": "private", "x-oss-meta-sha256": item["sha256"],
                            "Content-MD5": observed["md5"]})
                    head = self.bucket.head_object(key)
                    if head.content_length != observed["size"] or head.headers.get("x-oss-meta-sha256") != item["sha256"]:
                        raise RuntimeError("uploaded compressed-source original metadata mismatch")
                    if self.bucket.get_object_acl(key).acl != "private":
                        raise RuntimeError("uploaded original is not private")
                    self.urls[item["url"]] = self.bucket.sign_url("GET", key, 3600)
                    self.archives.append({"url": item["url"], "sha256": item["sha256"], "size": observed["size"],
                                          "controller_input": "streamed verified gzip of unchanged original bytes; OSS Content-MD5 enforced"})
                    continue
                archive = self.directory / "archive"
                sha256 = hashlib.sha256()
                md5 = hashlib.md5(usedforsecurity=False)
                size = 0
                deadline = time.monotonic() + 900
                try:
                    local_directory = os.environ.get("ABX_STEP_LOCAL_ARCHIVE_DIR")
                    local = Path(local_directory) / item["sha256"] if local_directory else None
                    headers=reviewed_download_headers(item)
                    request=urllib.request.Request(item['url'],headers=headers)if headers else item['url']
                    stream = local.open("rb") if local and local.is_file() else urllib.request.urlopen(request, timeout=120)
                    with stream as response, archive.open("xb") as output:
                        while block := response.read(1024 * 1024):
                            size += len(block)
                            if size > reviewed_asset_limit(item) or time.monotonic() > deadline:
                                raise RuntimeError("official cache input exceeds archive budget")
                            sha256.update(block)
                            md5.update(block)
                            output.write(block)
                    expected_size = item.get("size", item.get("bytes"))
                    if sha256.hexdigest() != item["sha256"] or expected_size is not None and size != expected_size:
                        raise RuntimeError("official cache input hash/size mismatch")
                    key = "owned/" + item["sha256"]
                    # Save before upload: a lost response must not lose ownership.
                    self.keys.append(key)
                    self.save()
                    self.bucket.put_object_from_file(key, str(archive), headers={
                        "x-oss-object-acl": "private", "x-oss-meta-sha256": item["sha256"],
                        "Content-MD5": base64.b64encode(md5.digest()).decode()})
                    observed = self.bucket.head_object(key)
                    if observed.content_length != size or observed.headers.get("x-oss-meta-sha256") != item["sha256"]:
                        raise RuntimeError("uploaded asset-cache metadata mismatch")
                    if self.bucket.get_object_acl(key).acl != "private":
                        raise RuntimeError("uploaded asset is not private")
                    self.urls[item["url"]] = self.bucket.sign_url("GET", key, 3600)
                    self.archives.append({"url": item["url"], "sha256": item["sha256"], "size": size})
                finally:
                    archive.unlink(missing_ok=True)
        return {"architecture": self.architecture, "urls": self.urls}

    def cleanup(self) -> bool:
        if self.cleanup_verified:
            return True
        if not self.created:
            if not self.creation_attempted:
                self.cleanup_verified = True
                self.save()
                return True
            if not self.preflight_absent:
                return False
            try:
                self.bucket.get_bucket_acl()
            except self.sdk.exceptions.NoSuchBucket:
                # A lost create response may still complete later. Absence alone
                # does not establish cancellation of that unknown operation.
                self.save()
                return False
            self.created = True
        for key in self.keys:
            self.bucket.delete_object(key)
            if self.bucket.object_exists(key):
                return False
        self.bucket.delete_bucket()
        try:
            self.bucket.get_bucket_acl()
        except self.sdk.exceptions.NoSuchBucket:
            self.cleanup_verified = True
        self.save()
        return self.cleanup_verified

    def public_proof(self) -> dict:
        return {"service": "Alibaba Cloud OSS", "private_acl_verified": self.private_acl_verified,
                "archives": self.archives, "signed_get_ttl_seconds": 3600,
                "cleanup_verified": self.cleanup_verified}
