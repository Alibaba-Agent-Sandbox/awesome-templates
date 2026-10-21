"""Root build only: verify original ELF bytes and prepare an empty owned node path."""
import hashlib,json,os,platform,pwd,stat,tempfile,time,urllib.request
from pathlib import Path
ROOT=Path('/opt/k3s')
META=json.loads(Path(__file__).with_name('upstream.json').read_text())
PIN={'version':'v1.37.1+k3s1','architecture':'x86_64','url':'https://github.com/k3s-io/k3s/releases/download/v1.37.1%2Bk3s1/k3s','size':81543330,'sha256':'92b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0'}

def verify(path):
    if path.is_symlink()or not path.is_file()or path.stat().st_size!=PIN['size']:raise ValueError('original K3s size/type differs')
    with path.open('rb')as source:
        if hashlib.file_digest(source,'sha256').hexdigest()!=PIN['sha256']:raise ValueError('original K3s SHA256 differs')

def install():
    if os.geteuid()!=0 or platform.system()!='Linux'or platform.machine()!='x86_64':raise RuntimeError('reviewed K3s install requires root Linuxx64 build stage')
    if any(META.get(key)!=value for key,value in PIN.items()):raise ValueError('unreviewed original K3s artifact')
    if ROOT.is_symlink():raise ValueError('original K3s destination cannot be a symlink')
    ROOT.mkdir(mode=0o755,exist_ok=True)
    if ROOT.stat().st_uid!=0 or ROOT.stat().st_mode&0o022:raise ValueError('original K3s destination ownership differs')
    binary=ROOT/'k3s'
    if binary.exists():verify(binary)
    else:
        with tempfile.TemporaryDirectory(prefix='.original-k3s-',dir=ROOT)as name:
            temporary=Path(name)/'original';digest=hashlib.sha256();size=0;deadline=time.monotonic()+900
            with urllib.request.urlopen(PIN['url'],timeout=120)as source,temporary.open('xb')as output:
                while block:=source.read(1024*1024):
                    size+=len(block)
                    if size>PIN['size']or time.monotonic()>deadline:raise RuntimeError('bounded original K3s download exceeded')
                    digest.update(block);output.write(block)
            if size!=PIN['size']or digest.hexdigest()!=PIN['sha256']:raise ValueError('original K3s download integrity differs')
            verify(temporary);temporary.chmod(0o555);os.replace(temporary,binary)
    binary.chmod(0o555);os.chown(binary,0,0)
    license_file=Path(__file__).with_name('UPSTREAM-LICENSE.md');target=ROOT/'LICENSE';data=license_file.read_bytes()
    if target.exists()or target.is_symlink():
        if target.is_symlink()or not target.is_file()or target.read_bytes()!=data:raise ValueError('pre-existing foreign license is preserved')
    else:target.write_bytes(data)
    target.chmod(0o444)
    account=pwd.getpwnam('user');parent=Path('/etc/rancher');node=parent/'node'
    if parent.is_symlink():raise ValueError('native node parent cannot be a symlink')
    parent.mkdir(mode=0o755,exist_ok=True)
    if parent.stat().st_uid!=0 or parent.stat().st_mode&0o022:raise ValueError('native node parent identity differs')
    if node.is_symlink():raise ValueError('native node directory cannot be a symlink')
    node.mkdir(mode=0o700,exist_ok=True)
    if not node.is_dir()or list(node.iterdir())or node.stat().st_uid not in {0,account.pw_uid}:raise ValueError('pre-existing native node state is preserved')
    node.chmod(0o700);os.chown(node,account.pw_uid,account.pw_gid)

if __name__=='__main__':install()
