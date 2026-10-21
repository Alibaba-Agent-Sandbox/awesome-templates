"""Only sanitized startup vocabulary leaves the owned original process boundary."""
import ast
from pathlib import Path
import re

source=ast.parse(Path(__file__).with_name('worker.py').read_text())
function=next(node for node in source.body if isinstance(node,ast.FunctionDef)and node.name=='startup_words')
namespace={'re':re}
exec(compile(ast.Module(body=[function],type_ignores=[]),'worker.py','exec'),namespace)
startup_words=namespace['startup_words']

def test_startup_vocabulary_omits_paths_addresses_credentials_and_opaque_values():
    result=startup_words([b'time=2026 level=fatal msg="failed to open /tmp/private-state/db: missing file at https://private.invalid/xyz"\nserver token super-private-key\nfailed on sandbox-12345 at 10.2.3.4\n',b''])
    assert 'failed to open'in result and 'missing file'in result
    assert all(value not in result for value in ['private-state','private.invalid','super-private-key','12345','10.2.3.4'])
    assert re.fullmatch('[a-z _-]*',result)

def test_startup_vocabulary_is_bounded_and_omits_invalid_bytes():
    assert len(startup_words([b'failed '*1000,b'\xff']))<=600
