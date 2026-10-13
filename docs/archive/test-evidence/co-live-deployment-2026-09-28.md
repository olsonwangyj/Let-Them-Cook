# CO v2 deployment and physical verification — 28 September 2026

The running Ultra96 service and both physical FireBeetles were updated at the user's request. The initial captures below used an independent Python TLS subscriber, **not the native iPhone**. After building and connecting the updated app, the user completed the separate aggregate iPhone count check recorded in the final section. This is a record of implementation/deployment tests, not a demonstration checklist.

Final state: both ESPs are restored to 10 Hz, and the updated Ultra96 process remains running. The highest tested clean setting was 70 Hz, producing approximately **66 packets/second per device and 33.792 kbps combined** on its repeat; the next tested setting, 75 Hz, failed. Commands, 4096-byte files and right-device power recovery were physically exercised. The updated native iPhone later passed a 1320-result aggregate count check at 10 Hz. Range verification remains deferred by the user.

## Installed software

- Left / device 1: BLE `38:18:2B:19:82:AE`, protected `firebeetle32-left` v2 firmware. Binary SHA-256 `02e13b37d659f8a21654ef2dd731b33ced4809daa700db58c6b9587c30773eba`.
- Right / device 2: BLE `38:18:2B:18:9D:6A`, protected `firebeetle32-right` v2 firmware. Binary SHA-256 `6206564b96e571b381a5d82cbe9da5f627ac3581bbf25f906c28c970967811b0`.
- Ultra96 source: `/var/tmp/cg4002-week7-yanjie-20260907/source-co-v2-20260928T122047Z`; process PID `105159` at deployment, session `week7-demo`, loopback ingestion/results ports `8888` / `9999`.
- Previous runtime copied to `/var/tmp/cg4002-week7-yanjie-20260907/rollback-co-20260928T122047Z`. Existing TLS files and verified SSH route retained. Deployment checked source hashes, remote Python compilation, process ownership and listening sockets; local record: `.week7-local/deployment-20260928T122047Z.json`.

Authenticated BLE bonds and protected characteristics were verified after commissioning. Both negotiated ATT MTU 517. Targeted bond recovery was required after the GATT schema change; the application does not automatically erase bonds or lower security. The adapter was the laptop's Intel Wireless Bluetooth adapter. USB programming/power during these engineering tests does not establish the separate assessed setup requirement prohibiting USB connections to the relay laptop.

Host conditions: Windows 11 build 26200, Intel Bluetooth driver 24.40.10.3 (28 April 2026), Python 3.12.7, Bleak 3.0.1, ACK window 32, input queue 64 and freshness limit 2 seconds. The initial diagnostic scan measured left/right RSSI of -31/-46 dBm; physical distance was not measured. Additional environment metadata is saved in `.week7-local/co-hardware-environment-20260928.json`.

## Baseline on both updated devices

Artifact: `.week7-local/co-live-suite-20260928T122421Z/baseline-10hz/report.json`, with raw packet/result JSONL files and source fingerprints in the same directory.

- Concurrent steady observation: **65.016 seconds at 10 Hz per device**.
- Left: 652 generated = received = board-ACKed; right: 653 generated = received = board-ACKed. Totals include startup/drain; goodput uses only the common steady interval.
- Six keyboard-equivalent commands (three per device) used the actual keyboard dispatch path, verified ESP value transformations, and produced six individually correlated results.
- Each ESP reconstructed a **4096-byte** transfer spanning 23 BLE chunks and returned matching length/SHA-256. The peer's received packets and results advanced during each transfer.
- **1311 unique results**, exactly matching 1305 accepted sensor records plus six commands. All were v2; no missing, duplicate or unexpected result IDs.
- Combined sensor goodput: **5.118740 kbps**, counting unique valid 32-byte packets, excluding controls/files/overhead. No source, queue, validation or evidence-log losses in this capture.

## Initial rate failure and investigation

The first 25 Hz candidate failed and remains recorded as a failure at `.week7-local/co-live-suite-20260928T122421Z/benchmark-25hz/`. Left observed 1082 packets during the 65-second interval instead of approximately 1625; right observed 1624 and reconciled all 1631 generated records over its full source boundary. The result subscriber received all 2761 accepted records exactly once. The combined 10.657477 kbps from this failed capture is **not** a sustainable-rate claim.

Left loss consisted of 35 bursts of 15 consecutive sequence numbers. A subsequent same-boot source read reported next sequence 2311, submitted 1782, failed 529. Subtracting the original start boundary 652 gives 1659 generated, 1130 submitted and 529 rejected; 1130 equals the accepted records, and 529 equals 525 internal gaps plus four trailing records. That later read diagnoses source submission rejection; it does not replace the missing final boundary of the original failed capture.

