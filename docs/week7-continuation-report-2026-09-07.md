# Week 7 Ultra96 continuation — 2026-09-07

This report continues local completion at `03790c1` and the pre-VPN retry at `ec7a08e`, in `D:\LetThemCook-worktrees\week7-stage-d-onward` on `feature/week7-stage-d-onward`. The user's original autonomous authorization remains in force. Earlier failures, firmware evidence and local soaks are preserved in the [previous report](week7-continuation-report-2026-09-06.md). The [selected design](week7-selected-design-2026-09-06.md) now records 33 decisions; no protocol or security approval is pending.

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

At the first Phone handoff, the extended RESET and final clean captures had
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

Subsequent operator-pasted iSH output confirms **OpenSSH_8.6p1** and successful
Python SSL import reporting **OpenSSL 1.1.1l (24 Aug 2021)**. The version inquiry
first used lowercase `ssh -v` without a destination and printed usage; uppercase
`ssh -V` returned the version. This was a command-case issue, not an installation
failure. After the bootstrap printed `SETUP READY`, SCP prompted for both host
passwords, transferred the public ZIP at **100% / 11 KB**, and returned to the
iSH shell. This establishes the user-observed Phone SSH/SCP route through port
22. The existing `/home/xilinx` chdir/.bashrc permission warnings appeared but
did not stop the transfer; no home repair is needed for this procedure.
Phone-side ZIP checksum/extraction and installation remain the next step;
no Phone local forward, application TLS, SUBSCRIBED or result has yet been
observed. The original pending-SCP paragraph above records the pre-download
handoff and is superseded by this later observation.

The user then confirmed **`files ready`** after the supplied guarded ZIP
verification, scoped-file installation, receiver `--help` and CA-fingerprint
commands. This is operator confirmation, not an independently collected Phone
filesystem audit. Phone tunnel startup/control-socket output is now requested.

At the 14:48 UTC preflight, the former idle Laptop SSH session reported
`Connection reset` / `Unknown error` and its 18888 listener was absent. The
Cisco AnyConnect adapter was Up; the cause of that idle-session loss was not
determined. No physical capture was active, so this is not a new measured
interruption experiment. Interactive strict SSH authentication restored the
ingestion forward as **PID 47768**, parent 19508, with explicit port 22 on both
hops. Fresh inspection confirmed unchanged Ultra96 PID 43932/source-db6769a
and loopback 8888/9999. An independent Laptop TLS handshake through restored
18888 passed CA/name validation for `ultra96.week7.internal` with **TLS 1.3**.
The current Laptop listener is only 127.0.0.1:18888; no desktop subscriber or
19999 listener was restarted. No passwords were written to files or logs.

For the upcoming 100-message attempt, use local operator coordination: stage
the Laptop sender before starting the Phone receiver, then press Laptop Enter
immediately when the Phone prints `subscribed`. Do not wait for a chat reply
during the Phone's five-second initial idle deadline. Prepared outside Git:
`D:\LetThemCook-builds\iphone-live-20260907\phone100-laptop-command.txt`, a
PowerShell block with an Enter prompt, fresh evidence directory, real protected
BLE sender and preserved stdout/stderr/exit files. Syntax and sender CLI
arguments were checked; it has not yet run. Existing code cannot guarantee BLE
startup within that deadline, and `--target 100` is a polled threshold. Preserve
any timeout, reconnect, overshoot or missing-ID attempt and retry with fresh
complete logs; do not trim it into a clean pass. This practical procedure adds
no production protocol change or Phone file replacement.

The next iSH output supplied the exact original CA fingerprint,
**`SSH startup exit=0`** and **`Master running (pid=45)`**. The Phone's strict
Python SSL probe then connected to its own 127.0.0.1:19999, required TLS >=1.2,
validated the existing CA and `ultra96.week7.internal` hostname, and printed
**`PHONE_TLS_OK TLSv1.3`**. Thus Phone SSH background startup/control socket and
actual forwarded TLS are now user-observed successes. This probe sent no
SUBSCRIBE or sensor input; it does not establish result delivery. The Laptop
still owns only ingestion 18888 (PID 47768), while actual Ultra96 service 43932
continues on loopback 8888/9999. No desktop subscriber was introduced.

For the Phone capture, use an immediate `tee` of combined receiver stdout/stderr
so `subscribed` is displayed without `tail -f` polling delay. Preserve the exact
combined log and the receiver's separately recorded exit code. After transfer,
extract only validated GESTURE_RESULT records to a derived JSONL for the strict
existing ID auditor, retaining all original status/error lines and source hash;
the combined text log itself is not raw result-only JSONL. This does not change
the installed receiver or its timeout/deduplication semantics. The helper is
prepared outside Git at
`D:\LetThemCook-builds\iphone-live-20260907\phone100-ish-command.txt`; actual
capture execution remains pending. A private uid-1000/mode-700 directory
`/var/tmp/cg4002-week7-yanjie-20260907/phone-captures-20260907` is ready to receive
the complete Phone evidence after the run through the Phone's existing SSH
route. No evidence file has yet been received there.

