"""Bind CI Docker archives to the current public source before cloud registration."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import shlex
import yaml

try:
    from .prepare_steps import instructions
    from .server_package import server_version
except ImportError:
    from prepare_steps import instructions
    from server_package import server_version

PUBLIC_PROOF_KEYS = {
    'schema_version','verification_type','template','template_version','github_repository',
    'source_head_commit','checkout_commit','workflow_run_id','artifact_id','archive_sha256',
    'image_config_sha256','pushed_image_digest','server_package_version','context_sha256',
    'artifact_verified','image_context_verified','image_non_root','registry_push_verified',
    'registry_private_repo_verified','registry_credentials_storage',
    'registration_reference_type','tag_digest_verified_before_registration','tag_digest_verified_after_runtime',
}


def validate_resources(config: dict) -> None:
    resources=config.get('resources',{});cpu=resources.get('cpu');memory=resources.get('memory')
    if (not isinstance(cpu,int) or isinstance(cpu,bool) or cpu<1 or not isinstance(memory,int)
        or isinstance(memory,bool) or memory%64 or not 1024*cpu<=memory<=4096*cpu):
        raise ValueError('Alibaba FC requires64MiB memory multiples and1..4GiB per vCPU')


def context_sha256(source: Path) -> dict[str,str]:
    source=source.resolve()
    dockerfile=(source/'Dockerfile').read_bytes()
    result={'Dockerfile':hashlib.sha256(dockerfile).hexdigest()}
    if (source/'.dockerignore').exists():
        result['.dockerignore']=hashlib.sha256((source/'.dockerignore').read_bytes()).hexdigest()
    manifest=yaml.safe_load((source/'template.yaml').read_text())
    result['template.yaml:contract']=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for kind,value in instructions(dockerfile.decode()):
        if kind!='COPY':continue
        words=shlex.split(value)
        if words and words[0].startswith('--chown='):words.pop(0)
        if len(words)<2 or any(w.startswith('--') for w in words):raise ValueError('unsupported image COPY profile')
        for name in words[:-1]:
            if any(c in name for c in '*?['):raise ValueError('image context COPY must be explicit')
            path=source/name
            if not path.exists() or path.is_symlink() or not path.resolve().is_relative_to(source):raise ValueError('image context escapes source or is missing')
            files=sorted(path.rglob('*')) if path.is_dir() else [path]
            for entry in files:
                if entry.is_symlink():raise ValueError('symlinked image COPY input')
                if not entry.is_file():continue
                if entry.name=='.env' or entry.name.startswith('.env.') or entry.suffix in {'.pem','.key'}:raise ValueError('secret-named image COPY input')
                with entry.open('rb') as stream:result[str(entry.relative_to(source))]=hashlib.file_digest(stream,'sha256').hexdigest()
    return result


def validate_proof(source: Path, proof: dict, image_ref: str) -> dict:
    if not isinstance(proof,dict) or set(proof)-PUBLIC_PROOF_KEYS:raise ValueError('image proof contains unapproved fields')
    if not re.fullmatch(r'registry\.[a-z0-9-]+\.aliyuncs\.com/[a-z0-9_.-]+/e2e-ci-image-[a-f0-9]{16}:review',image_ref):raise ValueError('a nonce-owned personal ACR review tag is required')
    if proof.get('registration_reference_type')!='owned tag with digest readback' or proof.get('tag_digest_verified_before_registration') is not True:
        raise ValueError('owned image tag needs independently read-back digest before registration')
    config=yaml.safe_load((source/'template.yaml').read_text())
    validate_resources(config)
    if proof.get('schema_version')!=1 or proof.get('verification_type')!='ci-docker-archive':raise ValueError('unsupported image proof schema')
    if proof.get('template')!=config['name'] or proof.get('template_version')!=str(config['version']):raise ValueError('image proof template/version mismatch')
    if proof.get('github_repository','').lower()!='alibaba-agent-sandbox/awesome-templates':raise ValueError('image proof repository mismatch')
    for key in ['source_head_commit','checkout_commit']:
        if not re.fullmatch(r'[a-f0-9]{40}',str(proof.get(key,''))):raise ValueError('image proof lacks immutable source')
    for key in ['archive_sha256','image_config_sha256']:
        if not re.fullmatch(r'[a-f0-9]{64}',str(proof.get(key,''))):raise ValueError('image proof lacks checked bytes')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',str(proof.get('pushed_image_digest',''))):raise ValueError('image proof lacks a checked registry digest')
    if proof.get('server_package_version')!=server_version(source):raise ValueError('image server package differs from declared version')
    for key in ['artifact_verified','image_context_verified','image_non_root','registry_push_verified','registry_private_repo_verified']:
        if proof.get(key) is not True:raise ValueError('required image proof is not verified: '+key)
    if proof.get('registry_credentials_storage')!='anonymous RAM fd':raise ValueError('image credential storage must remain in RAM')
    if proof.get('context_sha256')!=context_sha256(source):raise ValueError('current image build/runtime inputs differ from verified source')
    for key in ['workflow_run_id','artifact_id']:
        if not str(proof.get(key,'')).isdigit():raise ValueError('image proof lacks public CI identity')
    return dict(proof)
