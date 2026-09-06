# Week 7 autonomous continuation report — 2026-09-06 to 2026-09-07

> Historical local-completion and pre-VPN evidence. The [2026-09-07 Ultra96 continuation](week7-continuation-report-2026-09-07.md) supersedes the remote-access blocker and records the subsequent real SSH/Ultra96 deployment and acceptance. The observations below remain preserved as they occurred.

This report continues the 2026-09-05 handover at clean base `67100864c4f6a450feab218a5f004ded1b48a32b`. Work remains in `D:\LetThemCook-worktrees\week7-stage-d-onward`, branch `feature/week7-stage-d-onward`. The user's latest instruction superseded all previous design/approval gates. No push or merge is authorized or performed; the original main checkout is preserved.

## Decision authority and exhaustive closure

[Selected design](week7-selected-design-2026-09-06.md) is the current Week 7 contract; the original architecture/plan and previous reports are retained as history and linked to this successor. The [runbook](week7-runbook.md) and [Phone runbook](week7-phone-runbook.md) provide operational commands and physical acceptance.

| Previous open issue | Selected practical decision and reason | Cost/limit if changed |
|---|---|---|
| Packet/UUID approval after D | W7 v1, 32 bytes, separate 0005 Notify UUID, existing service/diagnostics retained | Both codecs/fixtures and firmware must change together |
| Sensor fields/widths/units/scaling/rate/batch | Eight signed int16 dimensionless dummy sentinels; N=1 at 10 Hz; explicit LE | This is not final real-sensor calibration or 50 Hz acquisition |
| MTU/fragmentation | Require actual per-connection MTU >=35; reject before send, no fragmentation/truncation | Smaller-MTU devices cannot run this packet unchanged |
| Framing/size/partial/malformed policy | Four-byte BE length, strict UTF-8 JSON object, 1..16384 bytes, bounded deadlines; close invalid/partial frames | Future schema expansion needs versioning; no resynchronization |
| ACK vs result | Correlated INGEST_ACK confirms acceptance only; GESTURE_RESULT flows solely to separate subscriber | ACK is not viewer-delivery evidence |
| Dummy inference/result schema | Four deterministic gestures by seq%4; unique trace ID, fixed confidence1.0 | Real AI must replace this explicitly labelled test mapping |
| Ports/process decomposition | One stdlib Python process, two loopback services8888/9999 | Process failure affects both services; later IPC can split them |
| Session/association/routing/registration | Explicit configured week7-demo, one live viewer, latest subscriber replaces previous; boot/seq never route identity | SSH-authorized users share demo trust; no multi-user authorization |
| Queue capacities/freshness/writer | Raw queue64, viewer32; drop-oldest,2 s local residence, one writer+correlated ACK | Tunable demo defaults, not unsynchronized end-to-end age guarantees |
| Retries/dedup/stale replay | No resend of ambiguous input;4096 recent trace cache; no disconnected viewer backlog | Eviction/restart permits reacceptance; no durable exactly-once guarantee |
| TLS/security approval | TLS>=1.2 both ports; private Week7 CA; SAN/SNI ultra96.week7.internal; exact CA verification | Provision/reprovision clients together; no insecure fallback |
| Certificates/trust/mTLS/rotation | CA365 days, service30 days; keys outside Git; no mTLS, SSH authentication is access boundary | Does not isolate other authorized users of the same Ultra96 |
| SSH hostname/ports/ownership | User-supplied stujump;18888->8888 and independent19999->9999; strict trust both hops; owned subprocess supervision | Actual login presently fails at jump host; no remote pass inferred |
| BLE pairing/bonding/permissions | Stack-generated serial passkey, SC+MITM+bond, secure CCCDs/control, verified callback gating | Pairing requires physical serial/Windows path; no downgrade |
| Windows pairing behavior | Explicit WinRT ProvidePin at authenticated protection; cancellable hidden console input | Windows-specific helper; native radio failures remain possible |
| Bond loss/recovery | Deliberate local Windows unpair and ESP erase-bonds, then verified re-pair | Operator can remove only the intended device's bond |
| HMAC/HKDF/AES-GCM/transcript/nonces/key rotation | Excluded from Week7 because authenticated BLE plus TLS/SSH supplies the selected protection | No application-layer replay/crypto claim; rubric compliance not asserted |
| Phone inner TLS protocol | Same framed TLS+SUBSCRIBE contract, Python standalone and portable Unity C# core | Actual teammate Unity scene/Android runtime remains integration work |
| Mobile SSH/VPN/key storage/lifecycle/platform | Android foreground Termux OpenSSH, Phone-owned key+known_hosts; explicit battery/VPN procedure; optional same-foreground-app iSH/Python experiment documented | Device/vendor/VPN facts require a real Phone; embedded SSH and iOS Unity remain excluded |
| Clock sync, two gloves,50x16 windows,multi-user/four connections | Explicitly outside this one-real-ESP dummy Week7 demo | Future sensor/AI scope needs a separately versioned implementation |
| Old cleanup/fixture/queue defects | Preserved prior fixes; new bounded native-operation cap, socket abort and tests | Noncooperative native operations can still outlive supervisor |
| Gate C new boot ambiguity | Four-byte counter alone cannot prove reboot; W7 boot_id plus serial boot evidence supplies distinction | True USB power loss still requires physical manipulation |