Local import-guide checks passed: shell and embedded Python syntax, both real
`ssh -G` expansions, exact public-key comparison and unchanged ZIP hash.
Independent review checked failure guards and the separated authentication
block. All 37 local links across the changed entry documents resolved, and
`git diff --check` passed. This follow-up changes public provisioning and
documentation only; production firmware/application code is unchanged.

### First Phone-test sender capture — 2026-09-08 local time

The operator ran the prepared Laptop command at 00:12 local time and supplied
the complete PowerShell output. The saved attempt is
`D:\LetThemCook-builds\iphone-live-20260907\phone100-20260908-001125`, with
context recording revision `b174863` and start marker
`2026-09-07T16:12:02.7295184Z`. The marker records the instruction to press Enter
after Phone subscription; it does not independently confirm that subscription.

Two independent local checks confirmed exactly 201 matching JSON records in
the original sender file and pasted output: 100 decoded real BLE packets,
100 accepted ACKs and one passing summary. All IDs are unique and contiguous,
`1:1594988637:1408` through `1:1594988637:1507`. Every 32-byte packet matches
its decoded schema and expected dummy values; firmware uptime increments by
100 ms. Sender duration is **13.750 s**, first ACK **3.766 s**, last ACK
**13.516 s**, largest inter-ACK gap **0.157 s** and maximum including the
shutdown tail **0.234 s**. There was one BLE and one ingestion connection;
all reported error, drop, duplicate, gap and reboot counters are zero.
Sender exit is **0** and stderr is empty. The sender SHA-256 is
`9a0a5c714965e5e75d19802b2451bbb8af6e16581c0c10b95e709a344e9f145c`.

A read-only audit through the existing SSH control session independently found
the same 100 sequence numbers accepted exactly once on the actual Ultra96,
from `2026-09-07 16:12:06,823` to `16:12:16,624` UTC. The full board-log snapshot
had 1,203,345 bytes and SHA-256
`f363b3376cb5c577971d2308691b84c06fa2a2249a276b96375b3a9b85439e13`.
Local `sender-audit.json` preserves the sender/attachment hashes and checks;
`board-acceptance-observation.json` records the remotely observed audit,
explicitly distinguishing it from a downloaded board log. The first root
audit invocation used an incorrect helper import and stopped before writing;
the corrected `common.sensor` invocation passed. Production code is unchanged.

**This completes the ingestion half of this attempt only.** No Phone output
was included in the pasted attachment, and its board upload directory was
still empty at 16:13:13 UTC. Next, retain and transfer the existing complete
Phone capture, including receiver exit and all status/error lines, then compare
its validated result IDs with these exact 100 ACKs. Do not rerun or discard the
current attempt merely because the Phone evidence has not yet been supplied.
Actual 100-message Phone success, the 600-second Phone soak and lifecycle checks
remain unverified.

### Resumption after idle — 2026-09-08 10:28 UTC

The user clarified that the Phone test had **not been performed** before the
idle interval. The saved 100-message Laptop/board evidence above remains valid
for ingestion only. The earlier instruction to upload an existing Phone capture
is superseded: no Phone capture has been established for that attempt, and a
new coordinated sender/Phone run is required after restoring runtime readiness.

Fresh local inspection found the Cisco AnyConnect adapter **Disabled**, no
18888 or 19999 listener, and the old SSH control session terminated with
`client_loop: send disconnect: Connection reset` (exit 1). The exact time/cause
of the earlier session loss is unknown; this is not a measured recovery test.
Windows reported no serial port, so the ESP's USB-only power connection also
needs operator confirmation. No new firmware or bond change is indicated.
The existing public CA and prepared Laptop sender command remain available.

The next required human action is to reconnect the authorized VPN on both
Laptop and iPhone and power the ESP by USB. Then restore the Laptop ingestion
forward, inspect the actual board service and verify TLS. On iPhone, retain the
installed receiver, CA and pinned SSH configuration; inspect scoped control
sockets rather than trusting old shell variables or PID 45. Reuse a verified
live master or establish one fresh forward, then perform a strict TLS probe
before the new coordinated 100-message capture. Do not delete old evidence,
kill unrelated SSH processes or start a competing desktop subscriber. Ultra96
remains externally reachable only through its SSH port 22; app ports remain
board loopback. No production code or remote service was changed in this check.

After the user confirmed readiness, the 10:35–10:37 UTC preflight found
AnyConnect **Up**, the CH340 **COM3** device and Bluetooth present. A read-only
BLE scan found **LTC-W7 / 38:18:2B:19:82:AE**; it did not connect or generate
sensor traffic. Interactive authentication with both pinned Ed25519 host keys
restored the Laptop ingestion tunnel as **PID 36432**, bound only to
`127.0.0.1:18888`. Both SSH hops explicitly use port 22. The old tunnel was not
reused, and no desktop viewer or 19999 listener was created.

