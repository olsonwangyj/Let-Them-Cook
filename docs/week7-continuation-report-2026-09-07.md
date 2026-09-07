# Week 7 Ultra96 continuation — 2026-09-07

This report continues local completion at `03790c1` and the pre-VPN retry at `ec7a08e`, in `D:\LetThemCook-worktrees\week7-stage-d-onward` on `feature/week7-stage-d-onward`. The user's original autonomous authorization remains in force. Earlier failures, firmware evidence and local soaks are preserved in the [previous report](week7-continuation-report-2026-09-06.md). The [selected design](week7-selected-design-2026-09-06.md) now records 30 decisions; no protocol or security approval is pending.

## VPN resolved the access blocker

### Teacher demo materials completed

The user's follow-up asked for all materials needed to demonstrate Week 7 dummy packets and correct connections. The new [teacher demo pack](week7-demo-pack/README.md) supplies an executable operator checklist, 3–5 minute talk track and Q&A, a self-contained three-page [HTML brief](week7-demo-pack/teacher-brief.html) and [printable PDF](week7-demo-pack/teacher-brief.pdf), a byte/framing [packet walkthrough](week7-demo-pack/packet-walkthrough.md), generated illustrative JSON, and a portable recorded 100-message capture with hashed provenance. This fills the gap between engineering runbooks and a teacher-facing demonstration. The written official grading rubric was unavailable; materials describe the team's stated scope without claiming rubric acceptance.

New `python -m tools.week7_demo` commands:

- `packet`: offline illustrative device 1 / boot 7 / sequence 42, exact 32-byte hex, decoded fields, deterministic OPEN result and all five network frame examples. This is explicitly not captured hardware evidence.
- `sender --ca ... --target 100 --duration 60`: protected real BLE using the existing Bridge, emitting the decoded packet/reconstructed bytes and correlated ACK after validation. It owns no viewer, server or SSH process; actual Phone mode can therefore retain the independent Phone result path. First ACK latency and inter-ACK/trailing silence are reported; a successful clean sender requires the requested coverage and no silence over five seconds after activity begins.
- `audit LOG [--phone-results PHONE_JSONL] --minimum-count N`: bounded offline schema/session/trace comparison. Exact ID sets, duplicate/missing/unexpected records, minimum count and completed summary are checked. Reconnect/fault events cannot pass even if a recorded boolean claims success. Malformed, deeply nested, truncated or cross-session files fail safely; Windows UTF-8 BOM capture is supported. This verifies saved content, not physical provenance or Phone timing.

The presentation/tooling rulings and reasons are in [the completed materials plan](superpowers/plans/2026-09-07-week7-demo-materials.md): reuse existing protocols, select offline printable artifacts, add an observational sender instead of a result relay, and independently audit identity sets. Phone output is post-deduplication and has no per-result timestamps; its raw JSONL cannot alone establish uninterrupted Phone delivery or absence of duplicate wire arrivals. Operator instructions require separate timed device observation/status for those claims.

Verification: **203 tests passed, 2 skipped in 73.08 s** for `python -m pytest laptop/tests tests phone/tests -q`. The unchanged skips are Windows exclusions for Linux signal behavior, separately verified earlier. The new suite has 22 tests; a final focused rerun passed all 22 in 0.60 s, and a combined bridge/SSH/demo checkpoint passed 41. Tests include literal packet bytes, actual local TLS sender/independent result delivery, rejected uncorrelated ACKs, log inconsistencies and CLI exit codes. Review reproduced and fixed wrong-session summaries, deeply nested JSON errors and interruption-evidence handling; the sender's silence limits have a deterministic clock test. These new sender tests use local TLS fixtures and do not constitute a new physical Phone or Ultra96 run.

Fresh offline audits reproduced the recorded clean 100/100 and 5,965/5,965 results; the recorded viewer fault correctly failed with 585 matched and 279 missing results. The portable `recorded-demo100.jsonl` preserves only the original application events/summary; its omitted context and original/export hashes are documented in `evidence-index.json`. All 38 operator-document local links resolve; 13 PowerShell blocks parse, command help/certificate metadata and capture/exit behavior were checked. PDF export produced three A4 landscape pages (115,314 bytes), rendered with Poppler and visually inspected with no overflow or overlap. Its 181 Python / 44 portable C# figure is explicitly labelled historical baseline verification.

No remote deployment, firmware, bond, SSH configuration or existing transport source changed while making these materials. The actual Phone/Unity and separately observed physical interruption gates remain pending. The pack is ready to rehearse/present the verified desktop route and contains the exact procedure to complete the Phone route when that device is available.

### Port 22 constraint reaffirmed after completion

