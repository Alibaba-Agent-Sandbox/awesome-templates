"""Install only original encrypted data; protected source stays encrypted in images."""
import hashlib
import importlib.metadata
import json
import urllib.request
from pathlib import Path

ROOT=Path('/opt/appworld-bootstrap')


def verify_package(meta):
    site=Path('/opt/appworld-venv/lib/python3.13/site-packages')
    matches=[value for value in importlib.metadata.distributions(path=[str(site)]) if value.metadata['Name'].lower()=='appworld']
    if len(matches)!=1:
        raise RuntimeError('fixed native AppWorld distribution unavailable')
    distribution=matches[0]
    if distribution.version!=meta['version']:
        raise RuntimeError('installed native AppWorld version differs')
    package=Path(distribution.locate_file('appworld')).resolve()
    for name,digest in meta['protected_bundles'].items():
        path=package/name
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                raise RuntimeError('original encrypted package bundle differs')
    if (package/'apps/amazon').exists():
        raise RuntimeError('protected app source must remain encrypted in distributable image')
    return package


def install():
    meta=json.loads((ROOT/'upstream.json').read_text())
    verify_package(meta)
    data=meta['data']
    if data['url']!='https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.1.0.bundle':
        raise RuntimeError('unreviewed original data URL')
    target=ROOT/'data.bundle'
    digest=hashlib.sha256()
    size=0
    with urllib.request.urlopen(data['url'],timeout=120) as source,target.open('xb') as output:
        while block:=source.read(1024*1024):
            size+=len(block)
            if size>data['size']:
                raise RuntimeError('original encrypted data exceeds expected bound')
            digest.update(block)
            output.write(block)
    if size!=34280074 or digest.hexdigest()!=data['sha256']:
        target.unlink()
        raise RuntimeError('original encrypted data integrity differs')
    print('Verified native AppWorld0.1.3.post1 and original encrypted source/data; no protected unpack during image build')


if __name__=='__main__':
    install()
