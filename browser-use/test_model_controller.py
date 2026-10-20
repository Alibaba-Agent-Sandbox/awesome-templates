"""Negative acceptance guards are synthetic, never real-model/provider proof."""
import importlib.util,io
from pathlib import Path
import pytest
from PIL import Image
s=importlib.util.spec_from_file_location('browser_model_controller',Path(__file__).with_name('model_e2e_test.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def fixture():
    output=io.BytesIO();Image.new('RGB',(960,720),(30,80,160)).save(output,format='PNG');png=output.getvalue()
    result={'done':True,'success':True,'result':'native completed','final_url':'http://127.0.0.1:9011/fixture/','bytes':len(png)}
    return result,{'count':3,'code':'expected-code'},png

@pytest.mark.parametrize('bad',['unchanged_counter','wrong_code','fake_png','unrelated_url','failed_native','boolean_byte_length'])
def test_static_done_cannot_bypass_independent_browser_evidence(bad):
    result,state,png=fixture()
    if bad=='unchanged_counter':state['count']=0
    elif bad=='wrong_code':state['code']='wrong'
    elif bad=='fake_png':png=b'\x89PNG\r\n\x1a\n'+b'x'*2000;result['bytes']=len(png)
    elif bad=='unrelated_url':result['final_url']='https://unrelated.invalid/'
    elif bad=='failed_native':result['success']=False
    elif bad=='boolean_byte_length':result['bytes']=True
    with pytest.raises((AssertionError,OSError)):c.validate(result,state,png,'http://127.0.0.1:9011/fixture/','expected-code')

def test_actual_png_state_and_native_result_contract():
    result,state,png=fixture();proof=c.validate(result,state,png,'http://127.0.0.1:9011/fixture/','expected-code')
    assert proof['counter']==3 and proof['png_bytes']==len(png)