The user reaffirmed that **Ultra96 TCP port 22 is the only externally accessible port and serves SSH**. This is a fixed network constraint for every continuation. Both application listeners remain on Ultra96 loopback (`127.0.0.1:8888` ingestion, `127.0.0.1:9999` Gateway); Laptop and Phone reach them through their own SSH local forwards over port 22 through the jump host. Client ports 18888/19999 are local loopback endpoints. The local listener inventory below does not imply that any other Ultra96 port is externally reachable.

A follow-up configuration check reproduced that inherited `Host * / Port 2222` could redirect the generated SSH destination. The generator now explicitly selects `Port=22` in interactive and supervised modes; PowerShell SSH/SCP and Phone recipes likewise pin the Ultra96 destination to 22. Decision 12 and entry-point documentation record the reason. This is a client command/documentation change; the verified Ultra96 service and remote test evidence are unchanged.

Verification: both real OpenSSH `ssh -G` regression cases first failed with effective port 2222, then passed with port 22 after the fix. `python -m pytest tests/test_ssh_trust.py tests/test_bridge.py -q` passed **19 tests in 2.10 s**. Independent read-only review confirmed the loopback bindings and tunnel topology; no remote restart or network change was needed.

### Verified VPN login

After the user enabled VPN, the exact PowerShell `ssh -J` route offered a jump-host password prompt. Its original 10 s destination connection timeout expired during interactive login (`Connection timed out during banner exchange`). The hardened route with a 20 s proxy timeout and 60 s destination timeout accepted both supplied passwords and reached hostname `pynq`. Existing host keys were verified. Passwords were entered only into OpenSSH's hidden prompts, never stored in files, command arguments or reports.

The earlier publickey-only advertisement was a real observation before this network-state change. It did not prove the passwords were wrong or that public-key enrollment was always required. No SSH key enrollment, alternate account selection or host-key bypass was needed.

## Actual board and deployment

| Property | Observed value / selected action |
|---|---|
| Remote account | uid 1000 `xilinx`, gid 1000, groups adm/sudo; no sudo used |
| Host / architecture | `pynq`, aarch64 |
| Runtime | Python 3.10.4 at `/usr/bin/python3`; OpenSSL 3.0.2 |
| Home problem | `/home/xilinx` owner UID 127 / GID 135, mode 750; account cannot enter it |
| Deployment root | `/var/tmp/cg4002-week7-yanjie-20260907`, owned xilinx:xilinx, mode 700 |
| TLS | `tls/` mode 700, `server-key.pem` mode 600; only server certificate/key copied; CA key remains on Laptop |
| Service identity | TLS SAN/SNI stays `ultra96.week7.internal`; hostname `pynq` does not replace it |
| Ports | 8888/9999 were free; unrelated 22/80/139/445/9090 services preserved |
| Active service snapshot | `source-db6769a`; stdlib imports and compileall passed on the board |
| Service binding | Verified `ss -ltnp`: only 127.0.0.1:8888 and 127.0.0.1:9999 for this process |
| Independent forwards | Laptop 127.0.0.1:18888 -> Ultra96 127.0.0.1:8888; separate viewer 127.0.0.1:19999 -> Ultra96 127.0.0.1:9999 |

Initial source archive at `ec7a08e` had SHA-256 `A1AA3720D34576A9F54BA0D9E3DE529035E96F98AB90564937C7EBEC30620855`; its first service PID was 43820. The updated archive at `db6769a477623fea3a6e6b5137e3150e56b812ec` had SHA-256 `8A5AE93FAA072712C47E832713815C670014760538CEF5E7887278906EF1ECEF`; its second service PID was 43881. Both archive hashes matched after transfer. The original service exited 143 on SIGTERM as expected before the shutdown fix; updated shutdown evidence is recorded below. Source snapshots are retained instead of overwriting an existing shared application.

The first independently verified Windows tunnel owners were PID 28968 (ingestion) and PID 30840 (viewer), in separate OpenSSH processes, each with its own jump connection. These are historical evidence IDs, not reusable stop commands; always verify the current PID, command and endpoint ownership.

## New implementation and review decisions

