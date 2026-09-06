# Week 7 Ultra96 continuation — 2026-09-07

This report continues local completion at `03790c1` and the pre-VPN retry at `ec7a08e`, in `D:\LetThemCook-worktrees\week7-stage-d-onward` on `feature/week7-stage-d-onward`. The user's original autonomous authorization remains in force. Earlier failures, firmware evidence and local soaks are preserved in the [previous report](week7-continuation-report-2026-09-06.md). The [selected design](week7-selected-design-2026-09-06.md) now records 28 decisions; no protocol or security approval is pending.

## VPN resolved the access blocker

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

After every induced fault and the `cf03318` cleanup fix, the final protected remote check passed **100 ACKs / 100 exact matching results in 13.422 s**, traces `1:247619978:316` through `1:247619978:415`. One BLE/TLS/subscriber connection, no reboot, every reported error/gap/queue/stale drop zero, maximum ACK/result gap 0.328 s; one late callback discarded at shutdown. This is the last physical data run, and the ESP retains the protected firmware and stored authenticated bond.

Copied only the dedicated remote evidence directory back to `D:\LetThemCook-builds\remote-evidence-20260907\ultra96-evidence`. An independent parser then recomputed the full ACK/result sets for all eight stream runs and compared every ID with the actual Ultra96 acceptance logs. All IDs were present. The three server logs contained 203, 7,501 and 927 accepted records, **8,631 unique traces in total**. The clean soak's 5,965 exact matches were independently confirmed; the viewer outage's 279 missing results and reset run's one result without an observed ACK remained explicit. Saved `independent-evidence-audit.json` contains these checks and `manifest.json` records SHA-256 and byte counts for 25 evidence files. No certificate/private-key file is included in that evidence directory.

## Final process and repository state

- The deployed service is intentionally **left running** as uid 1000, PID **43932**, from `/var/tmp/cg4002-week7-yanjie-20260907/source-db6769a`, using absolute certificate/key paths under its private `tls/` directory. It was started with nohup, not installed as a system service. Current log: `evidence/server-after-restart.log`; current PID record: `evidence/server.pid`. Verify PID/cwd/arguments before any later stop because PIDs can be reused.
- After closing the control SSH session, a fresh verified Gateway TLS connection negotiated **TLS 1.3** and returned the exact SUBSCRIBED response. This proves the service survived control-session logout. The Laptop's test tunnels were then closed; there are no test listeners on 8888, 9999, 18888 or 19999 and no retained owned rehearsal/tunnel processes. Serial monitors closed COM3. No unrelated process was stopped.
- Remote ownership/modes were checked again: root and TLS directory 1000:1000 / 700; server key 1000:1000 / 600. Only the required server certificate/key were provisioned. The existing public CA fingerprint and expiry procedure remain in the earlier report/runbook; no CA key, SSH password or BLE passkey was put in Git/evidence.
- The requested worktree and branch are retained with local commits. Main at `D:\LetThemCook` remains clean at `f6bc999`. Documentation links and `git diff --check` pass. No push, merge, global SSH change, home-permission repair, sudo operation or service-manager installation occurred.

## Acceptance status and remaining work

| Area | Completed evidence | What still requires unavailable hardware or human action |
|---|---|---|
| A–E firmware, discovery, counter, MTU, packet | Both builds/upload, >5 min serial, dedicated 1,001-counter and 600 s counter runs, exact protected MTU boundary, fixed 32-byte packet and real stream | Physical RESET-button press and true USB removal/reconnection, with actual new-boot recovery evidence |
| F–J TLS, SSH, bridge, inference, independent viewer | Actual board deployment/binding, 100 synthetic and protected messages, 11 negative/routing checks, exact server/client trace correlation, ingestion/viewer/server interruption and recovery | No software or remote-access blocker remains for this desktop-viewer topology |
| K protected path | Actual ESP -> Laptop -> verified SSH/TLS -> Ultra96 -> separate SSH/TLS desktop subscriber, 600 s and 5,965 exact results; separate tunnel/server/RTS faults and final clean regression | True USB power-loss experiment remains distinct; no real Phone claim |
| L BLE protection | Authenticated SC/MITM/bond, both earlier bond-loss negatives and restoration, protected C/D/E/K, authenticated reset reconnect | True physical power-cycle regression |
| M real Phone / teammate integration | Runnable standalone Python receiver, compiled portable C# core; supplied Unity component, not compiled here; Android foreground password/key procedures and explicit iSH experiment | Actual Phone runtime/install/network/VPN/SSH/display, 100/600 s correlation, lifecycle faults and teammate Unity build/integration |

The next operator can keep VPN connected, open the two generated independent SSH forwards, and run the current remote runner against the already deployed service. For Gate M, the Phone must own its own forward to Ultra96; stop the desktop subscriber so it does not replace the Phone's subscription. Follow the [current runbook](week7-runbook.md) and [Phone runbook](week7-phone-runbook.md), verify the public CA and host keys, and collect the remaining physical evidence. No protocol, TLS, security, architecture or implementation decision is awaiting approval. Real sensors/AI/FPGA, two-glove synchronization and AR UI retain the explicitly selected scope exclusions.
