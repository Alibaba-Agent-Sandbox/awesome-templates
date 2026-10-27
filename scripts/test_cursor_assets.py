"""Exact artifact/ordinary-client transport boundaries; no vendor or cloud call."""
import json
import pytest
from prepare_steps import ROOT,parallel_assets
from step_assets import CURSOR_NATIVE,MAX_BYTES,reviewed_asset_limit,reviewed_cursor_native,reviewed_download_headers

def test_exact_cursor_artifact_uses_normal_public_client_without_larger_budget():
    item=parallel_assets(ROOT/'cursor-agent')['x86_64'][0]
    assert item==CURSOR_NATIVE and reviewed_cursor_native(item)
    assert reviewed_download_headers(item)=={'User-Agent':'curl/8.0','Accept':'*/*'}
    assert reviewed_asset_limit(item)==MAX_BYTES==300*1024**2

@pytest.mark.parametrize('field,value',[('url','https://downloads.cursor.com/unreviewed.tar.gz'),('sha256','0'*64),('size',183733395)])
def test_changed_identity_cannot_receive_native_origin_or_client_exception(tmp_path,field,value):
    item={**CURSOR_NATIVE,field:value}
    assert not reviewed_cursor_native(item)and reviewed_download_headers(item)=={}
    source=tmp_path/'cursor-agent';source.mkdir();metadata=json.loads((ROOT/'cursor-agent/upstream.json').read_text());metadata['archive'][field]=value
    (source/'upstream.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError,match='unreviewed original Cursor'):parallel_assets(source)