- `db6769a`: interactive SSH uses proxy/destination 20/60 s, while supervised key mode remains 10/10 s. Real `ssh -G` tests against deliberately unsafe defaults verify both hops' strict trust, mode and keepalives. The same commit adds graceful CLI SIGTERM with final metrics, socket release and restartability, preserving Ctrl+C and fatal listener failures.
- `1adb464`: new remote acceptance runner starts no server or SSH process, subscribes before production, emits JSONL ACK/result evidence, and checks exact trace IDs with a bounded 65,536-ID ledger per side. Every synthetic run gets a fresh boot ID so repeated tests do not collide with the live server's duplicate cache.
- `cf03318`: preserve cancellation during failed TLS teardown. Abort and clear owned streams, log only operation/type, and re-raise cancellation so the writer cannot silently resume after cancellation. Reset/timeout errors remain counted and aborted. Four reproduced regressions passed, the focused suite passed 34 tests, and independent review passed 23 tests plus an actual one-second close timeout with no retained task.
- Review reproduced three false acceptance risks and fixed them with regressions: a duration-long partial-frame deadline, a single packet followed by silence passing a duration run, and a boot change passing as a clean run. Initial idle waiting is now separate from the 5 s frame-completion deadline. A clean 600 s run requires at least 5,400 ACKs and unique matching results, no silence over 5 s between successive messages or after final activity, no reboot/extra connections and no recorded errors. Initial startup latency is reported separately. Fault recovery is evaluated separately from this clean-pass flag.
- Private writable deployment under `/var/tmp` avoids changing the shared board's home permissions. Android foreground SSH supports the verified password route; key-only background/supervisor recipes state that narrower requirement explicitly.

Runner SHA-256 used for the sustained run: `36F694530383F23B0474B42EB88C45A0271EEBFA77CBDAA7842FE65EF7691376` (commit `1adb464`). Remote server code is the `db6769a` snapshot; the later runner executes on the Laptop and does not change server code.

## Software verification

Final Windows command `python -m pytest laptop/tests tests phone/tests -q` passed **181 tests, 2 skipped, in 75.79 s**, including `cf03318`. The skips are Linux-only process-signal tests, separately executed in WSL: all three signal tests and all three existing accept-recovery tests passed. Earlier whole-suite checkpoints were 174 passed / 2 skipped in 64.94 s and 177 passed / 2 skipped in 73.82 s. Focused remote-runner/local-rehearsal tests passed 11 in 32.25 s; independent review reran them successfully in 32.18 s. Earlier portable C# verification remains 44 passed; no Phone/Unity source changes were needed in this continuation.

The new code required no firmware upload and no remote third-party Python installation. Both firmware profiles and the final protected upload remain the verified artifacts from the earlier report.

## Actual remote acceptance evidence

Safe event logs and test scripts are retained outside Git at `D:\LetThemCook-builds\remote-evidence-20260907`. All local port provenance below was verified against the actual SSH process and remote listeners; localhost success alone is not treated as proof of Ultra96 execution.

| Experiment | Result |
|---|---|
| Synthetic remote 100 | 100 accepted ACKs and 100 exact matching results in 10.625 s; traces `1:1995138198:0`..`:99`; every reported error/drop/anomaly zero; remote log agrees |
| Protected real BLE remote 100 | 100 accepted ACKs and 100 exact matching results in 13.859 s; traces `1:4178664849:100`..`:199`; one BLE, TLS and subscriber connection; all reported errors/drops zero |
| Protected real BLE remote 600 s | **5,965 accepted ACKs / 5,965 exact matching results in 600.563 s**; traces `1:4178664849:200`..`:6164`; one BLE/TLS/subscriber connection, no reboot, every stream/transport/cleanup error and queue/stale drop zero; one shutdown callback-generation discard |
| Live TLS/schema/routing checks | 11 checks passed against actual Ultra96 through the two forwards, detailed below |

The 11 live checks: wrong CA rejected; wrong SAN rejected; plaintext rejected; zero-length frame rejected; partial prefix closed after 5.016 s; wrong dummy values rejected; wrong session rejected; latest subscriber replaced old subscriber; duplicate input received a duplicate ACK with no second result during a 0.6 s observation; a result accepted while disconnected was not replayed after resubscription; extra subscriber input was rejected. The no-replay trace was `1:381947998:1`, followed by fresh `1:381947998:2`. A first invocation of the one-off harness mistakenly used local port 8888 instead of forward 18888 and failed with connection refusal; correcting the harness endpoint produced the 11 passes. This was a harness setup error, not a service fault.

The sustained run passed the explicit 5,400 minimum and activity criteria: first ACK at 3.922 s, last at 600.219 s, maximum ACK gap 0.375 s; first result at 3.875 s, last at 600.235 s, maximum result gap 0.500 s. A result can precede its independent input ACK in the Laptop logs because the two network streams are separate. Exact ID sets, not cross-stream arrival order, establish correlation.

A 30.172 s concurrent serial observation retained only whitelisted status lines. All 30 showed protected=1/authenticated=1/MTU 517; sensor submissions advanced 1,137 -> 1,427, with zero MTU suppressions and submission errors. The cumulative security-suppressed count stayed 44, inherited from earlier authentication setup and bond-loss tests; those were suppressed intervals, not unprotected transmissions. No raw serial/passkey log was saved.

The Ultra96's own acceptance log independently contained exactly 5,965 unique, ordered traces for boot 4178664849 and sequence 200 through 6164. Its saved `evidence/clean-soak-server-summary.json` confirms the exact contiguous range, matching both Laptop ID sets.

### Deliberately induced faults

