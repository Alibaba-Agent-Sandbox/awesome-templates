"""Small bounded client for the original browser's DevTools protocol."""
import asyncio,json,time
from urllib.parse import urlsplit,urlunsplit
import aiohttp


def endpoint_url(base, path, *, websocket=False):
    """Append a native route to the provider-resolved path and fixed query."""
    resolved=urlsplit(base);native=urlsplit(path)
    scheme=('wss'if resolved.scheme=='https'else'ws')if websocket else resolved.scheme
    query='&'.join(value for value in [resolved.query,native.query]if value)
    return urlunsplit((scheme,resolved.netloc,resolved.path.rstrip('/')+'/'+native.path.lstrip('/'),query,''))


class Page:
    def __init__(self,base,headers=None):
        self.base=base;self.headers=headers or{};self.session=None;self.ws=None;self.counter=0

    async def __aenter__(self):
        self.session=aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=40),headers=self.headers,trust_env=False)
        try:
            async with self.session.get(endpoint_url(self.base,'/json/list'))as response:
                response.raise_for_status();data=await response.json()
            target=next((item for item in data if item.get('type')=='page'),None)
            if target is None:
                async with self.session.put(endpoint_url(self.base,'/json/new?about:blank'))as response:
                    response.raise_for_status();target=await response.json()
            self.target_id=target['id']
            url=endpoint_url(self.base,target['webSocketDebuggerUrl'],websocket=True)
            self.ws=await self.session.ws_connect(url,max_msg_size=4*1024*1024,heartbeat=20)
            await self.send('Page.bringToFront')
            await self.send('Page.enable')
            return self
        except BaseException:
            await self.__aexit__(None,None,None);raise

    async def __aexit__(self,*args):
        if self.ws is not None:await self.ws.close()
        if self.session is not None:await self.session.close()

    async def send(self,method,params=None):
        self.counter+=1;identifier=self.counter
        await self.ws.send_json({'id':identifier,'method':method,'params':params or{}})
        for _ in range(1024):
            message=await self.ws.receive(timeout=30)
            if message.type!=aiohttp.WSMsgType.TEXT:raise RuntimeError('native CDP stream closed')
            if len(message.data)>4*1024*1024:raise RuntimeError('native CDP response exceeds bound')
            value=json.loads(message.data)
            if value.get('id')!=identifier:continue
            if value.get('error'):raise RuntimeError('native CDP command failed')
            return value.get('result',{})
        raise RuntimeError('native CDP event budget exceeded')

    async def evaluate(self,expression):
        result=await self.send('Runtime.evaluate',{'expression':expression,'returnByValue':True})
        if result.get('exceptionDetails'):raise RuntimeError('native browser evaluation failed')
        return result.get('result',{}).get('value')

    async def navigate(self,url):
        result=await self.send('Page.navigate',{'url':url})
        if result.get('errorText'):raise RuntimeError('native browser navigation failed')
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            state=await self.evaluate('({url:location.href,title:document.title,ready:document.readyState,visible:document.visibilityState,width:innerWidth,height:innerHeight})')
            tree=await self.send('Page.getFrameTree');frame=tree.get('frameTree',{}).get('frame',{})
            current=frame.get('loaderId')==result['loaderId']if result.get('loaderId')else state.get('url')==url
            if current and state.get('ready')in ['interactive','complete']and state.get('visible')=='visible'and state.get('width',0)>0 and state.get('height',0)>0:return state
            await asyncio.sleep(.1)
        raise RuntimeError('native browser navigation deadline exceeded')
