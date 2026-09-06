# Week 7 communications runbook

Current design authority: [selected decisions](week7-selected-design-2026-09-06.md). This runbook implements the 2026-09-06 autonomous continuation; historical approval blockers no longer apply. Preserve separate evidence for local, real BLE, Ultra96/SSH, and real Phone tests.

## Setup and local checks

Run from the feature worktree in PowerShell:

```powershell
Set-Location 'D:\LetThemCook-worktrees\week7-stage-d-onward'
python -m pip install -r laptop/requirements.txt
python -m pip install -r requirements-dev.txt
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest laptop/tests tests phone/tests -q
pwsh -NoProfile -File phone/tests/run_core_tests.ps1
```

Windows BLE/pairing requires Python >=3.10 because Bleak 3.0.1 declares that floor; tests here use Python 3.12. Ultra96 and the standalone Phone receiver require Python >=3.8; Ultra96's actual version must be checked after SSH access works. cryptography is provisioning/test-only; the deployed server has no third-party Python dependency. Pin Bleak 3.0.1 as declared. The C# test command requires PowerShell 7 `pwsh`; see the Phone runbook.

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

Physical testing found that immediate repeated pairing in the same process after Windows unpair could return FAILED without a passkey event. Fresh-process pairing succeeded after deliberate bond cleanup. The cause inside Windows is unproven; do not respond by weakening security or adding automatic bond deletion. When testing one-sided loss, collect the zero-data/authentication-failure evidence first, then use this explicit recovery procedure. True USB power loss must still be tested by physically disconnecting power.

## SSH access prerequisite and deployment

Use this hardened command for the user-selected jump route:

```powershell
$week7Proxy = 'ssh -o StrictHostKeyChecking=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -W "[%h]:%p" yanjie@stujump.comp.nus.edu.sg'
$week7SshOptions = @('-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10', '-o', "ProxyCommand=$week7Proxy")
ssh @week7SshOptions xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg
```

On 2026-09-06 the jump host advertised only publickey authentication and denied access. No private key existed in the usual .ssh directory and no ssh-agent was running. A password cannot satisfy a server that offers only publickey. A valid authorized key/agent or corrected institutional access path is required; do not bypass known_hosts or invent another username. Host keys for both named endpoints already exist locally.

The 2026-09-07 follow-up confirmed the same result for the exact `-J` route and an explicit password/keyboard-interactive diagnostic; neither password could be submitted. The earlier key inventory covered Windows. WSL Ubuntu also has an existing nondefault `/home/yanjie/.ssh/id_ed25519_codex`; offering it explicitly after strict host verification was rejected. Do not assume that a private-key file's existence proves institutional authorization.