Fresh remote inspection at `2026-09-08T10:36:31Z` confirmed uid 1000 on `pynq`,
the unchanged **PID 43932 / source-db6769a** server, and only board-loopback
8888/9999 app listeners. The existing private Phone capture directory is still
available. A new Laptop SSL probe passed CA/hostname validation with **TLS 1.3**
and SAN `ultra96.week7.internal`; the service certificate expires
`2026-10-06 15:11:29 UTC`. No service restart or certificate replacement was
needed. Phone VPN readiness is operator-reported; its current SSH/TLS state
still requires the scoped master check/restart and fresh Phone probe, followed
by a new coordinated capture. The receiver and sender have not been started
during this resumption preflight.

The next operator-pasted iSH output contained `ash: missing ]` in the scoped
socket discovery and post-start guard lines; the displayed commands were
missing the intended `||` separators. That discovery attempt therefore did
not reliably establish whether a prior master existed. The subsequent fresh
SSH command reported **`SSH startup exit=0`** after authentication (one jump
password attempt was rejected before the successful retry). The final shell
guard also failed, so do not interpret the wrapper status as a complete
readiness check or start another tunnel immediately. The next instruction is
a standalone scoped `-S "$week7_ssh_socket" -O check`, followed by the separate
strict TLS probe only if the master check succeeds. Use simple individual
commands for this paste path. At 10:40:08 UTC the Laptop 18888 owner remained
36432 and both actual board-loopback app listeners were still present. Current
Phone master/TLS and the packet capture remain unverified.

The operator then supplied a successful standalone control check,
**`Master running (pid=60)`**, and a fresh strict Python probe reporting
**`PHONE_TLS_OK TLSv1.3`**. This establishes the resumed Phone master and
CA/hostname-validated forwarded TLS despite the earlier wrapper paste errors.
The probe did not subscribe or receive gesture results. At 10:43:57 UTC the
Laptop ingestion listener still belonged to PID 36432 and the actual board
still exposed its app listeners only on loopback 8888/9999. The next action is
the previously reviewed coordinated 100-message procedure with fresh evidence:
stage the Laptop Enter prompt, start the Phone's immediate-tee receiver capture,
then press Laptop Enter immediately when `subscribed` appears on Phone. Retain
all output and both exit codes; no clean Phone-delivery claim is made until
the complete new sender and Phone captures have been independently correlated.

### Resumed sender capture — 2026-09-08 18:54 local time

The next pasted attachment included both the earlier 00:12 Laptop run and a
new complete run. The new saved directory is
`D:\LetThemCook-builds\iphone-live-20260907\phone100-20260908-185338`, with
revision `533c7b5` and operator start marker
`2026-09-08T10:54:28.7324398Z`. Independent checks isolated the two runs and
confirmed that the attachment's final 201 JSON records exactly match the new
file: **100 packets, 100 accepted ACKs, one passing summary**. The first 201
records match the earlier preserved run; they are not new evidence.

New IDs are unique and contiguous, **`1:2375739948:0` through
`1:2375739948:99`**. All 32-byte records independently unpack to the recorded
schema and deterministic dummy values, with 100 ms firmware uptime steps.
The boot differs from the previous day; this does not establish a reboot
during the capture. Sender duration is **14.078 s**, first/last ACK
**4.047/13.844 s**, largest inter-ACK gap **0.172 s**, and maximum including
shutdown tail **0.234 s**. One BLE and one ingestion connection were used;
exit is **0**, stderr empty. All stream/error/drop/reboot counters are zero
except **`callback_generation_dropped=1`**. That counter includes raw queued
items cleared at generation invalidation and callbacks rejected for inactive
generations. It is consistent with shutdown, but the exact mechanism, payload
and time are not captured. Do not call it sequence 100, a proven late callback,
or a missing packet among these 100 accepted IDs. The current sender's pass
criteria intentionally do not classify this counter as a stream error.

The actual Ultra96 log independently contains these exact 100 IDs accepted
once, from **10:54:33,122 to 10:54:42,972 UTC**. Its observed full-log snapshot
has 1,212,235 bytes and SHA-256
`dd7a67efc96436b69ddf19830aa558362c9634ed0a75f9c645e1279e5541e67c`.
The new sender file SHA-256 is
`6084addeb2414015c7d34d7b3b7e6b732d4a30426e9a6ad2d8273d53d77b0793`.
Local `sender-audit.json` and `board-acceptance-observation.json` retain hashes,
checks and the distinction between observed board output and downloaded logs.
The attachment contains no Phone result/status evidence, and the private
Phone upload directory remained empty at this check. Obtain the current iSH
output and complete Phone capture before deciding whether this attempt needs
a retry. Do not count either Laptop-only capture as verified Phone delivery.

