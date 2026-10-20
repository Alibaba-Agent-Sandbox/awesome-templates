"""Canonical source manifest contract: only provider qualification is excluded."""
from __future__ import annotations
import hashlib
import json
import yaml

def manifest_contract_sha256(content: bytes) -> str:
    data=yaml.safe_load(content)
    if not isinstance(data,dict):raise ValueError("manifest must be a mapping")
    data=dict(data);data.pop("tested_on",None)
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