For enrollment prerequisites, consult the current SoC-login-protected [NUS Jump Host](https://dochub.comp.nus.edu.sg/cf/services/network/sjump) and [SSH Keys](https://dochub.comp.nus.edu.sg/cf/services/network/skeys) guides. A public [NUS staff example](https://www.comp.nus.edu.sg/~chowcm/sjump.html) describes the `skeys.comp.nus.edu.sg` public-key submission workflow, but names `sjump`; confirm its applicability to the assigned `stujump` account through the current guides or [NUS Computing support](https://dochub.comp.nus.edu.sg/cf/contact). Submit only an authorized public key through that procedure, never its private companion. No enrollment was performed here.

Once authenticated, inspect before deployment:

```sh
hostname
python3 --version
uname -m
ss -ltn
```

Use a fresh user-owned directory `~/cg4002-week7-20260906`, so no existing application is replaced. On the Laptop prepare a tracked-source archive after commits:

```powershell
git archive --format=tar --output="$env:TEMP\cg4002-week7-20260906.tar" HEAD
scp @week7SshOptions "$env:TEMP\cg4002-week7-20260906.tar" 'xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg:cg4002-week7-20260906.tar'
```

On Ultra96:

```sh
mkdir -m 700 ~/cg4002-week7-20260906
tar -xf ~/cg4002-week7-20260906.tar -C ~/cg4002-week7-20260906
mkdir -m 700 ~/cg4002-week7-20260906-tls
```

Transfer only server-cert.pem/server-key.pem into that TLS directory with `scp @week7SshOptions` over the verified path; use `chmod 600 ~/cg4002-week7-20260906-tls/server-key.pem`. Do not add certificates/keys to Git. The explicit ProxyCommand is equivalent to the user-selected jump route while forcing trust/timeouts independently on both hops; plain -J does not inherit every destination option. Check that ports 8888 and 9999 are free; select alternate configurable ports if another service owns them. Run foreground in a dedicated SSH session:

```sh
cd ~/cg4002-week7-20260906
python3 -m ultra96.server --cert ../cg4002-week7-20260906-tls/server-cert.pem --key ../cg4002-week7-20260906-tls/server-key.pem
```

From another session verify `ss -ltn` shows only 127.0.0.1:8888 and 127.0.0.1:9999 for these services. Capture safe stdout/stderr for correlation; the server logs session/device/boot/sequence and metrics, never credentials.

On the Laptop create its ingestion forward:

```powershell
python -m tools.ssh_tunnel
```

Execute the printed command in its own terminal. It uses `-N -T -L 127.0.0.1:18888:127.0.0.1:8888`, strict host trust, keepalives and ExitOnForwardFailure. For key/agent authentication, `python -m tools.ssh_tunnel --run` supervises and restarts only its owned SSH process. Password/MFA entry belongs to foreground OpenSSH; it is never stored by the supervisor. If separate identities are needed for jump and target, configure explicit Host aliases in the user's SSH config; a final-target -i is not silently a jump-host identity.

Open a **second independent SSH process** for the simulator:

```powershell
python -m tools.ssh_tunnel --local-port 19999 --remote-port 9999
```

Execute that printed command. Then run simulator and producer in separate terminals:

```powershell
python -m laptop.phone_simulator --host 127.0.0.1 --port 19999 --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --count 100
python -m laptop.bridge --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --mock --target 100 --duration 40
```

Replace `--mock` with real BLE (omit it) after the independent remote transport test passes. The simulator must subscribe before sending input: live results have no history. An ACK confirms server input acceptance and does not prove viewer delivery.

For the sustained 600-second real-ESP route and separate fault experiments, keep both tunnels open and run the following in separate terminals:

```powershell
python -m laptop.phone_simulator --host 127.0.0.1 --port 19999 --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --count 0 --reconnect
python -m laptop.bridge --ca 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem' --duration 600 --target 0
```

Stop the simulator with Ctrl+C after the producer ends. On an actual Phone, use `python ~/week7-phone/receiver.py --ca ~/week7-private/ca-cert.pem --port 19999 --session week7-demo --count 0 --duration 600`. Run only one viewer: a newly subscribed same-session viewer replaces the previous owner.

## Physical acceptance sequence

Record date, Git commit, profiles, OS/SDK/Bleak versions, hardware IDs, endpoints, duration, safe logs and all failure counters. Preserve failures separately from passes.

| Gate / experiment | Procedure | Acceptance |
|---|---|---|
| A serial | 5 min output; press RESET; physically unplug/replug USB | Stable alive sequence; reset and true USB power loss each produce a new boot |
| B discovery | Service/Notify discovery; connect/disconnect; compare submitted sequence logs | Expected UUIDs; no unexpected reboot |
| C/E protected stream | Receive >=1000 counters; run separate 600 s stream; physically power loss during W7 bridge | Gap/duplicate/order metrics visible; rescan, rediscover, resubscribe; W7 boot_id changes after actual reboot |
| D protected boundary | Run mtu_probe with safe serial correlation | Both endpoint MTU; exact 20 and MTU-3, oversize rejected; zero malformed/cleanup anomalies |
| E packet | Real 100-packet W7 local TLS rehearsal | Exact 32-byte/version/sentinels; seq/boot trace agrees; insufficient MTU suppresses before send |
| F/G remote | 100 mock inputs through actual Laptop SSH forward | 100 correlated INGEST_ACK in Laptop + Ultra96 logs; loopback-only listener |
| G identity negative | Trust wrong CA or use localhost as SNI in isolated test | TLS fails; no frame accepted and no plaintext fallback |
| G/H tunnel loss | Stop only Laptop-owned ingestion tunnel during stream, then restart | Bounded queue; error/drop/stale counters rise; next fresh input succeeds; ambiguous input not resent |
| I/J subscriber | 100 inputs; invalid input; duplicate trace; second same-session subscriber | Correct unique dummy results; invalid/duplicate no new result; latest subscriber owns live delivery |
| J/K Phone tunnel loss | Stop only simulator/Phone-owned tunnel and restart/subcribe | Laptop ACK path continues; results lost while disconnected are not replayed |
| K ingestion process loss | Stop only Week7 server, restart same ports/cert, reconnect clients | Fresh transport/subscription resumes; no durable exactly-once claim across restart |
| K real path soak | Real ESP -> Laptop -> actual Ultra96 -> independent simulator for 600 s; induce each fault separately | Counts and gaps correlated across endpoints, bounded queues, no stale backlog replay |
| L bond recovery | Remove Windows bond only, reconnect; deliberately erase ESP bonds with serial command; pair again | Failure is visible, no downgrade; explicit re-pair restores verified authenticated state |
| L restart | Power-cycle ESP and restart Laptop client using stored bonds | Authenticated reconnect and protected C/E/K regression pass |
| M actual Phone | Follow Phone runbook with physical Android and teammate receiver | Phone owns its SSH -L, receives direct Ultra96 results and displays/prints them; complete 600 s protected route |

Fault tests intentionally create nonzero anomaly counters; keep their expected-recovery evidence distinct from clean soak exit codes. A serial reset is not a USB power-loss test. A desktop simulator is not a Phone. Local TLS does not prove SSH, remote service binding or full K/M.

## Resource and failure semantics

- Raw BLE bytes and wakeups are bounded. Capacity 64 drop-oldest; monotonic local residence freshness 2 s is checked again after TLS connect.
- One writer owns one request/ACK at a time. Write and ACK deadlines are bounded. No ambiguous in-flight retransmission.
- BLE generation transitions discard queued data/late callbacks. Track stream boot and uint32 sequence separately from connection state.
- Server accepts at most eight active clients/handshakes, bounds frames at 16384 and dedup cache at 4096.
- Viewer queue is 32, drops oldest, expires after 2 s. Sending gets only remaining freshness budget. Bytes already in OS/TLS buffers cannot be recalled; local residence is not a source-to-Phone age measurement.
- Recent dedup is volatile and bounded; after cache eviction or process restart the same trace may be accepted again. Unique IDs help clients correlate; this is not durable exactly-once delivery.
- Diagnostic BLE cleanup uses supervised retained tasks. The supervisor is bounded, but a non-cooperative native operation may outlive it or delay interpreter shutdown; record cleanup errors and terminate only the owned test process if necessary.

See [Phone setup and Unity adapter](week7-phone-runbook.md) and [current continuation evidence](week7-continuation-report-2026-09-06.md).
