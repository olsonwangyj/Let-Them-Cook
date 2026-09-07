# Week 7 Android Phone receiver

**Current operator device (2026-09-07): iPhone.** Follow the separate
[iPhone quickstart](week7-iphone-quickstart.md) for the prepared public setup
bundle and foreground iSH password-authentication experiment. That recipe is
not yet verified on the physical iPhone; the Android baseline below remains
available. The older key-only iSH appendix is an alternative, not a prerequisite
for the password recipe.

The selected baseline is an Android Phone running its own OpenSSH local forward
in Termux and either the standalone Python receiver or the Unity sample. The
application connects to **Phone `127.0.0.1:19999`**, which forwards directly to
Ultra96 `127.0.0.1:9999`. The Laptop independently forwards ingestion to 8888.
The Phone never connects to a Laptop address. No `-R` or public application
listener is needed.

**Ultra96 TCP 22 is its only externally accessible port and serves SSH.**
The Phone's SSH connection reaches that port through the jump host; remote
`127.0.0.1:9999` is reached inside the SSH tunnel, not as an exposed Ultra96 port.

This implements the selected test contract in
[week7-selected-design-2026-09-06.md](week7-selected-design-2026-09-06.md).
The sample prints dummy results; integrating the teammate's existing scene and
testing an actual Android device remain physical Gate M work.

## Required items

- An Android Phone with a current Termux installation from an official supported
  source; use the project's [installation instructions](https://github.com/termux/termux-app#installation).
- The authorized NUS network/VPN path, Ultra96 hostname and login names, and
  **independently verified** bastion and Ultra96 SSH host keys.
- Phone-owned SSH credentials provisioned outside this repository. Password/MFA
  entry, if required, happens interactively in Termux; never put secrets in a
  command, config committed to Git, screenshot or evidence log.
- The public `ca-cert.pem` from the existing Week 7 PKI, verified against the
  provisioning machine's SHA-256 fingerprint. Do not generate another CA on the
  Phone, install an unrelated public root, or copy either CA/server private key.
- Ultra96's TLS Gateway running on loopback 9999 with a currently valid service
  certificate for `ultra96.week7.internal`.
- Python 3.8+ for the standalone receiver. For Unity, use a desktop Unity Editor
  with Android Build Support/SDK/NDK/OpenJDK and .NET Standard 2.1 compatibility.
  Unity's [.NET profile documentation](https://docs.unity3d.com/2022.3/Documentation/Manual/dotnetProfileSupport.html)
  describes the API profile; the actual teammate Editor/device combination must
  be compiled and exercised before it is marked supported.

The authorized VPN path and password authentication through both SSH hops have
now worked from the Laptop. Institutional SSH key enrollment is not a general
prerequisite for this route. The Phone must still establish its own VPN/network
access and authenticate both hops; this Laptop result is not Phone evidence.

## Phone-owned SSH forward

Run the following in Termux. `~/.ssh` and `~/week7-private` are private Phone
directories outside the source checkout.

```sh
pkg update
pkg install openssh python openssl
mkdir -p ~/.ssh ~/week7-private ~/week7-phone
chmod 700 ~/.ssh ~/week7-private
```

Provision verified `known_hosts` entries and the public CA by the team's approved
transfer procedure. Provision a Phone private key only if choosing key
authentication; authorized passwords are a valid foreground option. SSH
host-key fingerprints must be verified through an authoritative channel before
use. `ssh-keyscan` output alone is not proof of authenticity. Do not set
`StrictHostKeyChecking=no`.

Create `~/.ssh/config` on the Phone with these entries, replacing the two example
usernames and Ultra96 hostname with the assigned values. Keep an already working
authorized credential configuration if it differs. The configured jump spelling
is `stujump.comp.nus.edu.sg` from the selected design; only a successful verified
login proves the actual path.

```sshconfig
Host week7-jump
    HostName stujump.comp.nus.edu.sg
    User YOUR_SOC_USERNAME
    StrictHostKeyChecking yes
    UserKnownHostsFile ~/.ssh/known_hosts
    BatchMode no
    ConnectTimeout 20
    ServerAliveInterval 15
    ServerAliveCountMax 3

Host week7-ultra96
    HostName YOUR_ASSIGNED_ULTRA96_HOST
    Port 22
    User YOUR_ULTRA96_USERNAME
    ProxyJump week7-jump
    StrictHostKeyChecking yes
    UserKnownHostsFile ~/.ssh/known_hosts
    BatchMode no
    ConnectTimeout 60
    ServerAliveInterval 15
    ServerAliveCountMax 3
```

