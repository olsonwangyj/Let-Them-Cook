# iSH locked-root recovery for the replacement iPhone

The actual replacement Phone printed `PHONE_ROOT_LOCKED` before the original
bootstrap wrote files or attempted SSH. Its root password field has a leading
`!`; the exact field has not been collected. Decision 33 selects the documented
iSH `chpasswd -e` remedy with the unusable field `*`, preserving the original
field on Phone before the change. The scoped daemon still requires the one
client key, with password and keyboard-interactive authentication disabled.

This changes the Linux account's eligibility globally inside iSH. The script
first requires no detected `sshd`, `sshd-session`, `sshd-auth` or `dropbear`
process. This process-name check fits the expected installed SSH software; it
is not a universal detector for every authentication service. No listener is
opened by the account operation and global SSH configuration is unchanged.

The original field is saved exclusively, mode 600, under root-owned mode-700
`~/week7-private/ish-root-before-control.txt`, flushed/fsynced before mutation.
The account tool receives its input through stdin; no original value is put
in command arguments or printed. The backup stays only on Phone and must be
excluded from all evidence uploads. An existing backup blocks a second account
mutation rather than being overwritten. If a later SSH step fails after the
account change, the backup remains and the original field is not automatically
restored; either resume setup or use the restore procedure below.

## Resume setup

Copy the whole updated block from
`D:\LetThemCook-builds\iphone-control-20260908\w7-fd3c60de\replacement-key-setup-command.txt`
into foreground iSH on the replacement Phone. It includes the account remedy
only when the actual field is locked, then runs the verified connection setup.
The original setup and its failing observation remain preserved. The updated
block is 6,133 bytes with SHA-256
`902495b5b3ab11b5660de9c2a14c69f1e78e7e7562e11ebd5d426f1b2e6ed5fb`.

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
    if os.geteuid() != 0:
        raise SystemExit('Run this in the replacement iPhone iSH root shell.')
    original = spwd.getspnam('root').sp_pwdp
    if not original.startswith('!') or ':' in original or '\n' in original or '\r' in original:
        raise SystemExit('Root is not in the expected locked state; nothing changed.')
    servers = subprocess.run(['pidof', 'sshd', 'sshd-session', 'sshd-auth', 'dropbear'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    if servers.returncode != 1 or servers.stdout.strip() or servers.stderr.strip():
        raise SystemExit('An SSH server exists or its absence could not be checked; nothing changed.')
    private = Path.home() / 'week7-private'
    private.mkdir(mode=0o700, exist_ok=True)
    info = private.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
        raise SystemExit('Private backup directory is unsafe; nothing changed.')
    backup = private / 'ish-root-before-control.txt'
    fd = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as saved:
        saved.write(original)
        saved.flush()
        os.fsync(saved.fileno())
    if spwd.getspnam('root').sp_pwdp != original:
        raise SystemExit('Account changed during preparation; no change applied by this script.')
    result = subprocess.run(['chpasswd', '-e'], input='root:*\n', text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if result.returncode != 0 or spwd.getspnam('root').sp_pwdp != '*':
        raise SystemExit('Account update needs inspection; private backup retained. Stop here.')
    print('KEY_LOGIN_READY; original locked password field saved privately on this iPhone.')
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
    'restore-ish-root-lock.py': '144e550e49f2e0bd818054c5b1b1e38c79ae1475a51268c465072c22497fb81a',
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
    print('Restore helper:', scope / 'restore-ish-root-lock.py', flush=True)
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

After the update, the script checks the field is exactly `*`. It then uses the
existing strict host pins, fresh own result master, hashed downloads and scoped
key-only helper. The download includes `restore-ish-root-lock.py`; its actual
Phone path is printed before helper startup. No Phone authentication or packet
pass is implied by the local test results or prepared scripts.

## Restore after maintenance, including when download failed

First shut down the owned maintenance daemon and its active sessions, cancel
only its board reverse listener and close the Laptop maintenance client.
Keep the independent application tunnel as needed. Verify no known SSH server
or session process remains on Phone. From the local iSH console, run the
printed restore-helper path, or paste the complete block below. This block
needs no new download and is available even when the setup transfer failed.

```sh
python3 - <<'WEEK7_RESTORE'
import os
from pathlib import Path
import spwd
import stat
import subprocess

if os.geteuid() != 0:
    raise SystemExit('Run this from the local iSH root console after maintenance shutdown.')
servers = subprocess.run(['pidof', 'sshd', 'sshd-session', 'sshd-auth', 'dropbear'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
if servers.returncode != 1 or servers.stdout.strip() or servers.stderr.strip():
    raise SystemExit('Close the owned maintenance daemon and its sessions first; nothing changed.')
private = Path.home() / 'week7-private'
backup = private / 'ish-root-before-control.txt'
for path, directory in ((private, True), (backup, False)):
    info = path.lstat()
    valid_type = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if not valid_type or info.st_uid != 0 or info.st_mode & 0o077:
        raise SystemExit('Private backup ownership or mode is unsafe; nothing changed.')
original = backup.read_text(encoding='utf-8')
if not original.startswith('!') or ':' in original or '\n' in original or '\r' in original:
    raise SystemExit('Invalid saved root password field; nothing changed.')
current = spwd.getspnam('root').sp_pwdp
if current == original:
    print('ORIGINAL_ROOT_LOCK_ALREADY_RESTORED')
elif current != '*':
    raise SystemExit('Account changed since setup; refusing to overwrite the new value.')
else:
    result = subprocess.run(['chpasswd', '-e'], input='root:' + original + '\n', text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if result.returncode != 0 or spwd.getspnam('root').sp_pwdp != original:
        raise SystemExit('Restore needs inspection; private backup retained.')
    print('ORIGINAL_ROOT_LOCK_RESTORED; private backup retained.')
WEEK7_RESTORE
```

Restoration validates the backup, requires the current field to be `*` or
already equal to the original, uses `chpasswd -e` through stdin, and rereads
actual state. Any unexpected account change is preserved for inspection.
Retain the backup until `ORIGINAL_ROOT_LOCK_RESTORED` or
`ORIGINAL_ROOT_LOCK_ALREADY_RESTORED` is verified. This restores the original
password field; it does not promise exact restoration of all shadow metadata,
since password tools can update password-age fields. Restoring a lock by itself
does not terminate established SSH sessions.

## Validation and sources

Seven isolated account-workflow cases passed: enable, existing backup,
existing SSH daemon, restore, changed account, active daemon on restore, and
already restored. Five isolated combined-bootstrap cases passed, including
the newly locked account. Account/root/permission and subprocess operations
were simulated; no actual Phone account was changed in these tests. Python
3.8 grammar parsing passed. Independent review found no blocking issue.
The separate local `root-lock-remedy-manifest.json` records source hashes.

- [iSH official SSH instructions](https://github.com/ish-app/ish/wiki/Running-an-SSH-server#troubleshooting-passwordless-login)
  document the locked-root remedy.
- [OpenSSH 8.6 platform lock check](https://raw.githubusercontent.com/openssh/openssh-portable/V_8_6_P1/platform.c)
  describes its platform-specific account locking behavior.
- [chpasswd manual](https://man7.org/linux/man-pages/man8/chpasswd.8.html)
  describes encrypted input and password-age updates; actual iSH behavior still
  requires the reported state checks.
