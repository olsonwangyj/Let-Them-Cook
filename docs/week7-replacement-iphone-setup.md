# Replacement iPhone: one-time maintenance setup

Use this on the replacement iPhone after installing iSH, OpenSSH, Python and
OpenSSL and connecting that Phone's own NUS VPN. Keep the original Phone's
saved evidence. This creates the replacement Phone's independent result SSH
forward and temporary maintenance access; it does not run packet tests.

Copy the whole shell block into foreground iSH. OpenSSH prompts for the two
passwords through the terminal; no password belongs in this block or its logs.
The existing verified Ed25519 host keys are the complete SSH trust set. Conflicting
scoped files, a locked account, an occupied local port, or a bad download stop
the attempt. If a later step fails, only this newly created master is closed.

The original source and ready-to-copy text are retained under
`D:\LetThemCook-builds\iphone-control-20260908\w7-fd3c60de` as
`replacement-setup.py` and `replacement-setup-command.txt`. The command text is
4,244 bytes, SHA-256 `5b14bbc70cefd7354ea3348be8ebf90bce8859ecaacddf24af1393eaa4f937d5`.
The separate manifest records source and dependency hashes. Five isolated
control-flow cases passed (success, bad hash, failed SSH, conflicting config,
locked account); root identity/permissions and subprocesses were simulated,
so these are not physical Phone acceptance results. Python 3.8 grammar passed.

```sh
python3 - <<'WEEK7_SETUP'
import hashlib
import os
from pathlib import Path
import socket
import ssl
import stat
import subprocess
import sys
import tempfile

try:
    import spwd
except ImportError:
    raise SystemExit('PHONE_RUNTIME_CHECK: spwd is unavailable; send python3 --version before continuing.')

if sys.version_info < (3, 8):
    raise SystemExit('Python 3.8 or newer is required.')
if os.geteuid() != 0 or not Path('/usr/sbin/sshd').is_file():
    raise SystemExit('Run in the iSH root shell after installing openssh.')
if spwd.getspnam('root').sp_pwdp.startswith('!'):
    raise SystemExit('PHONE_ROOT_LOCKED: stop here and send this message; nothing changed.')
with open('/dev/tty', 'rb'):
    pass
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 19999))
print('Runtime:', sys.version.split()[0], ssl.OPENSSL_VERSION, flush=True)

sshdir = Path.home() / '.ssh'
sshdir.mkdir(mode=0o700, exist_ok=True)
info = sshdir.lstat()
if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
    raise SystemExit('Unsafe .ssh directory; nothing replaced.')
known = sshdir / 'week7-known_hosts'
config = sshdir / 'week7-ish-password.conf'
keys = '''stujump.comp.nus.edu.sg ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILfypXFWxIhmHZ1nZZKsNKIYRZvnXrra4sqWpnBRy66i
makerslab-fpga-35.ddns.comp.nus.edu.sg ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC7by9bvClMnRjk3KKoR+QpRdhuUXhIhVPC1+F2FnV39
'''
settings = f'''Host *
    UserKnownHostsFile "{known}"
    GlobalKnownHostsFile /dev/null
    StrictHostKeyChecking yes
    HostKeyAlgorithms ssh-ed25519
    Port 22
    ServerAliveInterval 15
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
Host week7-jump
    HostName stujump.comp.nus.edu.sg
    User yanjie
    ConnectTimeout 20
Host week7-ultra96
    HostName makerslab-fpga-35.ddns.comp.nus.edu.sg
    User xilinx
    ProxyJump week7-jump
    ConnectTimeout 60
'''
files = [(known, keys), (config, settings)]
for path, content in files:
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077 or path.read_bytes() != content.encode():
            raise SystemExit('Existing setup differs; left unchanged: ' + str(path))
for path, content in files:
    if not path.exists():
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as output:
            output.write(content)
scope = Path(tempfile.mkdtemp(prefix='week7-replacement.', dir=str(sshdir)))
control = str(scope / 'control')
print('Setup folder:', scope, flush=True)
check = ['ssh', '-F', '/dev/null', '-S', control, '-O']
remote = 'week7-ultra96:/var/tmp/cg4002-week7-yanjie-20260907/phone-control-w7-fd3c60de/'
expected = {
    'ish_control-v2.py': 'de224697bd472ecc016c0e72363c7ae7b32e0ae0e5365818fdfcdcbca9ef65ed',
    'control-public.json': 'd25c11cdad0ab0f17adc9ba5ac93fc597eb415e93089aeda5b042c65e340d10e',
}
try:
    subprocess.run(['ssh', '-F', str(config), '-f', '-N', '-T', '-M', '-S', control,
                    '-L', '127.0.0.1:19999:127.0.0.1:9999', 'week7-ultra96'], check=True)
    subprocess.run(check + ['check', '127.0.0.1'], check=True, timeout=10)
    subprocess.run(['scp', '-F', str(config), '-o', 'ControlPath=' + control,
                    '-o', 'ControlMaster=no', '-o', 'BatchMode=yes', '-o', 'ProxyCommand=false',
                    '-o', 'ClearAllForwardings=yes'] + [remote + name for name in expected] + [str(scope)],
                   check=True, timeout=60)
    for name, digest in expected.items():
        if hashlib.sha256((scope / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Downloaded file hash mismatch: ' + name)
    print('CONTROL_FILES_VERIFIED', flush=True)
    subprocess.run([sys.executable, str(scope / 'ish_control-v2.py'), control], check=True)
except BaseException:
    print('SETUP_FAILED; closing only this attempt\'s SSH master.', flush=True)
    try:
        subprocess.run(check + ['exit', '127.0.0.1'], timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        print('Master cleanup needs inspection:', control, flush=True)
    raise
WEEK7_SETUP
```

After `PHONE_CONTROL_READY`, keep iSH foreground and let the Laptop operator
verify the board listener, pin the returned Phone host key, authenticate and
check actual Phone TLS. That marker alone is not proof of working remote
root access. A runtime/account error must be diagnosed from the actual output;
do not bypass host-key checks or change the account password pre-emptively.

The maintenance path, isolation and cleanup requirements are in the
[control guide](week7-iphone-control.md). The v2 download includes the committed
helper's malformed saved-state guard; the older public helper is preserved.
