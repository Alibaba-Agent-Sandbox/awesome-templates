"""Exact original ELF transport retains generic archive/wire boundaries."""
import json
from pathlib import Path
import pytest
from prepare_steps import ROOT,parallel_assets
from step_assets import MAX_BYTES,reviewed_asset_limit

def test_original_k3s_profile_uses_exact_published_binary_and_generic_limit():
    item=parallel_assets(ROOT/'k3s')['x86_64'][0]
    assert item['size']==81543330 and item['sha256']=='92b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0'
    assert reviewed_asset_limit(item)==MAX_BYTES==300*1024**2

@pytest.mark.parametrize('field,value',[('url','https://github.com/unreviewed/binary'),('size',81543331),('sha256','0'*64),('architecture','aarch64'),('version','latest')])
def test_changed_native_identity_is_rejected(tmp_path,field,value):
    source=tmp_path/'k3s';source.mkdir();item=json.loads((ROOT/'k3s/upstream.json').read_text());item[field]=value
    (source/'upstream.json').write_text(json.dumps(item))
    with pytest.raises(ValueError,match='unreviewed original K3s'):parallel_assets(source)
