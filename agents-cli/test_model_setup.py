"""Explicit native profile preparation preserves caller configuration and secrets."""
import importlib.util,os,tomllib
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('agents_setup',Path(__file__).with_name('commands.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
@pytest.fixture
def settings(tmp_path,monkeypatch):
 home=tmp_path/'codex-home';monkeypatch.setenv('CODEX_HOME',str(home));monkeypatch.setenv('OPENAI_API_KEY','synthetic-never-written-model-key');monkeypatch.setenv('OPENAI_BASE_URL','https://approved.example.invalid/v1');return home

def test_explicit_profile_uses_native_responses_and_never_serializes_key(settings):
 assert c.agents_configure_codex()=={'configured':True,'wire_api':'responses','credential_written':False}
 p=settings/'config.toml';before=p.stat().st_mtime_ns;raw=p.read_text();d=tomllib.loads(raw);provider=d['model_providers'][d['model_provider']]
 assert provider['base_url']=='https://approved.example.invalid/v1' and provider['env_key']=='OPENAI_API_KEY'
 assert provider['wire_api']=='responses' and provider['supports_websockets']is False
 assert 'synthetic-never-written-model-key'not in raw and p.stat().st_mode&0o777==0o600
 c.agents_configure_codex();assert p.stat().st_mtime_ns==before

def test_existing_foreign_config_is_preserved(settings):
 settings.mkdir();p=settings/'config.toml';p.write_text('caller setting')
 with pytest.raises(ValueError,match='existing Codex config differs'):c.agents_configure_codex()
 assert p.read_text()=='caller setting'

def test_symlink_config_target_is_never_overwritten(settings,tmp_path):
 settings.mkdir();target=tmp_path/'unrelated';target.write_text('caller setting');(settings/'config.toml').symlink_to(target)
 with pytest.raises(ValueError,match='symlinked'):c.agents_configure_codex()
 assert target.read_text()=='caller setting'

@pytest.mark.parametrize('base',['','file:///tmp/x','https://user:key@example.invalid','https://example.invalid/v1?key=x'])
def test_invalid_endpoint_does_not_create_profile(settings,base,monkeypatch):
 monkeypatch.setenv('OPENAI_BASE_URL',base)
 with pytest.raises(ValueError,match='explicit HTTP'):c.agents_configure_codex()
 assert not settings.exists()
