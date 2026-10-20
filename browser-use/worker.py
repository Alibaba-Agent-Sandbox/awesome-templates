"""Native browser-use0.13.11 and owned Chromium, isolated to one worker call."""
import asyncio,contextlib,http.server,json,os,sys,threading
from importlib.metadata import version
from pathlib import Path

ALLOWED={'done','navigate','click','input','scroll','wait','go_back','switch','close','find_text','find_elements','search_page','select_dropdown','dropdown_options','send_keys'}
ALL_ACTIONS={'click','close','done','dropdown_options','evaluate','extract','find_elements','find_text','go_back','input','navigate','read_file','replace_file','save_as_pdf','screenshot','scroll','search','search_page','select_dropdown','send_keys','switch','upload_file','wait','write_file'}

def error_summary(errors,value):
    result=[]
    for error in errors:
        if not error:continue
        text=str(error)
        for key in ['api_key','base_url']:
            if value.get(key):text=text.replace(value[key],'[REDACTED]')
        result.append(text.encode('utf-8')[:1024].decode('utf-8','ignore'))
        if len(result)==20:break
    return result

async def run(value):
    from browser_use import Agent,Browser,ChatOpenAI
    from browser_use.browser import BrowserProfile
    from browser_use.tools.service import Tools
    profile=BrowserProfile(executable_path=value['browser_binary'],headless=True,chromium_sandbox=False,use_cloud=False,enable_default_extensions=False,keep_alive=True,user_data_dir=str(Path(os.environ['HOME'])/'profile'),args=['--disable-dev-shm-usage','--remote-debugging-address=127.0.0.1'],viewport={'width':960,'height':720})
    browser=Browser(browser_profile=profile)
    fixture=thread=None
    try:
        if value['mode']=='self-test':
            class H(http.server.BaseHTTPRequestHandler):
                def log_message(self,*args):pass
                def do_GET(self):
                    body=b'<html><title>BROWSER_USE_NATIVE_OK</title><h1>Actual native CDP</h1></html>'
                    self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            fixture=http.server.ThreadingHTTPServer(('127.0.0.1',0),H);thread=threading.Thread(target=fixture.serve_forever,daemon=True);thread.start()
            await browser.start();page=await browser.get_current_page();await page.goto('http://127.0.0.1:'+str(fixture.server_port)+'/')
            for _ in range(30):
                if await page.get_title()=='BROWSER_USE_NATIVE_OK':break
                await asyncio.sleep(.1)
            else:raise RuntimeError('native fixture title failed')
            data=await browser.take_screenshot(format='png')
            if not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data)<1000:raise RuntimeError('native screenshot failed')
            return {'self_test':'BROWSER_USE_NATIVE_OK','png_bytes':len(data)}
        tools=Tools(exclude_actions=sorted(ALL_ACTIONS-ALLOWED))
        if set(tools.registry.registry.actions)!=ALLOWED:raise RuntimeError('native action surface differs from pinned profile')
        llm=ChatOpenAI(model=value['model'],api_key=value['api_key'],base_url=value['base_url'],max_retries=0,timeout=90,max_completion_tokens=4096,add_schema_to_system_prompt=True,dont_force_structured_output=True)
        agent=Agent(task=value['task'],llm=llm,browser=browser,tools=tools,use_vision=False,use_judge=False,use_thinking=False,generate_gif=False,file_system_path=str(Path(os.environ['HOME'])/'files'),calculate_cost=False,initial_actions=[{'navigate':{'url':value['url']}}] if value['url'] else [],max_failures=1,llm_timeout=100,step_timeout=120,max_actions_per_step=3)
        if set(agent.tools.registry.registry.actions)!=ALLOWED:raise RuntimeError('agent altered the pinned browser action surface')
        history=await agent.run(max_steps=value['max_steps'])
        data=await browser.take_screenshot(path=value['screenshot_path'],format='png');page=await browser.must_get_current_page();url=(await page.get_target_info()).get('url','')
        if not data.startswith(b'\x89PNG\r\n\x1a\n') or not 1000<len(data)<=16*1024**2:raise RuntimeError('native screenshot size/type guard')
        return {'result':history.final_result() or '', 'final_url':url,'screenshot_path':value['screenshot_path'],'bytes':len(data),'steps':len(history.history),'done':history.is_done(),'success':history.is_successful() is True,'error_summary':error_summary(history.errors(),value)}
    finally:
        try:await browser.kill()
        finally:
            if fixture:fixture.shutdown();fixture.server_close()
            if thread:thread.join(timeout=5)

def main():
    if len(sys.argv)==2 and sys.argv[1]=='--version':print(version('browser-use'));return 0
    data=sys.stdin.buffer.read(512*1024+1)
    if len(data)>512*1024:raise ValueError('private input size guard')
    with contextlib.redirect_stdout(sys.stderr):result=asyncio.run(run(json.loads(data)))
    print(json.dumps(result,ensure_ascii=False));return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'native_error_type':type(exc).__name__}),flush=True)
        raise SystemExit(1) from None
