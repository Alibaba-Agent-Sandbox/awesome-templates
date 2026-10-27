import importlib.util
from pathlib import Path
import socket
import pytest
spec=importlib.util.spec_from_file_location('dev_services_commands',Path(__file__).with_name('commands.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
PASSWORD='synthetic_local_password_123'

@pytest.fixture(autouse=True)
def setup(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKSPACE',str(tmp_path))
    monkeypatch.setenv('DEV_SERVICES_REDIS_PORT','16379')
    monkeypatch.setenv('DEV_SERVICES_POSTGRES_PORT','5432')
    yield tmp_path
    c.services_stop()


def test_actual_authentication_sql_redis_persistence_and_owned_cleanup(setup,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-must-not-reach-database')
    assert c.services_versions()=={'postgres':'17.11','redis':'8.0.2'}
    assert c.services_start(PASSWORD)=={'postgres':5432,'redis':16379,'running':True,'exposed':False}
    for life in [c._PG,c._REDIS]:
        assert b'synthetic-must-not-reach-database' not in Path('/proc/'+str(life._STATE['process'].pid)+'/environ').read_bytes()
    assert c.services_sql('CREATE TABLE check_value (v integer); INSERT INTO check_value VALUES (42); SELECT v FROM check_value').splitlines()[-1]=='42'
    assert c.services_redis('SET','proof','42')=='OK'
    assert c.services_redis('GET','proof')=='42'
    with pytest.raises(RuntimeError):c._sql('SELECT 1','wrong_password',Path(c._SESSION['private'].name))
    with pytest.raises(RuntimeError):c._redis(['PING'],'wrong_password',Path(c._SESSION['private'].name))
    assert c.services_status()['running']
    assert c.services_stop()=={'running':False}
    assert not c._PG._listener_exists(5432) and not c._REDIS._listener_exists(16379)
    assert (setup/'service-data'/'postgres'/'PG_VERSION').read_text().strip()=='17'
    c.services_start(PASSWORD)
    assert c.services_sql('SELECT v FROM check_value')=='42'
    assert c.services_redis('GET','proof')=='42'
    c.services_stop()


def test_password_bounds_do_not_create_any_data(setup):
    for password in ['', 'short','space inside password 123','x'*129]:
        with pytest.raises(ValueError):c.services_start(password)
    assert list(setup.iterdir())==[]


def test_caller_directory_symlink_and_path_escape_preserved(setup):
    (setup/'existing').mkdir();(setup/'existing'/'caller').write_bytes(b'keep')
    with pytest.raises(ValueError):c.services_start(PASSWORD,data_dir='existing')
    assert (setup/'existing'/'caller').read_bytes()==b'keep'
    (setup/'linked').symlink_to('/tmp',target_is_directory=True)
    for path in ['linked','../outside','/tmp/outside','nested/path']:
        with pytest.raises(ValueError):c.services_start(PASSWORD,data_dir=path)
    assert not c._SESSION


def test_unrelated_listener_is_never_stopped(setup):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind(('0.0.0.0',16379));listener.listen()
        with pytest.raises(RuntimeError,match='already in use'):c.services_start(PASSWORD)
        c.services_stop();assert c._REDIS._listener_exists(16379)
    assert list(setup.iterdir())==[]


def test_unsafe_actions_and_empty_sql_are_rejected(setup):
    for action in ['CONFIG','SHUTDOWN','ACL','FLUSHALL']:
        with pytest.raises(ValueError):c.services_redis(action)
    with pytest.raises(ValueError):c.services_sql('')
    assert c.services_status()=={'running':False}


def test_actual_self_test_preserves_caller_file_and_removes_nonce_data(setup):
    (setup/'caller').write_bytes(b'keep')
    assert c.services_self_test()=='POSTGRES_REDIS_OK'
    assert sorted(x.name for x in setup.iterdir())==['caller']
    assert (setup/'caller').read_bytes()==b'keep'


def test_configured_redis_port_preserves_foreign_default_listener(setup,monkeypatch):
    monkeypatch.setenv('DEV_SERVICES_REDIS_PORT','16479')
    with socket.socket() as foreign:
        foreign.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);foreign.bind(('0.0.0.0',16379));foreign.listen()
        assert c.services_self_test()=='POSTGRES_REDIS_OK'
        assert c._REDIS._listener_exists(16379)
        assert not c._REDIS._listener_exists(16479)
        assert not c._PG._listener_exists(5432)
        assert list(setup.iterdir())==[]


@pytest.mark.parametrize('postgres,redis',[(True,16379),(5432,5432),(9000,16379),(5432,65536),(1023,16379)])
def test_invalid_ports_refuse_before_data_mutation(setup,postgres,redis):
    with pytest.raises(ValueError):c.services_start(PASSWORD,postgres_port=postgres,redis_port=redis)
    assert list(setup.iterdir())==[]
