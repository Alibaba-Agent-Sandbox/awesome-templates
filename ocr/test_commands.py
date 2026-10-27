"""Real process/resource boundaries and synthetic protocol fixtures; real OCR is explicit."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import time
import zlib

from PIL import Image
import pytest

spec=importlib.util.spec_from_file_location('ocr_test_commands',Path(__file__).with_name('commands.py'))
commands=importlib.util.module_from_spec(spec);sys.modules[spec.name]=commands;spec.loader.exec_module(commands)


def alive(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().split()[2]!='Z'
    except FileNotFoundError:return False


def stopped(pid):
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        if not alive(pid):return
        time.sleep(.02)
    pytest.fail('owned descendant survived actual process cleanup')


def script(tmp_path,source):
    path=tmp_path/'worker.py';path.write_text(source);return [sys.executable,str(path),'synthetic-private-argument']


@pytest.mark.parametrize('exit_code',[0,7])
def test_leader_exit_cleans_real_redirected_descendants_and_preserves_foreign_group(tmp_path,exit_code):
    pidfile=tmp_path/'child';foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
    source=f"import subprocess,sys,pathlib; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);pathlib.Path({str(pidfile)!r}).write_text(str(p.pid));sys.exit({exit_code})"
    try:
        code,_,_=commands._process(script(tmp_path,source),cwd=str(tmp_path),timeout=3)
        assert code==exit_code;stopped(int(pidfile.read_text()));assert foreign.poll() is None
    finally:
        os.killpg(foreign.pid,signal.SIGKILL);foreign.wait()


def test_timeout_kills_actual_term_ignoring_group_without_exposing_argv(tmp_path):
    pidfile=tmp_path/'child'
    source=f"import subprocess,sys,pathlib,time,signal;signal.signal(signal.SIGTERM,signal.SIG_IGN);p=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);pathlib.Path({str(pidfile)!r}).write_text(str(p.pid));time.sleep(60)"
    with pytest.raises(RuntimeError,match='wall-clock') as error:commands._process(script(tmp_path,source),cwd=str(tmp_path),timeout=.3)
    assert 'synthetic-private' not in str(error.value);stopped(int(pidfile.read_text()))


def test_cancellation_cleans_real_group_before_leader_reap(tmp_path,monkeypatch):
    ready=tmp_path/'child';original=commands.os.waitid
    def interrupt(*args):
        if ready.exists():raise KeyboardInterrupt
        return original(*args)
    source=f"import subprocess,sys,pathlib,time;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);pathlib.Path({str(ready)!r}).write_text(str(p.pid));time.sleep(60)"
    monkeypatch.setattr(commands.os,'waitid',interrupt)
    with pytest.raises(KeyboardInterrupt):commands._process(script(tmp_path,source),cwd=str(tmp_path),timeout=3)
    stopped(int(ready.read_text()))


def test_both_diagnostic_pipes_are_drained_beyond_pipe_capacity(tmp_path):
    source="import os;os.write(1,b'a'*200000);os.write(2,b'b'*200000)"
    code,out,err=commands._process(script(tmp_path,source),cwd=str(tmp_path),timeout=3)
    assert code==0 and out==b'a'*200000 and err==b'b'*200000


def test_diagnostic_byte_cap_is_a_failure_and_kills_the_writer(tmp_path):
    source="import os,time;os.write(2,b'x'*4000000);time.sleep(60)"
    with pytest.raises(RuntimeError,match='diagnostics exceeded'):commands._process(script(tmp_path,source),cwd=str(tmp_path),timeout=3)


@pytest.fixture
def root(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKSPACE',str(tmp_path));return tmp_path


@pytest.mark.parametrize('value',['../private.png','/etc/passwd','x\x00.png','','\ud800'])
def test_workspace_input_boundary_omits_private_input(root,value):
    with pytest.raises(ValueError):commands.ocr(value)
    assert not list(root.glob('.ocr-*'))


@pytest.mark.parametrize('kind',['symlink','directory','fifo','oversized'])
def test_real_filesystem_types_and_encoded_byte_limit_fail_before_decode(root,kind):
    path=root/'input'
    if kind=='symlink':path.symlink_to('/etc/passwd')
    elif kind=='directory':path.mkdir()
    elif kind=='fifo':os.mkfifo(path)
    else:
        with path.open('wb') as stream:stream.truncate(commands.MAX_INPUT+1)
    with pytest.raises(ValueError):commands.ocr(str(path))
    assert not list(root.glob('.ocr-*'))


def test_symlinked_parent_inside_workspace_is_not_followed(root):
    actual=root/'actual';actual.mkdir();(actual/'input').write_bytes(b'x');(root/'link').symlink_to(actual,target_is_directory=True)
    with pytest.raises(ValueError,match='without symlinks'):commands.ocr('link/input')


@pytest.mark.parametrize('dimensions',[(8193,1),(5000,4000)])
def test_oversized_decompressed_headers_reject_before_pixel_allocation(root,dimensions,monkeypatch):
    def chunk(kind,value):return struct.pack('>I',len(value))+kind+value+struct.pack('>I',zlib.crc32(kind+value)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',*dimensions,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''))+chunk(b'IEND',b'')
    def never_load(self,*args,**kwargs):raise AssertionError('oversized image pixels must not be decoded')
    monkeypatch.setattr(Image.Image,'load',never_load)
    with pytest.raises(ValueError,match='16 million'):commands._normalize(data,root/'output.png')
    assert not (root/'output.png').exists()


def test_non_raster_and_multiframe_inputs_are_not_accepted(root):
    for kind in ('GIF','PNG'):
        stream=io.BytesIO();image=Image.new('RGB',(20,20),'white')
        image.save(stream,format=kind,save_all=True,append_images=[Image.new('RGB',(20,20),'black')])
        with pytest.raises(ValueError):commands._normalize(stream.getvalue(),root/'output.png')


def test_orientation_metadata_is_applied_and_removed(root):
    image=Image.new('RGB',(80,40),'white');exif=Image.Exif();exif[274]=6
    stream=io.BytesIO();image.save(stream,format='JPEG',exif=exif)
    assert commands._normalize(stream.getvalue(),root/'output.png')==(40,80)
    with Image.open(root/'output.png') as result:assert result.mode=='RGB' and not result.getexif()


def test_tsv_rejects_invalid_geometry_nonfinite_confidence_and_malformed_header():
    header='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
    for row in ('5\t1\t1\t1\t1\t1\t0\t0\t999\t2\t90\tword\n','5\t1\t1\t1\t1\t1\t0\t0\t2\t2\tnan\tword\n'):
        with pytest.raises(RuntimeError):commands._words(header+row,10,10)
    with pytest.raises(RuntimeError):commands._words('fake\theader\n',10,10)


def fixture_cli(root,monkeypatch,fail=False):
    executable=root/'fixture-cli';observation=root/'observed.json'
    body=f'''#!{sys.executable}
import sys,os,pathlib,json,resource
if '--version' in sys.argv:
 print('tesseract 5.5.0');sys.exit(0)
pathlib.Path({str(observation)!r}).write_text(json.dumps({{'argv':sys.argv,'env':dict(os.environ),'limits':{{str(k):resource.getrlimit(k) for k in (resource.RLIMIT_AS,resource.RLIMIT_CPU,resource.RLIMIT_FSIZE,resource.RLIMIT_CORE)}}}}))
if {fail!r}:
 print('synthetic-private-diagnostic',file=sys.stderr);sys.exit(7)
pathlib.Path(sys.argv[2]+'.txt').write_text('synthetic\\n')
pathlib.Path(sys.argv[2]+'.tsv').write_text('level\\tpage_num\\tblock_num\\tpar_num\\tline_num\\tword_num\\tleft\\ttop\\twidth\\theight\\tconf\\ttext\\n5\\t1\\t1\\t1\\t1\\t1\\t1\\t1\\t3\\t3\\t99\\tsynthetic\\n')
'''
    executable.write_text(body);executable.chmod(0o700)
    monkeypatch.setenv('OCR_TESSERACT_BINARY',str(executable));monkeypatch.setenv('OCR_TESSDATA_DIR',str(root/'tessdata'))
    (root/'tessdata').mkdir();(root/'tessdata/eng.traineddata').write_bytes(b'fixture')
    image=root/'synthetic-private-$(never-execute).png';Image.new('RGB',(30,20),'white').save(image)
    return image,observation


def test_fixture_protocol_uses_private_argv_preserves_home_drops_keys_and_applies_real_limits(root,monkeypatch):
    image,observed=fixture_cli(root,monkeypatch)
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-private-key');monkeypatch.setenv('ABX_SERVER_TOKEN','synthetic-server-token')
    result=commands.ocr(str(image));data=json.loads(observed.read_text())
    assert {'OPENAI_API_KEY','ABX_SERVER_TOKEN'}.isdisjoint(data['env'])
    assert data['env'].get('HOME')==os.environ.get('HOME')
    assert str(image) not in data['argv'] and all('never-execute' not in item for item in data['argv'])
    assert not Path(data['argv'][1]).exists()
    assert data['limits'][str(__import__('resource').RLIMIT_AS)]==[536870912,536870912]
    assert data['limits'][str(__import__('resource').RLIMIT_FSIZE)]==[4194304,4194304]
    assert data['limits'][str(__import__('resource').RLIMIT_CPU)]==[30,31]
    assert data['limits'][str(__import__('resource').RLIMIT_CORE)]==[0,0]
    assert data['env']['OMP_THREAD_LIMIT']=='1' and data['env']['OMP_NUM_THREADS']=='1'
    directory=Path(result['artifact_dir']);assert directory.stat().st_mode&0o777==0o700
    for path in (result['text_path'],result['tsv_path']):assert Path(path).stat().st_mode&0o777==0o600
    assert hashlib.sha256(Path(result['text_path']).read_bytes()).hexdigest()==result['text_sha256']
    for path in directory.iterdir():path.unlink()
    directory.rmdir()


def test_nonzero_fixture_omits_diagnostics_and_cleans_private_intermediates(root,monkeypatch):
    image,observed=fixture_cli(root,monkeypatch,fail=True)
    with pytest.raises(RuntimeError) as error:commands.ocr(str(image))
    assert 'synthetic-private' not in str(error.value) and not list(root.glob('.ocr-*'))
    assert not Path(json.loads(observed.read_text())['argv'][1]).exists()


def test_concurrent_jobs_refuse_without_queued_image_allocation(root):
    commands._JOB_LOCK.acquire()
    try:
        with pytest.raises(RuntimeError,match='already running'):commands.ocr('anything')
    finally:commands._JOB_LOCK.release()


@pytest.mark.skipif(os.environ.get('OCR_TEST_REAL')!='1',reason='actual pinned Tesseract explicitly required for real OCR case')
def test_actual_pinned_tesseract_reads_real_pixels_and_cleans_its_own_fixture(root):
    assert commands.ocr_smoke()=='Tesseract image/text/TSV artifacts OK'
    assert not list(root.glob('.ocr-*'))
