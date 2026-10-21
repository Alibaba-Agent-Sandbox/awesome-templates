"""Bounded RFB3.8 VNC authentication and raw desktop capture; no fake framebuffer."""
import asyncio,io,struct

MAX_PIXELS=2048*2048


async def capture(read,write,password,pointer=None):
    from Crypto.Cipher import DES
    from PIL import Image
    version=await read(12)
    if version!=b'RFB 003.008\n':raise RuntimeError('RFB3.8 required')
    await write(version)
    count=(await read(1))[0]
    if not 0<count<=16:raise RuntimeError('invalid RFB security negotiation')
    if 2 not in await read(count):raise RuntimeError('native VNC password authentication required')
    await write(b'\x02')
    challenge=await read(16)
    if not isinstance(password,str)or len(password)!=8 or not password.isascii():raise ValueError('expected8-character owned VNC password')
    key=bytes(int(f'{value:08b}'[::-1],2)for value in password.encode())
    await write(DES.new(key,DES.MODE_ECB).encrypt(challenge))
    if await read(4)!=b'\x00'*4:raise RuntimeError('native VNC authentication failed')
    await write(b'\x01')
    header=await read(24);width,height=struct.unpack('>HH',header[:4]);name_length=struct.unpack('>I',header[20:])[0]
    if not width or not height or width*height>MAX_PIXELS or name_length>4096:raise RuntimeError('RFB desktop exceeds bounded geometry')
    await read(name_length)
    if pointer is not None:
        x,y=pointer
        if type(x)is not int or type(y)is not int or not 0<=x<width or not 0<=y<height:raise ValueError('VNC pointer outside native desktop')
        await write(struct.pack('>BBHH',5,1,x,y));await write(struct.pack('>BBHH',5,0,x,y))
    # Request32-bit little-endian true-color BGRX and raw rectangles only.
    await write(b'\x00\x00\x00\x00'+struct.pack('>BBBBHHHBBBxxx',32,24,0,1,255,255,255,16,8,0))
    await write(struct.pack('>BBHi',2,0,1,0))
    await write(struct.pack('>BBHHHH',3,0,0,0,width,height))
    image=Image.new('RGB',(width,height));painted=False
    for _ in range(32):
        kind=(await read(1))[0]
        if kind==2:continue
        if kind==3:
            text_header=await read(7);size=struct.unpack('>I',text_header[3:])[0]
            if size>65536:raise RuntimeError('RFB clipboard exceeds64KiB')
            await read(size);continue
        if kind!=0:raise RuntimeError('unsupported native RFB server message')
        update=await read(3);rectangles=struct.unpack('>H',update[1:])[0]
        if rectangles>256:raise RuntimeError('invalid RFB rectangle count')
        if not rectangles:
            await write(struct.pack('>BBHHHH',3,0,0,0,width,height));continue
        total=0
        for _ in range(rectangles):
            x,y,w,h,encoding=struct.unpack('>HHHHi',await read(12))
            total+=w*h
            if encoding!=0 or not w or not h or x+w>width or y+h>height or total>MAX_PIXELS:
                raise RuntimeError('invalid or oversized raw RFB rectangle')
            raw=await read(w*h*4)
            image.paste(Image.frombytes('RGB',(w,h),raw,'raw','BGRX'),(x,y));painted=True
        if painted:
            output=io.BytesIO();image.save(output,format='PNG')
            return output.getvalue(),width,height
    raise RuntimeError('no native VNC framebuffer received')


async def capture_tcp(port,password,pointer=None):
    reader,writer=await asyncio.wait_for(asyncio.open_connection('127.0.0.1',port),10)
    async def write(value):writer.write(value);await writer.drain()
    try:return await asyncio.wait_for(capture(reader.readexactly,write,password,pointer),30)
    finally:writer.close();await writer.wait_closed()


async def capture_websocket(url,password,headers=None,pointer=None):
    import aiohttp
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=40),trust_env=False)as session:
        async with session.ws_connect(url,headers=headers or{},protocols=['binary'],max_msg_size=4*1024*1024)as ws:
            buffer=bytearray()
            async def read(count):
                if count>MAX_PIXELS*4:raise RuntimeError('RFB read exceeds bound')
                while len(buffer)<count:
                    message=await ws.receive(timeout=30)
                    if message.type!=aiohttp.WSMsgType.BINARY:raise RuntimeError('native VNC binary stream closed')
                    buffer.extend(message.data)
                    if len(buffer)>MAX_PIXELS*4+65536:raise RuntimeError('RFB buffer exceeds bound')
                value=bytes(buffer[:count]);del buffer[:count];return value
            return await capture(read,ws.send_bytes,password,pointer)
