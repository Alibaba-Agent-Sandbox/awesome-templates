"""Maintain the explicit created-sandbox target binding in model controllers."""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]
NAMES=['copilot-cli','qm','cline','prime-agent','grok','muse','tau2-bench','appworld']
HELPER='''# Generated from scripts/sync_controller_ownership.py; do not edit this function alone.
def owned_loopback_gateway(base):
    import re
    sandbox_id=os.environ.get('E2E_OWNED_SANDBOX_ID','')
    bound=os.environ.get('E2E_OWNED_GATEWAY_URL','').rstrip('/')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',sandbox_id) or bound!=base.rstrip('/'):
        return False
    path=urlsplit(base).path.rstrip('/')
    return '/sandboxes/'not in path or path.endswith('/sandboxes/'+sandbox_id+'/proxy/9000')
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name in NAMES:
        p=ROOT/name/'e2e_test.py';s=p.read_text()
        if name=='copilot-cli':old="or urlsplit(base).hostname in ['127.0.0.1','localhost','::1']";new="or (urlsplit(base).hostname in ['127.0.0.1','localhost','::1'] and not owned_loopback_gateway(base))"
        else:
            predicate='local(base)'if name in {'tau2-bench','appworld'}else'local_target(base)'
            old='or '+predicate;new='or ('+predicate+' and not owned_loopback_gateway(base))'
        if args.check:
            if s.count(HELPER)!=1 or s.count(new)!=1:raise SystemExit('ownership synchronization drift: '+name)
        else:
            if HELPER not in s:
                if 'def owned_loopback_gateway('in s:raise SystemExit('unexpected existing ownership helper: '+name)
                at=s.index('\ndef ');s=s[:at]+'\n'+HELPER+'\n'+s[at:]
            if new not in s:
                if s.count(old)!=1:raise SystemExit('unexpected ownership predicate: '+name)
                s=s.replace(old,new)
            p.write_text(s)
    print('ownership controllers synchronized: '+str(len(NAMES)))

if __name__=='__main__':main()