Each experiment below used protected real BLE through the actual Ultra96. These runs correctly retain `passed=false`; recovery is not presented as a clean soak. Control timestamps and verified owned process IDs are in `fault-control.jsonl`.

| Fault / duration | Observed interruption and recovery |
|---|---|
| Ingestion SSH stopped / 100.531 s | Verified owner PID 28968 stopped at 17:04:53.923 UTC; replacement PID 36048 listened at 17:05:27.389. Received 849; ACKs/results 610/610 with exact ID match. Transport errors 7 (one ambiguous item), queue drops 90, stale drops 232, source-observed gaps 90 and viewer gaps 329. One BLE connection, two TLS connections, one subscriber; no reboot/BLE error. Final trace `1:4178664849:7104` proves fresh data resumed. Maximum ACK/result gaps 35.000/34.922 s; cleanup error 1 and three shutdown callback-generation discards retained. |
| Viewer SSH stopped / 92.391 s total, 90 s input | Verified viewer PID 30840 stopped at 17:07:01.742 UTC; replacement PID 23468 listened at 17:07:29.909. Ingestion continued with **864 ACKs and zero bridge transport/stream errors**; viewer received 585, with 279 missing IDs/gaps and no unexpected or duplicate results. Subscriber reconnected (two connections, six transport errors, one cleanup error), maximum result gap 27.969 s. Last result `1:4178664849:7971` establishes resumed live delivery; disconnected results were not replayed. One shutdown callback-generation discard. |
| Ultra96 service SIGTERM/restart / 60.359 s | Verified uid/cwd/argv before signalling PID 43881 at 17:09:56 UTC. It exited **0** and printed final metrics, including 7,501 accepted, no rejected input/duplicates/accept failures/queue drops, and 278 disconnected results across its lifetime. After a deliberate 5 s pause, replacement PID 43932 was listening on the same loopback ports at 17:10:02. The run received 564, ACKed/delivered 507 exact matching IDs, with 53 stale drops, four transport errors and one ambiguous item; viewer gaps 57, two TLS/subscriber connections, no BLE/cleanup errors or reboot. Final trace `1:4178664849:8536` proves fresh recovery; max ACK/result gaps 7.844/7.812 s. One shutdown callback-generation discard. |
| ESP RTS reset / 60.407 s | Injected RTS at 12 s using final bridge code `cf03318`. Boot 4178664849 -> 247619978; 383 received, 381 ACKs, 382 results, two ambiguous items and one transport error. All 381 ACKs matched results; result `1:247619978:314` arrived without a recorded ACK at shutdown and remains explicitly unmatched. No gaps, queue/stale drops, malformed input, duplicate, BLE or cleanup errors; two BLE/TLS connections, one subscriber, and one observed new boot on both sides. Max ACK/result gaps 17.453/17.407 s; one shutdown callback-generation discard. Safe serial confirmed approved auth mode 13 and MTU 517 before/after reset, including an additional firmware connection during Windows reconnection setup. |

The ingestion loss arithmetic reconciles: 849 received minus 610 ACKs equals 232 stale drops plus 7 transport failures; 90 queue drops + 232 stale drops + 7 transport failures equals the viewer's 329 missing sequence positions. Its cleanup error is consistent with an abrupt TLS reset: an isolated reproduction counted the reset, aborted the transport, cleared references and left no retained close tasks. The specific physical exception was not logged by the then-current code, so no exact exception type is asserted. Review separately reproduced swallowed cancellation in that cleanup path; its fix and final regression are recorded below.

### Final regression and independent evidence audit

After every induced fault and the `cf03318` cleanup fix, the final protected remote check passed **100 ACKs / 100 exact matching results in 13.422 s**, traces `1:247619978:316` through `1:247619978:415`. One BLE/TLS/subscriber connection, no reboot, every reported error/gap/queue/stale drop zero, maximum ACK/result gap 0.328 s; one late callback discarded at shutdown. This was the last physical data run before the later user-operated USB/RESET follow-up below; the ESP retained the protected firmware and stored authenticated bond.

Copied only the dedicated remote evidence directory back to `D:\LetThemCook-builds\remote-evidence-20260907\ultra96-evidence`. An independent parser then recomputed the full ACK/result sets for all eight stream runs and compared every ID with the actual Ultra96 acceptance logs. All IDs were present. The three server logs contained 203, 7,501 and 927 accepted records, **8,631 unique traces in total**. The clean soak's 5,965 exact matches were independently confirmed; the viewer outage's 279 missing results and reset run's one result without an observed ACK remained explicit. Saved `independent-evidence-audit.json` contains these checks and `manifest.json` records SHA-256 and byte counts for 25 evidence files. No certificate/private-key file is included in that evidence directory.

## Final process and repository state