The failure also exposed a cleanup bug: two notification-stop timeouts could exhaust a shared one-second deadline, leaving native disconnect only one millisecond. Disconnect now receives its own bounded one-second budget. A failing regression reproduced the resource-release failure before the fix; 64 relevant tests passed afterward.

An independent short timing experiment (`.week7-local/co-link-probe-20260928T123035Z.json`) measured 60 ms default intervals on both links and accepted 15 ms intervals after the Windows throughput preference request. Each device delivered approximately 300 packets during each 12-second phase at 25 Hz, including the fresh default phase, so the initial capacity problem varies by connection; this short diagnostic alone does not establish a sustainable rate or a unique root cause. ATT MTU is not the LE link-layer data length. Windows documents the throughput preference as a connection-scoped request with concurrency/power tradeoffs: [Microsoft API documentation](https://learn.microsoft.com/en-us/uwp/api/windows.devices.bluetooth.bluetoothledevice.requestpreferredconnectionparameters).

## Physical power loss

Artifact: `.week7-local/co-power-20260928T123201Z/report.json`; operator confirmation saved separately beside it.

The user removed power from the right ESP and restored it, keeping the left powered. The recording observed an actual native BLE disconnect at `12:33:08.175660 UTC`, authenticated reconnection at `12:33:19.214254 UTC`, and resumed accepted data. Right boot changed from `1904893660` to `3829790198`.

During the **11.047-second detected-disconnect-to-reconnect interval**, the left delivered **111 packets and 111 ACKs**, kept boot `1209560267`, and had no gaps, disconnects or errors. Its maximum reception silence during that interval was 0.125 seconds (0.188 seconds over the wider ready-to-recovery period). The recovery check completed 14.782 seconds after detected disconnection, including three seconds of resumed traffic.

This proves the recorded one-device power recovery and healthy-peer continuity. The affected device's first received new-boot packet (`2:3829790198:0`) was not ACKed or delivered as a result; the report records one ambiguous drop and one transport error before subsequent packets resumed. The optional subscriber's 1327 unique results exactly match accepted ACK identities. This fault pass does not imply lossless affected-device recovery.

The recording does not measure electrical power-off duration, prove outage replay, or establish total source loss across reboot. Cross-boot source loss remains unknown. The user deferred the physical range trial and native iPhone build/test.

## Fresh post-fault baseline and regression checks

Artifact: `.week7-local/co-tuned-suite-20260928T124014Z/baseline-10hz/report.json`. After the power trial and the laptop cleanup/timing updates, both devices completed a fresh **65.000-second** common observation at 10 Hz. Left reconciled 658 generated/received/ACKed records; right reconciled 652. The independent subscriber received **1316 matching unique results**, including six further verified commands. Both 4096-byte source files are saved alongside their matching receiver digests, and peer traffic continued during each transfer. Steady sensor goodput was **5.120 kbps** combined. The run had no source, queue, validation, cleanup or evidence errors; source files remained unchanged during capture.

The laptop timing helper requests the Windows throughput preference only above the baseline rate, holds separate owned handles until cleanup, and records accepted request status separately from measured connection settings. Unsupported/denied requests are diagnostics, not evidence of a changed interval. Before the subsequent shutdown-tail correction, the complete Python regression command `python -m pytest laptop/tests tests phone/tests -q` passed 452 tests with 3 skipped. Existing C# checks passed 57 checks, and both protected firmware builds passed earlier in this implementation. Native Swift build/install is still deferred to the user's Mac.

The first tuned 25 Hz run (`co-tuned-suite-20260928T124014Z/benchmark-25hz`) observed 15 ms intervals and no internal sequence gaps or source submission failures. It nevertheless failed the strict final source audit: right generated/submitted 1626 records but received/ACKed 1625, missing the final sequence 2317 during shutdown. All 3278 accepted results arrived exactly once. A subsequent 65-second 10 Hz fallback passed and both rates were reset. That suite's overall baseline/fallback acceptance does not mean its 25 Hz candidate passed.

The shutdown issue was reproduced separately at 100 Hz in `.week7-local/co-tail-probe-20260928T124557Z.json`: ordinary stop lost one final packet in 3 of 12 short trials, while disabling remote notifications and retaining the local handler briefly lost none in 12 trials. Neither mode had duplicate callbacks or source submission failures. These are diagnostic trials, not sustainable-speed acceptance. The production correction uses an uncached source-counter boundary and a bounded drain before removing the notification callback, retaining strict loss accounting.

## Final software verification

With both laptop fixes installed, the complete Python regression command passed **465 tests with 3 skipped** in 104.67 seconds. A separate focused run passed 102 tests, and an independent review passed 45 checks covering the tail boundary, source accounting and cleanup. The source-counter reads share one timeout budget; the tail wait is capped at 0.5 seconds and fails conservatively on missing packets or host backlog. Native operation admission, cancellation, rejected CCCD writes, changed source snapshots and missing-tail behavior have regression coverage. No source loss tolerance was added.

Final physical artifacts use `.week7-local/co-final-suite-20260928T125539Z/`. Its 65.000-second 10 Hz baseline reconciled left 652 and right 654 generated/received/ACKed records, six further commands, both saved 4096-byte file transfers and **1312 exact unique results**. Both final source counters matched their quiesced snapshots; the laptop evidence logger reported no losses. Combined steady sensor goodput was 5.120 kbps.

## Coarse rate sweep after the fixes

Every row below used two concurrent physical devices and a common observation interval of at least 65 seconds. All accepted ACK identities matched independently received results exactly once. Goodput counts sensor bytes only. High-rate captures observed 15 ms connection intervals on both devices, zero peripheral latency and 2000 ms supervision timeouts.

| Requested Hz per ESP | Observed packets/s left / right | Combined sensor kbps | Full accepted result count | Verdict |
|---|---:|---:|---:|---|
| 10 | 10.000 / 10.000 | 5.120 | 1312, including six commands | Pass |
| 25 | 24.994 / 24.978 | 12.793 | 3254 | Pass |
| 50 | 49.985 / 49.969 | 25.588 | 6512 | Pass |
| 100 | 66.646 / 98.985 | 42.401 | 10832 | Fail: left gaps and incomplete source shutdown |
| 50, repeated after failure | 49.985 / 49.938 | 25.580 | 6503 | Pass |

At 100 Hz, left recorded 2077 internal sequence gaps and could not complete its remote notification stop/source boundary under overload. Right reconciled all 6453 generated/received/ACKed records. The failed run's 42.401 kbps is not a reliable-rate claim. Rates 150/200 were not attempted after that failure. The clean 50 Hz repeat verifies recovery to the preceding passing point.

A later diagnostic reconciliation of the same left boot confirms source submission congestion across the wider between-run interval: previous clean 50 Hz ended at `(next_seq=12356, submitted=11827, failures=529)`; the fallback started at `(18821, 16206, 2615)`, derived from its final snapshot and clean 3253-record delta. Thus 6465 generated = 4379 submitted + 2086 rejected submissions. All 4379 submitted packets were received/ACKed; 2077 internal gaps plus nine trailing IDs account for the rejected samples. This later calculation does not replace the failed capture's missing shutdown boundary.

Both ESPs acknowledged the final reset to 10 Hz. That initial BLE-only reset helper had no receipt consumer, so its source-tail check reported two harness-only timeouts despite successful rate ACKs; cleanup captures are explicitly excluded from throughput acceptance. The helper was subsequently corrected to process BLE receipts without opening TLS or claiming board ACKs.

## Fine rate sweep and final reset

Artifacts: `.week7-local/co-fine-suite-20260928T130746Z/`, with a combined numerical index at `.week7-local/co-rate-measurements.json`. Each candidate and the fallback used a 65.000-second common observation. The source settings are commands, not measured packet rates: firmware pacing and link behavior produce the rates in the second column. The existing rate-coverage check requires at least 90% of the requested rate, while source/receipt/ACK reconciliation requires no missing generated records for a clean pass.

| Requested Hz per ESP | Observed packets/s left / right | Combined sensor kbps | Full accepted result count | Verdict |
|---|---:|---:|---:|---|
| 60 | 58.508 / 58.492 | 29.952 | 7613 | Pass |
| 65 | 62.015 / 62.000 | 31.748 | 8088 | Pass |
| 70 | 66.015 / 66.000 | 33.796 | 8595 | Pass |
| 75 | 71.000 / 66.600 | 35.226 | 9014 | Fail: right rejected 260 source submissions |
| 70, repeated after failure | 66.000 / 66.000 | 33.792 | 8638 | Pass |

At 75 Hz, left reconciled all 4632 generated/received/ACKed records. Right generated 4642, successfully submitted 4382 and rejected 260; all 4382 submitted records reached both ingestion ACK and result receipt. Both devices completed their source shutdown boundaries without errors. This is an observed source-capacity failure, not missing downstream delivery or a shutdown-tail loss. Its 35.226 kbps is not a clean operating-rate claim.

The 70 Hz repeat reconciled left 4345 and right 4293 generated/received/ACKed records; all **8638 unique results** matched the accepted identities. Both 70 Hz runs passed, supporting a measured clean rate of approximately **66 packets/second per ESP**, or **33.792 kbps combined**. This is the highest tested clean setting under the recorded conditions, not proof of an absolute maximum. Rates between 70 and 75 were not tested.

Independent review reconciled raw ACK/result identities for all five fine captures, with no missing, unexpected or duplicate results. Every quiesced source snapshot equaled its verified final snapshot. All 35 captured software fingerprints matched across the fine runs and the final workspace; there were no evidence-log overflows or cleanup errors. Both links measured 15 ms intervals, zero peripheral latency and 2000 ms supervision timeouts; owned preference handles were released afterward.

The corrected final cleanup capture (`cleanup-reset-10hz/report.json`) confirmed **10 Hz on both ESPs**, processed three local sensor receipts per device, and completed matching source shutdown boundaries without source-statistics or cleanup errors. This BLE-only operation made no TLS connections, sends or ingestion ACKs and is explicitly excluded from benchmark acceptance. Its source `clean` field is false because ingestion ACKs are intentionally absent; it is not an end-to-end delivery run.

## Final running-service check

At `2026-09-28 13:15:41 UTC`, `.week7-local/co-production-final-check.json` verified PID **105159**, its original start time, command and deployed working directory. That process still owned loopback ports **8888/9999**. All ten deployed `common`/`ultra96` files matched both the uploaded SHA-256 manifest and the current workspace. A fresh certificate/hostname-verified TLS result connection received the expected `SUBSCRIBED` response for `week7-demo`. The check left the service running and closed its own subscriber and temporary tunnels.

The running service's optional bounded diagnostic trace was **52,428,580 bytes**, within 220 bytes of its **52,428,800-byte** lifetime cap. Treat that server trace as capped/incomplete for later events. Its `status.json` is not finalized while the process runs, so the initial zero counters are not evidence of zero server errors. The per-capture client packet, ACK and independent result ledgers are complete and separately audited with no evidence overflow; they support the delivery totals above. The service was not restarted merely to reset its diagnostic logger.

## Updated native iPhone follow-up

After merge commit `3e58e3eeec51dec89e8f4909c0af8c9b132d0b3a`, the user reported building the new app on the iPhone and connecting it. Build provenance is the operator's report; the installed revision and Xcode build log were not independently extracted. Before the test the operator reported **`Subscribed, Received: 0`**.

Artifact: `.week7-local/co-iphone-v2-20260928T133928Z/`. The capture ran from `13:39:29.914549` to `13:40:39.956873 UTC`, including setup and cleanup, with a **65.000-second** simultaneous observation at 10 Hz per ESP. The harness opened ingestion connections only, leaving the iPhone as the result receiver. It sent three keyboard-equivalent commands per device through the actual dispatch path, verified all eight transformed values for each response, and obtained six correlated ingestion ACKs.

| Device | Boot ID | Sensor sequence interval | Generated = received = ACKed | Command ACKs | Expected results |
|---|---:|---|---:|---:|---:|
| Left / 1 | 1209560267 | 43211–43871 inclusive | 661 | 3 | 664 |
| Right / 2 | 3829790198 | 39953–40605 inclusive | 653 | 3 | 656 |
| Total | | | **1314** | **6** | **1320** |

Both source boundaries were complete and clean, with zero missing records, source failures, sequence anomalies, identity errors, BLE disconnects, transport errors or cleanup errors. All commands completed without rejection or failure. The evidence logger wrote 2674 events with no drops, write errors or unfinished events, and captured software fingerprints remained unchanged. Combined steady sensor goodput was **5.123938 kbps**; it excludes commands and startup/drain packets.

After the sender stopped, the operator reported **`Subscribed, Received: 1320`**. The increase from zero exactly matches the 1314 sensor records plus six commands. This is a **pass for the updated native iPhone's aggregate result count during concurrent v2 streaming and command traffic**, based on operator observations. It does not establish individual phone receipt for each expected result ID or separately observed command IDs. Expected command identities and transformations are saved in `expected-results.json` and `commands.jsonl`; the phone observation and SHA-256-bound acceptance summary are in `operator-after.json` and `iphone-acceptance.json`.

Read-only board checks found the same service PID `105159` and established result socket inode `802867` before and after the capture. The deployed files still matched their uploaded manifest and the merged source, allowing for Git's Windows line-ending conversion. These endpoint socket checks are not continuous subscriber-lifecycle evidence. The existing server diagnostic trace remained capped, so this follow-up does not claim a complete server event ledger. No desktop result subscriber was opened and the production service was not restarted. Both source rates remain 10 Hz. The separate physical range trial is still deferred.
