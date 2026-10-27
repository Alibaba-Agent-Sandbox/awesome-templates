"""Exact artifact/ordinary-client transport boundaries; no vendor or cloud call."""
import json
import pytest
from prepare_steps import ROOT,parallel_assets
from step_assets import DEVIN_NATIVE,MAX_BYTES,reviewed_asset_limit,reviewed_devin_native,reviewed_download_headers

def test_exact_devin_artifact_uses_normal_public_client_without_larger_budget():
    item=parallel_assets(ROOT/'devin')['x86_64'][0]
    assert item==DEVIN_NATIVE and reviewed_devin_native(item)
    assert reviewed_download_headers(item)=={}
    assert reviewed_asset_limit(item)==MAX_BYTES==300*1024**2

@pytest.mark.parametrize('field,value',[('url','https://static.devin.ai/unreviewed.tar.gz'),('sha256','0'*64),('size',67245545)])
def test_changed_identity_cannot_receive_native_origin_or_client_exception(tmp_path,field,value):
    item={**DEVIN_NATIVE,field:value}
    assert not reviewed_devin_native(item)and reviewed_download_headers(item)=={}
    source=tmp_path/'devin';source.mkdir();metadata=json.loads((ROOT/'devin/upstream.json').read_text());metadata['archive'][field]=value
    (source/'upstream.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError,match='unreviewed original Devin'):parallel_assets(source)
