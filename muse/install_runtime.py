"""Install unchanged official Muse ELF; never execute it during this installer."""
import hashlib,json,os,platform,secrets,time,urllib.request
from pathlib import Path

VERSION='1.4.11-R6667.1'
EXPECTED={'url':'https://lookaside.facebook.com/lookaside/muse/download/?channel=muse&version=1.4.11-R6667.1&file=muse-x86-linux','size':384809176,'sha256':'6fda12a6a4f236528dafa707384cf6395fe859b1438ef77c7be26ed9d7976839'}
PREFIX=Path('/opt/muse')

def metadata():
    value=json.loads(Path(__file__).with_name('upstream.json').read_text())
    if value.get('version')!=VERSION or any(value.get(k)!=v for k,v in EXPECTED.items()):raise ValueError('unreviewed original Muse artifact')
    return value

def verify_binary(path):
    if path.is_symlink()or not path.is_file()or path.stat().st_size!=EXPECTED['size']:raise ValueError('original Muse executable size/type differs')
    with path.open('rb')as stream:
        header=stream.read(20);stream.seek(0)
        if header[:6]!=b'\x7fELF\x02\x01'or int.from_bytes(header[18:20],'little')!=62:raise ValueError('original Linuxx64 ELF required')
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=EXPECTED['sha256']:raise ValueError('original Muse executable SHA256 differs')

def install():
    value=metadata()
    if platform.machine()!='x86_64':raise RuntimeError('reviewed Muse profile requires Linuxx64')
    directory=PREFIX/'bin'
    if PREFIX.is_symlink()or directory.is_symlink():raise ValueError('install destination cannot be a symlink')
    directory.mkdir(parents=True,exist_ok=True);target=directory/'muse'
    if target.exists()or target.is_symlink():verify_binary(target);return
    temporary=directory/('.owned-original-'+secrets.token_hex(16));digest=hashlib.sha256();size=0;deadline=time.monotonic()+900
    try:
        descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'wb')as output,urllib.request.urlopen(value['url'],timeout=120)as response:
            while block:=response.read(1024*1024):
                size+=len(block)
                if size>EXPECTED['size']or time.monotonic()>deadline:raise RuntimeError('bounded original Muse download exceeded')
                digest.update(block);output.write(block)
        if size!=EXPECTED['size']or digest.hexdigest()!=EXPECTED['sha256']:raise ValueError('original Muse download SHA256/size differs')
        verify_binary(temporary);temporary.chmod(0o755);os.replace(temporary,target)
        (PREFIX/'upstream.json').write_text(json.dumps(value,indent=2)+'\n')
        (PREFIX/'upstream.json').chmod(0o644)
    finally:temporary.unlink(missing_ok=True)

if __name__=='__main__':install()
