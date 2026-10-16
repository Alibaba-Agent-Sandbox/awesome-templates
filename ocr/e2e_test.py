#!/usr/bin/env python3
"""HTTP contract and independently generated pixels/artifact OCR verification."""
import base64
import csv
import hashlib
import io
import os
from pathlib import Path,PurePosixPath
import re
import secrets
import sys
import uuid

import httpx
from PIL import Image,ImageDraw,ImageFont


def main():
    headers={}
    if os.environ.get('E2E_TOKEN'):headers['X-Access-Token']=os.environ['E2E_TOKEN']
    if os.environ.get('E2E_SERVER_TOKEN'):headers['Authorization']='Bearer '+os.environ['E2E_SERVER_TOKEN']
    failures=0
    def check(ok,label):
        nonlocal failures
        failures+=not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}",flush=True)
    root=os.environ.get('E2E_WORKSPACE') or os.environ.get('E2E_BASE_DIR','/home/user/app')
    prefix=root.rstrip('/')+'/.ocr-controller-'+uuid.uuid4().hex
    owned=[]
    with httpx.Client(base_url=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/'),headers=headers,timeout=90) as client:
        def call(name,**arguments):
            response=client.post('/commands/'+name,json=arguments);response.raise_for_status();return response.json()['result']
        def upload(path,data):
            response=client.post('/files/upload-stream',json={'path':path,'content_base64':base64.b64encode(data).decode()});response.raise_for_status();owned.append(path)
        def read(path):
            response=client.get('/files/download-stream',params={'path':path});response.raise_for_status();return base64.b64decode(response.json()['content_base64'],validate=True)
        def artifacts(result):
            directory=result['artifact_dir']
            assert PurePosixPath(directory).parent==PurePosixPath(root) and re.fullmatch(r'\.ocr-[0-9a-f]{32}',PurePosixPath(directory).name)
            assert result['text_path']==directory+'/text.txt' and result['tsv_path']==directory+'/words.tsv'
            owned.append(directory)
            text=read(result['text_path']);tsv=read(result['tsv_path'])
            assert hashlib.sha256(text).hexdigest()==result['text_sha256'] and hashlib.sha256(tsv).hexdigest()==result['tsv_sha256']
            assert text.decode()==result['text']
            return text.decode(),list(csv.DictReader(io.StringIO(tsv.decode()),delimiter='\t'))
        try:
            response=client.get('/health');check(response.status_code==200,'server health')
            response=client.get('/commands');names={item['name'] for item in response.json().get('commands',[])}
            check(response.status_code==200 and {'ocr','ocr_version','ocr_setup_check','ocr_smoke'}<=names,'typed OCR commands registered')
            response=client.post('/commands/ocr',json={});check(response.status_code==400,'required image_path conversion contract')
            response=client.post('/commands/ocr',json={'image_path':'/etc/passwd'})
            check(response.status_code==500 and response.json().get('type')=='ValueError' and '/etc/passwd' not in response.text,'outside-workspace input rejected without private path')
            invalid=prefix+'-invalid.bin';upload(invalid,b'not a PNG or JPEG')
            response=client.post('/commands/ocr',json={'image_path':invalid})
            check(response.status_code==500 and response.json().get('type')=='ValueError' and invalid not in response.text,'invalid encoded image rejected without private path')
            setup=call('ocr_setup_check')
            check(setup.get('pinned_version')=='5.5.0' and setup.get('language')=='eng','declared fixed engine and English capability')
            required=os.environ.get('E2E_REQUIRE_OCR','').lower() in {'1','true','yes'}
            if not setup.get('available'):
                if required:check(False,'required pinned OCR engine and language data are available')
                else:print('[SKIP] pinned OCR runtime unavailable; HTTP contract is not real image/cloud acceptance',flush=True)
            else:
                check(call('ocr_version')=='tesseract 5.5.0' and setup.get('pillow_version')=='11.3.0','actual fixed Tesseract and Pillow versions')
                check(call('ocr_smoke')=='Tesseract image/text/TSV artifacts OK','actual packaged pixels to text and TSV smoke')
                nonce=''.join(secrets.choice('2346789') for _ in range(6))
                image=Image.new('RGB',(1400,360),'white');draw=ImageDraw.Draw(image);font=ImageFont.load_default(size=80)
                draw.text((50,40),'SANDBOX OCR '+nonce,font=font,fill='black');draw.text((50,180),'ALPHA BETA',font=font,fill='black')
                stream=io.BytesIO();image.save(stream,format='PNG');pixels=stream.getvalue();path=prefix+'-text.png';upload(path,pixels)
                result=call('ocr',image_path=path)
                expected={'SANDBOX','OCR',nonce,'ALPHA','BETA'}
                check(expected<=set(result['text'].split()) and result['engine_version']=='5.5.0' and result['language']=='eng','independent random-digit pixels recognized by actual OCR')
                check((result['width'],result['height'])==(1400,360) and result['word_count']>=5,'recognized image dimensions and real word count')
                text,rows=artifacts(result)
                check(expected<=set(text.split()),'controller downloads and independently verifies complete TXT bytes and SHA')
                words=[row for row in rows if row['level']=='5' and row['text'].strip()]
                check(expected<={row['text'] for row in words if float(row['conf'])>50} and all(0<=int(row['left'])<1400 and 0<=int(row['top'])<360 and 0<int(row['width'])<=1400-int(row['left']) and 0<int(row['height'])<=360-int(row['top']) for row in words),'controller downloads meaningful TSV words confidence and pixel bounds')
                check(read(path)==pixels,'original uploaded image remains byte-identical')
                blank=Image.new('RGB',(600,200),'white');stream=io.BytesIO();blank.save(stream,format='PNG');path=prefix+'-blank.png';upload(path,stream.getvalue())
                empty=call('ocr',image_path=path);text,rows=artifacts(empty)
                check(not text.strip() and empty['word_count']==0 and not any(row['level']=='5' and row['text'].strip() for row in rows),'real blank-image negative control returns no fabricated words')
        except Exception as exc:
            check(False,'OCR acceptance aborted ('+type(exc).__name__+'); response omitted')
        finally:
            for path in reversed(owned):
                response=client.delete('/files',params={'path':path})
                check(response.status_code in (200,404),'owned controller artifact cleanup')
    return 1 if failures else 0


if __name__=='__main__':sys.exit(main())
