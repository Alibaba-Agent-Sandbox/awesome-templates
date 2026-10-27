"""Synthetic negative guards; never provider or model acceptance."""
import base64,importlib.util,io,json,re,shlex
from pathlib import Path
import pytest
from PIL import Image

spec=importlib.util.spec_from_file_location('http_browser_controller',Path(__file__).with_name('http_model_e2e.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
KIND=Path(__file__).parent.name

class Response:
    status_code=200
    def __init__(self,value):self.value=value
    def raise_for_status(self):pass
    def json(self):return self.value

class Client:
    def __init__(self,count):
        self.count=count;self.nonce=None;self.states=0;self.called=False;output=io.BytesIO();Image.new('RGB',(1024,768),(40,80,160)).save(output,format='PNG');self.png=output.getvalue()
    def post(self,path,json=None,**kwargs):
        if path=='/files/upload-stream':self.nonce=re.search(r'owned-browser-model-([a-f0-9]{32})',json['path']).group(1);return Response({})
        if path=='/shell':
            code=shlex.split(json['command'])[-1]
            compile(code, '<guest-controller>', 'exec')
            if 'subprocess.Popen'in code:value=__import__('json').dumps({'pid':234,'start':'99'})
            elif 'urlopen'in code:
                value=__import__('json').dumps({'count':0,'code':''}if not self.states else {'count':self.count,'code':('browser-receipt-'if KIND=='browser-use'else'stagehand-receipt-')+self.nonce});self.states+=1
            elif 'OWNED_PROCESS_ABSENT'in code:value='OWNED_PROCESS_ABSENT'
            else:value='ABSENT'
            return Response({'exit_code':0,'stdout':value})
        assert path=='/commands/'+('browser_use'if KIND=='browser-use'else'stagehand');self.called=True
        value={'screenshot_path':'/home/user/app/'+KIND+'-artifacts/'+'a'*32+'.png','final_url':json['url']}
        if KIND=='browser-use':value.update(done=True,success=True,result='claimed done',bytes=len(self.png))
        else:value.update(sdk_sha256='bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0',version='4.3.0',action={'success':True,'actions':[{}]},extracted={'text':'stagehand-receipt-'+self.nonce},model_calls=2,png_bytes=len(self.png))
        return Response({'result':value})
    def get(self,path,**kwargs):assert path=='/files/download-stream';return Response({'content_base64':base64.b64encode(self.png).decode()})
    def delete(self,*a,**kw):return Response({})

def test_required_model_refuses_unowned_target_before_any_http(monkeypatch):
    monkeypatch.delenv('E2E_REMOTE_SANDBOX',raising=False);results=[]
    module.verify(None,lambda ok,label:results.append((ok,label)),KIND)
    assert len(results)==1 and results[0][0]is False

@pytest.mark.parametrize('counter_ok',[False,True])
def test_model_claim_cannot_replace_actual_page_state_and_cleanup(monkeypatch,counter_ok):
    monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');expected=3 if KIND=='browser-use'else 1
    client=Client(expected if counter_ok else 0);results=[]
    module.verify(client,lambda ok,label:results.append((ok,label)),KIND)
    assert client.called
    assert all(ok for ok,_ in results)is counter_ok
    assert results[-1][0]is True and 'independently absent'in results[-1][1]
