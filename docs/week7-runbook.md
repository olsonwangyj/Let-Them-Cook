# Week 7 communications runbook

Current design authority: [selected decisions](week7-selected-design-2026-09-06.md). This guide includes the verified 2026-09-07 VPN/password access and deployment procedure. Historical approval blockers no longer apply. Preserve separate evidence for local, real BLE, Ultra96/SSH, and real Phone tests.

## Setup and local checks

Network constraint: **Ultra96 TCP port 22 is the only externally accessible port, and it serves SSH.** Ingestion `127.0.0.1:8888` and Gateway `127.0.0.1:9999` are internal TLS listeners reached through SSH local forwards. Laptop `18888` and Phone `19999` are loopback ports on their respective clients. Both clients reach Ultra96 SSH port 22 through the selected jump host; no direct network connection to Ultra96 application ports is required. Keep this constraint for all future development and physical acceptance tests.

Run from the feature worktree in PowerShell:

```powershell
Set-Location 'D:\LetThemCook-worktrees\week7-stage-d-onward'
python -m pip install -r laptop/requirements.txt
python -m pip install -r requirements-dev.txt
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest laptop/tests tests phone/tests -q
pwsh -NoProfile -File phone/tests/run_core_tests.ps1
```

Windows BLE/pairing requires Python >=3.10 because Bleak 3.0.1 declares that floor; Windows tests here use Python 3.12. Ultra96 and the standalone Phone receiver require Python >=3.8. The actual Ultra96 reported Python 3.10.4 at /usr/bin/python3, OpenSSL 3.0.2 and aarch64, satisfying that floor. cryptography is provisioning/test-only; the deployed server has no third-party Python dependency. Pin Bleak 3.0.1 as declared. The C# test command requires PowerShell 7 `pwsh`; see the Phone runbook.

Generate credentials in a **new empty directory outside all Git worktrees**:

```powershell
python -m tools.generate_week7_pki --output-dir 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906'
python -m tools.rehearse_week7 --pki-dir 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906' --duration 30 --target 100
```

If that directory already exists, reuse it; generation refuses to overwrite. CA certificate lasts 365 days, server certificate 30 days. The only trust root clients receive is ca-cert.pem. Never copy ca-key.pem to Ultra96 or a Phone. The server receives server-cert.pem and server-key.pem. Fingerprint the CA over a trusted local channel:

```powershell
openssl x509 -in 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' -noout -fingerprint -sha256 -dates
```

Regenerate a fresh directory and reprovision before expiry; restart services and replace every client's pinned CA together. No automatic renewal, mTLS or production rotation is claimed. TLS SNI/SAN is always `ultra96.week7.internal`; TCP connects to local 127.0.0.1. Never disable certificate validation to fix a localhost mismatch.

## Firmware and pairing

Use the installed PlatformIO executable or activate its environment. Keep build products outside the repository:

```powershell
$env:PLATFORMIO_BUILD_DIR=Join-Path $env:TEMP 'cg4002-week7-build'
& 'C:\Users\Yanjie Wang\.platformio\penv\Scripts\platformio.exe' run --project-dir firmware/esp32 -e firebeetle32
& 'C:\Users\Yanjie Wang\.platformio\penv\Scripts\platformio.exe' run --project-dir firmware/esp32 -e firebeetle32 --target upload --upload-port COM3
```

The normal profile requires authenticated Secure Connections bonding. The explicitly named diagnostic profile is only for unprotected comparison; consult platformio.ini for its exact name. No Wi-Fi is enabled.

Open the COM3 115200-baud monitor locally without saving raw output. Start `python -m laptop.windows_pairing` in another terminal. Enter the ESP's six-digit passkey at the hidden prompt. Never record the `PAIR LOCALLY:` line in logs/screenshots. Safe evidence contains only `ble_security_complete` fields, requiring successful current-peer auth with SC+MITM+bond flags, and the Windows authenticated bond result.

