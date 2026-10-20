"""Verify the immutable official archive, then retain the text retail slice."""
import hashlib, json, tarfile, tempfile, urllib.request
from pathlib import Path

def install(meta, root):
    commit = meta['source_commit']
    assert commit == 'fc0055dc4e0a316c3f83133267fbd6faaa770992'
    root.mkdir()
    with tempfile.TemporaryDirectory(prefix='tau2-source-') as private:
        archive = Path(private) / 'source.tar.gz'
        digest = hashlib.sha256()
        size = 0
        with urllib.request.urlopen('https://codeload.github.com/sierra-research/tau2-bench/tar.gz/' + commit, timeout=120) as response, archive.open('xb') as output:
            while (block := response.read(1024 * 1024)):
                size += len(block)
                if size > meta['size']:
                    raise RuntimeError('official archive size exceeded')
                digest.update(block)
                output.write(block)
        assert size == meta['size'] and digest.hexdigest() == meta['sha256'], 'official source size/SHA256 mismatch'
        with tarfile.open(archive) as source:
            for item in source:
                parts = Path(item.name).parts
                relative = Path(*parts[1:])
                if relative.is_absolute() or '..' in relative.parts:
                    raise RuntimeError('invalid source archive path')
                keep = str(relative) in ['pyproject.toml', 'README.md', 'LICENSE'] or str(relative).startswith(('src/tau2/', 'data/tau2/domains/retail/', 'data/tau2/user_simulator/'))
                if not keep or item.isdir():
                    continue
                if not item.isfile() or item.size > 64 * 1024 * 1024:
                    raise RuntimeError('unexpected source member')
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(item) as data, target.open('xb') as output:
                    while (block := data.read(1024 * 1024)):
                        output.write(block)
    (root / 'SOURCE_REV').write_text(commit + '\n')
    print('Verified official tau2 source and retained native text retail domain')
if __name__ == '__main__':
    install(json.loads(Path('/opt/tau2-bootstrap/upstream.json').read_text()), Path('/opt/tau2'))