`BatchMode no` allows each hop to prompt in this terminal. The jump connection
has a 20-second connection timeout and the destination has 60 seconds: the
destination's banner wait includes time spent authenticating the jump hop. The
previous 10-second destination setting expired while waiting for the first
password in the observed Laptop run. These settings still need Phone validation.

If choosing a provisioned key, add `IdentityFile ~/.ssh/week7-phone` and
`IdentitiesOnly yes` to each applicable host block, then run
`chmod 600 ~/.ssh/week7-phone`. A key passphrase may be entered interactively or
provided by an authorized agent; no key file is required for password login.

```sh
chmod 600 ~/.ssh/config ~/.ssh/known_hosts
ssh -G week7-jump
ssh -G -p 22 week7-ultra96
termux-wake-lock
ssh -p 22 -N -T -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:19999:127.0.0.1:9999 week7-ultra96
```

Before connecting, inspect the two `ssh -G` expansions for strict host-key
checking, destination `port 22`, `batchmode no`, jump/destination timeouts 20/60, and keepalive interval
15 with count 3. Expansion itself makes no network connection. Enter the
authorized passwords only at SSH's prompts; do not record them.

Keep this Termux session running. Open another session for Python, or switch to
Unity. This is a Phone process and Phone-local listener, independently of the
Laptop tunnel. If SSH exits, inspect the error and restart this same command.
Do not copy the Laptop's local endpoint or expose a Phone wildcard listener.

