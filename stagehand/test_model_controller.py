"""Independent authored negative oracles; no native or real model execution."""
import importlib.util
import io
from pathlib import Path
from PIL import Image
import pytest

s=importlib.util.spec_from_file_location('stagehand_owned_model_controller',Path(__file__).with_name('model_e2e_test.py'))
c=importlib.util.module_from_spec(s)
s.loader.exec_module(c)


def fixture():
    output=io.BytesIO();Image.new('RGB',(1024,768),'white').save(output,format='PNG');png=output.getvalue()
    result={'sdk_sha256':'bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0','version':'4.3.0','action':{'success':True,'actions':[{'method':'click'}]},'final_url':'http://127.0.0.1:9011/owned/',
        'extracted':{'text':'fresh-fixture-receipt'},'model_calls':2,'png_bytes':len(png)}
    return result,{'count':1,'code':'fresh-fixture-receipt'},png


def test_independent_positive_authored_oracle():
    result,state,png=fixture();proof=c.validate(result,state,png,result['final_url'],'fresh-fixture-receipt')
    assert proof['native_extraction_matches'] and len(proof['png_sha256'])==64


@pytest.mark.parametrize('field',['action','state','extract','url','calls','png'])
def test_marker_stale_state_bad_extraction_and_wrong_png_fail(field):
    result,state,png=fixture()
    if field=='action':result['action']={'success':True,'message':'DONE','actions':[]}
    if field=='state':state['count']=0
    if field=='extract':result['extracted']['text']='stale receipt'
    if field=='url':result['final_url']='http://127.0.0.1:9011/other/'
    if field=='calls':result['model_calls']=True
    if field=='png':png=b'not-png'
    with pytest.raises(AssertionError):c.validate(result,state,png,'http://127.0.0.1:9011/owned/','fresh-fixture-receipt')
