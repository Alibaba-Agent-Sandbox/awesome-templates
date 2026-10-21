"""Install only the verified original headed Chrome-for-Testing archive."""
import hashlib,json,os,re,stat,subprocess,tempfile,urllib.request,zipfile
from pathlib import Path,PurePosixPath


def install(metadata,root,info):
    assert metadata['browser_version']=='145.0.7632.6'
    assert metadata['url']=='https://cdn.playwright.dev/chrome-for-testing-public/145.0.7632.6/linux64/chrome-linux64.zip'
    root.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='abx-chrome-install-')as private:
        archive=Path(private)/'chrome.zip';digest=hashlib.sha256();size=0
        with urllib.request.urlopen(metadata['url'],timeout=120)as response,archive.open('xb')as output:
            while block:=response.read(1024*1024):
                size+=len(block)
                if size>metadata['size']:raise RuntimeError('official Chrome archive exceeded expected size')
                digest.update(block);output.write(block)
        if size!=metadata['size']or digest.hexdigest()!=metadata['sha256']:raise RuntimeError('official Chrome archive size/SHA256 mismatch')
        with zipfile.ZipFile(archive)as bundle:
            items=bundle.infolist()
            if len(items)>5000 or sum(item.file_size for item in items)>1536*1024*1024:raise RuntimeError('Chrome archive expansion exceeds reviewed bound')
            for item in items:
                name=PurePosixPath(item.filename);mode=item.external_attr>>16
                if name.is_absolute()or'..'in name.parts or not name.parts or name.parts[0]!='chrome-linux64'or stat.S_ISLNK(mode):raise RuntimeError('invalid Chrome archive member')
                target=root/str(name)
                if item.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                if item.file_size>512*1024*1024:raise RuntimeError('Chrome archive member exceeds512MiB')
                target.parent.mkdir(parents=True,exist_ok=True)
                with bundle.open(item)as source,target.open('xb')as output:
                    while block:=source.read(1024*1024):output.write(block)
                target.chmod(0o755 if mode&0o111 else 0o644)
    binary=root/'chrome-linux64/chrome';binary.chmod(0o755)
    result=subprocess.run([str(binary),'--version'],capture_output=True,text=True,timeout=30,check=True)
    if not re.search(r'\b145\.0\.7632\.6\b',result.stdout):raise RuntimeError('installed Chrome native version differs')
    with binary.open('rb')as source:binary_sha=hashlib.file_digest(source,'sha256').hexdigest()
    info.write_text(json.dumps({'browser_version':metadata['browser_version'],'binary':str(binary),
        'binary_sha256':binary_sha,'archive_sha256':metadata['sha256']},indent=2)+'\n')
    print('Verified original headed Chrome145.0.7632.6 archive, native version and binary SHA256')


if __name__=='__main__':
    install(json.loads(Path('/opt/chrome/browser.json').read_text()),Path('/opt/chrome-browser'),Path('/opt/chrome/browser-info.json'))