Bleak 3.0.1's generic pairing helper supports ConfirmOnly and may lower protection; the supplied WinRT helper instead requests ProvidePin at EncryptionAndAuthentication. Pairing confirms a stored Windows bond; firmware independently gates live notification submission on its authentication-completion event. See [Microsoft pairing API](https://learn.microsoft.com/en-us/uwp/api/windows.devices.enumeration.deviceinformationpairing.pairasync) and [Espressif security configuration](https://docs.espressif.com/projects/esp-idf/en/v4.1.2/api-reference/bluetooth/esp_gap_ble.html).

After pairing, stop the monitor if another tool needs COM3. Run:

```powershell
python -m tools.rehearse_week7 --pki-dir 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906' --ble --target 100 --duration 40
python -m laptop.ble_counter_receiver --target-received 1000
python -m laptop.ble_counter_receiver --duration-seconds 600
python -m laptop.mtu_probe
```

The counter target and duration modes are separate runs. The existing four-byte counter cannot distinguish a reboot from a reconnect: use W7's boot_id and serial boot evidence for the new-boot requirement. All three Windows clients force uncached GATT discovery: otherwise a bonded Windows session can report cached MTU 23 before a real connection has exchanged MTU.

### Deliberate bond recovery

1. Stop all clients for this ESP. Wait for the safe `ble_disconnected` event before issuing serial commands; a Python process returning does not prove Windows has released the physical link. Do not remove unrelated devices or restart the machine's Bluetooth services.
2. In the local 115200-baud monitor, type `erase-bonds` followed by Enter. Require `erase_bonds_complete remaining=0`; a rejected/busy command is not a successful erasure. If the radio cannot settle, an operator can reset this ESP, wait until it is disconnected/advertising, and retry. Preserve any rejected attempts as evidence.
3. Remove only this ESP's Windows Bluetooth bond through Windows device settings. Close any previous pairing/diagnostic process.
4. Run `python -m laptop.windows_pairing` in a **fresh process**, allowing fresh advertised discovery. Enter the new local serial passkey without recording it. Require Windows authenticated protection and firmware `success=1 auth_mode=13 approved=1 current_peer=1`.
5. Repeat the 100-packet protected BLE/local TLS test above. Normal recovery requires a clean positive result, not merely a successful pairing dialog.

