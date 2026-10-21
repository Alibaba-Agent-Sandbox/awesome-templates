"""Read-only image provenance and fixed native browser path."""
import hashlib,json,re
from pathlib import Path


def browser():
    value=json.loads(Path('/opt/chrome/browser-info.json').read_text())
    path=Path(value['binary']).resolve(strict=True)
    if value.get('browser_version')!='145.0.7632.6'or not path.is_relative_to('/opt/chrome-browser')or not path.is_file():raise RuntimeError('invalid fixed native Chrome provenance')
    if value.get('archive_sha256')!='b5e3195041af345a668d110f5daf5581961fa3608626ea588c97dd0fe81c4e38':raise RuntimeError('native Chrome archive differs from reviewed asset')
    with path.open('rb')as source:
        if hashlib.file_digest(source,'sha256').hexdigest()!=value.get('binary_sha256'):raise RuntimeError('actual native Chrome binary integrity differs')
    return str(path),value
