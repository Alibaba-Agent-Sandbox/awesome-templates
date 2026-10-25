#!/usr/bin/env python3
"""Validate a public CI image archive and transfer it using RAM-only ACR auth.

The image is built by the repository's existing keyless L1 workflow. This tool
never emulates Docker build or claims platform-step execution. Private output and
ownership journals must stay outside the checkout; no credentials are written.
"""
from __future__ import annotations
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime,timezone
from email.utils import format_datetime
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
import yaml
try:
    from .ci_image import context_sha256,server_version,validate_resources
except ImportError:
    from ci_image import context_sha256,server_version,validate_resources

GITHUB='https://api.github.com/repos/Alibaba-Agent-Sandbox/awesome-templates'
REGION='cn-hangzhou'
REGISTRY='registry.cn-hangzhou.aliyuncs.com'
MAX_ARCHIVE=8*1024**3
MAX_ZIP=2*1024**3


def _json_request(url,headers=None,method='GET'):
    req=urllib.request.Request(url,headers=headers or {},method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as response:
            raw=response.read(4*1024*1024)
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError('remote API HTTP '+str(exc.code)) from None


def github(path):
    if not path.startswith('/') or path.startswith('//'):raise ValueError('relative repository API path required')
    headers={'Accept':'application/vnd.github+json','User-Agent':'AgentSandbox-CI-Image-Review'}
    token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:headers['Authorization']='Bearer '+token
    return _json_request(GITHUB+path,headers)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def artifact_download(artifact_id: int, target: Path) -> dict:
    artifact=github('/actions/artifacts/'+str(artifact_id))
    if artifact.get('expired') or not artifact.get('name','').startswith('image-'):raise ValueError('artifact is expired or not an image')
    if not 0<artifact.get('size_in_bytes',0)<MAX_ZIP:raise ValueError('artifact exceeds compressed size budget')
    headers={'User-Agent':'AgentSandbox-CI-Image-Review'}
    token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:headers['Authorization']='Bearer '+token
    request=urllib.request.Request(GITHUB+'/actions/artifacts/'+str(artifact_id)+'/zip',headers=headers)
    try:
        urllib.request.build_opener(NoRedirect()).open(request,timeout=60)
        raise RuntimeError('expected a signed artifact redirect')
    except urllib.error.HTTPError as exc:
        if exc.code!=302:raise RuntimeError('artifact redirect HTTP '+str(exc.code)) from None
        location=exc.headers['Location']
    if urllib.parse.urlparse(location).scheme!='https':raise ValueError('artifact download must be HTTPS')
    # The signed location remains only in memory. Never forward GitHub headers.
    total=0;digest=hashlib.sha256()
    with urllib.request.urlopen(location,timeout=120) as response,target.open('xb') as output:
        while chunk:=response.read(4*1024*1024):
            total+=len(chunk)
            if total>MAX_ZIP:raise ValueError('download exceeds compressed size budget')
            digest.update(chunk);output.write(chunk)
    expected=artifact.get('digest')
    if expected and expected!='sha256:'+digest.hexdigest():raise ValueError('GitHub artifact ZIP digest mismatch')
    return artifact


def archive_runtime(archive: Path) -> tuple[str,bytes]:
    """Inspect actual image config and final commands bytes, honoring whiteouts."""
    with tarfile.open(archive) as image:
        manifest_entry=image.getmember('manifest.json')
        if not manifest_entry.isfile() or manifest_entry.size>1024*1024:raise ValueError('invalid image manifest')
        manifest=json.load(image.extractfile(manifest_entry))
        if not isinstance(manifest,list) or len(manifest)!=1:raise ValueError('exactly one Docker archive image is required')
        entry=manifest[0];config_entry=image.getmember(entry['Config'])
        if not config_entry.isfile() or config_entry.size>4*1024*1024:raise ValueError('invalid image config')
        config_bytes=image.extractfile(config_entry).read();config=json.loads(config_bytes)
        if config.get('os')!='linux' or config.get('architecture')!='amd64':raise ValueError('only the tested Linux amd64 image profile is supported')
        if config.get('config',{}).get('User')!='user' or config.get('config',{}).get('WorkingDir')!='/home/user/app':raise ValueError('image must select non-root user and reviewed workspace')
        wanted='home/user/app/commands.py'
        ancestors={'home','home/user','home/user/app'}
        deletions={'.wh.home','home/.wh.user','home/user/.wh.app','home/user/app/.wh.commands.py',
                   '.wh..wh..opq','home/.wh..wh..opq','home/user/.wh..wh..opq','home/user/app/.wh..wh..opq'}
        for name in reversed(entry['Layers']):
            layer_entry=image.getmember(name)
            if not layer_entry.isfile() or layer_entry.size>MAX_ARCHIVE:raise ValueError('invalid layer')
            found=None;hidden=False
            with tarfile.open(fileobj=image.extractfile(layer_entry),mode='r|*') as layer:
                for member in layer:
                    path=member.name.removeprefix('./').lstrip('/')
                    if path in deletions or path in ancestors and not member.isdir():hidden=True
                    if path==wanted:
                        if not member.isfile() or member.size>1024*1024:raise ValueError('runtime commands must be a regular bounded file')
                        found=layer.extractfile(member).read()
            if found is not None:return hashlib.sha256(config_bytes).hexdigest(),found
            if hidden:raise ValueError('a later layer hides or deletes runtime commands')
    raise ValueError('image contains no final runtime commands')


def verify_source(source: Path, checkout: str, expected: dict[str,str]) -> None:
    root=Path(subprocess.check_output(['git','-C',str(source),'rev-parse','--show-toplevel'],text=True).strip())
    relative=str(source.resolve().relative_to(root))
    for name,digest in expected.items():
        filename='template.yaml' if name=='template.yaml:contract' else name
        result=subprocess.run(['git','-C',str(root),'show',checkout+':'+relative+'/'+filename],capture_output=True)
        if result.returncode:raise ValueError('reviewed image source is unavailable; fetch the exact public checkout first')
        content=result.stdout
        if name=='template.yaml:contract':
            data=yaml.safe_load(content);content=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
        if hashlib.sha256(content).hexdigest()!=digest:raise ValueError('current source differs from the actual CI image checkout: '+filename)


def validate_archive_origin(metadata: dict, workflow: dict) -> None:
    """Accept only the explicit reviewed export paths, retaining public package provenance."""
    origin = metadata.get('origin')
    if origin == 'template-image-l1' and workflow.get('path') == '.github/workflows/image-build.yml':
        if not isinstance(metadata.get('server_package_version'), str):
            raise ValueError('L1 export requires its verified public server package version')
        return
    if origin != 'public-template-launch' or workflow.get('path') != '.github/workflows/public-template-launch.yml':
        raise ValueError('image export has an unrecognized workflow origin')
    if metadata.get('public_source_commit') != metadata.get('source_head_commit'):
        raise ValueError('public image export must identify its pinned public input separately from the verifier')
    if not re.fullmatch(r'[a-f0-9]{64}', str(metadata.get('source_snapshot_digest', ''))):
        raise ValueError('public image export lacks its observed CLI source snapshot')
    packages = metadata.get('installed_packages', {})
    if packages.get('distribution') != 'published':
        raise ValueError('public image export requires published-package acceptance')
    for key, registry in [('cli', 'https://registry.npmjs.org'),
                          ('python_client', 'https://pypi.org/simple'),
                          ('python_server', 'https://pypi.org/simple')]:
        package = packages.get(key, {})
        if package.get('registry') != registry or not isinstance(package.get('version'), str):
            raise ValueError('public image export lacks official package provenance')
    if not isinstance(metadata.get('server_package_version'), str) or not metadata['server_package_version']:
        raise ValueError('public image export lacks observed runtime server version')


def validate_archive_revisions(metadata: dict, workflow: dict, artifact: dict, name: str) -> None:
    """Keep public template input revisions distinct from verifier workflow revisions."""
    checkout, head = metadata['checkout_commit'], metadata['source_head_commit']
    if not all(isinstance(value, str) and re.fullmatch(r'[a-f0-9]{40}', value) for value in (checkout, head)):
        raise ValueError('image export needs immutable public source revisions')
    verifier = metadata.get('verifier_commit') if metadata.get('origin') == 'public-template-launch' else head
    if not isinstance(verifier, str) or not re.fullmatch(r'[a-f0-9]{40}', verifier):
        raise ValueError('public image export needs a distinct verifier commit')
    if workflow['event'] != 'workflow_dispatch' or checkout != head or workflow['head_sha'] != verifier or artifact['workflow_run']['head_sha'] != verifier:
        raise ValueError('use a completed explicit exact-source image export')
    if str(metadata['workflow_run_id']) != str(workflow['id']) or artifact['name'] != 'image-' + name + '-' + verifier:
        raise ValueError('CI identity mismatch')


def download_verified(artifact_id: int, source: Path, output: Path) -> dict:
    source=source.resolve()
    validate_resources(yaml.safe_load((source/'template.yaml').read_text()))
    if output.resolve().is_relative_to(source.parent):raise ValueError('image staging must stay outside the repository')
    output.mkdir(parents=True,exist_ok=False);output.chmod(0o700)
    archive_zip=output/'artifact.zip';artifact=artifact_download(artifact_id,archive_zip)
    template=yaml.safe_load((source/'template.yaml').read_text());name=template['name']
    archive_name=name+'-image.tar';metadata_name=name+'-image-metadata.json'
    allowed={archive_name,archive_name+'.sha256',metadata_name}
    with zipfile.ZipFile(archive_zip) as archive:
        if set(archive.namelist())!=allowed:raise ValueError('unexpected artifact members')
        size=archive.getinfo(archive_name).file_size
        if not 0<size<MAX_ARCHIVE or size+256*1024**2>shutil.disk_usage(output).free:raise ValueError('insufficient image archive budget/free space')
        for filename in allowed:
            with archive.open(filename) as data,(output/filename).open('xb') as target:shutil.copyfileobj(data,target,4*1024*1024)
    archive_zip.unlink()
    metadata=json.loads((output/metadata_name).read_text())
    with (output/archive_name).open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=metadata['archive_sha256'] or digest!=(output/(archive_name+'.sha256')).read_text().split()[0]:raise ValueError('Docker archive SHA256 mismatch')
    if metadata.get('format')!='docker-archive' or metadata.get('template')!=name or metadata.get('repository','').lower()!='alibaba-agent-sandbox/awesome-templates':raise ValueError('image identity mismatch')
    if metadata.get('server_package_version')!=server_version(source):raise ValueError('CI server package version mismatch')
    run=github('/actions/runs/'+str(artifact['workflow_run']['id']))
    if run.get('status')!='completed' or run.get('conclusion')!='success':
        raise ValueError('image CI workflow is not successful')
    validate_archive_origin(metadata,run)
    checkout=metadata['checkout_commit'];head=metadata['source_head_commit']
    validate_archive_revisions(metadata,run,artifact,name)
    context=context_sha256(source);verify_source(source,checkout,context)
    config_hash,commands=archive_runtime(output/archive_name)
    if metadata['local_image_id']!='sha256:'+config_hash or commands!=(source/'commands.py').read_bytes():raise ValueError('actual image config/runtime bytes mismatch')
    proof={'schema_version':1,'verification_type':'ci-docker-archive','template':name,'template_version':str(template['version']),
        'github_repository':'Alibaba-Agent-Sandbox/awesome-templates','source_head_commit':head,'checkout_commit':checkout,
        'workflow_run_id':str(run['id']),'artifact_id':str(artifact_id),'archive_sha256':digest,'image_config_sha256':config_hash,
        'server_package_version':server_version(source),'context_sha256':context,'artifact_verified':True,'image_context_verified':True,'image_non_root':True,
        'registry_push_verified':False,'registry_private_repo_verified':False,'registry_credentials_storage':'anonymous RAM fd'}
    if metadata.get('origin') == 'public-template-launch':
        origin={key: metadata[key] for key in ('origin','installed_packages','server_package_version')}
        origin.update({key:metadata[key] for key in ('verifier_commit','public_source_commit','source_snapshot_digest')})
        (output/'public-package-origin.json').write_text(json.dumps(origin,indent=2)+'\n')
    (output/'validated-image.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof


def acr_request(method: str,path: str):
    if not path.startswith('/') or path.startswith('//'):raise ValueError('relative ACR API path required')
    access=os.environ['ALICLOUD_ACCESS_KEY_ID'];secret=os.environ['ALICLOUD_ACCESS_KEY_SECRET']
    headers={'Accept':'application/json','Content-Type':'application/json','Date':format_datetime(datetime.now(timezone.utc),usegmt=True),
        'x-acs-signature-method':'HMAC-SHA1','x-acs-signature-nonce':str(uuid.uuid4()),'x-acs-signature-version':'1.0','x-acs-version':'2016-06-07'}
    canonical=''.join(k+':'+headers[k].strip()+'\n' for k in sorted(headers) if k.startswith('x-acs-'))
    text=method+'\napplication/json\n\napplication/json\n'+headers['Date']+'\n'+canonical+path
    headers['Authorization']='acs '+access+':'+base64.b64encode(hmac.new(secret.encode(),text.encode(),hashlib.sha1).digest()).decode()
    return _json_request('https://cr.'+REGION+'.aliyuncs.com'+path,headers,method)


def temporary_registry_credentials() -> tuple[str,str]:
    data=acr_request('GET','/tokens')['data']
    user,token=data['tempUserName'],data['authorizationToken']
    if not isinstance(user,str) or not user or not isinstance(token,str) or not token:raise ValueError('registry token response is incomplete')
    return user,token


@contextmanager
def ram_registry_auth(username: str,password: str):
    """A symlink contains only an fd number; actual auth bytes live in anonymous RAM."""
    if not hasattr(os,'memfd_create'):raise RuntimeError('Linux anonymous RAM auth is required')
    descriptor=os.memfd_create('abx-acr-auth',os.MFD_CLOEXEC)
    folder=Path(tempfile.mkdtemp(prefix='abx-acr-ram-auth-'));folder.chmod(0o700)
    try:
        auth=base64.b64encode((username+':'+password).encode()).decode()
        os.write(descriptor,json.dumps({'auths':{REGISTRY:{'auth':auth}}}).encode());os.lseek(descriptor,0,os.SEEK_SET)
        (folder/'config.json').symlink_to('/proc/self/fd/'+str(descriptor))
        yield {'PATH':os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin'),'DOCKER_CONFIG':str(folder)},(descriptor,)
        if not (folder/'config.json').is_symlink():raise RuntimeError('registry client attempted persistent auth storage')
    finally:
        os.close(descriptor);shutil.rmtree(folder)


def crane_call(binary: str,args: list[str],username: str,password: str,timeout: int) -> str:
    with ram_registry_auth(username,password) as (env,descriptors):
        result=subprocess.run([binary,*args],env=env,pass_fds=descriptors,capture_output=True,text=True,timeout=timeout,start_new_session=True)
    if result.returncode:raise RuntimeError('registry client failed; sensitive output omitted')
    return result.stdout.strip()


def save_private(path: Path,data: dict):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    descriptor,temporary=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(descriptor,'w') as stream:
            json.dump(data,stream);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def repo_is_private(metadata) -> bool:
    kinds=[]
    def walk(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key.replace('_','').lower()=='repotype':kinds.append(item)
                else:walk(item)
        elif isinstance(value,list):
            for item in value:walk(item)
    walk(metadata)
    return bool(kinds) and all(kind=='PRIVATE' for kind in kinds)


def owned_registry_cleanup(journal: dict,path: Path) -> bool:
    if journal.get('preflight_absent') is not True or journal.get('push_attempted') is not True:return False
    if journal.get('namespace')!=os.environ.get('ACR_NAMESPACE') or journal.get('owned_tags')!=['source-guard','review']:
        raise ValueError('registry ownership context differs from the active account namespace')
    namespace=urllib.parse.quote(journal['namespace'],safe='');name=journal['repository']
    if not re.fullmatch(r'e2e-ci-image-[a-f0-9]{16}',name):raise ValueError('unowned registry cleanup identifier')
    base='/repos/'+namespace+'/'+name
    for target in [base+'/tags/source-guard',base+'/tags/review',base]:
        try:acr_request('DELETE',target)
        except RuntimeError as exc:
            if str(exc)!='remote API HTTP 404':raise
        deadline=time.monotonic()+60
        while True:
            try:acr_request('GET',target)
            except RuntimeError as exc:
                if str(exc)=='remote API HTTP 404':break
                raise
            if time.monotonic()>deadline:return False
            time.sleep(1)
    journal['cleanup_verified']=True;save_private(path,journal)
    return True


def push_verified(stage: Path,source: Path,binary: str,journal_path: Path) -> tuple[str,dict,dict]:
    proof=json.loads((stage/'validated-image.json').read_text());name=proof['template']
    if proof['context_sha256']!=context_sha256(source):raise ValueError('source changed after archive validation')
    archive=stage/(name+'-image.tar')
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=proof['archive_sha256']:raise ValueError('archive changed after validation')
    namespace=os.environ['ACR_NAMESPACE']
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]*',namespace):raise ValueError('invalid ACR namespace')
    repository='e2e-ci-image-'+uuid.uuid4().hex[:16]
    base='/repos/'+urllib.parse.quote(namespace,safe='')+'/'+repository
    journal={'namespace':namespace,'repository':repository,'tag':'review','owned_tags':['source-guard','review'],'preflight_absent':False,'push_attempted':False}
    if journal_path.exists():raise ValueError('refuse ownership journal reuse')
    save_private(journal_path,journal)
    try:acr_request('GET',base)
    except RuntimeError as exc:
        if str(exc)!='remote API HTTP 404':raise
        journal['preflight_absent']=True
    else:raise ValueError('registry name unexpectedly already exists')
    journal['push_attempted']=True;save_private(journal_path,journal)
    username,password=temporary_registry_credentials()
    tagged=REGISTRY+'/'+namespace+'/'+repository+':review'
    # Bootstrap contains only this tool's public empty-image metadata. Check
    # server-enforced privacy before any reviewed platform/base content is sent.
    guard=stage/'source-guard.tar'
    empty=json.dumps({'architecture':'amd64','os':'linux','config':{},'rootfs':{'type':'layers','diff_ids':[]},'history':[]},separators=(',',':')).encode()
    filename=hashlib.sha256(empty).hexdigest()+'.json'
    manifest=json.dumps([{'Config':filename,'RepoTags':['source-guard:review'],'Layers':[]}]).encode()
    with tarfile.open(guard,'w') as output:
        for key,content in [(filename,empty),('manifest.json',manifest)]:
            entry=tarfile.TarInfo(key);entry.size=len(content);output.addfile(entry,io.BytesIO(content))
    crane_call(binary,['push',str(guard),REGISTRY+'/'+namespace+'/'+repository+':source-guard'],username,password,120)
    if not repo_is_private(acr_request('GET',base)):raise ValueError('registry destination is not private; source image was not uploaded')
    journal['private_destination_verified']=True;save_private(journal_path,journal)
    crane_call(binary,['push',str(archive),tagged],username,password,1200)
    digest=crane_call(binary,['digest',tagged],username,password,90)
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',digest):raise ValueError('registry digest readback is invalid')
    private=repo_is_private(acr_request('GET',base))
    if not private:raise ValueError('registry repository privacy is unconfirmed')
    journal['digest']=digest;save_private(journal_path,journal)
    proof.update(pushed_image_digest=digest,registry_push_verified=True,registry_private_repo_verified=True,
        registration_reference_type='owned tag with digest readback',tag_digest_verified_before_registration=True,tag_digest_verified_after_runtime=False)
    return tagged,proof,journal


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-id',type=int,required=True);parser.add_argument('--template',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();proof=download_verified(args.artifact_id,args.template,args.output)
    print(json.dumps({'template':proof['template'],'archive_verified':True,'source_head_commit':proof['source_head_commit'],'archive_sha256':proof['archive_sha256']}))

if __name__=='__main__':main()
