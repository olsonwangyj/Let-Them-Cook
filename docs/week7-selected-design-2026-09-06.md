# Week 7 completion design — 2026-09-06

This selected Week 7 contract supersedes earlier Proposed/TBD/approval blockers in the architecture draft, original plan, and 2026-09-05 reports. The user's 2026-09-06 instruction explicitly authorizes autonomous decisions, implementation, tests, deployment attempts, and local commits. Historical evidence is preserved. This is a reversible demonstration contract, not a final sensor/AI or course-security certification.

## Decisions and reasoning

1. Retain the specified linked worktree/feature branch; keep commits local. Main remains untouched.
2. One real ESP is sufficient for Week 7; device IDs 1 and 2 reserve left/right without claiming two-device synchronization. Real sensor calibration, 50 Hz acquisition, inference windows, AI/FPGA, multi-user and AR remain explicitly outside Week 7.
3. Freeze W7 version 1, N=1, exactly 32 bytes: Python struct `<2sBBIII8h`: magic ASCII W7, version uint8=1, device_id uint8 (1 or 2), boot_id uint32 LE, seq uint32 LE, uptime_ms uint32 LE, eight signed int16 LE. Dummy channel i = (seq % 2000) - 1000 + 10*i, i=0..7; 10 Hz. Values are dimensionless test sentinels, not calibrated channels. No application fragmentation, CRC, or compression: BLE supplies transport integrity and fixed length/version validation detects schema mismatch. Send only when ATT MTU >=35, with explicit suppression metrics otherwise.
4. Existing diagnostic UUIDs remain. Dummy Notify UUID is 6e1c0005-7a45-4dc4-b678-3f2d5a9c1001 under existing 6e1c0001 service. No offline ESP backlog; increment seq only on notification submission, uptime captures outages. Boot is random uint32 correlation, not security identity.
5. Network framing is uint32 BE body length + strict UTF-8 JSON object; maximum 16384 bytes, reject zero length, malformed UTF-8/JSON, duplicate keys, NaN/Infinity, non-object and wrong schemas. Frame read/write timeout 5 s by default; close malformed/partial/timed-out connections. No resynchronization or plaintext deployed mode.
6. SENSOR_BATCH fields exactly: v=1,type="SENSOR_BATCH",session_id string,device_id int 1/2,boot_id uint32,seq uint32,uptime_ms uint32,values eight int16. Session is separately configured "week7-demo", never inferred from boot/sequence. Subscription request fields exactly v=1,type="SUBSCRIBE",session_id. Session IDs contain 1..128 Unicode scalar characters, no U+0000..001F controls or lone surrogates. Session ID is configuration/association, not a secret or authentication token.
7. Ultra96 runs ingestion, deterministic inference, result router and gateway in one Python process (stdlib, Python >=3.8). Bind only 127.0.0.1:8888 ingestion and 127.0.0.1:9999 gateway, configurable ports. Ingestion replies with INGEST_ACK fields v,type,session_id,device_id,boot_id,seq,status ("accepted" or "duplicate"). It never sends GESTURE_RESULT to Laptop.
8. GESTURE_RESULT fields exactly v=1,type,session_id,device_id,boot_id,seq,result_id,gesture,confidence. result_id = "device_id:boot_id:seq"; gesture cycles ["REST","FIST","OPEN","POINT"][seq%4], confidence=1.0; clearly dummy inference. Reject wrong dummy values. Only accepted unique input emits a result. Use bounded recent deduplication (4096 traces) and single configured session; duplicate suppression is best-effort within this live cache, not durable exactly-once across service restart.
9. Gateway accepts SUBSCRIBE for configured session, sends SUBSCRIBED fields v,type,session_id, then live results. Latest subscriber replaces old subscriber (one Phone owner). No retained history: disconnected subscriber loses results. Bounded output queue 32, drop oldest, 2 s freshness, bounded send timeout. Reconnect subscribes anew. Cross-session messages are rejected.
10. Laptop callback only copies/enqueues; queue capacity 64, drop oldest, 2 s monotonic reception age; one writer owns framed TLS and reads correlated ACK. Transport errors drop ambiguous in-flight item (no automatic retransmit) and reconnect with capped backoff 0.5..5 s; bounded queue continues then discards stale data. Track raw drops, stale drops, malformed, gaps, duplicates, out-of-order, new boots, connection/reconnect/ACK errors. Each BLE reconnect rediscovers/resubscribes. No Laptop result relay.
11. TLS >=1.2 on both service ports, server authentication by dedicated locally generated Week 7 CA; SAN/SNI identity ultra96.week7.internal even when connecting to local 127.0.0.1 forward. No hostname bypass or plaintext fallback. CA/server private keys kept outside Git, generated certs short-lived (30-day service cert; 365-day CA), server key owner-only permissions on Ultra96. mTLS is deliberately excluded for Week 7 because SSH authenticates access; anyone with authorized Ultra96 shell access is inside this demo trust boundary. Production per-user auth and rotation are a separate scope.
12. Ultra96 TCP 22 is the only externally accessible port and serves SSH (user reaffirmed 2026-09-07). Pin the destination SSH port to 22 so inherited SSH configuration cannot change it. SSH host keys must match existing known_hosts; no accept-any bypass, credentials never stored in repo/logs. Bastion selection uses user-provided stujump.comp.nus.edu.sg. Laptop local forward 18888 -> 8888, independent simulator local forward 19999 -> 9999. Phone uses its own 19999 -> 9999. All forward endpoints are loopback; remote 8888/9999 remain internal TLS listeners, never externally accessed application ports. Use -N -T -L 127.0.0.1:... ExitOnForwardFailure and ServerAlive settings. A bounded supervisor may restart exited SSH; OS process termination must be scoped to children it owns.
13. BLE security selects Secure Connections bonding with a freshly generated six-digit passkey displayed only on local ESP serial, keyboard entry on Windows, MITM/encrypted characteristic/CCCD permissions and authenticated-state notification gating. Do not embed/log the passkey in repository evidence. Bond failure requires deliberate operator removal on Windows and ESP serial erase-bonds command, then new pairing; no automatic downgrade. Keep separate explicit diagnostic build if unprotected comparison is needed; normal build is protected. Real encrypted/authenticated state and bond recovery need physical evidence.
14. Do not add HMAC/HKDF/AES-GCM over BLE for this Week 7 path: authenticated BLE link plus SSH/TLS avoids an unreviewed second key/nonce protocol. Provisioning/nonces/replay-window/app-key-rotation questions are therefore closed as not applicable to this demo. This is a selected engineering policy, not a claim of rubric acceptance.
15. Phone baseline is Android with its own foreground OpenSSH local forward (Termux) and TLS/framed JSON receiver, same SUBSCRIBE contract. Supply runnable Python receiver and a Unity C# adapter/sample with CA validation guidance. Android battery/background/VPN behavior and actual teammate integration require the physical Phone. The Phone runbook also selects a same-foreground-app iSH/OpenSSH/Python experiment for a possible iPhone JSON display; its forwarding/runtime remain untested on-device. Embedded mobile SSH, iOS Unity integration, WS/WSS, and app-managed key storage are outside this baseline. This closes the platform design choice while preserving actual device acceptance.
16. Gate evidence distinguishes unit, local TLS integration, real Ultra96 over SSH, real BLE, protected regression and full physical E2E. Local success cannot promote K or M. Finish only when implementation/docs/tests possible here are complete and remaining checks need unavailable resources.