- The deployed service is intentionally **left running** as uid 1000, PID **43932**, from `/var/tmp/cg4002-week7-yanjie-20260907/source-db6769a`, using absolute certificate/key paths under its private `tls/` directory. It was started with nohup, not installed as a system service. Current log: `evidence/server-after-restart.log`; current PID record: `evidence/server.pid`. Verify PID/cwd/arguments before any later stop because PIDs can be reused.
- After closing the control SSH session, a fresh verified Gateway TLS connection negotiated **TLS 1.3** and returned the exact SUBSCRIBED response. This proves the service survived control-session logout. The Laptop's test tunnels were then closed; there are no test listeners on 8888, 9999, 18888 or 19999 and no retained owned rehearsal/tunnel processes. Serial monitors closed COM3. No unrelated process was stopped.
- Remote ownership/modes were checked again: root and TLS directory 1000:1000 / 700; server key 1000:1000 / 600. Only the required server certificate/key were provisioned. The existing public CA fingerprint and expiry procedure remain in the earlier report/runbook; no CA key, SSH password or BLE passkey was put in Git/evidence.
- The requested worktree and branch are retained with local commits. Main at `D:\LetThemCook` remains clean at `f6bc999`. Documentation links and `git diff --check` pass. No push, merge, global SSH change, home-permission repair, sudo operation or service-manager installation occurred.

## Acceptance status and remaining work

### User-operated USB reconnection and RESET follow-up

After the user reported reconnecting USB and pressing RESET, COM3 reappeared as the CH340 adapter. A safe serial precheck observed boot **738264655**, uptime 85,016 through 89,016 ms, versus the preceding verified boot **247619978**. No reset pulse or firmware upload was injected by the collector. Subsequent monitoring and BLE packets retained boot 738264655, with increasing uptime; opening the monitor did not introduce a new boot in the observed sequence. The user's actions occurred before capture, so this first check establishes protected recovery afterward, not separate measured USB/button interruption intervals.

At 2026-09-06 17:36:11 UTC, the fresh protected remote run passed **100 ACKs / 100 exact matching results in 14.110 s**, traces `1:738264655:0` through `:99`. One BLE/TLS/subscriber connection, no errors, malformed packets, gaps, duplicates, queue/stale drops or ambiguous sends; maximum ACK/result gap 0.297 s. One late callback was discarded at shutdown. Safe serial recorded `success=1 auth_mode=13 approved=1 current_peer=1`, negotiated MTU 517, and authenticated submissions advancing 3 -> 93. Five pre-authentication intervals were correctly suppressed; this count stayed unchanged after authentication, with zero MTU suppression/submission errors. The existing bond worked without a new pairing prompt or bond changes.

Fresh remote inspection confirmed the same owned service PID 43932/source-db6769a and both loopback listeners. Independent ingestion/viewer SSH owners 35704/40260 explicitly selected Ultra96 port 22; their proxy processes expanded the destination to `makerslab-fpga-35.ddns.comp.nus.edu.sg:22`. Read-only aggregation of the actual Ultra96 log independently returned exactly 100 unique sequential records 0..99 for the new boot. A separate local parser checked exact equality of those expected IDs and both captured streams.

Follow-up evidence is outside Git at `D:\LetThemCook-builds\physical-followup-20260907`: `post-action100.jsonl`, `post-action100-safe-serial.json`, `post-action100-remote-audit.json`, and the current one-off `post_action_check.py` collector. The collector retains only numeric allowlisted serial status lines, uses deasserted DTR/RTS, sends no serial command, and never records passkeys. Its BLE/TLS/serial handles closed after this first check; the SSH forwards were reused. The collector was subsequently extended to reopen a disconnected serial port for the live test, so its retained source is not the exact first-run snapshot.

A further **180.469 s** monitored run passed **1,768 ACKs / 1,768 exact matching results**, boot 738264655, sequences 101..1868. It exceeded the 1,620-message minimum, with maximum ACK/result silence 0.422/0.375 s (including trailing shutdown silence), one BLE/TLS/subscriber connection, zero recorded errors/gaps/queue/stale drops, and one discarded shutdown callback. Safe serial retained 363 records, one open, no serial errors, approved auth mode 13 and MTU 517. Four more pre-authentication intervals were suppressed on reconnect (cumulative 5 -> 9); authenticated delivery then kept that count stable, with zero MTU suppression/submission errors.

The operator was prompted to unplug/reconnect USB and then separately press RESET while this capture was active. **No additional boot, serial loss or BLE interruption was observed during the window**, and no confirmation of repeated physical actions arrived during capture. This is retained as a clean stability run (`live-physical180.jsonl` and safe-serial companion), not a completed during-stream USB/button fault experiment. Sequence 100 lies between the two captures, outside either measured stream. Independent local set comparison and the actual remote log both matched precisely the combined expected 1,868 IDs: 0..99 plus 101..1868. The separate physical interruption measurements and real Phone/Unity acceptance remain outstanding.

