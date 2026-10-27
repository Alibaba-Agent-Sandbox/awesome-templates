"""A login page mentioning workbench must not pass authenticated UI acceptance."""
import importlib.util
from pathlib import Path
from urllib.parse import parse_qs
import httpx
import pytest


@pytest.mark.parametrize('strip_cookie',[False,True])
def test_external_controller_requires_authenticated_workbench(monkeypatch,strip_cookie):
    monkeypatch.setenv('E2E_BASE_URL','http://application.invalid')
    monkeypatch.setenv('E2E_CODE_SERVER_URL','http://ide.invalid')
    monkeypatch.setenv('E2E_GATEWAY_HEADERS_JSON','{}')
    monkeypatch.setenv('ABX_SERVER_TOKEN','synthetic-application-token')
    spec=importlib.util.spec_from_file_location('ide_cookie_acceptance_controller',Path(__file__).with_name('e2e_test.py'))
    controller=importlib.util.module_from_spec(spec);spec.loader.exec_module(controller)
    running=False;stopped=[]
    login_html='<html>workbench application<script src="workbench.js"></script><form><input type="password"></form></html>'
    def handle(request):
        nonlocal running
        path=request.url.path
        if request.url.host=='application.invalid':
            if path=='/health':return httpx.Response(200,json={'status':'ok'})
            if path.endswith('/code_server_version'):return httpx.Response(200,json={'result':'4.141.0'})
            if path.endswith('/code_server_self_test'):return httpx.Response(200,json={'result':'CODE_SERVER_OK'})
            if path.endswith('/code_server_start'):
                import json
                if len(json.loads(request.content)['password'])<8:return httpx.Response(400)
                running=True;return httpx.Response(200,json={'result':{'port':8443,'running':True,'auth':'password'}})
            if path.endswith('/code_server_status'):return httpx.Response(200,json={'result':{'running':running}})
            if path.endswith('/code_server_stop'):
                running=False;stopped.append(True);return httpx.Response(200,json={'result':{'running':False}})
            return httpx.Response(404)
        assert request.url.host=='ide.invalid'
        if request.method=='POST'and path=='/login':
            password=parse_qs(request.content.decode())['password'][0]
            if password=='synthetic-wrong-password':return httpx.Response(401,text=login_html)
            return httpx.Response(302,headers={'location':'/','set-cookie':'key=synthetic-session; Path=/; HttpOnly'})
        if path=='/login':return httpx.Response(200,text=login_html)
        if not strip_cookie and'key=synthetic-session'in request.headers.get('cookie',''):
            return httpx.Response(200,text='<html><div class="monaco-workbench">workbench</div></html>')
        return httpx.Response(302,headers={'location':'/login'})
    original=httpx.Client
    monkeypatch.setattr(controller.httpx,'Client',lambda *a,**kw:original(*a,transport=httpx.MockTransport(handle),**kw))
    if strip_cookie:
        with pytest.raises(AssertionError):controller.main()
    else:assert controller.main()==0
    assert running is False and stopped==[True]