## Implementation rulings after measurement and review

17. Windows BLE requires Python >=3.10 (Bleak 3.0.1), while stdlib Ultra96/Phone runtime remains >=3.8. Force uncached Windows GATT discovery: the protected physical trial otherwise reported cached MTU 23; uncached discovery measured 517 and carried exact 32-byte data. Cost: fresh discovery adds connection latency.
18. Use explicit OpenSSH ProxyCommand for generated Laptop commands so strict host trust, timeout and supervised BatchMode apply independently to both hops. Phone config aliases enforce the same policy. Cost: printed command is longer than -J; route and uppercase -L topology are unchanged.
19. Limit pending supervised native operations to two and wait for prior native BLE work to settle before reconnecting. Abort TLS transports on timed-out/cancelled close, preserve cancellation propagation, and log only cleanup operation/type. Cost: a broken native stack pauses reconnection instead of accumulating tasks; process shutdown may still need the OS operation to settle.
20. Read MTU control bytes only from the actual GATTS WRITE event and correct handle; prepared/execute-write union data must never be interpreted as a normal write. Cost: prepare/execute writes are unsupported by this test control API.
21. Include unfinished TLS handshakes in the server's eight-client cap. Abort owned sockets through cancellation-safe finally blocks, use POSIX reuse-address for restart, retry transient accepts with bounded backoff, and surface fatal accept-loop death. Cost: a fatal listener error ends the service visibly and requires restart; no silent half-working process.
22. Use cancellable hidden Windows console input for pairing, strict bounded Phone integer parsing, and fresh live-only viewer queues. Cost: pairing CLI needs an interactive Windows terminal; automated physical commissioning may supply the passkey through an in-memory serial provider instead.
23. Skip notification-stop only when a BLE link is already disconnected; always attempt bounded local disconnect cleanup and preserve cancellation arriving during cleanup. Log cleanup operation/type without arbitrary exception contents. Cost: a disconnect race can still produce a counted native error, but cannot silently restart a cancelled worker.
24. Bond recovery is an explicit commissioning procedure: stop clients, confirm physical disconnect, deliberately erase the intended ESP bond and remove its Windows bond, then pair from fresh advertised discovery in a fresh process. Same-process repeated pairing after bond mutation failed without a PIN event in physical testing; a fresh process succeeded. Do not add automatic bond deletion, lower the required protection, or claim an unproven Windows root cause. Cost: this exceptional recovery needs operator state checks; normal stored-bond reconnect was physically tested.
25. VPN state is part of the actual institutional access prerequisite. After the user enabled VPN, the same PowerShell route accepted password authentication on both hops. Earlier publickey-only observations remain historical and do not establish an unconditional key requirement. Interactive commands now allow 20 s proxy connection and 60 s destination banner setup so the first password prompt does not consume the destination's old 10 s deadline; supervised key/agent mode retains 10 s on both. Credentials remain interactive and outside files/logs.
26. Deploy into a private, user-owned `/var/tmp/cg4002-week7-yanjie-20260907` hierarchy because `/home/xilinx` is owned by another UID/GID and inaccessible. Retain immutable source snapshots, TLS and evidence as separate subdirectories; mode 700 directories and mode 600 server key. Do not use sudo or change the shared board's home ownership. Cost: this is a user-managed deployment, with explicit start/stop commands and no system-service/autostart guarantee.
27. Actual remote acceptance uses two verified, independently owned SSH forwards and `tools.rehearse_remote_week7`; it starts no server or tunnel. Require SUBSCRIBED before input, exact bounded ACK/result ID matching, a long initial idle allowance followed by a 5 s deadline once a result frame begins, and explicit remote provenance. A target-zero clean soak must deliver at least ceil(duration * 10 Hz * 0.90) ACKs and unique matching results, have no silence over 5 s between successive messages or after final activity, no unexpected reboot or extra connection, and no recorded stream/transport errors. Initial startup latency is reported separately. Cost: deliberate fault runs retain failure status even when recovery succeeds; one packet during a long observation can never certify a clean soak.
28. Handle SIGTERM gracefully in the Ultra96 CLI, closing owned sockets/listeners and printing final metrics, while preserving Ctrl+C and fatal-listener failure behavior. Unsupported signal-handler platforms keep their existing cancellation path. Cost: start/stop remains scoped to the verified Week 7 PID, and no automatic service manager is installed.

