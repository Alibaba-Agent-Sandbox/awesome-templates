"""Forward the pinned SDK's accepted local connect extensionId parameter."""
import hashlib
from pathlib import Path
import sys

ORIGINAL_SHA256 = '38ec56a2a1af1fb72c3e361a66b256def8e3665cca527e0d337f8a76a8308bd1'
OLD = b'extension: { localExtensionDir: STAGEHAND_EXTENSION_DIRECTORY_PATH },'
NEW = b'extension: parsed.extensionId ? { extensionId: parsed.extensionId } : { localExtensionDir: STAGEHAND_EXTENSION_DIRECTORY_PATH },'


def patched(data):
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256 or data.count(OLD) != 1:
        raise ValueError('unreviewed upstream SDK bytes; compatibility patch refused')
    return data.replace(OLD, NEW, 1)


if __name__ == '__main__':
    target = Path(sys.argv[1])
    value = patched(target.read_bytes())
    target.write_bytes(value)
    print('stagehand_connect_patch_sha256='+hashlib.sha256(value).hexdigest())