The operator subsequently supplied actual iSH result output and the saved
tail from **`/root/week7-evidence/phone100.DDMJjm`**. It reports
**`received=100`, `reconnects=1`, capture exit 0 and receiver exit 0**.
The four distinct visible tail records are boot 2375739948 sequences
96/REST, 97/FIST, 98/OPEN and 99/POINT, each with confidence 1.0. Both Phone and
server contract validators accepted those four reconstructed observations,
and their IDs match the new sender ACKs. The repeated tail paste is not a
second reception or additional packet count. Local `phone-operator-summary.json`
records this as partial, operator-pasted evidence rather than a downloaded
original Phone log.

This establishes user-observed actual Phone result display and a reported
100-result completion. **It is not an uninterrupted pass:** the receiver counts
connection/read/protocol failures in `reconnects`, while its exit 0 checks the
requested received count only. The tail does not establish the reconnect
reason, whether it occurred before the first result, or equality of all 100
Phone/sender ID sets. Collect the entire existing combined log and exit file
through the Phone's SSH route into the prepared private board directory before
diagnosing or retrying. Preserve every status line and original byte/hash when
deriving result-only JSONL for correlation. At 11:11:33 UTC the destination
directory was still available and empty. No software or protocol change is
justified by this partial observation alone.

### Full actual Phone capture collected and correlated