No unresolved packet, protocol, TLS or security design approval remains. Exclusions above are explicit scope decisions, not pending decisions disguised as blockers.

## Local commits and implementation

- `2392cfe`: selected architecture and completion plan.
- `061e362`: Python/C++ packet, immutable vectors, protected ESP32 firmware, prepared-write event guard and diagnostic profile.
- `8e36ce4`: strict TLS framing/schemas, bounded two-listener Ultra96 server, deterministic result routing, simulator, private PKI.
- `ba77cc4`: standalone Android/Python receiver, portable Unity core/component, tests and Phone procedures.
- `ecc2467`: bounded BLE bridge, Windows pairing and uncached GATT discovery, strict two-hop SSH supervisor, local rehearsal and regression tests.
- `f8b33e6`: transient accept retry and visible fatal listener failure, with three reproduced regressions.
- `e82f7e2`: skip notification-stop on a lost link, preserve cancellation during cleanup, and log only cleanup operation/type; five boundary regressions.

The final documentation commit records this report, reconciled original-plan banners, 24 selected decisions, both runbooks and development dependencies. Resolve its full ID with `git log -1`; the report cannot embed the hash of its own containing commit.

The generic queue primitive from the previous continuation remains available. The new raw BLE inbox separately bounds cross-thread wakeups and generations; it does not alter the prior queue's contract.

## Test and review evidence

Initial baseline: `python -m pytest laptop/tests -q` passed 53 tests in 23.33 s. The historical environment's project venv lacks pytest; tests used installed Anaconda Python 3.12.7 with Bleak 3.0.1. Pyserial 3.5 was installed locally for serial observations. No repository credentials were introduced.

After the listener fix, Windows command `python -m pytest laptop/tests tests phone/tests -q` passed 160 tests in 42.10 s (earlier integration baseline: 157 in 43.96 s). C# was actually compiled/executed with PowerShell 7 Roslyn: 44 checks passed, including real TLS trust/SAN/expiry failures. This is portable core evidence, not Unity Editor or Android execution. A final synthetic rehearsal at `f8b33e6` passed 100 ACKs and 100 results in 10.953 s, with all error/drop metrics zero.

**Final code verification**, including the cleanup/cancellation changes committed as `e82f7e2`: the same complete Windows pytest command passed **165 tests in 43.77 s**. The portable C# compile/runtime command passed **44 checks** again. Scoped regression review also passed 24 cleanup/bridge/connection/pairing tests after observed RED failures. No further firmware changes followed the verified build/upload below.

WSL Ubuntu Python 3.10.12 / OpenSSL 3.0.2 validation passed 89 tests, 1 skipped and 21 subtests in 17.42 s. Scope: transport, cleanup, rehearsal, bridge, Phone, packet. Only native C++ was skipped (compiler unavailable on Linux); Windows native C++ vector/event checks passed. That isolated Linux venv used pytest 9.1.1 / cryptography 50.0.1 / Bleak 3.0.2; it and test keys/processes were cleaned. No actual Linux BLE or Ultra96 claim.

Review found and fixed, with observed failing regressions before passing fixes:

