import hashlib,json,pathlib,shutil,subprocess,sys,tempfile
source=pathlib.Path('/tmp/original-tests.py').read_bytes()
assert hashlib.sha256(source).hexdigest()=='6572f0585e3be203aa51a624834b4da96cf0ccc7532de3c00bdf2638e3d81270'
for turn in ('first','final'):
 with tempfile.TemporaryDirectory(prefix='abx-original-tests-') as temporary:
  root=pathlib.Path(temporary);(root/'tests').mkdir();(root/'tests/test_aggregate.py').write_bytes(source)
  shutil.copyfile('/tmp/downloads/'+turn+'/aggregate.py',root/'aggregate.py')
  r=subprocess.run([sys.executable,'-I','-m','unittest','discover','-s',str(root/'tests'),'-v'],capture_output=True,timeout=40)
  assert r.returncode==0,(turn,'independent_original_tests_failed')
  assert b'Ran 3 tests' in r.stderr
print(json.dumps({'downloadedFirstVersionOriginalTests':3,'downloadedFinalVersionOriginalTests':3,'allPassed':True,'network':'none'}))
