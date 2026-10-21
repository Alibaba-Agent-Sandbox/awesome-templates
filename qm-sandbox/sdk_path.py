"""Authored bounded path operations; invoked through the actual SDK shell API."""
import json
from pathlib import Path
import sys


def operate(action,root,path):
    root=Path(root).resolve(strict=True)
    if not root.is_dir():raise ValueError('backend root must be an existing directory')
    if not isinstance(path,str)or len(path.encode())>4096 or '\0'in path:raise ValueError('invalid bounded relative path')
    unresolved=root/path
    if action=='remove'and unresolved.is_symlink():raise ValueError('cannot remove symlink target')
    candidate=unresolved.resolve()
    if not candidate.is_relative_to(root):raise ValueError('path outside selected backend root')
    if action=='provision':return str(root)
    if action=='read':
        if not candidate.is_file():raise FileNotFoundError('backend file absent')
        if candidate.stat().st_size>1024*1024:raise ValueError('backend file exceeds1MiB')
    elif action=='write':
        if candidate==root:raise ValueError('cannot replace backend root')
        candidate.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        if not candidate.parent.resolve().is_relative_to(root):raise ValueError('parent escaped backend root')
    elif action=='list':
        if not candidate.is_dir():raise NotADirectoryError('backend directory absent')
        names=[]
        for item in candidate.iterdir():
            names.append(item.name)
            if len(names)>1024:raise ValueError('backend directory exceeds1024entries')
        names=sorted(names)
        if len(json.dumps(names,ensure_ascii=False).encode())>32768:raise ValueError('backend directory response exceeds32KiB')
        return names
    elif action=='remove':
        if candidate==root:raise ValueError('cannot remove caller backend root')
        if candidate.is_symlink():raise ValueError('cannot remove symlink target')
        if candidate.exists():
            import shutil
            if candidate.is_dir():shutil.rmtree(candidate)
            else:candidate.unlink()
        if candidate.exists():raise RuntimeError('owned backend target still present')
        return True
    else:raise ValueError('unsupported path operation')
    return str(candidate)


if __name__=='__main__':
    try:
        print(json.dumps({'result':operate(*sys.argv[1:])}))
    except Exception as exc:
        print(json.dumps({'error_type':type(exc).__name__}))
        raise SystemExit(1)