1. SDK static-PIN helper silently changed security flags: avoid it and configure SC+MITM+bond explicitly.
2. Arduino characteristic callback also receives execute-write union: parse MTU requests only in exact GATTS WRITE_EVT/handle branch; native event mutation detects regression.
3. Clean EOF counted as malformed: distinguish normal between-frame EOF from partial frames.
4. Cancelled/stalled TLS close leaked sockets: abort and release ownership even during cancellation.
5. Linux pending-handshake restart failed EADDRINUSE: POSIX-only reuse-address with real Linux regression.
6. Plain ProxyJump did not inherit strict/batch options: build explicitly configured proxy and destination; real ssh -G tests with deliberately conflicting configuration validate both hops.
7. Bridge retry backoff reset on stale input: reset only after a valid ACK.
8. Cancellation-resistant native BLE tasks could accumulate: cap outstanding tasks and suppress overlapping connection attempts.
9. Default-executor passkey prompt could block interpreter shutdown: use cancellable Windows console polling.
10. Phone giant JSON integers escaped as ValueError: bounded lexical conversion and reconnectable protocol error.
11. Phone TLS close timeout/cancellation did not abort: socket abort with propagated cancellation.
12. Windows cached GATT gave MTU 23 despite capable physical link: force uncached discovery in all three Windows clients; physical RED/GREEN below.
13. Transient accept errors could kill a listener silently: retry transient errors, expose fatal listener failure and terminate the CLI visibly; three regressions reproduced before the fix.
14. BLE link loss tried to stop notifications on an already-disconnected client: skip that remote operation while still releasing local resources with bounded disconnect. Physical reset evidence below reproduced cleanup error 1 before the guard and 0 afterward. Actual cleanup exceptions now log only operation and exception type.
15. Android documentation left the jump-host timeout implicit: independent `ssh -G` review exposed no timeout; both Phone aliases now explicitly set timeout 10 s and keepalive 15 s / 3 misses.
16. Cancellation arriving during link-loss cleanup was swallowed, allowing reconnection after shutdown was requested: retain/re-raise cancellation after bounded cleanup. Five new fake-boundary tests cover live/gone links, both cleanup cancellation positions and safe exception logging.

These review findings are implementation defects resolved locally, not manual approval blockers.

## Physical firmware and BLE evidence

Board: CH340 COM3, actual ESP32-D0WD revision1.1, BLE address38:18:2B:19:82:AE. PlatformIO Core/environment uses Espressif32 7.1.0, Arduino 3.20017.241212 and BLE 2.0.0.

Both protected and explicit unprotected-diagnostic profiles built. The final prepared-write-fix build took 37.459 s together; protected RAM 39,116/532,480 and flash 1,116,553/1,310,720 (85.2%). Latest protected upload from `D:\LetThemCook-builds\firmware-event-review-20260906` succeeded in 22.543 s with image verification and RTS reset. The connected board is running the protected profile.

Protected `firebeetle32/firmware.bin` SHA-256: `E7634D8A379671F1157B5ECB74D8284025DC8B66C715650CE065032C3ACEE4E9`. This artifact remains outside Git.

Pairing observations, secrets redacted:

- First attempt returned pairing failure with no observed passkey event. This failed observation is preserved; no unsupported root cause is assigned.
- A later attempt recorded one in-memory passkey event and succeeded. Windows bond metadata required EncryptionAndAuthentication. Firmware recorded `ble_security_complete success=1 auth_mode=13 approved=1 current_peer=1 reason=0`. Passkey and raw serial lines were never retained.
- Before uncached discovery, a 40 s protected bridge run received 0, reported 8 BLE errors for apparent MTU 23, and emitted 0 results; all transport counts remained 0.
- Direct uncached discovery then measured 517 and received 21 exact 32-byte packets, with firmware auth_mode 13 and MTU 517.
- After the final firmware upload and client fix, real protected BLE/local-TLS rehearsal passed 100 accepted packets and 100 matching direct results in 14.219 s. First trace `1:3703486763:0`, last `1:3703486763:99`. One BLE connection, one TLS connection; zero gaps, duplicates, malformed, stale, queue drops, ACK, transport, BLE or cleanup errors. One callback/generation item was discarded at shutdown and is reported rather than hidden.
- Protected counter regression received 21 in 12.328 s with all stream/reconnect/cleanup counters 0.
- A 310.015 s serial stability observation recorded 310 consecutive alive lines, one boot 3703486763, 0 anomalies. Last stats: protected 1 / authenticated 1, MTU 517, 3,582 sensor submissions, 0 MTU suppression and 0 submission errors. The cumulative 12 security-suppressed intervals include connection authentication setup; they are not transmitted unprotected data.
- A second concurrent counter-discovery soak was stopped using only its verified owned PID because the already connected ESP intentionally stops advertising. It did not establish a counter-soak pass; long acceptance runs are performed separately.

