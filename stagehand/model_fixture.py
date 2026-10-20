"""Owned single-click receipt fixture; model output never chooses its expected result."""
import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--nonce',required=True);parser.add_argument('--port',type=int,required=True);args=parser.parse_args()
    code='stagehand-receipt-'+args.nonce;state={'count':0,'code':''};lock=threading.Lock();root='/'+args.nonce
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def reply(self,value,kind='application/json'):
            body=value.encode() if isinstance(value,str) else json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.path==root+'/state':
                with lock:self.reply(dict(state))
            elif self.path==root+'/':
                self.reply('<!doctype html><meta charset="utf-8"><title>Native Stagehand receipt</title><h1>Receipt verification</h1><button id="publish">Publish receipt</button><p id="receipt">Not published</p><script>document.querySelector("#publish").onclick=async()=>{const r=await fetch('+json.dumps(root+'/click')+',{method:"POST"});const v=await r.json();document.querySelector("#receipt").textContent=v.code;};</script>','text/html;charset=utf-8')
            else:self.send_error(404)
        def do_POST(self):
            if self.path!=root+'/click':self.send_error(404);return
            with lock:state.update(count=state['count']+1,code=code);self.reply(dict(state))
    ThreadingHTTPServer(('0.0.0.0',args.port),Handler).serve_forever()


if __name__=='__main__':main()