Physical testing found that immediate repeated pairing in the same process after Windows unpair could return FAILED without a passkey event. Fresh-process pairing succeeded after deliberate bond cleanup. The cause inside Windows is unproven; do not respond by weakening security or adding automatic bond deletion. When testing one-sided loss, collect the zero-data/authentication-failure evidence first, then use this explicit recovery procedure. True USB power loss requires physically disconnecting the only power source. The [evening 2026-09-07 evidence](week7-continuation-report-2026-09-07.md#live-usb-only-power-loss-test-evening-2026-09-07) separately captures that USB-only interruption and physical RESET, with stored-bond recovery after each.

## Verified SSH access and deployment

Enable the authorized NUS VPN first. On 2026-09-07, interactive passwords succeeded on both the selected jump host and Ultra96 after VPN was enabled. Key enrollment is not required for this verified route. Keep passwords in OpenSSH's interactive prompts; never include them in arguments, scripts or captured session transcripts. Both endpoint host keys must still match independently verified known_hosts entries.

Historical evidence remains valid for the earlier attempts: on 2026-09-06 and before VPN was enabled on 2026-09-07, the jump offered only publickey and rejected the exact -J route, explicit password/keyboard-interactive attempts and the existing WSL key. Those failures did not establish a permanent key-only requirement. No institutional key enrollment was performed.

Use these PowerShell options for interactive login and SCP:

```powershell
$week7Proxy = 'ssh -o StrictHostKeyChecking=yes -o BatchMode=no -o ConnectTimeout=20 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -W "[%h]:%p" yanjie@stujump.comp.nus.edu.sg'
$week7SshOptions = @('-o', 'Port=22', '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=no', '-o', 'ConnectTimeout=60', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', '-o', "ProxyCommand=$week7Proxy")
ssh @week7SshOptions xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg
```

The destination's banner deadline also covers time spent answering the jump password prompt. The earlier 10-second destination deadline expired during that interaction; the selected interactive limits are 20 seconds for the proxy and 60 for the destination. Generated supervised commands retain 10/10-second limits and BatchMode=yes for already authorized key/agent authentication. Explicit ProxyCommand applies trust/timeouts independently to both hops along the same selected route.

### Inspect the actual board and keep existing services

Run in the verified Ultra96 session:

```sh
id
hostname
pwd
/usr/bin/python3 -c 'import sys, ssl; assert sys.version_info >= (3, 8); print(sys.version); print(ssl.OPENSSL_VERSION); print(ssl.TLSVersion.TLSv1_2)'
uname -m
stat -c '%u:%g %a %n' /home/xilinx
ss -ltnp
```

The inspected board reported hostname pynq, uid 1000 xilinx, aarch64, Python 3.10.4 and OpenSSL 3.0.2. Its /home/xilinx was owned by 127:135 with mode 750, causing an inaccessible-home warning and initial working directory /. Use absolute paths under the owned mode-700 directory `/var/tmp/cg4002-week7-yanjie-20260907`; do not repair home permissions or use sudo. Existing unrelated listeners on 22, 80, 9090 and Samba ports were preserved. Ports 8888 and 9999 were free before Week 7 deployment; inspect ownership again before every start. If another service owns either port, choose configurable alternatives and update the corresponding independent forwards together.

### Source and TLS provisioning

The deployed service revision is db6769a in `/var/tmp/cg4002-week7-yanjie-20260907/source-db6769a`. The Laptop's remote runner was added in 1adb464; record both revisions because the runner and remote service can differ. The existing TLS directory is `/var/tmp/cg4002-week7-yanjie-20260907/tls`, mode 700, with server-key.pem mode 600 and owner uid 1000. Reuse that verified identity for a code-only restart. Client CA verification always expects ultra96.week7.internal; the board's hostname pynq does not change the certificate identity.

After the verified restart, the current deployment writes `/var/tmp/cg4002-week7-yanjie-20260907/evidence/server-after-restart.log` and records its PID in `/var/tmp/cg4002-week7-yanjie-20260907/evidence/server.pid`. The completed clean soak and first fault logs are evidence/server-db6769a.log; the earlier ec7a08e log is evidence/server.log. Read and verify the current PID record before use; no numeric PID in a historical report should be treated as permanently current.

For a new deployment, select an unused source/archive label. The example `db6769a-redeploy-01` must be changed once used. Never extract over the active source directory. First verify the existing parent, then create the fresh source directory on Ultra96:

```sh
stat -c '%u:%g %a %n' /var/tmp/cg4002-week7-yanjie-20260907
umask 077
mkdir -m 700 /var/tmp/cg4002-week7-yanjie-20260907/source-db6769a-redeploy-01
```

Require parent ownership uid 1000 and mode 700 before proceeding. For a first installation only, create a new unused parent with mkdir -m 700; do not adopt or chmod an unknown existing directory. On the Laptop, archive the exact reviewed revision and use an absolute SCP destination:

```powershell
$week7Archive = Join-Path $env:TEMP 'cg4002-week7-db6769a-redeploy-01.tar'
git archive --format=tar --output=$week7Archive db6769a
scp @week7SshOptions $week7Archive 'xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg:/var/tmp/cg4002-week7-yanjie-20260907/db6769a-redeploy-01.tar'
```

Extract and smoke-check the exact source on Ultra96:

```sh
tar -xf /var/tmp/cg4002-week7-yanjie-20260907/db6769a-redeploy-01.tar -C /var/tmp/cg4002-week7-yanjie-20260907/source-db6769a-redeploy-01
cd /var/tmp/cg4002-week7-yanjie-20260907/source-db6769a-redeploy-01
/usr/bin/python3 -m compileall -q common ultra96
/usr/bin/python3 -c 'from ultra96.server import Week7Server; from common.tls import server_context; server_context("/var/tmp/cg4002-week7-yanjie-20260907/tls/server-cert.pem", "/var/tmp/cg4002-week7-yanjie-20260907/tls/server-key.pem"); print("server imports and TLS key/certificate load passed")'
```

For initial TLS provisioning or an explicit identity replacement, create a fresh private directory first, for example `/var/tmp/cg4002-week7-yanjie-20260907/tls-redeploy-01` with mkdir -m 700. Copy only these two files from the provisioning machine:

```powershell
scp @week7SshOptions 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\server-cert.pem' 'xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg:/var/tmp/cg4002-week7-yanjie-20260907/tls-redeploy-01/server-cert.pem'
scp @week7SshOptions 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\server-key.pem' 'xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg:/var/tmp/cg4002-week7-yanjie-20260907/tls-redeploy-01/server-key.pem'
```

Then run chmod 600 on that server-key.pem and verify directory/file ownership and modes with stat. Keep all private keys outside Git and keep ca-key.pem on the provisioning machine. Update the smoke-check and start command to the chosen TLS directory if it changed. Public CA fingerprints and validity dates are safe evidence; clients need correct wall clocks for certificate validity checks. /var/tmp is a deployment location, not an installation or persistence guarantee: inspect files again after a board restart.

### Start and identify the owned server

For the existing revision, the foreground command is:

```sh
cd /var/tmp/cg4002-week7-yanjie-20260907/source-db6769a
/usr/bin/python3 -u -m ultra96.server --cert /var/tmp/cg4002-week7-yanjie-20260907/tls/server-cert.pem --key /var/tmp/cg4002-week7-yanjie-20260907/tls/server-key.pem
```

Keep that SSH session open. Alternatively, launch this same foreground program as one owned background process so the interactive control session can close. This is not a daemon or systemd installation. Only start after the old owned service is stopped and both ports are free. Select the fresh source path when deploying a new archive. The example creates distinct per-run log/PID files in the existing private evidence directory, rather than overwriting the current deployment's records:

```sh
cd /var/tmp/cg4002-week7-yanjie-20260907/source-db6769a
umask 077
week7_run=$(date -u +%Y%m%dT%H%M%SZ)
week7_log="/var/tmp/cg4002-week7-yanjie-20260907/evidence/server-${week7_run}.log"
week7_pidfile="/var/tmp/cg4002-week7-yanjie-20260907/evidence/server-${week7_run}.pid"
nohup /usr/bin/python3 -u -m ultra96.server --cert /var/tmp/cg4002-week7-yanjie-20260907/tls/server-cert.pem --key /var/tmp/cg4002-week7-yanjie-20260907/tls/server-key.pem >"$week7_log" 2>&1 </dev/null &
week7_pid=$!
printf '%s\n' "$week7_pid" >"$week7_pidfile"
printf 'pid=%s log=%s pidfile=%s\n' "$week7_pid" "$week7_log" "$week7_pidfile"
ps -p "$week7_pid" -o pid=,uid=,args=
readlink -f "/proc/$week7_pid/cwd"
ss -ltnp
```

Record the PID, exact source revision/path, command arguments, log and pidfile. Require the server's listening JSON and ownership of only 127.0.0.1:8888 and 127.0.0.1:9999. A saved PID alone is not sufficient proof because a later process can reuse it. Revision db6769a handles SIGTERM gracefully, closes owned connections/listeners and prints stopped JSON with final metrics. No automatic service restart is configured.

## Two independent SSH forwards and clean remote checks

On the Laptop, print the ingestion command and execute it in its own terminal:

```powershell
python -m tools.ssh_tunnel
```

It owns `-N -T -L 127.0.0.1:18888:127.0.0.1:8888`. Print and execute the viewer command in a **second independent terminal/process**:

```powershell
python -m tools.ssh_tunnel --local-port 19999 --remote-port 9999
```

Both commands enforce strict host trust, keepalives and ExitOnForwardFailure, with the interactive 20/60-second limits described above. Keep both open and answer passwords interactively on every restart. `python -m tools.ssh_tunnel --run` is only for an already authorized key/agent route; its BatchMode=yes supervisor cannot answer passwords. A destination -i does not also select the jump's identity; use explicit authorized Host configuration if the two identities differ.

Check that these two owned SSH processes actually terminate on the verified Ultra96 and that the remote loopback service is running. Do not infer remote provenance solely from local listeners. The runner below starts no SSH process or server; it consumes the two existing independent forwards. The `--confirmed-remote-topology` flag records the operator's verified topology, rather than discovering it.

Use the runner from commit 1adb464 or later for clean gates. It completes strict TLS and SUBSCRIBED before starting the producer, emits a subscribed readiness event and trace events, then reports exact ACK/result correlation. First use synthetic input, then protected real BLE:

```powershell
python -m tools.rehearse_remote_week7 --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --confirmed-remote-topology --target 100 --duration 45
python -m tools.rehearse_remote_week7 --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --confirmed-remote-topology --ble --target 100 --duration 45
```

Run the sustained clean route separately, with no deliberate interruption:

```powershell
python -m tools.rehearse_remote_week7 --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --confirmed-remote-topology --ble --target 0 --duration 600
```

Require exit zero and summary passed=true. For 600 seconds at 10 Hz, the clean soak requires at least 5400 ACKs and unique results, exact correlation with no missing/extra/repeated IDs, one BLE/ingestion/viewer connection, no new boot and zero checked error/drop/gap/duplicate/order counters. Each ACK/result stream must have no gap between successive messages or trailing silence greater than five seconds; initial startup latency is reported separately. The separately reported callback_generation_dropped metric can include late callbacks rejected during shutdown and does not by itself fail this runner; inspect its context. A few successful packets over a long elapsed duration cannot satisfy the count/activity gate. The runner is a desktop subscriber and does not establish actual Phone Gate M.

An ACK confirms input acceptance; it does not prove viewer delivery. Stop other viewers before running the runner because a new same-session subscription replaces the previous owner. For an actual Phone, use its own 19999 -> 9999 forward and the [Phone guide](week7-phone-runbook.md); never route Phone results through the Laptop.

## Deliberate remote fault experiments

Run these after the clean baseline, one fault per recorded experiment. The clean runner deliberately fails on reconnects and correlation loss; use separate manual producer/viewer processes for recovery observation. In two terminals:

```powershell
python -m laptop.phone_simulator --host 127.0.0.1 --port 19999 --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --count 0 --reconnect
python -m laptop.bridge --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --duration 180 --target 0
```

The bridge command uses real protected BLE; add --mock only for an explicitly synthetic experiment. The manual simulator has a five-second idle timeout and no subscription-ready output. Its process starting does not prove readiness; --reconnect allows it to recover while BLE connects. Establish a positive baseline of fresh correlated results before inducing a fault. Use enough duration for interactive password reentry and a post-recovery observation window. Never use a manual viewer's process start as a clean 100-result gate.

### Ingestion tunnel loss

1. Record the current result IDs and the identity of the SSH terminal owning local port 18888. Leave the viewer's 19999 tunnel and remote service running.
2. Press Ctrl+C only in the ingestion SSH terminal. Keep the BLE bridge running for at least five seconds to cross its transport deadline; record errors/drops and the interruption interval.
3. Execute the same ingestion command in that terminal and enter passwords interactively. The bridge retries automatically with bounded backoff.
4. Require fresh post-recovery ACK/result IDs. Queues remain bounded, stale input is dropped and an ambiguous in-flight input is not retransmitted. Expected interruption counters are preserved as fault evidence.

### Viewer tunnel loss

1. After a positive baseline, press Ctrl+C only in the SSH terminal owning local port 19999. Keep ingestion and the remote service running.
2. Observe that the Laptop ingestion ACK path continues while viewer output stops. Record the accepted IDs during the absence.
3. Restart that same viewer tunnel interactively. The manual simulator reconnects and subscribes anew.
4. Require new live results; inputs accepted while no subscriber owned the gateway are not replayed. Lost result IDs are expected in this experiment. Do not launch a second competing viewer to diagnose it.

### Owned server termination and restart

1. Read the recorded PID for this specific server run. Validate that it is a positive numeric PID, still owned by uid 1000, with cwd exactly equal to the recorded Week 7 source directory and arguments matching the recorded ultra96.server command and TLS paths. Inspect with ps -p PID -o pid=,uid=,args= and readlink -f /proc/PID/cwd. If any identity check fails, stop this procedure and locate the correct owned process. Do not use pkill, killall or a port-wide process kill.
2. With both tunnels and manual clients still running, execute kill -TERM PID for that verified PID. For a foreground server, Ctrl+C in its own session is also graceful. Require the server log's stopped event/final metrics and release of its two listeners. A stale pidfile or kill command alone does not prove shutdown.
3. Reinspect port ownership, then restart the same reviewed source and TLS identity using the foreground or owned-background command above. Record the new PID/log and verify the new listening event and both loopback bindings. If the control SSH session was lost, reopen it through the VPN/password route first.
4. Require fresh ingestion and re-subscription through the independently retained forwards. If a tunnel also exited, restart only that owned tunnel and record the additional fault. Recent dedup state resets with the server process; no durable exactly-once claim applies across restart.

Stop the manual simulator with Ctrl+C after its producer finishes. Fault runs can correctly exit nonzero because errors, missing results or gaps were deliberately induced. Review recovery evidence separately, then rerun a clean check. Keep true ESP power loss and Phone/VPN recovery as separately identified physical experiments.

### Safe evidence collection

Use distinct filenames per run outside Git. Capture only the runner/bridge/simulator's stdout and stderr and the dedicated server log; do not capture the interactive SSH/password or serial passkey sessions. For example, append redirections to a runner command after creating a private local evidence directory: 1> run.stdout.jsonl 2> run.stderr.log. Keep the command's exit code, date, Laptop/service commits, source type, duration, endpoints, owned PID/paths, readiness event, final summary and anomaly counters together.

Copy a selected server log with the same verified SCP options and its **absolute** remote path. For the current db6769a deployment, use `scp @week7SshOptions 'xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg:/var/tmp/cg4002-week7-yanjie-20260907/evidence/server-db6769a.log' 'D:\week7-evidence\server-db6769a.log'`, using an existing private local evidence directory. For a later run, substitute its recorded log path. Never copy server-key.pem or ca-key.pem into evidence. Retain failed attempts alongside later positive results; an actively running soak is not a completed pass.

## Physical acceptance sequence

Record date, Git commit, profiles, OS/SDK/Bleak versions, hardware IDs, endpoints, duration, safe logs and all failure counters. Preserve failures separately from passes.

| Gate / experiment | Procedure | Acceptance |
|---|---|---|
| A serial | 5 min output; press RESET; physically unplug/replug USB | Stable alive sequence; reset and true USB power loss each produce a new boot |
| B discovery | Service/Notify discovery; connect/disconnect; compare submitted sequence logs | Expected UUIDs; no unexpected reboot |
| C/E protected stream | Receive >=1000 counters; run separate 600 s stream; physically power loss during W7 bridge | Gap/duplicate/order metrics visible; rescan, rediscover, resubscribe; W7 boot_id changes after actual reboot |
| D protected boundary | Run mtu_probe with safe serial correlation | Both endpoint MTU; exact 20 and MTU-3, oversize rejected; zero malformed/cleanup anomalies |
| E packet | Real 100-packet W7 local TLS rehearsal | Exact 32-byte/version/sentinels; seq/boot trace agrees; insufficient MTU suppresses before send |
| F/G remote | Ready-before-producer remote runner, synthetic --target 100 | At least 100 exact correlated ACK/result IDs plus Ultra96 logs; loopback-only listener |
| G identity negative | Trust wrong CA or use localhost as SNI in isolated test | TLS fails; no frame accepted and no plaintext fallback |
| G/H tunnel loss | Stop only Laptop-owned ingestion tunnel during stream, then restart | Bounded queue; error/drop/stale counters rise; next fresh input succeeds; ambiguous input not resent |
| I/J subscriber | 100 inputs; invalid input; duplicate trace; second same-session subscriber | Correct unique dummy results; invalid/duplicate no new result; latest subscriber owns live delivery |
| J/K Phone tunnel loss | Stop only simulator/Phone-owned tunnel and restart/subscribe | Laptop ACK path continues; results lost while disconnected are not replayed |
| K ingestion process loss | Stop only Week7 server, restart same ports/cert, reconnect clients | Fresh transport/subscription resumes; no durable exactly-once claim across restart |
| K real path soak | Real ESP -> Laptop -> actual Ultra96 -> independent desktop subscriber; clean runner --ble --target 0 --duration 600 | At least 5400 ACKs/results, exact correlation, count/activity coverage and all clean checks pass; faults run separately |
| L bond recovery | Remove Windows bond only, reconnect; deliberately erase ESP bonds with serial command; pair again | Failure is visible, no downgrade; explicit re-pair restores verified authenticated state |
| L restart | Power-cycle ESP and restart Laptop client using stored bonds | Authenticated reconnect and protected C/E/K regression pass |
| M actual Phone | Follow Phone runbook with physical Android and teammate receiver | Phone owns its SSH -L, receives direct Ultra96 results and displays/prints them; complete 600 s protected route |

Fault tests intentionally create nonzero anomaly counters; keep their expected-recovery evidence distinct from clean soak exit codes. A serial reset is not a USB power-loss test. A desktop simulator is not a Phone. Local TLS does not prove SSH, remote service binding or full K/M.

For physical USB and RESET interruption evidence, start a duration-based remote run (`--target 0 --duration 180`) and wait for live ACKs/results before the operator acts. Record the baseline boot ID, unplug USB for about five seconds, reconnect, and require a new boot plus fresh authenticated results. After recovery has been visible for at least 20 seconds, press RESET once and require another separate boot transition and fresh results. If the board has another power source, removing USB alone does not prove power loss. Preserve operator action times, safe serial status and the full trace log; evaluate recovery separately from the clean-pass flag, then perform a clean 100-packet regression. Actions completed before capture support post-action recovery only and cannot supply missing interruption measurements.

## Resource and failure semantics

- Raw BLE bytes and wakeups are bounded. Capacity 64 drop-oldest; monotonic local residence freshness 2 s is checked again after TLS connect.
- One writer owns one request/ACK at a time. Write and ACK deadlines are bounded. No ambiguous in-flight retransmission.
- BLE generation transitions discard queued data/late callbacks. Track stream boot and uint32 sequence separately from connection state.
- Server accepts at most eight active clients/handshakes, bounds frames at 16384 and dedup cache at 4096.
- Viewer queue is 32, drops oldest, expires after 2 s. Sending gets only remaining freshness budget. Bytes already in OS/TLS buffers cannot be recalled; local residence is not a source-to-Phone age measurement.
- Recent dedup is volatile and bounded; after cache eviction or process restart the same trace may be accepted again. Unique IDs help clients correlate; this is not durable exactly-once delivery.
- Diagnostic BLE cleanup uses supervised retained tasks. The supervisor is bounded, but a non-cooperative native operation may outlive it or delay interpreter shutdown; record cleanup errors and terminate only the owned test process if necessary.

See [Phone setup and Unity adapter](week7-phone-runbook.md), [2026-09-07 continuation evidence](week7-continuation-report-2026-09-07.md) and [historical 2026-09-06 evidence](week7-continuation-report-2026-09-06.md).
