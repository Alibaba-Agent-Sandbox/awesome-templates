"""Controller ownership/privacy negatives; mocks do not certify actual OSS."""
import hashlib
import io
import json
import platform
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from prepare_steps import ROOT, parallel_assets, prepare
from step_asset_cache import AssetCache


class MissingBucket(Exception):
    pass


class Bucket:
    def __init__(self):
        self.exists = False
        self.objects = {}
        self.lost_create = False
        self.lost_upload = False
        self.deletions = []

    def get_bucket_acl(self):
        if not self.exists:
            raise MissingBucket()
        return SimpleNamespace(acl="private")

    def create_bucket(self, acl):
        assert acl == "private"
        if self.lost_create:
            raise TimeoutError("synthetic lost creation response")
        self.exists = True

    def put_object_from_file(self, key, path, headers):
        assert headers["x-oss-object-acl"] == "private"
        from pathlib import Path
        self.objects[key] = (Path(path).read_bytes(), headers)
        if self.lost_upload:
            raise TimeoutError("synthetic lost upload response")

    def head_object(self, key):
        content, headers = self.objects[key]
        return SimpleNamespace(content_length=len(content), headers=headers)

    def get_object_acl(self, key):
        return SimpleNamespace(acl="private")

    def sign_url(self, method, key, seconds):
        assert method == "GET" and seconds == 3600
        return "https://private.invalid/owned?authorization=synthetic-read-token"

    def delete_object(self, key):
        self.deletions.append(key)
        self.objects.pop(key, None)

    def object_exists(self, key):
        return key in self.objects

    def delete_bucket(self):
        assert not self.objects
        self.exists = False


def setup(monkeypatch, tmp_path):
    bucket = Bucket()
    sdk = SimpleNamespace(Auth=lambda *args: object(), Bucket=lambda *args, **kwargs: bucket,
                          BUCKET_ACL_PRIVATE="private", exceptions=SimpleNamespace(NoSuchBucket=MissingBucket))
    monkeypatch.setitem(sys.modules, "oss2", sdk)
    monkeypatch.setenv("ALICLOUD_ACCESS_KEY_ID", "synthetic-cache-key")
    monkeypatch.setenv("ALICLOUD_ACCESS_KEY_SECRET", "synthetic-cache-secret")
    directory = tmp_path / "cache"
    directory.mkdir()
    monkeypatch.setattr("step_asset_cache.tempfile.mkdtemp", lambda **kwargs: str(directory))
    cache = AssetCache("cn-hangzhou")
    content = b"fixed official public artifact"
    item = {"url": "https://github.com/example/project/releases/download/v1/artifact", "sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
    return cache, bucket, content, {platform.machine(): [item]}


def test_private_cache_cleanup_and_public_receipt_exclude_authorization(monkeypatch, tmp_path):
    cache, bucket, content, assets = setup(monkeypatch, tmp_path)
    with patch("step_asset_cache.urllib.request.urlopen", return_value=io.BytesIO(content)):
        private = cache.prepare(assets)
    assert "synthetic-read-token" in str(private)
    assert "synthetic-read-token" not in json.dumps(cache.public_proof())
    assert cache.cleanup() and cache.cleanup()
    assert not bucket.exists and not bucket.objects
    assert cache.public_proof()["cleanup_verified"]


def test_hash_failure_uploads_nothing_and_cleans_owned_bucket(monkeypatch, tmp_path):
    cache, bucket, content, assets = setup(monkeypatch, tmp_path)
    with patch("step_asset_cache.urllib.request.urlopen", return_value=io.BytesIO(b"wrong bytes")):
        with pytest.raises(RuntimeError, match="hash/size"):
            cache.prepare(assets)
    assert cache.cleanup() and not bucket.objects


def test_lost_upload_response_retains_exact_key_authority(monkeypatch, tmp_path):
    cache, bucket, content, assets = setup(monkeypatch, tmp_path)
    bucket.lost_upload = True
    with patch("step_asset_cache.urllib.request.urlopen", return_value=io.BytesIO(content)):
        with pytest.raises(TimeoutError):
            cache.prepare(assets)
    assert json.loads((cache.directory / "intent.json").read_text())["keys"]
    assert cache.cleanup() and len(bucket.deletions) == 1


def test_existing_bucket_is_never_adopted_or_deleted(monkeypatch, tmp_path):
    cache, bucket, content, assets = setup(monkeypatch, tmp_path)
    bucket.exists = True
    with pytest.raises(RuntimeError, match="existing"):
        cache.prepare(assets)
    assert cache.cleanup() and bucket.exists and not bucket.deletions


def test_unknown_create_absence_does_not_certify_cancellation(monkeypatch, tmp_path):
    cache, bucket, content, assets = setup(monkeypatch, tmp_path)
    bucket.lost_create = True
    with pytest.raises(TimeoutError):
        cache.prepare(assets)
    assert not cache.cleanup()
    assert not cache.public_proof()["cleanup_verified"]


def test_nonofficial_origin_is_refused_before_bucket_creation(monkeypatch, tmp_path):
    cache, bucket, content, assets = setup(monkeypatch, tmp_path)
    assets[platform.machine()][0]["url"] = "http://169.254.169.254/private"
    with pytest.raises(ValueError, match="official"):
        cache.prepare(assets)
    assert not bucket.exists and not cache.creation_attempted


def test_private_execution_urls_never_enter_public_build_provenance():
    source = ROOT / "goose"
    arch = platform.machine()
    urls = {item["url"]: "https://private.invalid/file?authorization=synthetic-read-token" for item in parallel_assets(source)[arch]}
    manifest, proof = prepare(source, asset_transport="oss", asset_cache={"architecture": arch, "urls": urls})
    assert proof["asset_transport"] == "oss"
    assert "synthetic-read-token" not in json.dumps(proof)
    assert "private.invalid" not in json.dumps(proof)
    assert manifest["build"]["steps"][-1] == {"type": "USER", "args": ["user"]}


@pytest.mark.parametrize('url',['https://s3.us-west-2.amazonaws.com/other/data-0.1.0.bundle','https://s3.us-west-2.amazonaws.com/appworld.dev/unreviewed.bundle','https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.1.0.bundle?credential=x'])
def test_appworld_transport_does_not_admit_other_s3_objects(monkeypatch,tmp_path,url):
    cache,bucket,content,assets=setup(monkeypatch,tmp_path)
    assets[platform.machine()][0]['url']=url
    with pytest.raises(ValueError,match='fixed official'):
        cache.prepare(assets)
    assert not bucket.exists and not bucket.objects and not cache.creation_attempted


def test_exact_official_appworld_bundle_retains_integrity_and_private_cleanup(monkeypatch,tmp_path):
    cache,bucket,content,assets=setup(monkeypatch,tmp_path)
    assets[platform.machine()][0]['url']='https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.1.0.bundle'
    with patch('step_asset_cache.urllib.request.urlopen',return_value=io.BytesIO(content)):
        cache.prepare(assets)
    assert cache.cleanup() and not bucket.exists and not bucket.objects
