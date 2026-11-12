"""Canonical complete source manifest contract; no metadata is excluded."""
from __future__ import annotations
import hashlib
import json
try:
    from .template_application import _profile_module
except ImportError:
    from template_application import _profile_module

def manifest_contract_sha256(content: bytes) -> str:
    data=_profile_module.parse_yaml_v1(content)
    if not isinstance(data,dict):raise ValueError("manifest must be a mapping")
    data=dict(data)
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
