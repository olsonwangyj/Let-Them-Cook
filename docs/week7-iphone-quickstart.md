# Week 7 iPhone quickstart: foreground iSH experiment

This prepares an actual iPhone to receive the Week 7 dummy results through its
own SSH/TLS connection to Ultra96. **Actual iPhone delivery was verified on
2026-09-08: 100/100 exact result IDs, with one startup timeout before the first
result.** A clean zero-reconnect run, longer soak and lifecycle checks remain.
Android remains the selected baseline; this experiment establishes neither an
iOS Unity build nor background operation. The older iSH appendix's key-only
shell job is a different recipe. The candidate below lets OpenSSH prompt for
passwords before it backgrounds itself inside the foreground iSH app.

## 1. Have the human complete the Phone prerequisites

Install and open iSH from a channel linked by the [official iSH site](https://ish.app/).
Connect the iPhone's own authorized NUS VPN and complete its sign-in/MFA privately.
The working Laptop route used Cisco AnyConnect. NUS IT currently names
[Cisco Secure Client for mobile nVPN](https://nusit.nus.edu.sg/services/wifi_internet/nvpn/);
use the institution's current instructions and the appropriate authorized profile.
The bundle supplies no VPN server/profile, and Laptop VPN connectivity does not
establish iPhone connectivity. Do not substitute an invented server or another
VPN service. Keep iSH visible and the screen awake during the experiment.

The human must still confirm the iPhone/iOS version, installed iSH version,
working mobile VPN, and a chosen method to copy the ZIP from the Laptop to
iPhone Files. Credentials stay at the Phone's interactive prompts; never paste
them into chat, command lines, screenshots, source files or evidence.

In iSH, install packages using the project's documented
[Alpine package procedure](https://github.com/ish-app/ish/wiki/Using-iSH):

```sh
apk update
apk add openssh python3 openssl
python3 --version
ssh -V
python3 -c 'import sys, ssl; assert sys.version_info >= (3, 8); print(ssl.OPENSSL_VERSION); print(ssl.TLSVersion.TLSv1_2)'
umask 077
mkdir -p ~/week7-import ~/.ssh ~/week7-private ~/week7-phone ~/week7-evidence
chmod 700 ~/.ssh ~/week7-private ~/week7-evidence
printf '%s\n' "$HOME/week7-import"
```

If package installation or the SSL check fails, retain the actual version/error
and stop that setup attempt. This guide does not prescribe a filesystem upgrade
or changes to package repositories.

## 2. Import the public-only bundle

The prepared Laptop archive is
`D:\LetThemCook-builds\iphone-setup-20260907\week7-iphone-setup.zip`.
It contains exactly five files under `week7-iphone-setup/`: `receiver.py`,
`ca-cert.pem`, `known_hosts`, `ssh-config`, and `README.md`. No passwords,
SSH private keys, or TLS private keys are included. Nothing is automatically
sent, installed on the Phone, or served over the network.

After transferring the ZIP to iPhone Files by the human's chosen method, enable
iSH in Files' location-editing controls as described in the
[official Files integration guide](https://github.com/ish-app/ish/wiki/View-iSH-files-in-Files-App).
Copy the ZIP into the iSH filesystem directory printed above. In a default iSH
installation this is `/root/week7-import`; verify the printed path instead of
assuming another Files provider is already visible inside iSH. Then return to
iSH and run:

```sh
ls -l ~/week7-import/week7-iphone-setup.zip
python3 -m zipfile -l ~/week7-import/week7-iphone-setup.zip
python3 -m zipfile -e ~/week7-import/week7-iphone-setup.zip ~/week7-import
cp -i ~/week7-import/week7-iphone-setup/receiver.py ~/week7-phone/receiver.py
cp -i ~/week7-import/week7-iphone-setup/ca-cert.pem ~/week7-private/ca-cert.pem
cp -i ~/week7-import/week7-iphone-setup/known_hosts ~/.ssh/week7-known_hosts
cp -i ~/week7-import/week7-iphone-setup/ssh-config ~/.ssh/week7-ish-password.conf
chmod 600 ~/.ssh/week7-known_hosts ~/.ssh/week7-ish-password.conf
chmod 600 ~/week7-private/ca-cert.pem ~/week7-phone/receiver.py
```

The `cp -i` prompts protect an earlier attempt's scoped files. Compare any
existing files before replacing them. General `~/.ssh/config` and
`~/.ssh/known_hosts` are not modified.

## 3. Verify public trust and the two host configurations

The bundle's host entries are scoped copies of the existing verified Laptop
entries for the two exact hosts below. They were selected locally with
`ssh-keygen -F`, not collected from the network. Compare their fingerprints and
the public CA fingerprint against the trusted Laptop provisioning record through
the operator's trusted channel before authentication. A fingerprint printed from
the downloaded bundle alone is not independent verification.

```sh
ssh-keygen -lf ~/.ssh/week7-known_hosts -E sha256
openssl x509 -in ~/week7-private/ca-cert.pem -noout -fingerprint -sha256 -dates
python3 ~/week7-phone/receiver.py --help
ssh -F ~/.ssh/week7-ish-password.conf -G week7-jump
ssh -F ~/.ssh/week7-ish-password.conf -G week7-ultra96
```

The original CA's SHA-256 certificate fingerprint is
`4D:FB:A4:90:5C:17:1E:68:C3:62:3D:BC:95:21:54:14:90:76:ED:89:00:4B:85:D4:75:E8:58:CC:55:07:60:EC`.
Its validity is 2026-09-06 15:06:29 UTC through 2027-09-06 15:11:29 UTC;
the service certificate has its own shorter validity and must also be current.

The installed scoped configuration must contain:

```sshconfig
Host *
    StrictHostKeyChecking yes
    UserKnownHostsFile ~/.ssh/week7-known_hosts
    BatchMode no
    ServerAliveInterval 15
    ServerAliveCountMax 3
    ExitOnForwardFailure yes

Host week7-jump
    HostName stujump.comp.nus.edu.sg
    User yanjie
    Port 22
    ConnectTimeout 20

Host week7-ultra96
    HostName makerslab-fpga-35.ddns.comp.nus.edu.sg
    User xilinx
    Port 22
    ProxyJump week7-jump
    ConnectTimeout 60
```

Check both expanded hosts/users, port 22, strict checking, `batchmode no`,
20/60-second timeouts and 15-second keepalives with count 3. The explicit `-F`
configuration also reaches the generated ProxyJump SSH command; see the
[OpenSSH implementation](https://raw.githubusercontent.com/openssh/openssh-portable/master/ssh.c).

## 4. Authenticate first, then background the Phone tunnel

The operator must first verify the actual Ultra96 Gateway's owned process and
loopback listener, and stop the desktop subscriber and its viewer forward. Keep
the Laptop's independent ingestion forward. The Phone never connects to a
Laptop address: only its own `127.0.0.1:19999` listener forwards through SSH to
Ultra96 `127.0.0.1:9999`. Ultra96 TCP 22 is the externally accessible SSH port.

Run this directly in the foreground iSH terminal. Enter both passwords at the
SSH prompts; do not record this authentication step or append shell `&`.

```sh
if week7_control_dir=$(mktemp -d "$HOME/.ssh/week7-tunnel.XXXXXX"); then
  week7_ssh_socket="$week7_control_dir/control"
  ssh -F ~/.ssh/week7-ish-password.conf -f -N -T \
    -M -S "$week7_ssh_socket" \
    -L 127.0.0.1:19999:127.0.0.1:9999 week7-ultra96
  week7_ssh_exit=$?
  printf 'SSH startup exit=%s\n' "$week7_ssh_exit"
  ssh -F ~/.ssh/week7-ish-password.conf \
    -S "$week7_ssh_socket" -O check week7-ultra96
else
  printf '%s\n' 'No private control directory; tunnel was not started.'
fi
```

Continue only after startup exit 0 and a successful control check. The private
control socket provides a scoped shutdown command. These worked on the tested
iPhone (most recently master PID 60), but check each current session rather than
trusting that historical PID. If `mktemp` fails, do not
run the subsequent commands. If SSH reports a fork/daemon/control-socket error,
retain it and inspect the owned process before retrying. For foreground
diagnosis, use the same forwarding command with `-f` removed; this does not by
itself complete the one-terminal receiver experiment. Do not delete a socket or
kill an unverified PID to clear a failure.

[OpenSSH documents `-f`](https://man.openbsd.org/ssh#f) as accepting authentication
before backgrounding. `-N` runs no remote command and `-T` requests no remote
terminal. `ExitOnForwardFailure` detects setup failures, but does not establish
that the final remote application port is reachable; see its
[documented limit](https://man.openbsd.org/ssh_config#ExitOnForwardFailure).
TLS verification, subscription and received results are the application checks.
`$!`, `jobs` and shell `wait` do not identify this self-backgrounded SSH process.

## 5. Capture and display 100 actual Phone results

Have the Laptop operator stage `tools.week7_demo sender` with protected BLE and
100 packets before starting the Phone receiver. Do not run
`tools.rehearse_remote_week7` alongside the Phone: it starts a competing
subscriber. The original immutable setup ZIP has a five-second initial
frame/idle deadline, so start production immediately when it displays
`subscribed`. The updated repository receiver gives the first result byte
30 seconds while preserving the five-second partial-frame and later-result
deadlines (decision 31). Previously installed files do not update automatically.
Use the separately hashed [update/capture procedure](week7-iphone-startup-update.md)
for the current physical test.

This capture step creates a fresh directory. The `tail` shell job only displays
safe application output; SSH authentication has already finished.

```sh
if week7_run_dir=$(mktemp -d "$HOME/week7-evidence/phone100.XXXXXX") &&
   touch "$week7_run_dir/phone100.jsonl" "$week7_run_dir/phone100.status.txt"; then
  printf '%s\n' "$week7_run_dir"
  tail -f "$week7_run_dir/phone100.status.txt" "$week7_run_dir/phone100.jsonl" &
  week7_display_pid=$!
  python3 ~/week7-phone/receiver.py \
    --ca ~/week7-private/ca-cert.pem --port 19999 \
    --session week7-demo --count 100 --duration 180 \
    > "$week7_run_dir/phone100.jsonl" 2> "$week7_run_dir/phone100.status.txt"
  week7_receiver_exit=$?
  printf '%s\n' "$week7_receiver_exit" > "$week7_run_dir/phone100.exit.txt"
  printf 'Receiver exit=%s\n' "$week7_receiver_exit"
  jobs -l
else
  printf '%s\n' 'Evidence setup failed; display and receiver were not started.'
fi
```

If directory creation fails, stop before the following commands. Observe
`subscribed session=week7-demo` and live `GESTURE_RESULT` JSON on the iPhone.
After the receiver finishes, verify that the saved display PID still denotes
this run's `tail` job, then stop it:

```sh
kill "$week7_display_pid"
wait "$week7_display_pid"
cat "$week7_run_dir/phone100.exit.txt" "$week7_run_dir/phone100.status.txt"
```

Require receiver exit 0 and 100 unique valid results. Transfer the three safe
Phone evidence files back through the chosen method, preserving their Phone
origin. The Laptop operator must correlate the exact IDs with the sender ACKs
and Ultra96 accepted traces using the demo pack's Phone audit. A TCP listener,
successful SSH login, or an ingestion ACK alone is insufficient.

## 6. Finish the experiment and retain its limits

Stop only this Phone tunnel using its dedicated control socket:

```sh
ssh -F ~/.ssh/week7-ish-password.conf \
  -S "$week7_ssh_socket" -O exit week7-ultra96
ssh -F ~/.ssh/week7-ish-password.conf \
  -S "$week7_ssh_socket" -O check week7-ultra96
```

The final check should report that the master is unavailable. If the control
path fails unexpectedly, inspect the current process/command and endpoint
ownership before stopping a specific PID. Do not kill all SSH/Python processes.
This SSH invocation does not supervise or restart itself after a disconnect.

Record actual iPhone/iOS/iSH/Alpine/Python/OpenSSH versions, mobile VPN route,
trust checks, startup/cleanup outcome and any reconnects. A separate sustained
test uses sender `--target 0 --duration 600`, Phone `--count 0 --duration 630`,
fresh files and at least 5,400 correlated results. Retain timed on-device
observation across the full production interval: Phone JSONL is deduplicated
and contains no per-result timestamps, so counts alone prove neither continuous
delivery nor an absence of duplicate wire arrivals. Retain separately timed
TLS rejection and SSH/VPN/foreground recovery checks.

Keep iSH in the foreground throughout. The project's separate
[background mechanism](https://github.com/ish-app/ish/wiki/Running-in-background)
is outside this experiment. No iOS Unity integration, screen-lock reliability,
location permission or unattended background operation is claimed.