The follow-up manifest hashes seven evidence/source files. Both temporary SSH forwards and their proxy processes were closed after collection; no 18888/19999 listeners or owned SSH processes remained, and COM3 was present with its monitor closed. The Ultra96 service was left running without restart or configuration changes. This continuation changes evidence and manual procedures only; no production code or firmware changed.

### Live USB-only power-loss test, evening 2026-09-07

The user explicitly confirmed that the ESP32 was powered only by USB, selected
an iPhone, and then confirmed **"USB done"** after the instruction to unplug
for five seconds, reconnect the same port and leave RESET alone. Unlike the
earlier post-action checks, this action occurred inside the active capture.
The requested five-second hold is an instruction, not an independently timed
physical unplug interval; the observed interruption timings below come from
the collector. The collector never injected a reset or changed firmware/bonds.

The 300.422-second `usb-and-reset.jsonl` capture contains **2,715 accepted ACKs
and 2,715 exact matching results**, with no missing/unexpected/duplicate saved
IDs. Despite its original filename, it measures only the USB experiment;
the physical RESET button is a separate requested action. Boot **4133030820**
changed to **1986177356**, COM3 disappeared and reopened, and protected delivery
resumed. The new boot's first captured result was sequence 1; sequence 0 is not
claimed as observed. The bridge recorded two BLE/TLS connections, one BLE
error, one transport error and one ambiguous dropped item. Queue/stale drops,
malformed input, sequence gaps and cleanup errors were zero; one late callback
was discarded at shutdown. The subscriber stayed on its original connection
and observed the new boot. Maximum ACK/result silence was **25.656/25.594 s**.
The intentional outage correctly retains **`passed=false`**, even though the
2,700-message count threshold was exceeded and protected recovery succeeded.

An independent parser verified 1,133 old-boot matches (0..1132) and 1,582
new-boot matches (1..1582). The first serial error was at 13:22:23.411 UTC;
42 serial exceptions preceded reopening, a **21.431-second host-observed
serial outage**. This does not measure the exact physical time without power.
The independent audit is `independent-usb-audit.json`. A separate read-only
aggregation of the actual Ultra96 acceptance log confirmed every expected ID
in both USB ranges and the later clean range 1584..3343, with no duplicate
acceptances within those ranges; the board retains `evidence/live-usb-audit.json`.

Safe serial reopened at 13:22:44.843 UTC and recorded approved authentication
at 13:22:46.485 UTC (`success=1 auth_mode=13 approved=1 current_peer=1`). The
first new-boot result arrived at 13:22:49.220 UTC. Subsequent status retained
protected/authenticated state and MTU 517, with five pre-authentication
intervals suppressed and zero MTU suppression/submission errors. No password,
passkey, raw serial or private key was retained in this evidence.

A separate 180.390-second capture, `reset-button.jsonl`, then passed **1,760
ACKs / 1,760 exact matching results**, boot 1986177356 sequences 1584..3343.
Maximum ACK/result silence was 0.344 s; one BLE/TLS/subscriber connection,
zero reboot, stream/transport/cleanup errors or queue/stale drops, and one
discarded shutdown callback. **No RESET transition occurred during that
window**, so the filename does not establish a button test. It is a clean
post-USB stability check. Offline audits independently reproduced both sets
and preserved the USB fault run's failure flag.

Evidence is outside Git at `D:\LetThemCook-builds\physical-live-20260907`, with
separate safe serial companions and `operator-events.jsonl`. Current collector
`live_physical_check.py` reopens COM3 with DTR/RTS deasserted and saves only
numeric allowlisted status lines. Its context describes the original combined
test plan; observed events and individually confirmed actions determine which
physical test actually happened. Production Laptop revision remains `fd9bbf8`
for these captures; no production source or firmware changed in this follow-up.

### Separately observed physical RESET-button recovery

The user's **"RESET done"** confirmation arrived during the extended capture
and was recorded at 13:37:40.174 UTC. The collector observed boot **1986177356
-> 1594988637**, with USB serial remaining open. The last old-boot `alive` was
at 13:37:14.798 UTC (uptime 870,016 ms); the first new-boot `alive` was at
13:37:17.576 UTC (uptime 1,016 ms). These are observation bounds rather than
an exact button-press timestamp. The same continuous serial handle and the
user's confirmation distinguish this action from the earlier USB removal.

Approved stored-bond authentication resumed at 13:37:26.617 UTC
(`success=1 auth_mode=13 approved=1 current_peer=1`), followed by MTU 517.
Fresh new-boot sequence 1 arrived at 13:37:29.518 UTC. Last old-boot ACK/result
sequence 7870 had arrived at elapsed 456.187 s; first new result/ACK arrived
at 470.125/470.187 s, giving **13.938/14.000-second delivery gaps**.
No reset pulse, serial command, firmware upload or bond change was injected
by the collector. Both true USB-only power loss and the physical RESET button
now have separately attributed observations and authenticated recovery.