## Operator-device ruling (2026-09-07)

29. The user selected an iPhone for the current physical test. Choose the
foreground iSH/OpenSSH/Python JSON receiver experiment, with interactive
password authentication on both SSH hops. Use OpenSSH `-f` to authenticate
before it backgrounds itself inside the still-visible iSH app, and a fresh
private control socket for scoped checks/shutdown. This avoids requiring SSH
key enrollment for credentials already known to work through VPN. Preserve
strict host-key verification, dedicated scoped configuration, explicit port 22,
20/60-second hop timeouts, the existing CA and service identity. The public
setup bundle contains only receiver source, CA certificate, existing verified
host entries, configuration and instructions. The iPhone must establish its
own authorized VPN route; Laptop VPN does not supply it. Actual iSH fork,
socket, TLS, foreground display and interruption behavior remain physical
tests. Keep the Android baseline available and do not promote this experiment
to iOS Unity or background support. See the [iPhone quickstart](week7-iphone-quickstart.md)
for commands and primary-source references.

30. For the current iPhone commissioning, offer direct SSH/SCP import of the
existing public setup ZIP from the assigned Ultra96. This removes a dependency
on a separate Files transfer service while using the already required SSH
port 22. Bootstrap a fresh Phone-local directory with the two existing
verified Ed25519 host keys and a dedicated strict configuration; authenticate
interactively through the same jump host. Stage only the unchanged public ZIP
in a private owner-only directory on Ultra96, verify its existing SHA-256 both
after upload and before Phone extraction, then use the original receiver and
trust files. No additional network listener or private credential is involved.
The original Files import remains available, and the versioned ZIP is not
rewritten merely to add this alternative. Physical iSH SCP and application
TLS remain separate acceptance steps. See [SSH import](week7-iphone-ssh-import.md).

31. Separate the standalone Python Phone receiver's initial result-idle budget
from its frame-completion deadline. Actual iPhone evidence showed a successful
SUBSCRIBE followed by a TimeoutError before the first result, then 100 exact
results after resubscription. The five-second initial wait left little margin
for operator coordination and the measured roughly four-second BLE startup.
Allow 30 seconds for the first result's first byte while no valid result has
yet been received; once that byte arrives, allow only five seconds total for
the remaining prefix and body. After the first result, including subsequent
reconnections, preserve the existing five-second complete-frame/idle deadline.
Connection, TLS handshake and SUBSCRIBED deadlines remain five seconds, and
the overall CLI duration still bounds all waits. This follows the separation
already selected for the desktop remote viewer in decision 27 without changing
wire frames, TLS identity, replay or result semantics. Publish the updated
standalone receiver in a separately hashed public directory and retain the
original iPhone setup ZIP/capture evidence. Cost: an entirely silent initial
subscription can wait up to 30 seconds before retrying; partial frames and an
established result stream do not get this grace. The portable C#/Unity client
is unchanged. A physical zero-reconnect rerun is still required; the earlier
100-result delivery with its startup retry is not relabelled as uninterrupted.