The [Termux wake-lock script](https://github.com/termux/termux-tools/blob/master/scripts/termux-wake-lock.in)
requests a wake lock. It does not prove that a particular Android vendor will
keep a background SSH process alive; verify battery/background settings during
the physical rehearsal. Release it afterward with `termux-wake-unlock`.

## Standalone Python receiver

Copy only `phone/receiver.py` to `~/week7-phone/receiver.py`, and the verified
public CA PEM to `~/week7-private/ca-cert.pem`. This receiver has no third-party
Python dependencies and does not need a full repository checkout.

```sh
openssl x509 -in ~/week7-private/ca-cert.pem -noout -fingerprint -sha256
python ~/week7-phone/receiver.py \
  --ca ~/week7-private/ca-cert.pem --port 19999 \
  --session week7-demo --count 100 --duration 180
```

Compare the CA fingerprint with the authoritative original before connecting.
Standard output contains only received `GESTURE_RESULT` JSON; standard error
contains connection status and the final received/reconnect counts. Exit zero
with `--count 100` requires 100 unique results. An unmet count at the duration
limit exits one. Without `--count`, the receiver continues until its duration
limit or Ctrl+C; mere process success does not establish a result-count gate.

TLS certificate verification uses the supplied CA and checks
`ultra96.week7.internal` even though TCP connects to `127.0.0.1`. The receiver
does not offer an insecure TLS flag or plaintext fallback. It reconnects after
protocol/transport failure with 0.5–5 s backoff and subscribes anew. Its bounded
4096-result cache suppresses recent duplicates across those reconnects. It has
no persisted history or durable exactly-once guarantee across process restart.

## Unity sample

1. Copy `phone/unity/Week7PhoneCore.cs` and `Week7PhoneReceiver.cs` into the
   teammate Unity project's `Assets/Week7` folder. No Newtonsoft/JSON package is
   needed; the core validates this protocol's flat JSON object schema strictly.
2. Convert the **verified public CA** to DER outside the source repository:

   ```sh
   openssl x509 -in ca-cert.pem -outform DER -out week7-ca.bytes
   ```

   Import `week7-ca.bytes` as a Unity TextAsset. A public CA certificate may be
   packaged in the test app; CA/private server keys must never be imported.
3. Add one `Week7PhoneReceiver` component to an active GameObject. Assign the CA
   TextAsset, set `Local Forward Port = 19999`, `Session Id = week7-demo`, and
   leave `Show Overlay` enabled for the minimal display. Connect `On Result Json`
   to teammate logic if desired; it fires on Unity's main thread.
4. Select Android, .NET Standard 2.1 API compatibility, and **Internet Access:
   Require**. This explicitly adds the Android INTERNET permission even though
   the receiver uses sockets rather than UnityWebRequest. See the official
   [Player setting](https://docs.unity.cn/2022.3/Documentation/ScriptReference/PlayerSettings.Android-forceInternetPermission.html).
5. Build/install the Android app, establish the Phone SSH forward above, and
   foreground Unity. The overlay should show `Subscribed` and live JSON.
6. Pause/disable the component to stop its network task and close its socket.
   Resuming starts a new subscription. The queue clears at disconnect/pause;
   entries older than two seconds locally are discarded before main-thread
   delivery. Capacity is 32 with drop-oldest behavior.

The TLS callback requires both the platform hostname check and a valid server
authentication chain ending at the **exact supplied CA**. It permits only the
chain's untrusted-root status for that explicitly supplied private root, checks
all other chain errors, and never accepts a missing or mismatched-name
certificate. This uses portable `X509Chain` APIs rather than a permissive
callback or an operating-system-wide CA installation. The offline test CA has no
CRL/OCSP endpoint, so revocation lookup is disabled; certificate expiry remains
enforced. Microsoft's [SslStream guidance](https://learn.microsoft.com/en-us/dotnet/core/extensions/sslstream-best-practices)
explains the role of custom certificate validation. Android/Unity's chain
implementation still needs real-device verification; a platform rejection must
be diagnosed without removing validation.

The sample supports native Unity Android applications. It is not a WebGL
receiver, iOS SSH integration, background Android service, or a claim that the
teammate's project already compiles.

## Exact wire contract

Each frame is four-byte unsigned big-endian length plus a strict UTF-8 JSON
object, 1–16384 body bytes, with five-second frame deadlines. Duplicate keys,
unknown/missing fields, malformed UTF-8/JSON, non-finite numbers, mismatched
sessions and wrong field types are rejected. Integer fields do not accept JSON
booleans or floating-point encodings.

Phone sends:

```json
{"v":1,"type":"SUBSCRIBE","session_id":"week7-demo"}
```

Gateway replies before any results:

```json
{"v":1,"type":"SUBSCRIBED","session_id":"week7-demo"}
```

Then Gateway sends live results, for example:

```json
{"v":1,"type":"GESTURE_RESULT","session_id":"week7-demo","device_id":1,"boot_id":123,"seq":3,"result_id":"1:123:3","gesture":"POINT","confidence":1.0}
```

`device_id` is 1 or 2; boot and sequence are uint32; result ID is
`device_id:boot_id:seq`; gesture is `[REST,FIST,OPEN,POINT][seq % 4]`; confidence
is 1.0. These are test sentinels, not model inference. Session is explicitly
configured association, not a password. A newer subscriber replaces the old
subscriber; stop the desktop simulator before running the real Phone to avoid
the two clients repeatedly replacing each other.

## Reproducible local validation

From the repository root:

```powershell
python -m unittest discover -s phone/tests -p test_receiver.py -v
pwsh -NoProfile -File phone/tests/run_core_tests.ps1
python phone/receiver.py --help
```

Python test PKI generation additionally needs the repository's `cryptography`
development dependency; the deployed Phone receiver remains stdlib-only. The
C# script uses PowerShell 7's Roslyn compiler (`Add-Type`) and .NET runtime; a
dotnet SDK is unnecessary for this particular check. It suppresses only the
new-host warning about the certificate constructor retained for Unity API
compatibility. It compiles the portable core, **not the MonoBehaviour**.

The C# checks cover strict schemas, split/coalesced/malformed/oversized framing,
freshness/queue eviction, private-CA certificate validation, actual local TLS
accept/reject handshakes, malformed-subscription reconnect and cancellation.
Python checks cover the same contract/parser boundaries and a real local TLS
receiver run with reconnect, including wrong-CA/name rejection. Ephemeral test
PKI is outside Git and is removed when tests finish. See the final execution
report for observed counts and platform versions; do not interpret these tests
as Phone or Ultra96 deployment evidence.

## Physical Gate M checklist

- Record Android model/version, Unity Editor/backend/app version, Termux/OpenSSH
  versions, CA expiry/fingerprint, configured session, and actual network/VPN
  conditions. Record no passwords, private keys or pairing passkeys.
- Verify both SSH host keys and the CA fingerprint independently; verify the
  Phone TLS connection accepts the service SAN and rejects a wrong CA/name.
- Confirm the Phone owns its SSH process/loopback listener and that Ultra96's
  Gateway binds only `127.0.0.1`. Confirm the Laptop receives only ingestion ACKs.
- Run real ESP → protected BLE → Laptop TLS/its SSH → Ultra96 → Phone's SSH/TLS
  → real Phone display. Correlate at least 100 expected result IDs across logs.
- Test Phone SSH termination/restart, app reconnect, foreground/background and
  screen/battery behavior, VPN loss/recovery where applicable, and Gateway
  restart. Confirm old results are not replayed as new actions.
- Stop the simulator before Phone testing; test newest-subscriber replacement
  separately. Local residence freshness is not end-to-end latency proof because
  clocks are unsynchronized and results have no cross-device timestamp.
- Keep Unity foreground and configure Android battery treatment for Termux
  during the demo. Observe whether SSH survives switching apps; a wake lock
  alone is insufficient evidence. Do not claim unattended/background support.
- Record the actual teammate integration outcome. A printed Python result proves
  the minimal real-Phone display path, but does not independently prove the
  teammate Unity receiver or full AR behavior.
- After evidence collection, stop Python/Unity and the Phone SSH command, release
  the wake lock, and confirm no test forward remains running.

## Optional iOS appendix: foreground iSH JSON experiment — untested

Android remains the selected baseline. This appendix prepares a possible minimal
iPhone demonstration using **one foreground iSH app**: its OpenSSH process owns
the local forward and its Python process prints received JSON. It does not add
an iOS Unity integration or establish any physical Phone acceptance. A Windows
PnP inventory entry named iPhone does not prove a connected, unlocked, controllable
device, installed iSH, or a working network path.

The [official iSH site](https://ish.app/) describes a local Linux shell for iOS
and links its distribution channels. The project documents
[apk package installation](https://github.com/ish-app/ish/wiki/Using-iSH), and its
[compatibility list](https://github.com/ish-app/ish/wiki/Compatible-Applications%2C-Programs%2C-Packages)
records Python 3, the OpenSSH client and shell job control. These are project
compatibility reports, not a guarantee for the installed iOS/iSH/package versions.
The project also documents
[same-device localhost SSH](https://github.com/ish-app/ish/wiki/Running-an-SSH-server).

Local forwarding needs an actual device check. Historical
[issue 408](https://github.com/ish-app/ish/issues/408) includes an SSH `-L` failure
and mixed user outcomes; a
[maintainer reply](https://github.com/ish-app/ish/issues/408#issuecomment-513810489)
identifies the background-execution limitation. Combining these capabilities
into the following same-app foreground route is an engineering inference, not
a reproduced iPhone result. If it fails, record the failure and retain Android
as the runnable baseline; do not claim that a successful SSH login proves the
forward or TLS receiver works.

### Human setup on the iPhone

An operator must install/open iSH from a channel linked by the official project,
provision authorized Phone-owned SSH credentials and independently verified
host keys, and establish the required network/VPN access. VPN/password access
through both hops has worked from the Laptop; iPhone access remains untested.
The background shell-job recipe below specifically requires usable key/agent
authentication because it cannot prompt. That is a constraint of this recipe,
not an institutional requirement to enroll an SSH key. These commands are
instructions for that operator; none were executed on an iPhone here.

Inside iSH, install the packages and inspect the actual runtime:

```sh
apk update
apk add openssh python3 openssl
python3 --version
ssh -V
python3 -c 'import sys, ssl; assert sys.version_info >= (3, 8); print(ssl.OPENSSL_VERSION); print(ssl.TLSVersion.TLSv1_2)'
mkdir -p ~/.ssh ~/week7-private ~/week7-phone
chmod 700 ~/.ssh ~/week7-private
```

If packages or the Python SSL import are unavailable, stop this experiment and
record the installed versions/error. This procedure does not replace package
repositories or prescribe an unverified iSH filesystem upgrade.

Copy `phone/receiver.py` to `~/week7-phone/receiver.py`, the existing verified
public CA to `~/week7-private/ca-cert.pem`, the authorized Phone SSH key to
`~/.ssh/week7-phone`, and verified host entries to `~/.ssh/known_hosts`. iSH's
[Files-app integration instructions](https://github.com/ish-app/ish/wiki/View-iSH-files-in-Files-App)
provide an on-device file-access path; an operator must perform and verify the
transfer. Keep private keys outside source files and evidence. Copy neither
Week 7 TLS private key to iSH. Compare this public fingerprint with the trusted
provisioning original:

```sh
chmod 600 ~/.ssh/week7-phone ~/.ssh/known_hosts
openssl x509 -in ~/week7-private/ca-cert.pem -noout -fingerprint -sha256 -dates
python3 ~/week7-phone/receiver.py --help
```

Create a separate `~/.ssh/week7-ish.conf` inside iSH with the following contents,
replacing `YOUR_SOC_USERNAME` and the assigned board login/hostname as needed.
This does not modify any existing general SSH configuration. This particular
recipe requires verified host keys and usable key/agent authentication on both
hops; `BatchMode yes` prevents a background SSH job from waiting for a password
or key passphrase. Its noninteractive connection timeout remains 10 seconds on
each hop.

```sshconfig
Host *
    StrictHostKeyChecking yes
    UserKnownHostsFile ~/.ssh/known_hosts
    BatchMode yes
    ConnectTimeout 10
    ServerAliveInterval 15
    ServerAliveCountMax 3

Host week7-jump
    HostName stujump.comp.nus.edu.sg
    User YOUR_SOC_USERNAME
    IdentityFile ~/.ssh/week7-phone
    IdentitiesOnly yes

Host week7-ultra96
    HostName makerslab-fpga-35.ddns.comp.nus.edu.sg
    Port 22
    User xilinx
    ProxyJump week7-jump
    IdentityFile ~/.ssh/week7-phone
    IdentitiesOnly yes
```

```sh
chmod 600 ~/.ssh/week7-ish.conf
ssh -F ~/.ssh/week7-ish.conf -G week7-jump
ssh -F ~/.ssh/week7-ish.conf -G -p 22 week7-ultra96
```

Inspect each expanded configuration for the intended host, user, strict trust
and batch settings. A separately encrypted key must already be usable through
the operator's authorized agent setup; these commands do not unlock it. If only
password or interactive MFA credentials are available, this background-job
recipe cannot proceed as written. The Android foreground procedure above
supports interactive authentication; no password-capable iSH job-control
procedure has been validated here.

### Keep iSH foreground for the complete experiment

Start the Phone-owned forward as a shell job, then run the standalone receiver
in that same iSH terminal. Keep the screen awake and iSH visible throughout.
The `&` below backgrounds only a shell job **inside the foreground app**.

```sh
ssh -F ~/.ssh/week7-ish.conf -p 22 -N -T -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:19999:127.0.0.1:9999 week7-ultra96 </dev/null &
week7_tunnel_pid=$!
jobs -l
python3 ~/week7-phone/receiver.py \
  --ca ~/week7-private/ca-cert.pem --port 19999 \
  --session week7-demo --count 100 --duration 180
```

The actual Ultra96 service and Laptop producer must already be running, and the
desktop simulator must be stopped. Require the receiver's `subscribed` status
before starting the 100-packet input; live results are not retained for late
subscribers. A forward process existing or a port accepting TCP is insufficient:
require verified TLS and 100 correctly correlated `GESTURE_RESULT` records on
the physical iPhone. After a short pass, a separate foreground soak can use
`--count 0 --duration 600`; inspect its received/reconnect counts and correlate
them with the producer/server rather than treating exit zero alone as a pass.

When the receiver exits, inspect `jobs -l` and stop only the still-running SSH
job matching the saved `week7_tunnel_pid` and this command:

```sh
kill "$week7_tunnel_pid"
wait "$week7_tunnel_pid"
```

If that job already exited, use `wait` only; do not kill another job or an
unverified reused PID. Starting the same experiment again creates a fresh SSH
process and subscription. The Python client reconnects, but this shell recipe
does not supervise/restart an exited SSH process.

### Evidence still required

Record actual iPhone/iOS/iSH/Alpine/Python/OpenSSH versions, successful authorized
SSH on both hops, local-forward operation, TLS CA/name rejection checks, the
100-result correlation and a separate 600-second foreground soak. Also check
cleanup, interruption and foreground recovery on that exact device. No such iOS
execution, installation, credential provisioning or result delivery was observed
in this task.

Do not switch to Unity, another app or a locked screen and assume SSH continues.
iSH's [background guide](https://github.com/ish-app/ish/wiki/Running-in-background)
describes a separate location-based mechanism; this demonstration does not use
it, request location access, or claim background reliability. A future iOS Unity
receiver would need its own app-integrated SSH/lifecycle implementation and
physical verification. This appendix covers only foreground JSON display.