The completed **600.422-second** RESET capture contains **5,832 accepted ACKs
and 5,832 exact matching results**: 4,526 on the old boot (3345..7870), followed
by 1,306 on the new boot (1..1306). It correctly retains **`passed=false`**
because the deliberate interruption exceeded the clean five-second silence
limit and introduced a new boot/connection. The bridge received 5,833 and
recorded one ambiguous dropped item and one transport error; sequence 0 of
the new boot is absent from both observed streams, without an asserted exact
disposition. There were two BLE/TLS connections, one subscriber connection,
zero BLE/cleanup errors, no malformed/duplicate/out-of-order/gap/queue/stale
events, and one late callback discard. All 1,204 safe serial records came
through one uninterrupted open, with no serial errors. Authenticated status
retained MTU 517; security-suppression stayed 14 on the old boot and 5 on the
new boot, with zero MTU suppression or notification submission errors.

The fresh **final-post-reset100** regression then passed **100 ACKs / 100 exact
matching results in 13.797 seconds**, boot 1594988637 sequences 1308..1407.
It had one BLE/TLS/subscriber connection, no reboot, every recorded error/drop/
anomaly zero (including shutdown callbacks), and maximum ACK/result silence
0.250 seconds. Safe serial retained 32 records and approved mode-13
authentication/MTU 517; the five reconnect pre-authentication intervals were
suppressed (cumulative 5 -> 10), then the count stayed stable. Sequence 1307
is outside both measured capture ranges. The collector's retained generic
context is clarified by a separate `collector_purpose` operator event for
this clean run; no fault was requested or observed during it.

`tools.week7_demo audit` independently reproduced 5,832 exact IDs with exit 1
for the fault and 100 exact IDs with exit 0 for the clean check. A separate
parser saved `independent-reset-audit.json`; actual Ultra96 acceptance-log
aggregation independently confirmed every expected ID/count in both RESET
ranges and the final 100 range, retaining `evidence/live-reset-audit.json`
on the board. No capture is promoted to real Phone evidence.

`physical-session-manifest.json` hashes 13 completed source/evidence files,
including both independent audits, the four application/serial capture pairs,
the collector, operator events and locally recorded remote-aggregation results.
Operator events are explicitly a point-in-time snapshot. Teacher talk track,
HTML/PDF and operator README now show observed USB/RESET recovery rather than
listing those actions as pending. The refreshed PDF remains three A4 landscape
pages (115,743 bytes); all pages were rendered with Poppler and visually checked.
The brief retains explicit pending iPhone/Unity acceptance. The runbook and
current acceptance table agree; documentation review found no actionable issues.

### iPhone preparation and current operator handoff

Decision 29 chooses foreground iSH/OpenSSH/Python using interactive passwords
and OpenSSH `-f`, with a scoped control socket for tunnel ownership. This uses
the user's actual available Phone and working authentication method while
preserving strict trust and the Phone's independent Ultra96 connection. The
[iPhone quickstart](week7-iphone-quickstart.md) supplies installation, public
file import, exact configuration, TLS subscription, 100-message capture,
600-second soak and cleanup procedures. The public setup ZIP is prepared at
`D:\LetThemCook-builds\iphone-setup-20260907\week7-iphone-setup.zip`; it carries
only receiver source, public CA, scoped verified host entries, SSH configuration
and instructions. The user must transfer it and operate the Phone.

ZIP SHA-256 is `8796B9B94B760B33DD7797163762DBBDD5A818A3C84A144DB735EC5A0ADEA153`.
Archive CRC, five-file allowlist, individual hashes, current receiver/guide
equality, UTF-8 LF encoding, public CA identity and six host-key rows scoped
to the two hosts were verified. Independent review checked the shell setup
failure guards; `bash -n` checked shell syntax, and actual local `ssh -G`
confirmed both hosts, port 22, strict trust, interactive mode, forwarding-failure
handling and 20/60-second timeouts. These are local preparation checks, not
iPhone execution. No production code changed, so the previous 203-test/2-skip
software baseline was not rerun merely for documentation changes.

The evening connection initially found the Laptop's Cisco AnyConnect adapter
disabled and the jump route offering public-key authentication only. After
VPN became active, interactive password SSH reached the assigned Ultra96
again. The iPhone needs its own authorized VPN profile; the Laptop connection
does not supply a Phone route. No institution VPN endpoint is invented by the
guide. The user subsequently reported both Laptop and iPhone VPNs connected;
the Laptop continued receiving real Ultra96 results, while the Phone's actual
route still needs its own SSH test. Phone package/runtime, SSH fork/control socket, actual TLS/result display,
screen lock, app switching and recovery remain unverified on-device. The
existing Unity component still requires teammate compilation/integration.

