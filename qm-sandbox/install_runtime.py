"""Install immutable original QM/Node/SDK sources, retaining upstream notices."""
import hashlib,json,os,platform,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path,PurePosixPath


def validate(metadata):
    expected={
        'node':('https://nodejs.org/dist/v24.16.0/node-v24.16.0-linux-x64.tar.gz',57023429,'2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff'),
        'qm':('https://codeload.github.com/yc-software/qm/tar.gz/deef9b8b1e2b85bd4166dd833604bb31bcb8e255',10625243,'40fb0d69319753a1cfab2dc8a1e8574d206e92589d26b264e768e94fa9109b4e'),
        'agent-sandbox-node-sdk':('https://codeload.github.com/Alibaba-Agent-Sandbox/nodejs-sdk/tar.gz/63d7cd8ece221b9f968eef51eeb932ea334c90d3',42302,'6fe5ad0e27ca024eed2c2db29e6a2ecf310336505423de6802719baa3137b598'),
    }
    for name,pin in expected.items():
        item=metadata[name]
        if tuple(item[key]for key in ['url','size','sha256'])!=pin:raise ValueError('unreviewed original runtime archive')


def extract(archive,destination):
    destination.mkdir(parents=True)
    with tarfile.open(archive,'r:gz')as bundle:
        members=bundle.getmembers()
        if len(members)>20000 or sum(item.size for item in members)>512*1024**2:raise ValueError('public source expansion exceeds bound')
        prefix=PurePosixPath(members[0].name).parts[0]
        for member in members:
            original=PurePosixPath(member.name)
            if original.is_absolute()or '..'in original.parts or original.parts[0]!=prefix:raise ValueError('invalid source member path')
            parts=original.parts[1:]
            if not parts:continue
            path=destination.joinpath(*parts)
            if not path.resolve().is_relative_to(destination):raise ValueError('source member escaped root')
            if member.isdir():path.mkdir(parents=True,exist_ok=True)
            elif member.isfile():
                if member.size>192*1024**2:raise ValueError('source member exceeds bound')
                path.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(member)as source,path.open('xb')as output:
                    while block:=source.read(1024*1024):output.write(block)
                path.chmod(0o755 if member.mode&0o111 else 0o644)
            elif member.issym():
                target=(path.parent/member.linkname).resolve()
                if not target.is_relative_to(destination):raise ValueError('source symlink escaped root')
                path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(member.linkname)
            else:raise ValueError('unsupported source member type')


def install(metadata):
    validate(metadata)
    if platform.machine()!='x86_64':raise RuntimeError('reviewed original Linuxx64 profile required')
    for name,target in [('node','/opt/node/runtime'),('qm','/opt/qm'),('agent-sandbox-node-sdk','/opt/agent-sandbox-node-sdk')]:
        item=metadata[name]
        with tempfile.TemporaryDirectory(prefix='abx-qm-install-')as value:
            archive=Path(value)/'original.tar.gz';size=0;digest=hashlib.sha256()
            with urllib.request.urlopen(item['url'],timeout=120)as source,archive.open('xb')as output:
                while block:=source.read(1024*1024):
                    size+=len(block)
                    if size>item['size']:raise ValueError('original archive exceeds exact size')
                    digest.update(block);output.write(block)
            if size!=item['size']or digest.hexdigest()!=item['sha256']:raise ValueError('original archive size/SHA256 differs')
            extract(archive,Path(target))
    Path('/opt/node/current').symlink_to('/opt/node/runtime')
    for key,directory in [('qm','/opt/qm'),('agent-sandbox-node-sdk','/opt/agent-sandbox-node-sdk')]:
        for name,expected in metadata[key]['identity_files'].items():
            with (Path(directory)/name).open('rb')as source:
                if hashlib.file_digest(source,'sha256').hexdigest()!=expected:raise RuntimeError('original native source identity differs')
    binary=Path('/opt/node/current/bin/node')
    with binary.open('rb')as source:
        if binary.stat().st_size!=metadata['node']['binary_size']or hashlib.file_digest(source,'sha256').hexdigest()!=metadata['node']['binary_sha256']:raise RuntimeError('original Node executable differs')
    result=subprocess.run([str(binary),'--version'],env={'PATH':'/opt/node/current/bin:/usr/bin:/bin','HOME':'/tmp','LANG':'C.UTF-8'},capture_output=True,text=True,timeout=30,check=True)
    if result.stdout.strip()!='v24.16.0':raise RuntimeError('original Node version differs')
    print('Original QM source, Agent Sandbox SDK source and Node24.16.0 archive/executable identities verified')


if __name__=='__main__':install(json.loads(Path('/opt/qm-bootstrap/upstream.json').read_text()))