### Completed sustained and fault experiments

- Real protected BLE through the local TLS server and independent desktop subscriber passed **5,964 ACKs / 5,964 matching results in 600.188 s**. Traces `1:3703486763:101` through `1:3703486763:6064`; one BLE connection and one TLS connection; all reported anomaly, drop and cleanup counters zero. The process loaded commit `ecc2467`; later accept-error and disconnected-cleanup fixes were tested separately. This was local TLS, not actual Ultra96/SSH/Phone.
- Dedicated counter target: **1,001 received in 103.609 s**, exceeding the 1,000 target, all anomaly/reconnect/cleanup counters zero. Separate 600 s counter soak: **5,942 in 600.218 s**, all anomalies and cleanup counters zero. Rates include connection/setup time; no counter reboot identity is inferred.
- Protected MTU boundary passed initially after the counter soak, then again with concurrent safe serial correlation on 2026-09-07: Windows and ESP both 517; exact 20 and 514 bytes; no 515-byte notification; firmware explicitly logged `mtu_probe_rejected requested_length=515 negotiated_mtu=517 allowed_length=514`. Auth mode 13 was approved, and probe error/drop/cleanup counts were zero.
- First induced RTS reset at `f8b33e6`: boot 3703486763 -> 4162790477, two BLE and two TLS connections, 118 received / 117 ACKs and results, new_boots 1, transport_errors 1, ambiguous_dropped 1, cleanup_errors 1, server rejected 1. Stream malformed/gap/duplicate/stale/drop counts were zero. This is fault-recovery evidence; its strict clean-soak `passed` flag was false.
- Repeated RTS reset with the disconnected-client cleanup guard: boot 4162790477 -> 903179121, **120 received / 119 ACKs and results in 35.313 s**, two BLE/TLS connections, new_boots 1, transport_errors 1, ambiguous_dropped 1, server rejected 1, callback-generation discard 1 at shutdown, **cleanup_errors 0**; all stream anomalies zero. Firmware approved auth mode 13 before and after reset and renegotiated MTU 517. The runtime had the guard but preceded the later cancellation-preservation refinement. The expected transport interruption keeps `passed=false`; no clean-soak pass is claimed. The 5 s server input timeout can expire during a lengthy BLE reconnect, but no packet-level root cause is asserted for this particular transport error.
- An erase-bonds command issued shortly after a client returned was correctly rejected because Windows had not physically disconnected yet. An immediate pair attempt after Windows unpair also failed without a PIN event. After actual disconnect, ESP erasure confirmed remaining 0; fresh advertised discovery/Windows metadata and authenticated pairing restored the link. A subsequent protected run passed **100 ACKs/results in 13.625 s**, all errors zero (one shutdown callback-generation discard).
- Deliberate **ESP-only bond loss**: Windows still reported paired/protection 3; ESP erase confirmed one bond removed and remaining 0. A 12.047 s attempt delivered **zero packets/ACKs/results**, with firmware authentication failures (`success=0 auth_mode=0 approved=0 reason=102`) and zero TLS connections. The timed attempt ended before the application's long connect deadline, so its BLE-error counter remained 0; firmware evidence establishes the failed authentication. Windows unpair plus explicit authenticated pairing restored protection 3/auth mode 13, then **100 ACKs/results in 16.140 s**, all errors zero (one shutdown callback-generation discard).
- Deliberate **Windows-only bond loss**: a 12.031 s attempt delivered **zero packets/ACKs/results**, with one visible "authenticated Windows bond required" error and zero cleanup errors. Same-process re-pair failed without a passkey event; even the subsequent both-sides cleanup/re-pair in that process failed. These attempts are preserved as failures; the runtime cause is unproven. Firmware's later erase reported count 0, so Windows-only unpair is not assumed to leave the ESP's stored bond intact indefinitely.
- **Final restoration in a fresh process** succeeded: Windows paired/protection 3, firmware auth mode 13 approved, MTU 517. The complete final source (including cancellation preservation, later committed as `e82f7e2`) delivered **100 ACKs / 100 matching results in 13.625 s**, traces `1:4178664849:0` through `1:4178664849:99`. One BLE/TLS connection; every reported error, anomaly, queue, stale, generation, callback-generation and cleanup count was **zero**. The board and Windows are left paired in the protected configuration. This is the last physical data run.

