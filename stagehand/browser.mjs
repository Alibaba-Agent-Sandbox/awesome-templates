// Own Chrome's process/profile; native Stagehand still controls browser actions.
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {localBrowser} from '@browserbasehq/stagehand';

function targets(endpoint) {
  return new Promise((resolve,reject)=>{
    const ws=new WebSocket(endpoint);const timer=setTimeout(()=>finish(new Error('owned CDP target deadline')),5000);
    function finish(error,value) {clearTimeout(timer);ws.close();error?reject(error):resolve(value);}
    ws.addEventListener('open',()=>ws.send(JSON.stringify({id:1,method:'Target.getTargets'})));
    ws.addEventListener('error',()=>finish(new Error('owned CDP connection failed')));
    ws.addEventListener('message',event=>{
      try {
        const text=String(event.data);if(Buffer.byteLength(text)>256*1024)throw new RangeError('owned target response too large');
        const value=JSON.parse(text);
        if(value.id===1){if(value.error)throw new Error('owned target inspection failed');finish(null,value.result.targetInfos);}
      }catch(error){finish(error);}
    });
  });
}

export async function launchOwnedBrowser(binary) {
  const profile=path.join(process.cwd(),'browser');await fs.mkdir(profile,{mode:0o700});
  const extension=new URL('./node_modules/@browserbasehq/stagehand/dist/extension/',import.meta.url).pathname.replace(/\/$/,'');
  const child=spawn(binary,['--headless=new','--no-sandbox','--disable-dev-shm-usage',
    '--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',
    '--disable-component-extensions-with-background-pages','--disable-default-apps',
    '--enable-unsafe-extension-debugging','--remote-debugging-port=0','--remote-allow-origins=*',
    '--user-data-dir='+profile,'--load-extension='+extension,'--disable-extensions-except='+extension,'about:blank'],
    {detached:true,stdio:'ignore',env:process.env});
  let spawnError;
  const exited=new Promise(resolve=>{child.once('error',error=>{spawnError=error;resolve();});child.once('exit',resolve);});
  let handle;
  async function stop() {
    try{await handle?.close();}finally{
      if(child.exitCode===null && child.signalCode===null && !spawnError){
        try{process.kill(-child.pid,'SIGTERM');}catch(error){if(error.code!=='ESRCH')throw error;}
        await Promise.race([exited,new Promise(resolve=>setTimeout(resolve,2000))]);
        if(child.exitCode===null && child.signalCode===null){
          try{process.kill(-child.pid,'SIGKILL');}catch(error){if(error.code!=='ESRCH')throw error;}
        }
      }
      await exited;
    }
  }
  try{
    const deadline=Date.now()+30000;let cdpUrl,extensionId;
    while(Date.now()<deadline){
      if(spawnError || child.exitCode!==null || child.signalCode!==null)throw new Error('owned Chromium exited before readiness');
      try{
        const [port,route]=String(await fs.readFile(path.join(profile,'DevToolsActivePort'))).trim().split('\n');
        if(!/^\d{1,5}$/.test(port) || Number(port)<1 || Number(port)>65535 || !/^\/devtools\/browser\/[A-Za-z0-9-]+$/.test(route))throw new Error('invalid owned CDP descriptor');
        cdpUrl='http://127.0.0.1:'+port;
        const items=await targets('ws://127.0.0.1:'+port+route);
        const matches=items.filter(x=>x.type==='service_worker' && /^chrome-extension:\/\/[a-p]{32}\/service-worker\.js$/.test(x.url));
        if(matches.length>1)throw new Error('multiple Stagehand worker candidates');
        if(matches.length===1){extensionId=new URL(matches[0].url).hostname;break;}
      }catch(error){if(error.code!=='ENOENT' && !cdpUrl)throw error;}
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    if(!extensionId)throw new Error('bundled native extension did not become ready');
    handle=await localBrowser.connect({cdpUrl,extensionId});
    return {browser:handle,close:stop};
  }catch(error){await stop();throw error;}
}