32. Permit a temporary maintenance-only SSH reverse forward to a scoped iSH
daemon so the agent can run Phone commands and collect evidence. This resolves
the user's request to reduce manual copy/paste with the already installed SSH
software. The daemon and both new forward listeners use loopback, with a
dedicated client key, independently pinned Phone host key and separate config;
no root password, global SSH configuration or application route is changed.
Verify board `GatewayPorts` before creating the reverse forward and inspect its
actual binding afterward. Empty-config multiplex control commands prevent
accidental cancellation of the application's forward. This explicitly narrows
the historical no-`-R` constraint to the assessed application path: Phone
results still use the Phone's independent `-L` to board port 9999. Maintenance
shares the Phone master initially and may be lost on VPN/master interruption;
iOS actions and foreground restoration remain manual. Close the scoped access
after tests. See [maintenance design](week7-iphone-control.md).

## Interfaces

- common.sensor: SensorPacket(device_id, boot_id, seq, uptime_ms, values), encode_packet(packet)->bytes, decode_packet(data)->SensorPacket, dummy_values(seq)->tuple; packet.to_message(session_id)->dict.
- common.wire: async read_frame(reader, timeout=5.0)->dict, async write_frame(writer, message, timeout=5.0), encode_frame(message)->bytes, ProtocolError(ValueError).
- common.tls: client_context(ca_file)->SSLContext, server_context(cert_file,key_file)->SSLContext; TLS_SERVER_NAME="ultra96.week7.internal".
- ultra96.server: Week7Server(ssl_context, session_id="week7-demo", ingest_port=8888, gateway_port=9999); async start(), async close(); expose actual ingest_port/gateway_port for port=0 tests.
- CLI modules: python -m ultra96.server, python -m laptop.bridge, python -m laptop.phone_simulator; tools/generate_week7_pki.py and tools/ssh_tunnel.py.

## Wire reference

| Byte offset | Bytes | Encoding | Meaning |
|---|---:|---|---|
| 0 | 2 | ASCII | W7 |
| 2 | 1 | uint8 | Version 1 |
| 3 | 1 | uint8 | Device 1 or 2 |
| 4 | 4 | uint32 little endian | Boot correlation ID |
| 8 | 4 | uint32 little endian | Sequence; wraps modulo 2^32 |
| 12 | 4 | uint32 little endian | ESP uptime milliseconds; wraps modulo 2^32 |
| 16 | 16 | Eight int16 little endian | Dimensionless dummy sentinels |

The codec rejects wrong magic/version, any length other than 32, invalid device IDs and out-of-range/non-integer fields. Ingestion additionally requires the deterministic sentinels. Structural codec validation permits independent signed-boundary fixtures without claiming those boundary fixtures are valid live dummy input.

Every network object below is encoded as UTF-8 and preceded by its four-byte **big-endian byte length** (length excludes the prefix). No newline delimiter or BOM is used.

```json
{"v":1,"type":"SUBSCRIBE","session_id":"week7-demo"}
{"v":1,"type":"SUBSCRIBED","session_id":"week7-demo"}
{"v":1,"type":"SENSOR_BATCH","session_id":"week7-demo","device_id":1,"boot_id":7,"seq":42,"uptime_ms":4200,"values":[-958,-948,-938,-928,-918,-908,-898,-888]}
{"v":1,"type":"INGEST_ACK","session_id":"week7-demo","device_id":1,"boot_id":7,"seq":42,"status":"accepted"}
{"v":1,"type":"GESTURE_RESULT","session_id":"week7-demo","device_id":1,"boot_id":7,"seq":42,"result_id":"1:7:42","gesture":"OPEN","confidence":1.0}
```

These are five separate example frames, not one multiline JSON document. The first two belong to the Gateway connection, the third/fourth to ingestion, and the last goes only to the active Gateway subscriber. Incorrect session or schema closes that connection without an ERROR frame or result. Clean EOF is normal; EOF inside a prefix/body is malformed. The Gateway accepts no additional client bytes after subscription. A new subscriber replaces the previous one; readiness is confirmed by SUBSCRIBED before sending test input.

For Week 7, gaps are counts in diagnostics rather than separate GAP messages. New boot IDs reset per-device sequence baselines; same-boot sequence arithmetic distinguishes wrap, missing values, duplicates and backward values. A new TLS connection does not imply a new ESP boot. The server's bounded duplicate cache has no timed TTL and no durable storage.