RTS resets restart the ESP but do not physically remove USB power. No true USB power-loss or physical RESET-button observation is claimed. Passkeys were consumed in memory; only whitelisted security/MTU/bond/connection events were retained.

## SSH/Ultra96 observation

The supplied `ssh -J yanjie@stujump.comp.nus.edu.sg xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg` path, with existing host-key trust, reached stujump 137.132.80.25 (OpenSSH 9.6p1). It refused login and advertised only `publickey`; an explicit password/keyboard-interactive-only probe confirmed the same refusal. The usual .ssh directory held only known_hosts files, and ssh-agent was unavailable.

Thus the supplied password could not be submitted through an offered authentication method. No password or credential was written to the repository or logs. No authenticated Ultra96 session, remote deployment, application tunnel or remote application test occurred. Host-key bypass and plaintext fallback were not introduced. A usable authorized key/agent or corrected institutional access path is genuinely required.

### Follow-up retry — 2026-09-07 00:29 Asia/Shanghai

After the user supplied the passwords again, retried the exact `-J` route in an interactive terminal with existing host-key trust and a 10 s connection timeout. It again stopped at `yanjie@stujump.comp.nus.edu.sg: Permission denied (publickey)` before reaching Ultra96. An independent jump-only diagnostic explicitly enabled password/keyboard-interactive and disabled public-key authentication; the server still advertised only `publickey` and closed without a password prompt. Neither password was tested or rejected; there was no offered password method through which to submit it. No credentials were added to commands, files or this report. Existing software/hardware acceptance and the remote-access blocker are unchanged.

A further read-only environment check found a nondefault existing identity in WSL Ubuntu, `/home/yanjie/.ssh/id_ed25519_codex`, with its public companion and no agent socket. WSL's expanded configuration did not automatically select it for these hosts. An explicit, bounded key-authentication attempt used that identity and the already trusted Windows known_hosts file: the server host key matched, the client offered the key, and stujump rejected it with `Permission denied (publickey)`. Public-key fingerprint: `SHA256:3/1aREzLUAwLxfC449q/M3b45ge+ecIxnenPwTym6CQ`. The private key was neither displayed nor copied. An initial WSL attempt failed host verification because the space-containing known_hosts option needed internal quoting; the corrected attempt preserved strict checking and successfully verified the existing host key before authentication. Thus an existing WSL key is present, but this test did not establish that it is authorized for `yanjie` on stujump.

Official next-step references: NUS Computing's [SSH Jump Host guide](https://dochub.comp.nus.edu.sg/cf/services/network/sjump) and [SSH Keys guide](https://dochub.comp.nus.edu.sg/cf/services/network/skeys) require SoC login. A public [NUS staff guide](https://www.comp.nus.edu.sg/~chowcm/sjump.html) describes submitting a public key through `skeys.comp.nus.edu.sg` and selecting `jump`, but its example names `sjump`, so identical `stujump` eligibility is not assumed. The user must confirm the current account/host enrollment procedure or provide a working authorized environment; [NUS Computing support](https://dochub.comp.nus.edu.sg/cf/contact) provides the [ticket portal](https://rt.comp.nus.edu.sg). No key enrollment, credential changes or alternate-host login was performed. The current authentication advertisement does not prove the password is wrong, the account is eligible, or that an accepted key would never be followed by another factor.

## Gate status and remaining physical work

