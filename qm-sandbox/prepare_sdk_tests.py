"""Build the exact original SDK for local HTTP fixtures; never runs original QM/model."""
import json,os,subprocess,sys,tempfile,urllib.request,hashlib
from pathlib import Path
from install_runtime import extract,validate


def prepare(output):
    metadata=json.loads(Path(__file__).with_name('upstream.json').read_text());validate(metadata)
    item=metadata['agent-sandbox-node-sdk'];output=Path(output).resolve()
    if output.exists():raise ValueError('choose a fresh owned SDK test output directory')
    with tempfile.TemporaryDirectory(prefix='abx-qm-sdk-test-install-')as folder:
        archive=Path(folder)/'source.tar.gz';data=urllib.request.urlopen(item['url'],timeout=60).read(item['size']+1)
        if len(data)!=item['size']or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('original SDK source identity differs')
        archive.write_bytes(data);extract(archive,output)
        env={'PATH':os.environ['PATH'],'HOME':folder,'LANG':'C.UTF-8','NODE_OPTIONS':'--use-system-ca'}
        for argv in [['npm','ci','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org'],['npm','run','build']]:
            subprocess.run(argv,cwd=output,env=env,check=True,timeout=180)
    print('Original source-bound SDK test client ready; no QM/model execution')


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: prepare_sdk_tests.py FRESH_OWNED_OUTPUT')
    prepare(sys.argv[1])
