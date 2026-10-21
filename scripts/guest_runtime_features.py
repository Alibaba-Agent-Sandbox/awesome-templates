
import errno,json,os,platform,shutil,subprocess
from pathlib import Path
release={}
for line in Path('/etc/os-release').read_text().splitlines():
 k,_,v=line.partition('=')
 if k in ['ID','VERSION_ID']:release[k]=v.strip('"')
result={'uid':os.geteuid(),'system':platform.system(),'machine':platform.machine(),'os_release':release,'devices':{x:Path(x).exists()for x in ['/dev/kvm','/dev/dri','/dev/net/tun','/var/run/docker.sock']},'programs':{x:bool(shutil.which(x))for x in ['docker','podman','qemu-system-x86_64','emulator','adb','hyprctl','pacman','systemctl','unshare']},'memory_mib':int(Path('/proc/meminfo').read_text().split('MemTotal:')[1].split()[0])//1024}
try:
 fd=os.open('/dev/kvm',os.O_RDWR);os.close(fd);result['kvm_open']='PASS'
except OSError as exc:result['kvm_open']={'errno':exc.errno,'kind':errno.errorcode.get(exc.errno,'UNKNOWN')}
for name,args in [('user_namespace',['unshare','-Ur','true']),('mount_namespace',['unshare','-m','true'])]:
 try:r=subprocess.run(args,capture_output=True,timeout=5);result[name]={'exit_code':r.returncode}
 except Exception as exc:result[name]={'error_type':type(exc).__name__}
print(json.dumps(result),flush=True)
