"""Use the guest kernel's assigned interface address, not a proxy-selected source."""
import ast,fcntl,ipaddress,socket,struct
from pathlib import Path
import pytest
source=ast.parse(Path(__file__).with_name('worker.py').read_text())
function=next(n for n in source.body if isinstance(n,ast.FunctionDef)and n.name=='address')
namespace={'fcntl':fcntl,'ipaddress':ipaddress,'socket':socket,'struct':struct}
exec(compile(ast.Module(body=[function],type_ignores=[]),'worker.py','exec'),namespace)
address=namespace['address']

class Probe:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def fileno(self):return 123
    def connect(self,*args):pass
    def getsockname(self):return ('169.254.2.3',12345)

def install(monkeypatch,values):
    monkeypatch.setattr(socket,'socket',lambda *args:Probe())
    monkeypatch.setattr(socket,'if_nameindex',lambda:list(enumerate(values,1)))
    def ioctl(fd,request,arg):
        name=arg.split(b'\0',1)[0].decode()
        return b'\0'*20+socket.inet_aton(values[name])+b'\0'*8
    monkeypatch.setattr(fcntl,'ioctl',ioctl)

def test_kernel_assigned_ip_wins_over_intercepted_udp_source(monkeypatch):
    install(monkeypatch,{'lo':'127.0.0.1','link':'169.254.2.3','eth0':'198.18.0.2'})
    assert address()=='198.18.0.2'

def test_missing_valid_assigned_address_fails_without_inventing_endpoint(monkeypatch):
    install(monkeypatch,{'lo':'127.0.0.1','link':'169.254.2.3'})
    with pytest.raises(RuntimeError,match='assigned non-link-local'):address()
