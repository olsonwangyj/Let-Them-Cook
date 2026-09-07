# iPhone: import the public setup bundle through Ultra96 SSH

This is an alternate import path for the [iPhone quickstart](week7-iphone-quickstart.md).
It downloads the unchanged public ZIP through the assigned Ultra96's SSH port 22,
using the existing verified host keys. No Files transfer or new account is needed.
**Current physical progress (2026-09-07):** the operator's iSH output shows
both SSH password prompts, a completed 100% ZIP transfer and return to the
shell. The known inaccessible `/home/xilinx` warnings did not prevent that
transfer. On-Phone ZIP verification/installation, forwarding/forking and
TLS/result delivery still need confirmation.

Keep the iPhone's authorized VPN connected. The Laptop's VPN does not establish
the Phone's route. The Laptop operator must first confirm that the exact public
archive has been uploaded and its SHA-256 checked at the path below. The archive
contains no passwords or private keys. Enter passwords only at SSH/SCP prompts.

**Paste each block separately.** In particular, paste only the SCP block when
authenticating, enter both passwords when requested, and wait for the normal
iSH prompt before pasting the verification block. Later commands must not be
fed into a password prompt.

## 1. Check the runtime and prepare a private import directory

In the same foreground iSH terminal:

```sh
python3 -c 'import sys, ssl; assert sys.version_info >= (3, 8); print(sys.version.split()[0]); print(ssl.OPENSSL_VERSION); print(ssl.TLSVersion.TLSv1_2)'
ssh -V
```

Continue only if Python SSL and OpenSSH are available. The following block makes
a fresh directory and two scoped configuration files; it does not connect:

```sh
week7_bootstrap_ready=no
if week7_bootstrap=$(mktemp -d "$HOME/week7-ssh-import.XXXXXX"); then
  if (
    umask 077 &&
    cat > "$week7_bootstrap/known_hosts" <<'HOST_KEYS' &&
stujump.comp.nus.edu.sg ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILfypXFWxIhmHZ1nZZKsNKIYRZvnXrra4sqWpnBRy66i
makerslab-fpga-35.ddns.comp.nus.edu.sg ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC7by9bvClMnRjk3KKoR+QpRdhuUXhIhVPC1+F2FnV39
HOST_KEYS
    {
      printf 'Host *\n    UserKnownHostsFile "%s"\n' "$week7_bootstrap/known_hosts" &&
      cat <<'SSH_CONFIG'
    StrictHostKeyChecking yes
    HostKeyAlgorithms ssh-ed25519
    BatchMode no
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
SSH_CONFIG
    } > "$week7_bootstrap/ssh-config" &&
    chmod 600 "$week7_bootstrap/known_hosts" "$week7_bootstrap/ssh-config"
  ); then
    week7_bootstrap_ready=yes
    printf 'Private import directory ready: %s\n' "$week7_bootstrap"
  else
    printf '%s\n' 'File preparation failed; do not run SCP.'
  fi
else
  printf '%s\n' 'Directory preparation failed; do not run SCP.'
fi
```

Require `Private import directory ready`, then inspect the two local expansions:

```sh
ssh-keygen -lf "$week7_bootstrap/known_hosts" -E sha256
ssh -F "$week7_bootstrap/ssh-config" -G week7-jump
ssh -F "$week7_bootstrap/ssh-config" -G week7-ultra96
```

Both must show strict checking, only `ssh-ed25519` host keys, `batchmode no`,
port 22, and the scoped `known_hosts` path. The jump/destination users are
`yanjie`/`xilinx`; connection timeouts are 20/60 seconds and keepalives 15/count 3.
These commands make no network connection. Compare these existing verified
public fingerprints with the trusted Laptop record:

| Host | ED25519 SHA-256 fingerprint |
|---|---|
| `stujump.comp.nus.edu.sg` | `SHA256:UZRh6MN1S3Q9DI2OEH4POiJQ4fEaxrpI83ZSTTZtMYw` |
| `makerslab-fpga-35.ddns.comp.nus.edu.sg` | `SHA256:vrFwqkqWIfyDZ1S66aJb1gLy59wx3LakOqhnyQJEOhg` |

