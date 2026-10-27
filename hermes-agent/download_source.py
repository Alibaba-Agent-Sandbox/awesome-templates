"""Fetch the immutable upstream archive with bounded retries and exact integrity."""
from __future__ import annotations
import argparse
import datetime
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:return max(0,float(value))
        except ValueError:
            try:return max(0,(parsedate_to_datetime(value)-datetime.datetime.now(datetime.timezone.utc)).total_seconds())
            except (TypeError,ValueError,OverflowError):pass
    return min(2**attempt,8)


def fetch(url: str, output: Path, size: int, sha256: str, *, attempts: int=4,
          budget: float=120, _test_http: bool=False) -> None:
    parsed=urlsplit(url)
    if (parsed.scheme!='https'and not(_test_http and parsed.scheme=='http'and parsed.hostname=='127.0.0.1'))or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('source archive requires verified HTTPS')
    if not 0<size<=256*1024**2 or len(sha256)!=64 or attempts<1 or budget<=0:
        raise ValueError('invalid source download bounds')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    deadline=time.monotonic()+budget
    with tempfile.TemporaryDirectory(prefix='.hermes-source-',dir=output.parent)as directory:
        temporary=Path(directory)/'archive.tar.gz'
        for attempt in range(attempts):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise RuntimeError('pinned Hermes source retry budget exhausted')
            retry_after=None
            try:
                count=0;digest=hashlib.sha256()
                with urlopen(url,timeout=min(30,remaining))as response,temporary.open('wb')as stream:
                    while block:=response.read(1024*1024):
                        count+=len(block)
                        if count>size or time.monotonic()>deadline:raise ValueError('source archive exceeds download bounds')
                        digest.update(block);stream.write(block)
                if count!=size or digest.hexdigest()!=sha256:raise ValueError('pinned Hermes source integrity mismatch')
                os.replace(temporary,output)
                return
            except HTTPError as error:
                retry_after=error.headers.get('Retry-After')
                code=error.code;error.close()
                if code not in {408,429,500,502,503,504}:raise RuntimeError('pinned Hermes source download rejected')from None
            except (URLError,TimeoutError):pass
            if attempt+1==attempts:raise RuntimeError('pinned Hermes source download failed')from None
            delay=retry_delay(retry_after,attempt)
            if delay>=deadline-time.monotonic():raise RuntimeError('pinned Hermes source retry budget exhausted')from None
            time.sleep(delay)


def cached(archive: Path, output: Path, size: int, sha256: str) -> None:
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.hermes-source-',dir=output.parent)as directory:
        temporary=Path(directory)/'archive.tar.gz';count=0;digest=hashlib.sha256()
        with archive.open('rb')as source,temporary.open('wb')as target:
            while block:=source.read(1024*1024):
                count+=len(block)
                if count>size:raise ValueError('source archive exceeds download bounds')
                digest.update(block);target.write(block)
        if count!=size or digest.hexdigest()!=sha256:raise ValueError('pinned Hermes source integrity mismatch')
        os.replace(temporary,output)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--archive',type=Path);args=parser.parse_args()
    metadata=json.loads(Path(__file__).with_name('source.json').read_text())
    if args.archive:cached(args.archive,args.output,metadata['size'],metadata['sha256'])
    else:fetch(metadata['url'],args.output,metadata['size'],metadata['sha256'])
    print('verified pinned Hermes source archive:',metadata['size'],'bytes; sha256:'+metadata['sha256'])

if __name__=='__main__':main()