At the current handoff, the extended RESET and final clean captures have
finished and their BLE, TLS subscriber and COM3 handles are closed. The owned
desktop viewer SSH PID **29472** and proxy **4176** were stopped after the final
check; their processes and the Laptop's 19999 listener are absent. Ingestion
SSH PID **40940** retains only Laptop loopback **18888**, reaching Ultra96 SSH
port 22. These are live-session snapshots, not reusable stop commands. A fresh
remote check confirmed service **43932**, uid 1000, source-db6769a and only
loopback 8888/9999 application listeners. The service was not restarted.
The Phone can now establish its own independent 19999 forward/subscription
without a competing desktop subscriber. Start the staged Laptop sender when
the Phone receiver is ready; never run the desktop rehearsal subscriber
alongside it. Both devices' VPN connection is user-reported; actual iPhone
SSH/TLS/result display remains the next human-operated test.

The user subsequently confirmed **iSH ready, Python 3.9.16**, satisfying the
receiver's >=3.8 version requirement. OpenSSH/Python SSL version outputs were
requested separately; successful install alone does not prove the Phone route.
Decision 30 adds a [direct SSH import](week7-iphone-ssh-import.md) alternative
to the Files transfer. The original public-only ZIP was copied through the
existing verified SSH control session to
`/var/tmp/cg4002-week7-yanjie-20260907/phone-public-8796b9b94b76/week7-iphone-setup.zip`.
The board verified its exact 10,755 bytes, five expected archive entries,
ZIP CRC and unchanged SHA-256
`8796b9b94b760b33dd7797163762dbbdd5a818a3c84a144db735ec5a0adea153`.
The directory is uid 1000/mode 700 and file uid 1000/mode 600; no service restart,
new listener, private-key transfer or credential file was required. Remote
`scp` is present. The original bundle/README remain immutable; the new guide
provides a separate bootstrap using the two verified Ed25519 host keys,
strict scoped SSH configuration, interactive passwords and pre-extraction
hash verification. Actual Phone SCP, SSH/TLS and result receipt remain pending.

Local import-guide checks passed: shell and embedded Python syntax, both real
`ssh -G` expansions, exact public-key comparison and unchanged ZIP hash.
Independent review checked failure guards and the separated authentication
block. All 37 local links across the changed entry documents resolved, and
`git diff --check` passed. This follow-up changes public provisioning and
documentation only; production firmware/application code is unchanged.

| Area | Completed evidence | What still requires unavailable hardware or human action |
|---|---|---|
| A–E firmware, discovery, counter, MTU, packet | Both builds/upload, >5 min serial, dedicated 1,001-counter and 600 s counter runs, exact protected MTU boundary, fixed 32-byte packet and real stream; separately observed live USB-only power loss and physical RESET with new boots/protected recovery | No remaining listed physical interruption check on this ESP |
| F–J TLS, SSH, bridge, inference, independent viewer | Actual board deployment/binding, 100 synthetic and protected messages, 11 negative/routing checks, exact server/client trace correlation, ingestion/viewer/server interruption and recovery | No software or remote-access blocker remains for this desktop-viewer topology |
| K protected path | Actual ESP -> Laptop -> verified SSH/TLS -> Ultra96 -> separate SSH/TLS desktop subscriber, clean 600 s and 5,965 exact results; tunnel/server/RTS/USB/physical RESET faults and clean regressions | Desktop path complete; actual Phone remains Gate M |
| L BLE protection | Authenticated SC/MITM/bond, earlier bond-loss negatives/restoration, protected C/D/E/K, separately captured USB-only power loss and physical RESET with automatic approved mode-13 stored-bond recovery | No remaining listed BLE-protection check on this ESP/Laptop pair |
| M real Phone / teammate integration | Runnable standalone Python receiver, compiled portable C# core; supplied Unity component, not compiled here; Android procedures plus chosen iPhone password quickstart/public setup bundle | Actual iPhone runtime/install/network/VPN/SSH/display, 100/600 s correlation, lifecycle faults and teammate Unity build/integration |

The next operator can keep VPN connected, open the two generated independent SSH forwards, and run the current remote runner against the already deployed service. For Gate M, the Phone must own its own forward to Ultra96; stop the desktop subscriber so it does not replace the Phone's subscription. Follow the [current runbook](week7-runbook.md) and [Phone runbook](week7-phone-runbook.md), verify the public CA and host keys, and collect the remaining physical evidence. No protocol, TLS, security, architecture or implementation decision is awaiting approval. Real sensors/AI/FPGA, two-glove synchronization and AR UI retain the explicitly selected scope exclusions.