## 2. Download; answer the password prompts privately

Wait for the Laptop operator's upload/hash confirmation. Paste this block alone.
The SCP invocation is the final command in the authentication block; no shell
`&` or redirected password input is used. A host-key mismatch is a stop condition.

```sh
if [ "$week7_bootstrap_ready" = yes ]; then
  scp -F "$week7_bootstrap/ssh-config" \
    week7-ultra96:/var/tmp/cg4002-week7-yanjie-20260907/phone-public-8796b9b94b76/week7-iphone-setup.zip \
    "$week7_bootstrap/week7-iphone-setup.zip"
fi
```

Enter the authorized password for each host when prompted. A missing file or
permission error needs the operator to check the uploaded file; do not weaken
SSH checks or change the destination. Wait for SCP to finish and the shell prompt
to return before the next block.

## 3. Verify the exact ZIP before extracting or installing

The hash below belongs to the original unchanged public bundle. This block
extracts only after the SHA-256, exact five archive names, and ZIP CRC pass:

```sh
week7_import_verified=no
if [ "$week7_bootstrap_ready" = yes ] && python3 - "$week7_bootstrap" <<'VERIFY_ZIP'
import hashlib
import sys
import zipfile
from pathlib import Path

root = Path(sys.argv[1])
archive = root / "week7-iphone-setup.zip"
expected_hash = "8796b9b94b760b33dd7797163762dbbdd5a818a3c84a144db735ec5a0adea153"
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected_hash:
    raise SystemExit("SHA-256 mismatch; nothing extracted.")
names = {"week7-iphone-setup/" + name for name in
         ("receiver.py", "ca-cert.pem", "known_hosts", "ssh-config", "README.md")}
with zipfile.ZipFile(archive) as bundle:
    if len(bundle.namelist()) != 5 or set(bundle.namelist()) != names:
        raise SystemExit("Unexpected archive contents; nothing extracted.")
    if bundle.testzip() is not None:
        raise SystemExit("ZIP CRC failed; nothing extracted.")
    bundle.extractall(root)
print("Verified SHA-256 and five allowed files; extraction complete.")
VERIFY_ZIP
then
  week7_import_verified=yes
fi
```

Require the verification success message. Install the same scoped files used by
the quickstart; `cp -i` asks before replacing an earlier attempt's files:

```sh
if [ "$week7_import_verified" = yes ]; then
  umask 077
  mkdir -p ~/.ssh ~/week7-private ~/week7-phone ~/week7-evidence &&
  chmod 700 ~/.ssh ~/week7-private ~/week7-evidence &&
  cp -i "$week7_bootstrap/week7-iphone-setup/receiver.py" ~/week7-phone/receiver.py &&
  cp -i "$week7_bootstrap/week7-iphone-setup/ca-cert.pem" ~/week7-private/ca-cert.pem &&
  cp -i "$week7_bootstrap/week7-iphone-setup/known_hosts" ~/.ssh/week7-known_hosts &&
  cp -i "$week7_bootstrap/week7-iphone-setup/ssh-config" ~/.ssh/week7-ish-password.conf &&
  chmod 600 ~/.ssh/week7-known_hosts ~/.ssh/week7-ish-password.conf \
    ~/week7-private/ca-cert.pem ~/week7-phone/receiver.py
fi
```

Compare any existing files before approving replacement. General SSH
configuration is unchanged. Now continue at
[quickstart step 3: verify public trust](week7-iphone-quickstart.md#3-verify-public-trust-and-the-two-host-configurations),
then its password-before-background tunnel and result-capture steps. Compare
the CA fingerprint with the provisioning original before TLS use. A successful
SCP download proves neither local forwarding nor the Phone receiver; keep iSH
foreground, and require verified TLS, subscription and actual correlated results.

The SSH behavior follows the official [OpenSSH client manual](https://man.openbsd.org/ssh)
and [configuration manual](https://man.openbsd.org/ssh_config). This alternate
guide does not modify the ZIP or its embedded quickstart, publish a file server,
enroll keys, or claim completed iPhone acceptance.