| Gate | Implemented/tested here | Remaining acceptance |
|---|---|---|
| A | Current build/upload, repeated RTS resets, >5 min stable serial | Physical RESET-button and USB disconnect/reconnect evidence |
| B | Service/diagnostic discovery, protected Notify data, same-boot reconnect and new-boot correlation | No additional software work; physical USB experiment below remains |
| C | Separate 1,001-target and 5,942-counter/600 s clean runs; W7 reset recovery | Induced actual USB power-loss recovery |
| D | Protected exact boundary and explicit oversize rejection, MTU 517 on both endpoints, zero errors | None for the connected board's boundary test |
| E | Frozen codec/vectors/C++ serializer, 100-packet runs and 5,964-packet protected soak | Only actual USB loss / remote route acceptance |
| F | Strict real local TLS/fragmented/malformed/partial frame tests; loopback-only listeners | Actual Ultra96 deployment and ss evidence after SSH access |
| G | Verified TLS wrong-SAN/CA/plaintext rejection; strict SSH command/supervisor tests | Actual SSH100-message run and tunnel fault recovery |
| H | Bounded queue/generation/freshness/one-writer/ACK/recovery tests; real BLE/local TLS and reset recovery | Real Ultra96 bridge/fault rehearsal |
| I | Deterministic unique result and invalid/duplicate rejection tests | Actual Ultra96 observation |
| J | Independent subscriber, replacement/reconnect/malformed/slow-consumer tests | Desktop subscriber through its own actual SSH tunnel |
| K | Protected local-TLS 600 s rehearsal and separate reset fault | Real ESP->Laptop->Ultra96->independent viewer 600 s + separate faults |
| L | Real SC/MITM/bond authentication, protected C/D/E, reset reconnect, both bond-loss negatives and final authenticated restoration | True USB power-cycle and actual protected remote K |
| M | Python Android receiver, compiled/tested C# core, Unity component; Android and experimental foreground iOS procedures | Actual Phone setup/runtime and independent SSH/VPN path; teammate Unity build/device integration |

Real sensors, real AI/FPGA, two-glove synchronization, multi-user behavior, and AR UI are explicitly excluded from this practical Week7 Communications implementation. Their absence is not a coding blocker left for this continuation.

## Evidence limits and next task

Use the runbook's exact command sequence, separate clean soaks from deliberately induced failures, and retain all counters. Test-only timing defaults and 32-byte W7 sentinels are not final production contracts. Recent dedup is evicted by capacity or cleared at process restart and is not durable. App-queue freshness cannot recall bytes already inside TLS/TCP buffers. Native Windows BLE operations may outlive supervised cancellation and delay interpreter shutdown, though outstanding work is now bounded.

No Android adb runtime was available in PATH or the usual SDK locations, and no Unity Editor/build environment was available. Windows PnP entries for an iPhone/spacedesk do not establish access to an unlocked controllable Phone or a runnable receiver. The iOS appendix is an explicitly untested engineering experiment using official iSH documentation; it is not iOS acceptance.

Runtime PKI is retained outside Git in `C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906`, with owner-restricted permissions. Its public CA SHA-256 fingerprint is `4D:FB:A4:90:5C:17:1E:68:C3:62:3D:BC:95:21:54:14:90:76:ED:89:00:4B:85:D4:75:E8:58:CC:55:07:60:EC`. Check certificate validity before the next deployment. Neither private key nor any SSH password/passkey is part of the continuation artifacts.

Final housekeeping verified no surviving owned rehearsal/bridge/probe/counter/server/tunnel processes and no listeners on 8888, 9999, 18888 or 19999. Temporary serial monitors closed COM3. The original `D:\LetThemCook` checkout remained clean at `f6bc999` on main; the requested linked worktree/feature branch is retained. Current documentation links resolve, `git diff --check` passes, and no PKI/private-key file is tracked. All changes are kept in local commits; no push, merge, remote deployment, global SSH-config rewrite or Bluetooth-service reset occurred.

The next remote task is to restore authorized SSH access, inspect Python/ports on the actual Ultra96, deploy the committed source to a fresh user-owned directory, provision only the server certificate/key, and execute remote F/G/I/J before K/M. The Phone runbook includes an Android foreground OpenSSH baseline, public CA fingerprint verification, strict host trust, Unity wiring and battery/VPN checks, plus the foreground-only iSH experiment. Every remaining acceptance procedure is concrete; no packet, TLS, security or interface decision awaits approval.
