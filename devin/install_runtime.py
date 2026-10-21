"""Install the unchanged official archive; no original executable runs here."""
import hashlib,json,os,platform,tarfile,tempfile,time,urllib.request
from pathlib import Path,PurePosixPath

VERSION='3000.11.92'
ARCHIVE={'url': 'https://static.devin.ai/cli/3000.11.92/devin-3000.11.92-x86_64-unknown-linux.tar.gz', 'size': 67245544, 'sha256': '2d829139682e038cf122510f1170eee3d7060bcc7ebf92445cbc5d28c9fbcfa0'}
PREFIX=Path('/opt/devin')

def metadata():
    value=json.loads(Path(__file__).with_name('upstream.json').read_text())
    if value.get('version')!=VERSION or value.get('architecture')!='x86_64' or any(value.get('archive',{}).get(k)!=v for k,v in ARCHIVE.items()):
        raise ValueError('unreviewed original Devin artifact')
    return value

def verify_tree(root,value):
    for item in value['files']:
        path=root/item['path']
        if path.is_symlink()or not path.is_file()or path.stat().st_size!=item['size']:
            raise ValueError('original Devin file identity differs')
        with path.open('rb')as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=item['sha256']:raise ValueError('original Devin file SHA256 differs')

def extract(archive,destination,value):
    with tarfile.open(archive,'r:gz')as source:
        members=source.getmembers()
        if len(members)>2000 or sum(m.size for m in members if m.isfile())>1024**3:raise ValueError('original archive extraction exceeds bound')
        files=set()
        for member in members:
            parts=PurePosixPath(member.name).parts
            if not parts or parts[0]not in {'bin','share'} or '..'in parts or PurePosixPath(member.name).is_absolute()or not(member.isdir()or member.isfile()):
                raise ValueError('unexpected archive member or link')
            if member.isfile():files.add(PurePosixPath(*parts).as_posix())
        if files!={item['path']for item in value['files']}:raise ValueError('original archive file inventory differs')
        source.extractall(destination,filter='data')
    root=destination;verify_tree(root,value)
    for path in root.rglob('*'):
        if path.is_dir():path.chmod(0o755)
    for item in value['files']:(root/item['path']).chmod(0o555 if item['executable']else 0o444)
    root.chmod(0o755)
    return root

def install():
    value=metadata()
    if platform.system()!='Linux'or platform.machine()!='x86_64':raise RuntimeError('reviewed Devin profile requires Linuxx64')
    if os.geteuid()!=0:raise RuntimeError('install original package in the root build stage')
    if PREFIX.is_symlink():raise ValueError('install destination cannot be a symlink')
    if PREFIX.exists():verify_tree(PREFIX,value);return
    with tempfile.TemporaryDirectory(prefix='.abx-devin-install-',dir=PREFIX.parent)as name:
        private=Path(name);private.chmod(0o700);archive=private/'original.tar.gz';digest=hashlib.sha256();size=0;deadline=time.monotonic()+900
        request=urllib.request.Request(ARCHIVE['url'],headers={'User-Agent':'curl/8.0','Accept':'*/*'})
        with urllib.request.urlopen(request,timeout=120)as response,archive.open('xb')as output:
            while block:=response.read(1024*1024):
                size+=len(block)
                if size>ARCHIVE['size']or time.monotonic()>deadline:raise RuntimeError('bounded original download exceeded')
                digest.update(block);output.write(block)
        if size!=ARCHIVE['size']or digest.hexdigest()!=ARCHIVE['sha256']:raise ValueError('original archive size/SHA256 differs')
        package=private/'package';package.mkdir(mode=0o700);original=extract(archive,package,value);os.replace(original,PREFIX)

if __name__=='__main__':install()