The Phone uploaded both original files successfully through its own SSH route;
the known inaccessible-home warnings did not prevent transfer. Root retrieved
their exact bytes through the existing verified Laptop SSH session, with
matching board/local SHA-256 checks. The preserved local copy is under the new
sender directory's `phone100.DDMJjm` subdirectory. The original combined log
is **16,727 bytes**, SHA-256
`72bcbcc14bd542816258dd04625e2438a3a99eac0736de536abdf73e33c4c1a8`.
The exit file is exactly `0\n` (2 bytes), SHA-256
`9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.

The complete 104-line log is ordered as follows: line 1 is SUBSCRIBED status,
line 2 `reconnect reason=TimeoutError`, line 3 a second SUBSCRIBED status,
lines 4–103 all 100 results, and line 104 the 100-received/one-reconnect summary.
Two independent audits verified all schemas, deterministic gesture/confidence
fields and **exact ordered equality of Phone results, Laptop ACKs and the
independently observed board acceptance IDs 1:2375739948:0..99**. Each gesture
appears 25 times; there are no missing, unexpected or duplicate output IDs.
This is the first fully correlated actual iPhone delivery evidence.

`phone100.results.derived.jsonl` preserves exactly the original result lines
4–103; its SHA-256 is
`0c3768643884eac9cea4f9a955d40b19beac14d9e8a095c168a388f1758a5618`.
The existing CLI auditor passed with 100/100 exact matches. That derived-file
audit checks result identity/schema only: its zero interruption-event count
does not account for the original Phone status lines. `phone-full-audit.json`
therefore explicitly reports **delivery correlation passed, uninterrupted
acceptance failed**, preserving all original statuses and their line numbers.

The timeout occurred after the first successful subscription while awaiting
the first result frame, before any result was printed. After resubscribing,
the receiver delivered the entire 100-result sequence without another logged
reconnect. The file contains no per-result timestamps, so it cannot establish
the exact upstream cause or independently prove sub-five-second delivery gaps.
Retain this as a successful actual-Phone delivery run with one startup retry;
do not relabel it a zero-reconnect run or a VPN-fault experiment.

Decision 31 selects a bounded Python receiver startup grace to remove the
five-second race with human coordination and measured roughly four-second BLE
startup: 30 seconds for the first result byte, then the existing five-second
remaining-frame deadline. Later results, including post-result reconnections,
keep the existing five-second deadline. TLS, SUBSCRIBED, framing, validation,
and the overall duration stay bounded as before. Publish separately versioned
public receiver/capture files, retaining the original setup ZIP and evidence;
the changed receiver still requires a fresh physical zero-reconnect run.

Implementation and review completed with a regression that failed before the
change (`TimeoutError`/one reconnect during cold startup) and passed afterward.
**22 Phone tests passed in 6.57 s**, covering finite startup grace, delayed first
data, partial-frame and shared prefix/body deadlines, later idle and reconnect
state, invalid first results, EOF, cancellation, SUBSCRIBED and overall duration.
The full suite passed **215 tests, 2 skipped in 84.87 s**; the skips remain the
Windows-only exclusions for Linux signal behavior. Independent code review found
no material issue. Python 3.8 grammar parsing passed; this is not an actual
Python 3.8 runtime execution. The portable C#/Unity files were unchanged.

Published only two public files to the verified uid-1000/mode-700 directory
`/var/tmp/cg4002-week7-yanjie-20260907/phone-startup-b16c746255c9`, each mode 600:

- `receiver.py`: 9,663 bytes, SHA-256
  `b16c746255c9d91655b4da35cea6d5d240a260f4c289ca7b52c2e4441420e881`.
- `capture100.sh`: 1,210 bytes, SHA-256
  `d704700e5e184a0c02e47378577679de0d7b71d31d7b0cae81ce260911d3df39`.

The board rechecked both hashes, source grammar and `/bin/sh -n` syntax. No
new listener, private-key transfer, service restart, firmware or bond change
was involved. The original iPhone files and public setup ZIP are retained.
Local copies and their manifest are in
`D:\LetThemCook-builds\iphone-startup-update-20260908`. The prepared Laptop
`phone100-laptop-startup30-command.txt` passed PowerShell parsing and has SHA-256
`a1b1fa011a03638cfe783c4469f48f9f6bedf5a9142454bcff86bf683517d670`.
It records and deliberately waits six seconds after the operator's Enter press
before starting the unchanged BLE sender, so the next physical run exercises
a startup wait longer than the old five-second limit. The sender's own elapsed
time excludes that explicitly recorded delay.

Follow the [short update and capture guide](week7-iphone-startup-update.md): SCP
the versioned directory, verify both hashes on Phone, stage the Laptop Enter
prompt, and source the verified capture helper when ready. Phone installation
of this update and its fresh zero-reconnect result are still pending; do not
promote the local test result to physical acceptance.

The teacher README, talk track, HTML brief and three-page PDF now reflect the
actual 100/100 iPhone result correlation and explicitly retain its startup
retry. The clean desktop soak and observed USB/RESET evidence remain separately
labelled. The updated PDF is 115,418 bytes; all three A4 landscape pages were
rendered and visually checked, including a second review of the evidence page.
Its pending list includes the new receiver's physical rerun, Phone soak/lifecycle
and teammate Unity integration. Local documentation links/anchors and
`git diff --check` passed. No zero-reconnect or full Gate M completion claim
was added to the teacher materials.

The operator subsequently completed the versioned iPhone update download:
SCP reported **capture100.sh 100% / 1,210 bytes** and **receiver.py 100% /
9,663 bytes**. An earlier paste began with a shell redirection character and
failed with `-F: not found`; the corrected single-line SCP performed the actual
transfer. The known board-home warnings did not prevent it. On-Phone hash
verification and execution of the updated receiver remain pending. At
`2026-09-08T12:17:20Z`, Laptop ingestion still belonged to PID 36432 and both
actual board-loopback app listeners remained present. The next supplied
sequence verifies both Phone hashes, stages the six-second-delay Laptop helper,
then sources the short Phone capture helper and starts the sender after
SUBSCRIBED. No new physical packet run has yet been observed.

### Startup-grace rerun — 2026-09-08 20:31 local time

The new Laptop capture is
`D:\LetThemCook-builds\iphone-live-20260907\phone100-20260908-203121`.
Its context records revision `98e958f`, an operator start marker at
`2026-09-08T12:31:46.3572949Z`, and the intentional six-second delay. The pasted
terminal names the delayed helper and prints its delay announcement. The
sender's own elapsed time excludes that delay; exact Phone subscription-to-first
result latency is not timestamped.

Two independent audits found **201 matching saved/pasted JSON records**:
100 raw/decoded packets, 100 accepted ACKs and one passing summary. IDs are
unique, ordered and contiguous, **1:2375739948:101..200**. All 32-byte fields,
dummy values and 100 ms uptime increments validate. Sender duration is
**13.938 s**, first/last ACK **3.906/13.703 s**, maximum inter-ACK gap
**0.188 s**, and maximum including shutdown tail **0.235 s**. There is one
BLE and one ingestion connection; **every error, drop, duplicate, gap, reboot
and callback-discard counter is zero**. Sender exit is 0 and stderr empty.
Sequence 100 lies between measured attempts and is not assigned a proven
disposition. Sender SHA-256 is
`c833b038db625ca7a5e2fe2be0cd9fe113aaaafa5c5df4d6fffa13ad51d5329c`.

The actual board independently accepted the same 100 IDs exactly once, from
**12:31:56,601 to 12:32:06,458 UTC**. The observed full-log snapshot is 1,221,235
bytes with SHA-256
`6761a4fb7d8fc4e70e923564637366c9ed1bd4d9c28001f7d997f66977a8e1b88`.
Local `sender-audit.json` and `board-acceptance-observation.json` retain checks
and source hashes, distinguishing remotely observed output from a downloaded
board log.

The operator's iSH tail reports **received=100, reconnects=0, capture exit 0,
receiver exit 0**, saved in **`/root/week7-evidence/phone100.DoakOF`**. The ten
visible complete result records, sequences 191–200, have the correct gesture
cycle/confidence and match sender ACKs; local `phone-operator-summary.json`
records that limited observation. The full new Phone capture has not yet
arrived on the board (only the earlier `phone100.DDMJjm` was present). Collect
it and compare all 100 IDs before promoting this reported zero-reconnect result
to fully audited acceptance. Retain the earlier startup-retry evidence.

The following longer test will use matching **6,100-message** sender/Phone
targets and **660-second** overall failure limits. At the source's 10 Hz cadence,
that gives roughly 609.9 seconds between first/last generated packets, providing
margin beyond 600 seconds and letting the Phone exit naturally before a
post-sender idle timeout. Verify actual source/ACK timing and an independently
timed foreground Phone observation; count alone does not establish Phone gap
timing. Sender target polling can overshoot, so preserve complete logs and fail
any extra ACK/result-set mismatch rather than trim the attempt. The updated
receiver remains bounded as selected in decision 31; no additional protocol
or implementation change is needed for these test parameters.

### Reducing manual Phone commands

The user asked whether connecting the iPhone by USB would allow the agent to
perform all remaining tests. A read-only Windows check found the iPhone only
as a Bluetooth device; no USB iPhone entry, Apple Mobile Device service, or
`idevice_id`/`ideviceinfo`/`iproxy`/`usbmuxd` command was found. A cable alone
does not provide a shell: [libusbmuxd](https://github.com/libimobiledevice/libusbmuxd)
forwards TCP to an existing device service and requires a USB-multiplexing
backend. No USB software, driver, device trust or general Phone-control
configuration was installed or changed.

The practical next route is a scoped, temporary iSH SSH management channel,
using the existing verified SSH/VPN route and board-loopback forwarding while
keeping Ultra96 external access on port 22. The [official iSH SSH guide](https://github.com/ish-app/ish/wiki/Running-an-SSH-server)
documents an in-app server and a high localhost port. First confirm the actual
Phone has `/usr/sbin/sshd`, then prepare separate key-only server/host-key/config
files and verify forwarding before claiming remote control works. This route
is feasible but not yet configured or tested here; do not imply that USB or
the current result tunnel already grants Phone command access. It would enable
remote receiver runs and log collection, but unlocking, iOS/VPN approvals,
screen locking, switching apps and foreground recovery still require the user.
The latest `phone100.DoakOF` full-log upload/correlation remains pending while
this management-access check is pursued. Preserve that attempt unchanged.

### Temporary iSH management preparation — 2026-09-08

The operator confirmed `/usr/sbin/sshd` exists on the actual iPhone: root-owned,
mode 755, 927,832 bytes, package timestamp 2021-10-05. Decision 32 and the
[maintenance design](week7-iphone-control.md) select scoped key-only SSH access
through the existing Phone master, with an explicit maintenance-only reverse
forward. This resolves the USB/control design choice; USB charging does not
provide the shell and is not the maintenance transport.

The existing Laptop ingestion shell/tunnel remained live (exec session 83726,
Windows PID 36432), and the existing board service remained PID 43932 with
only loopback application listeners 8888/9999. The board's effective SSH
configuration for user xilinx and the actual jump address 137.132.80.24 was
checked with `sshd -T -C` using an isolated temporary host key, avoiding access
to system private host keys. Results: **gatewayports no, allowtcpforwarding yes,
disableforwarding no, permitlisten any**. Both generated preflight key files
were removed from the exact owned directory afterward. No system SSH config
or unrelated board service was changed.

A dedicated client key was generated in the Laptop private directory
`C:\Users\Yanjie Wang\.codex\private\iphone-control-w7-fd3c60de` with inheritance
removed and access granted only to the current Windows user. The public bundle
is prepared under `D:\LetThemCook-builds\iphone-control-20260908\w7-fd3c60de`,
targeting board owner-only directory
`/var/tmp/cg4002-week7-yanjie-20260907/phone-control-w7-fd3c60de`.
Only the client's public key belongs in that bundle. A separate authenticated
Laptop maintenance forward is active: exec session **23739**, SSH PID **18080**,
**127.0.0.1:12222 -> board 127.0.0.1:22222**, through the same verified hosts and
external port 22. This listener alone does not prove Phone access: the Phone
daemon/reverse forward, pinned host-key authentication and command probe remain
unperformed until the operator runs the prepared launcher.

Independent design review identified two concrete safeguards included in the
design: check effective GatewayPorts before creating any reverse listener, and
use `-F /dev/null` for multiplex forwarding/cancellation so other configured
forwards cannot be included. OpenSSH 8.6 cancellation can return zero despite a
failure, so actual listener removal must be observed. A locked iSH root account
must be diagnosed without logging or changing its password hash. The existing
application master/result tunnel is not stopped by maintenance setup/cleanup.

The implemented `phone/ish_control.py` and its 14 focused tests passed together
with all 22 receiver tests: **36 passed in 6.30 s** in the final root verification.
Independent review also reran the helper tests successfully. Regressions
cover locked accounts, occupied local/remote ports, missing master, rejected
configuration, uncertain forward failure, publication rollback, scoped PID
cleanup and metadata/path validation. Review caught and fixed missing `-e`
daemon logging, duplicate-forward ownership, and iSH's truncated `/proc`
process title/zero start timestamp. Startup rollback now uses the unreaped
owned subprocess; later shutdown checks executable, unique log descriptor,
process group and session. Failure to verify those facts refuses termination.
No account password/hash was changed or logged.

Published exactly two public files in the board bundle directory, mode 600:

- `ish_control.py`: **17,624 bytes**, SHA-256
  `a5e275ecfe7eb8603706d3cdca47ef59a099ab76fb3749bc39844574a6310628`.
- `control-public.json`: **245 bytes**, SHA-256
  `d25c11cdad0ab0f17adc9ba5ac93fc597eb415e93089aeda5b042c65e340d10e`.

Board/local hashes match. Python 3.8 grammar parsing and actual board Python
CLI help passed. An isolated configuration generated by the helper passed
the board's `sshd -t` with exit 0; its disposable host-key pair was removed
afterward. This checks board OpenSSH syntax, not actual iSH server behavior.
The board maintenance port 22222 remained free: neither Phone has activated
the daemon or reverse forward, and no Phone root authentication is claimed.

During preparation, the user chose **another iPhone** for further tests. Its
iSH/runtime, own NUS VPN, SSH trust/config and master must be established on
that device before invoking the helper. The former Phone's master/socket,
installation and test results do not establish readiness of the replacement.
Keep `/root/week7-evidence/phone100.DoakOF` unchanged on the original Phone;
its full capture is still pending collection and correlation. Label all future
replacement-Phone evidence separately, including device/iOS/runtime details,
and do not run competing receivers during either device's packet tests.

The longer-test wrappers are prepared outside Git under
`D:\LetThemCook-builds\iphone-soak-20260908`: `capture6100.sh`,
`phone6100-laptop.ps1`, instructions and a manifest. Both request 6,100 results
with 660-second limits and preserve original logs plus separate process/capture
exits. The Laptop wrapper offers `-Subscribed` for agent operation only after
the current Phone subscription has been observed. There is no deliberate
startup delay. Synthetic failure checks cover receiver/tee and sender/capture
failures; they do not run BLE or constitute a Phone soak. The existing current
receiver hash and CLI flags were checked. Install and run these on the selected
Phone only after its SSH/TLS readiness and short packet run are verified.

### Replacement Phone bootstrap prepared — 2026-09-08

The user reported completion of the replacement iPhone's iSH/package/VPN
prerequisites. Actual versions and SSH access remain unverified. At 13:48 UTC,
the existing board app listeners remained present, no maintenance listener
22222 existed, and no Phone readiness file had arrived. Laptop listeners
18888/PID 36432 and 12222/PID 18080 were still present.

Prepared the [one-time setup block](week7-replacement-iphone-setup.md) and its
ready-to-copy local file
`D:\LetThemCook-builds\iphone-control-20260908\w7-fd3c60de\replacement-setup-command.txt`.
The block checks the actual runtime/account/terminal and port, installs only
safe new or identical scoped SSH files, starts a fresh Phone master with its
own result forward, then downloads two exact files through that master with
network fallback disabled. Both hashes must match before it invokes the control
helper. Failure closes only the fresh bootstrap master. Existing conflicting
files are preserved; account passwords and global SSH files are not changed.
The user must paste this block and enter credentials at OpenSSH's terminal
prompts before the agent can operate the replacement Phone.

Five isolated bootstrap control-flow cases passed, with root/permissions and
SSH subprocesses simulated: success, corrupted download, SSH failure, existing
configuration conflict and locked root. Python 3.8 grammar and independent
source review passed. This is preparation evidence, not Phone access evidence.
The ready-to-copy text is **4,244 bytes**, SHA-256
`5b14bbc70cefd7354ea3348be8ebf90bce8859ecaacddf24af1393eaa4f937d5`.

The bootstrap uses separately published **`ish_control-v2.py`**, **17,715 bytes**,
SHA-256 `de224697bd472ecc016c0e72363c7ae7b32e0ae0e5365818fdfcdcbca9ef65ed`,
alongside unchanged `control-public.json` in the same board directory. Both
board and local hashes match. V2 aligns the public helper with the final
committed malformed-state guard in `stop_control`; the earlier public file and
manifest are retained. Startup behavior is unchanged. The new
`replacement-setup-manifest.json` records the exact selected versions and the
pending actual Phone commissioning. No packet run or Phone login occurred in
this preparation turn.

### Actual replacement Phone root-lock blocker

The operator pasted the complete bootstrap and received
**`PHONE_ROOT_LOCKED: stop here and send this message; nothing changed.`**
This is the original explicit account guard, before any setup file or network
operation. It establishes a leading `!` in that Phone's root password field;
the actual field was neither requested nor collected. Python imports, including
`spwd`, and the preceding root/sshd checks passed, but exact runtime versions
remain unreported. At 14:03 UTC the board application listeners remained live
and maintenance port 22222 remained absent. This is not a failed SSH password
or VPN observation, since authentication had not started.

Decision 33 resolves the observed account prerequisite with the
[official iSH remedy](https://github.com/ish-app/ish/wiki/Running-an-SSH-server#troubleshooting-passwordless-login):
an unusable `*` password field permits the selected key authentication on iSH.
The [new recovery guide](week7-ish-root-lock.md) includes the exact combined
setup and a complete offline restoration block. Before mutation, the script
requires no detected known SSH daemon/session processes and preserves the
original field exclusively, mode 600, in root-owned mode-700
`~/week7-private/ish-root-before-control.txt`, flushing/fsyncing the backup.
Account-tool input travels only through stdin, and the resulting field is
checked. The scoped server still requires public-key authentication and keeps
password/keyboard-interactive mechanisms disabled. This is a documented,
observed-need exception to the original no-account-field-change design.

The updated ready-to-copy file is
`D:\LetThemCook-builds\iphone-control-20260908\w7-fd3c60de\replacement-key-setup-command.txt`,
**6,133 bytes**, SHA-256
`902495b5b3ab11b5660de9c2a14c69f1e78e7e7562e11ebd5d426f1b2e6ed5fb`.
It continues into the original verified SSH/bootstrap after the remedy. It
also fetches the new public **`restore-ish-root-lock.py`**, **1,780 bytes**,
SHA-256 `144e550e49f2e0bd818054c5b1b1e38c79ae1475a51268c465072c22497fb81a`,
published mode 600 in the same board directory with its hash rechecked.
The original setup and public versions remain unchanged. No original password
field or private backup is part of the public bundle or evidence manifests.

Seven isolated account workflow checks and five isolated combined-bootstrap
checks passed; these simulate account/permission/SSH operations and changed no
real account. They cover existing backups/daemons, unexpected account changes,
idempotent restoration, and progressing past the newly locked root state.
Python 3.8 grammar and independent source review passed. The local
`root-lock-remedy-manifest.json` retains artifact hashes and verification scope.

Actual Phone execution of this updated block, account-state verification,
key authentication and packet tests are still pending. If later connection
setup fails after enabling the account, its private backup remains and the
account is not automatically restored. After maintenance shutdown, use the
saved helper or complete offline restore block; refuse restoration if the
account has since changed unexpectedly. Restore and verify the original
password field, retaining the backup until verified. Password-age metadata
may change through the account utility; no full shadow-metadata restoration
claim is made. Close existing maintenance sessions as well as its listener:
restoring an account lock alone does not terminate authenticated sessions.

The next operator paste showed Python statements being interpreted directly
by `ash` (`print` syntax errors, `except`/`raise`/`WEEK7_SETUP` not found).
The Python heredoc was not active for that pasted tail. Reissue the complete
existing tested command inline, including its opening
`python3 - <<'WEEK7_SETUP'` and closing `WEEK7_SETUP`, using one full copy/paste
at the normal iSH prompt. This is a presentation/input correction, not a new
SSH/protocol failure or a code change. The tail alone does not establish
whether an earlier part changed the account, so no new account or connection
success is claimed; preserve any backup and rely on the script's state guards.

| Area | Completed evidence | What still requires unavailable hardware or human action |
|---|---|---|
| A–E firmware, discovery, counter, MTU, packet | Both builds/upload, >5 min serial, dedicated 1,001-counter and 600 s counter runs, exact protected MTU boundary, fixed 32-byte packet and real stream; separately observed live USB-only power loss and physical RESET with new boots/protected recovery | No remaining listed physical interruption check on this ESP |
| F–J TLS, SSH, bridge, inference, independent viewer | Actual board deployment/binding, 100 synthetic and protected messages, 11 negative/routing checks, exact server/client trace correlation, ingestion/viewer/server interruption and recovery | No software or remote-access blocker remains for this desktop-viewer topology |
| K protected path | Actual ESP -> Laptop -> verified SSH/TLS -> Ultra96 -> separate SSH/TLS desktop subscriber, clean 600 s and 5,965 exact results; tunnel/server/RTS/USB/physical RESET faults and clean regressions | Desktop path complete; actual Phone remains Gate M |
| L BLE protection | Authenticated SC/MITM/bond, earlier bond-loss negatives/restoration, protected C/D/E/K, separately captured USB-only power loss and physical RESET with automatic approved mode-13 stored-bond recovery | No remaining listed BLE-protection check on this ESP/Laptop pair |
| M real Phone / teammate integration | Runnable Python receiver and portable C# core; actual iSH Python 3.9.16/OpenSSH 8.6p1, SSH/SCP install, matching CA, resumed SSH master60/Phone TLS1.3, original Phone capture with 100/100 exact ordered correlation and one startup timeout before first result; Unity component supplied but uncompiled here | Updated receiver physical acceptance, clean uninterrupted run, 600 s coverage, Phone TLS negative/lifecycle checks, device/OS details and teammate Unity build/integration |

The next operator can keep VPN connected, open the two generated independent SSH forwards, and run the current remote runner against the already deployed service. For Gate M, the Phone must own its own forward to Ultra96; stop the desktop subscriber so it does not replace the Phone's subscription. Follow the [current runbook](week7-runbook.md) and [Phone runbook](week7-phone-runbook.md), verify the public CA and host keys, and collect the remaining physical evidence. No protocol, TLS, security, architecture or implementation decision is awaiting approval. Real sensors/AI/FPGA, two-glove synchronization and AR UI retain the explicitly selected scope exclusions.
