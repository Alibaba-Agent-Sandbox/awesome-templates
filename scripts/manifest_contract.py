"""Canonical complete source manifest contract; no metadata is excluded."""
from __future__ import annotations
import hashlib
import json
import yaml

def manifest_contract_sha256(content: bytes) -> str:
    data=yaml.safe_load(content)
    if not isinstance(data,dict):raise ValueError("manifest must be a mapping")
    data=dict(data)
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
