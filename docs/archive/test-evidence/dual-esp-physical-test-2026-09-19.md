# Dual ESP32 physical test session — 2026-09-19

**Current result (`5d2e06f`): two physical ESPs → laptop → actual Ultra96 PASS for a 600-second, 10-Hz-per-device run. Native-iPhone acceptance remains unobserved.** The remote capture reconciled **6,005 / 6,001 generated/BLE/sent/ACK samples**, and the independent board-log audit confirmed all **12,006 IDs accepted exactly once in order**, with no missing, repeated or unrelated IDs. All capture anomaly counters were zero and the process exited 0. Independent review and the full **294 passed / 3 skipped** software suite passed. The new local baseline and independently audited TLS/reset recovery trials also passed their respective checks; the deliberate fault runs remain non-clean with one ambiguous drop each.

The results below describe finite runs under recorded conditions. They do not establish universally lossless operation or a guarantee that every future run will succeed.

Historical results at **`f058ef0`** remain preserved: the local 600-second soak passed with **6,002 / 6,001** exact samples, but two remote 600-second captures failed with **one** and then **33** stale discards. Per-packet timing exposed stop-and-wait ACK delays and queue aging, motivating the bounded-window implementation at `5d2e06f`. Those failed artifacts are not rewritten or treated as passing after the code change; the original failed reset-collector verdict also remains separate.

## Conditions and provenance

- Session started **2026-09-19 06:33:18 UTC / 14:33:18 China Standard Time**. Times below are UTC; add eight hours for the local session time.
- Initial checkout revision: **`f058ef0bf53e4f71fd9391a7d4ac586898e7b467`** (`f058ef0`), in `D:/LetThemCook-worktrees/dual-esp-reception`. Firmware builds and all initial physical captures, remote failures and timing diagnosis below use this revision. The later ACK-window implementation is **`5d2e06f2ec9b57d6cd7551d6f39d7d683b032aa3`** (`5d2e06f`); its separate validation is recorded afterward.
- Host: Windows 11 build 26200, Python 3.12.7. Initial user setup: new ESP connected by USB, previously tested ESP powered by a power bank. Later the user connected both boards to laptop USB. The latest user-reported setup has **both ESPs powered from laptop USB**, with the old known-working cable moved to the new board and the other cable moved to the old board. Only the known-working cable provides an enumerated data connection; COM4 now identifies the new board. This supersedes the earlier proposed old-board power-bank setup.
- Confirmed old BLE identity: **`38:18:2B:19:82:AE`**, advertised as **`LTC-W7`**, packet device ID **1**. The new ESP's base MAC is **`38:18:2B:18:9D:68`**, distinct from old base MAC **`38:18:2B:19:82:AC`**. The new BLE address was subsequently observed as **`38:18:2B:18:9D:6A`** and its packets verified as device ID **2**. Base MAC and BLE address are recorded separately.
- The user initially chose **local physical BLE testing first** after the SSH preflight. After the local baseline, the user enabled VPN and explicitly extended the session to all possible remote/native-iPhone tests. The completed local captures still used a local TLS server and desktop result receiver; they did not exercise campus Ultra96, SSH forwarding, or the native iPhone.
- Local evidence is retained outside Git under [the session directory](D:/LetThemCook-builds/dual-esp-20260919T063318Z). The linked JSON records contain allowlisted status/evidence; no passwords, private keys or BLE passkeys are reproduced here.

Initial host/device inventory: [preflight.json](D:/LetThemCook-builds/dual-esp-20260919T063318Z/preflight.json).

## Preparation and unsuccessful prerequisites

These preparation observations are separate from clean capture and controlled fault tests.

| Time (UTC) | Attempt | Recorded outcome and qualification |
| --- | --- | --- |
| 06:33:18 | Initial USB/BLE inventory | No serial ports enumerated; the old `LTC-W7` BLE address was visible. A subsequent user reseat still did not expose the intended new board; that reseat observation comes from the session, without a separate timestamped artifact in this checkpoint. |
| 06:37:38 | NUS jump-host TCP preflight | `stujump.comp.nus.edu.sg:22` was reachable and supplied an SSH banner. This proves reachability, not authenticated board access. |
| 06:38:09 | Noninteractive SSH authentication preflight | Exit **255**, jump-host `Permission denied (publickey)`. No service changes or forwards were performed. This does not prove that a correctly authenticated interactive/VPN route cannot work. Remote/native-Phone testing was deferred. |
| 06:39:03 | Inventory after user connected both ESPs by USB | Only **COM4**, `USB-SERIAL CH340`, VID:PID `1A86:7523`, location `1-3`, enumerated. Two plugged-in boards did not establish two usable USB devices. |
| 06:39:42–06:40:19 | Identify COM4 before upload | Safe serial status reported boot **3693720664**. An authenticated BLE probe of the old address returned the same boot and device ID 1, identifying COM4 as the **old** ESP. Serial capture recorded no passkeys and requested no reset. |

Evidence: [network preflight](D:/LetThemCook-builds/dual-esp-20260919T063318Z/network-preflight.json), [SSH preflight](D:/LetThemCook-builds/dual-esp-20260919T063318Z/ssh-preflight.json), [both-USB inventory](D:/LetThemCook-builds/dual-esp-20260919T063318Z/usb-both-connected.json), [safe COM4 identification](D:/LetThemCook-builds/dual-esp-20260919T063318Z/com4-safe-identification.json), and [matching BLE identification](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-esp-usb-identification.json).

Boot changes during USB preparation or firmware upload are setup events. They are **not** measured disconnect/recovery acceptance trials.

## Old firmware: protected single-device regression

| Run | Conditions and measured result | Scope |
| --- | --- | --- |
| BLE preflight, 06:34:43–06:34:47 | Stored authenticated bond verified; ATT MTU **517**; device 1, boot **1126181650**; ten valid deterministic packets, sequences **0–9**; no recorded errors. | Confirms the old board's current protected BLE packet path. GATT inventory did **not** expose source statistics. |
| Local target-100 regression, 06:36:01–06:36:16 | Actual capture contained **101** packets, sequences **10–110**, boot **1126181650**. Bridge received/sent/ACKed **101**; result receiver received **101**. Ordered ACK IDs and result IDs matched exactly. Server accepted **101**, with no duplicate/rejected input or result drops. Bridge error/drop/gap/duplicate/reboot counters were zero, queue empty and no unfinished work. | **PASS for this single-device BLE → local TLS → desktop-result run.** The name “local100” denotes its target; the measured count is 101. |

Evidence: [old BLE preflight](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-esp-preflight.json) and [local regression with exact ordered IDs](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-esp-local100.json).

The firmware in these runs lacked the generated-source statistics characteristic. There was no start/end generated interval to reconcile, so these results **do not prove complete source generation delivery, a clean dual capture, remote delivery, or native iPhone acceptance**. The observed contiguous range and exact ACK/result correlation retain their narrower value.

## Builds and verified upload

Both profiles were clean-built from `f058ef0`, using PlatformIO Core **6.1.19**, Espressif32 **7.1.0**, Arduino framework package **3.20017.241212+sha.dcc1105b**, and the `firebeetle32` board configuration. Each build exited **0**, produced a **1,123,552-byte** firmware image, and retained protected BLE security. Shared flags include `CORE_DEBUG_LEVEL=0`.

| Profile | Device ID | Build artifact time (UTC) | Firmware SHA-256 |
| --- | --- | --- | --- |
| `firebeetle32-left` | 1 | 06:36:43 | `2b76af5b80662a4c2aec3dc5ed154beafb93cc562e7c7054ce4234951bddfdd2` |
| `firebeetle32-right` | 2 | 06:37:01 | `52d52d0a3e9859820b9f34149f756d87fd2dcf564972bcb6190f41669cac9ce8` |

The [build manifest](D:/LetThemCook-builds/dual-esp-20260919T063318Z/build-manifest.json) records full tooling versions, firmware/log hashes, paths, and exit codes. Build logs: [left](D:/LetThemCook-builds/dual-esp-20260919T063318Z/build-left.log), [right](D:/LetThemCook-builds/dual-esp-20260919T063318Z/build-right.log). Its `upload_performed: false` describes the build-only step; the subsequent upload has separate evidence.

**06:40:52–06:41:15:** uploaded `firebeetle32-left` through **COM4** only after matching its serial boot to old BLE identity `38:18:2B:19:82:AE`. Upload exit code **0** is recorded in [the upload receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/upload-old-left-COM4.json), with [the upload log](D:/LetThemCook-builds/dual-esp-20260919T063318Z/upload-old-left-COM4.log). This establishes uploader completion. The separate runtime checks and recovery below establish the updated old board's protected source-statistics behavior. The subsequent right-board identification/upload is recorded separately below.

## Post-update discovery failures and targeted recovery

The two initial fresh-process BLE attempts after upload failed before receiving samples. They remain separate failed preflights; the later success does not replace their evidence.

| Time (UTC) | Attempt | Recorded result |
| --- | --- | --- |
| 06:41:50–06:41:52 | First post-update BLE probe | `PermissionError`, **WinError -2147024874** (“the device does not recognize the command”); no samples. |
| 06:43:33–06:43:36 | Fresh-process retry with safe serial inspection | Same error during WinRT GATT service/characteristic discovery. Windows already reported a stored protection-level-3 bond. Firmware reported `ble_security_complete success=1 auth_mode=13 approved=1 current_peer=1` and MTU **517** before the discovery error; boot **333362107**. Authentication had succeeded, so this observation does not support labeling the failure as rejected pairing. |
| 06:45:00–06:45:01 | Targeted Windows unpair | Removed only old address `38:18:2B:19:82:AE`; result **UNPAIRED**. |
| 06:45:34 | Targeted ESP bond erase | Sent the erase command only to verified old **COM4**; firmware reported `erase_bonds_complete remaining=0`. No passkeys recorded. |
| 06:45:35–06:45:40 | Fresh protected pairing and source-statistics inspection | Pairing completed using the locally read PIN in memory, without recording it. Authenticated Windows bond verified, MTU **517**, source-statistics UUID present, ten valid packets and no recorded inspection errors. |

Failed preflight evidence: [first post-update attempt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-esp-after-update.json) and [retry with safe serial/traceback](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-esp-after-update-safe-inspection.json). Targeted recovery evidence: [Windows unpair](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-targeted-windows-unpair.json), [old-ESP bond erase](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-targeted-esp-bond-refresh.json), and [fresh pairing/inspection](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-esp-fresh-pair-inspection.json).

The successful inspection observed device **1**, boot **333362107**, with source start `next_seq=0, submitted=0, failures=0` and source end `next_seq=10, submitted=10, failures=0`. All ten received packets had valid dummy values and consecutive sequences **0–9**. The **[0, 10)** generated interval therefore matches this finite BLE reception. This inspection does not contain TLS ACK or result evidence and is not a dual source-to-ACK test.

Rebonding resolved the observed post-firmware-update discovery failure. A stale Windows GATT database/cache relationship following the firmware service change is **consistent with the evidence**, but the OS-internal cause was not proven. No application source-code change or security downgrade was made. This deliberate commissioning recovery is distinct from a measured runtime fault/recovery acceptance test.

## Cable swap and new-board upload

At **06:48:24 UTC**, the [swapped-cable inventory](D:/LetThemCook-builds/dual-esp-20260919T063318Z/usb-cables-swapped.json) still listed only COM4. The user had moved the old working cable to the new ESP and the other cable to the old ESP, with both boards connected to laptop USB.

At **06:51:24–06:51:26**, an esptool `read_mac` operation on COM4 exited **0** and reported new base MAC **`38:18:2B:18:9D:68`**. It differs from the verified old base MAC **`38:18:2B:19:82:AC`**, establishing that the single enumerated port now reaches the **new** board. Evidence: [read-MAC receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/new-cable-COM4-read-mac.json) and [read-MAC log](D:/LetThemCook-builds/dual-esp-20260919T063318Z/new-cable-COM4-read-mac.log). The operation's logged RTS reset is a setup action, not a controlled runtime fault test.

The data connection following the known-working cable across boards supports a cable/data-path explanation for the earlier missing new-board serial port. It is not an electrical diagnosis or proof that the other cable is charge-only.

At **06:51:42–06:52:05**, the verified new COM4 target accepted the protected **`firebeetle32-right` / device ID 2** upload, exit **0**. The receipt records firmware SHA-256 `52d52d0a3e9859820b9f34149f756d87fd2dcf564972bcb6190f41669cac9ce8`, matching the right build manifest. Evidence: [right upload receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/upload-new-right-COM4.json) and [right upload log](D:/LetThemCook-builds/dual-esp-20260919T063318Z/upload-new-right-COM4.log). The subsequent pairing/inspection below supplies separate runtime evidence; upload completion alone does not establish those properties.

## New-board protected inspection and both advertisements

At **06:52:30 UTC**, the [post-flash scan](D:/LetThemCook-builds/dual-esp-20260919T063318Z/both-post-flash-advertising.json) observed both `LTC-W7` advertisements: old **`38:18:2B:19:82:AE`** and new **`38:18:2B:18:9D:6A`**, each advertising the expected Week 7 service. Simultaneous advertisements establish discovery, not concurrent connected-stream capacity.

At **06:52:39–06:52:45**, [new-board first-pair inspection](D:/LetThemCook-builds/dual-esp-20260919T063318Z/new-esp-first-pair-inspection.json) completed without recorded errors. Windows initially had no bond; protected pairing completed, authenticated bond verification passed, and safe firmware status recorded authentication success with mode **13**, approved/current peer **1**. ATT MTU was **517** and the source-statistics characteristic was present. No passkeys were recorded.

The new board returned device **2**, boot **358768252**, source start `next_seq=0, submitted=0, failures=0` and source end `next_seq=10, submitted=10, failures=0`. Ten received packets, sequences **0–9**, all had valid dummy values. Its finite generated interval **[0, 10)** therefore matches this BLE reception. As with the updated old-board inspection, this was an individual inspection without TLS ACK/result evidence; concurrent dual source-to-ACK capture was pending at that stage and was subsequently exercised by the baseline and soak below.

## Old board after the cable swap

At **06:53:36–06:53:40 UTC**, the [old-board post-swap inspection](D:/LetThemCook-builds/dual-esp-20260919T063318Z/old-esp-after-cable-swap-inspection.json) verified ID **1** at its known BLE address, using its existing Windows protection-level-3 bond and ATT MTU **517**. The new setup boot was **773972803**. Source counters moved from `next_seq=0, submitted=0, failures=0` to `next_seq=10, submitted=10, failures=0`; received sequences **0–9** were valid, with no recorded errors. The setup boot change is not a controlled fault acceptance result.

## Concurrent physical baseline — PASS

**07:00:43–07:01:17 UTC:** a **30.000-second common observation** exercised both protected physical ESPs concurrently through the production dual coordinator, a real local TLS `Week7Server`, and one desktop result collector. The total capture/cleanup elapsed time was **33.906 seconds**. The collector finished with `passed=true`, `clean=true`, and exit **0**; both per-device entries were clean.

| Device / BLE address | Boot | Generated interval | Generated / BLE received / ACKed / desktop results | Common-window notifications | Maximum common-window silence |
| --- | --- | --- | --- | --- | --- |
| 1 / `38:18:2B:19:82:AE` | 773972803 | **[10, 312)**, sequences 10–311 | **302 / 302 / 302 / 302** | 301 | 0.125 s |
| 2 / `38:18:2B:18:9D:6A` | 358768252 | **[10, 312)**, sequences 10–311 | **302 / 302 / 302 / 302** | 300 | 0.125 s |

For each source interval, exact generated, received, accepted-ACK and desktop-result IDs matched, including the first and last samples. There were no ledger overflows, source failures, missing IDs, sequence/identity/boot anomalies, BLE/transport errors, disconnects, queue drops, stale packets or unfinished work. Each board used one BLE connection and one TLS connection. The local server accepted **604** samples, with zero duplicate/rejected input, result drops/staleness or disconnected results. The generated interval includes the source snapshot boundaries around the common observation, so its 302 samples per board need not equal the 300 expected samples inside the timed window.

Evidence: [final baseline report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-baseline-30s/final-report.json), [complete run state / exit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-baseline-30s/run-state.json), [packet/ACK/result traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-baseline-30s/traces.jsonl), [progress](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-baseline-30s/progress.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-baseline-30s/server-metrics.json).

A separate [concurrency analysis](D:/LetThemCook-builds/dual-esp-20260919T063318Z/baseline-concurrency-analysis.json), produced at **07:06:43**, found both devices made ACK progress in **all 29 complete one-second bins** within their overlapping ACK interval. Each bin contained ten ACKs per device. This supports concurrent streaming throughout the overlap, without claiming identical physical radio-transmission instants.

The baseline's `source_worktree_dirty=true` includes this untracked report draft. The separate [source-provenance check](D:/LetThemCook-builds/dual-esp-20260919T063318Z/source-provenance.json), at **07:04:21**, verified all **23 checked runtime/config files** against `f058ef0`, with no changed tracked paths; `provenance_pass=true`. It records raw and line-ending-normalized hashes and identifies the untracked documentation separately. The one-off collector remains an external evidence helper with its own recorded hash.

This is a finite **two-physical-ESP → Windows BLE → local TLS → desktop** baseline. Its scope is separate from the longer soak and fault trials below, and it does not establish the campus route or native Phone delivery.

## Concurrent physical 600-second soak — PASS

**07:02:00–07:12:04 UTC:** the clean soak completed a **600.000-second common observation** with both protected physical devices, the local TLS server and desktop subscriber. Total capture/cleanup elapsed time was **604.203 seconds**. The final report and run state record `passed=true`, `clean=true`, exit **0**, no capture exception, no cleanup errors and no ledger overflow.

| Device | Boot | Source interval / received sequence range | Generated / BLE received / ACKed / desktop results | Common-window notifications | Maximum common-window silence |
| --- | --- | --- | --- | --- | --- |
| 1 | 773972803 | **[312, 6314)** / 312–6313 | **6,002 / 6,002 / 6,002 / 6,002** | 6,001 | 0.188 s |
| 2 | 358768252 | **[312, 6313)** / 312–6312 | **6,001 / 6,001 / 6,001 / 6,001** | 6,000 | 0.188 s |

Both exact-reconciliation entries pass for received, accepted-ACK and desktop-result IDs, with complete clean source snapshots. Each board used one BLE and one TLS connection; no runtime failures, source submission failures, missing IDs, sequence/identity/boot anomalies, disconnects, drops or stale/unfinished packets were reported. The local server accepted **12,003** samples with zero duplicates, rejects, result drops/staleness or disconnected results. The measured common-window rates met the configured 10 Hz expectation.

Evidence: [soak final report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-soak-600s/final-report.json), [complete run state / exit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-soak-600s/run-state.json), [full traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-soak-600s/traces.jsonl), [progress](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-soak-600s/progress.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-soak-600s/server-metrics.json).

The [independent literal soak audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-soak-600s/independent-soak-audit.json), generated at **07:13:38 UTC**, independently passed exact literal IDs, sequence order, source deltas, accepted statuses and deterministic dummy results. It found no missing, extra, duplicate or owner-mismatched IDs. Both devices progressed in **all 600 one-second observation slots**, separately for BLE reception, ACKs and desktop results; maximum interarrival gap was **0.188 seconds**. Input artifact hashes are recorded in the audit.

This is a clean finite local physical dual-stream soak under the recorded setup. Deliberate fault recovery and remote/native-Phone delivery have separate acceptance outcomes; neither is implied by this clean run.

## First right-board reset trial — original failed verdict retained

**07:12:23–07:13:27 UTC:** the first 60-second reset trial used collector v2 and deliberately reset only the new/right board through verified COM4 at **07:12:41.747 UTC**, 15 seconds after the common observation began. The reset action completed. The saved original result is **`passed=false`, `clean=false`, exit 1** and remains unchanged.

Positive hardware observations are narrower than that overall verdict: the old/left board stayed clean with **601 exact generated/received/ACK/result samples**, sequences **6314–6914**, boot **773972803**, no BLE reconnect and maximum ACK gap **0.125 seconds**. The right board disconnected, reconnected with a new boot, and accumulated **431 ACKs**; its total reception was 432, with one ambiguous drop. The local server recorded **1,032 accepted and one rejected** operation, so the original server anomaly is preserved.

The root collector review identified a timing error: an in-flight **old-boot ACK** arriving just after the reset marker was mistaken for resumed right-board progress. That selected an artificial **0.125-second** affected-path gap and reported **zero peer ACKs** in that interval, making the peer-progress check fail even though later new-boot recovery was visible. This diagnosis does not rewrite the saved verdict or erase the server rejection. The subsequent v3 repeat below requires a causal **new-boot** recovery ACK for the reset and strict per-connection attribution of any server error. No overall reset-recovery PASS is claimed from this first attempt.

Evidence: [original reset report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-60s/final-report.json), [original run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-60s/run-state.json), [original traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-60s/traces.jsonl), and [original server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-60s/server-metrics.json).

## Right-path TLS interruption — recovery PASS, non-clean capture

**07:14:28–07:15:32 UTC:** the 60-second TLS-fault trial deliberately aborted only the right bridge's transport at **07:14:47.028 UTC**, 15 seconds into the common observation. Its fault acceptance result is **`passed=true`, `expected_fault_evidence_passed=true`, exit 0**, while both the overall capture and affected right-device zero-loss verdict correctly remain **`clean=false`**. Exit 0 here denotes the collector's requested recovery checks, not a clean capture.

- **Unaffected device 1:** **602** generated, received, ACKed and desktop-result samples matched exactly, sequences **6915–7516**, boot **773972803**. Its source/bridge stayed clean with no errors or reconnects; maximum ACK gap was **0.141 seconds**.
- **Affected device 2:** **603** generated/BLE-received samples, sequences **280–882**, boot **2683815386**, but **602** ACKs and desktop results. One ambiguous sample was dropped at the forced abort; there was one transport error and a second TLS connection. BLE remained connected. The missing ACK remains visible in source reconciliation.
- Right-path ACK delivery resumed across a measured **0.625-second** gap. The old/left stream produced **six ACKs during that gap**; the right stream then produced **446 ACKs after transport reconnection**. Causal post-reconnect ACK and healthy-peer continuity checks passed.
- The server accepted **1,204** packets, with zero duplicate/rejected inputs and zero other reported server anomalies. No outage history or ambiguous packet was replayed as new live traffic.

Evidence: [TLS-fault report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-tls-60s/final-report.json), [complete fault run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-tls-60s/run-state.json), [fault traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-tls-60s/traces.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-tls-60s/server-metrics.json).

This run supports independent transport recovery and continued healthy-peer delivery. It explicitly does **not** demonstrate zero loss during the induced fault. The corrected physical-reset trial and subsequent fresh clean capture are documented below.

## Corrected right-board reset repeat — recovery PASS, non-clean capture

**07:18:28–07:19:32 UTC:** the repeated 60-second reset trial used external collector **v3**, with causal new-boot recovery timing and observed per-connection server errors. The production receiver/server code remained at **`f058ef0`**. Its saved outcome is **`passed=true`, `expected_fault_evidence_passed=true`, exit 0**, while overall **`clean=false`** correctly records the physical outage. The v3 collector hash is `7b2d62d969cb2ed1f2d6ea2b1f31dc5782da30fa63cb0b033bf0cfedbf28a2c5` in the report; observation/classification changes do not modify production acceptance rules.

The right-board reset began at **07:18:47.392 UTC**. Device 1 remained clean throughout: **602 exact generated/BLE/ACK/result samples**, boot **773972803**, sequences **7517–8118**, with no errors or reconnects. Its maximum ACK gap was **0.188 seconds**, and it produced **137 ACKs** during the right stream's measured **13.765-second** recovery gap.

The right board changed boot from **2683815386** to **2492093553**, reconnected and resumed fresh delivery. The qualifying recovery ACK at **07:19:01.160 UTC** carried the new boot and sequence **1**, rather than an old in-flight ACK. Across the run the right bridge received **470** packets and ACKed/delivered **469** desktop results; the first new-boot sample, sequence **0**, had an ambiguous drop. Its disconnected/changed-boot capture is intentionally non-clean and cannot be reconciled as one uninterrupted source interval. No zero-loss claim is made for the outage.

The server retains **1,071 accepted** and **one rejected** operation. This repeat directly attributes that rejection to a `TimeoutError` on the mapped pre-fault right connection **127.0.0.1:53143**, at **07:18:52.401 UTC**—five seconds after the reset and before causal recovery. The recorded classifier counts **one expected right-fault rejection, zero unexpected exceptions**, plus two normal shutdown EOFs. The rejected counter is not erased or described as zero.

Evidence: [reset-repeat final report and classifier](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-repeat-60s/final-report.json), [complete run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-repeat-60s/run-state.json), [full traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-repeat-60s/traces.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-right-reset-repeat-60s/server-metrics.json). The failed initial reset-run artifacts remain separate and unchanged.

The [independent fault audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/independent-fault-audit.json), generated at **07:23:03 UTC**, passed both the TLS and corrected-reset checks against the literal traces and recorded input hashes. It confirmed healthy-left exact reconciliation, causal recovery and continued peer progress, accepted ACK statuses, deterministic results, and precisely one received-only ambiguous ID in each affected stream. For the reset it independently matched the timeout to the pre-fault right connection. This corroborates recovery acceptance while retaining both non-clean outcomes.

The [local concurrency and reset-recovery chart](D:/LetThemCook-builds/dual-esp-20260919T063318Z/parallelization-evidence.png) visualizes the local 600-second soak and controlled-reset evidence. Its scope is the physical ESPs with the **local** TLS server and desktop collector; it does not depict Ultra96 or native-iPhone acceptance.

## Fresh post-fault 60-second clean capture — PASS

**07:19:59–07:21:03 UTC:** after both fault trials, a fresh **60.000-second common observation** completed with **`passed=true`, `clean=true`, exit 0**. Total capture/cleanup elapsed time was **63.813 seconds**. Both boards used one protected BLE connection and one TLS connection, with no capture exception, cleanup errors or unfinished work.

| Device | Boot | Source interval / received sequence range | Generated / BLE received / ACKed / desktop results | Common-window notifications | Maximum common-window silence |
| --- | --- | --- | --- | --- | --- |
| 1 | 773972803 | **[8119, 8721)** / 8119–8720 | **602 / 602 / 602 / 602** | 600 | 0.188 s |
| 2 | 2492093553 | **[319, 920)** / 319–919 | **601 / 601 / 601 / 601** | 600 | 0.125 s |

Exact source/received/accepted-ACK/desktop-result reconciliation passed for both devices, including first and last IDs. All source failures, identity/sequence/boot anomalies, missing IDs, drops and BLE/transport errors were zero. The server accepted **1,203** samples with zero duplicate/rejected inputs or other server anomalies; its two shutdown EOFs were classified as normal. This finite uninterrupted run establishes clean local operation after the controlled faults, without changing the faults' non-clean verdicts.

Evidence: [final clean report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-final-clean-60s/final-report.json), [complete run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-final-clean-60s/run-state.json), [full traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-final-clean-60s/traces.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/physical-final-clean-60s/server-metrics.json). The [independent final-clean audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/final-clean-audit.json), generated at **07:23:50 UTC**, passed literal source/received/ACK/result reconciliation, accepted ACK statuses and deterministic-result checks with recorded input hashes. Both devices progressed in **all 60 one-second slots** of each received/ACK/result stream; the largest gap was **0.188 seconds**.

## Fresh software regression

A fresh repository-wide `python -m pytest -q` at `f058ef0` completed with **285 passed, 3 skipped, 0 failed**, exit **0**, in **96.53 seconds**. The result was recorded at **07:19:23 UTC** in [software-regression.json](D:/LetThemCook-builds/dual-esp-20260919T063318Z/software-regression.json) from the completed test process. This is software regression evidence, distinct from the physical captures above.

## Remote scope resumed after VPN

After the user reported VPN connected, a **07:02:43 UTC** read-only jump-host probe returned exit **255** with `Permission denied (password)`, rather than the earlier `publickey` result. Preserve both attempts: [post-VPN preflight](D:/LetThemCook-builds/dual-esp-20260919T063318Z/ssh-after-vpn-preflight.json) and [earlier preflight](D:/LetThemCook-builds/dual-esp-20260919T063318Z/ssh-preflight.json). The new result demonstrates that the observed authentication method changed; it is not a completed login or proof that a supplied valid password was rejected.

A separate one-off helper provides strict enrolled-host verification, masked local credential entry, read-only board inspection and an ingestion-only loopback forward. It saves no passwords and starts no remote server or competing result subscriber. The helper's local login window was launched at **07:10:40 UTC**; that first attempt was subsequently cancelled and preserved. The documented saved credential file belongs to the earlier Mac's ignored local directory; no Windows copy was found in the searched locations. After the user supplied credentials, a second attempt used a reviewed terminal wrapper with hidden `getpass` input. Passwords are not placed in files, command-line arguments or output, and strict verification of both enrolled SSH hosts remains enabled.

At **07:23:10 UTC**, the second attempt **authenticated successfully** through `stujump.comp.nus.edu.sg` to `makerslab-fpga-35.ddns.comp.nus.edu.sg` (hostname `pynq`). Read-only preflight verified existing owned server **PID 43932**, its `ultra96.server` command and working directory **`/var/tmp/cg4002-week7-yanjie-20260907/source-db6769a`**, and the same PID's loopback listeners **127.0.0.1:8888 / 9999**. This identifies the deployed server's directory separately from the laptop's `f058ef0` revision; it does not assert that the board checkout was updated. The helper then opened only **127.0.0.1:18888 → board 127.0.0.1:8888**. No competing result subscriber was started. Evidence: [successful remote preflight](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-route-attempt-02/remote-preflight.json) and [route event journal](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-route-attempt-02/remote-route-state.jsonl).

## First actual Ultra96 dual ingestion baseline — PASS

**07:24:11–07:24:45 UTC:** both physical ESPs fed the production laptop dual bridge through the authenticated SSH route and TLS to the actual Ultra96 server. The **30.000-second common observation** finished **clean, exit 0**, with the final JSON saved successfully.

| Device | Boot | Source interval / received sequence range | Generated / BLE received / ACKed | Maximum common-window silence |
| --- | --- | --- | --- | --- |
| 1 | 773972803 | **[8721, 9022)** / 8721–9021 | **301 / 301 / 301** | 0.172 s |
| 2 | 2492093553 | **[920, 1222)** / 920–1221 | **302 / 302 / 302** | 0.187 s |

Both devices had complete clean source audits, no missing source/received/ACK samples, no sequence/identity/boot anomalies, drops or errors, and one BLE/TLS connection each. Each supplied 300 notifications in the common observation window. Evidence: [remote baseline final report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-baseline-30s/final-report.json), [process result](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-baseline-30s/process-result.json), and [live progress](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-baseline-30s/progress.log).

The completed [literal baseline board-log audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-baseline-30s/board-log-audit-frozen.json), at **07:30:32 UTC**, independently **passed**: all **603 expected IDs** appeared exactly once in the accepted log entries, with exact per-device order, no missing or repeated IDs, and no unrelated IDs inside the baseline bracket. The audit records hashes for its captured server-log prefix, offset metadata, CLI report and auditor.

This is actual **two-ESP → laptop BLE → SSH/TLS → Ultra96 ingestion/ACK** evidence. It does not establish native-iPhone result delivery or a per-packet Phone ledger. Both subsequently failed remote soaks are recorded below. A separate counted capture will be used once the native Phone is subscribed and its count baseline is recorded. The installed app needs no further build/install for that test.

## First remote 600-second soak — FAILED, preserved

**07:26:07–07:36:12 UTC:** the first actual-Ultra96 soak completed its **600.000-second common observation** over the one-off Paramiko route, but correctly returned **`clean=false`, exit 1**. No fault was deliberately injected. This is a failed clean-capture acceptance result, not a passing recovery trial.

| Device | Boot | Generated interval | Generated / BLE received / sent / ACKed | Outcome |
| --- | --- | --- | --- | --- | --- |
| 1 | 773972803 | **[9022, 15024)** | **6,002 / 6,002 / 6,002 / 6,002** | Clean; no errors or drops. |
| 2 | 2492093553 | **[1222, 7226)** | **6,004 / 6,004 / 6,003 / 6,003** | **Non-clean:** one stale discard, one missing ACK and one ACK-sequence anomaly. |

Both complete source audits reported zero source failures and zero missing BLE-received samples. Neither device reported a BLE disconnect, transport error, queue overflow, malformed packet or identity/boot change; each used one BLE/TLS connection. Thus the observed loss is downstream of BLE receipt: the right bridge's **`stale_dropped=1`** prevented one sample from being sent/ACKed. The board-log investigation identifies missing ID **`(2, 2492093553, 4599)`** around **07:31:50 UTC**. The failed verdict and missing ID remain part of this session's evidence even if a later repeat passes.

Evidence: [failed remote-soak final report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-soak-600s/final-report.json), [exit-1 process receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-soak-600s/process-result.json), and [progress log](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-soak-600s/progress.log). The exact transport-delay cause is **not established**. Shared Paramiko ingestion/SFTP traffic was an initial hypothesis; the subsequent OpenSSH failure without concurrent downloads does not support it as a sufficient explanation.

The completed [literal board-log audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-soak-600s/board-log-audit-final-failure.json), at **07:39:02 UTC**, independently confirms **FAILED**: **12,006 expected IDs, 12,005 accepted IDs**, with only **`(2, 2492093553, 4599)`** missing, no repeated expected IDs and no unrelated accepted IDs inside the run bracket. It hashes the captured server-log bytes, offset metadata, CLI report and auditor. The complete final snapshot was retained before the owned Paramiko route stopped with exit **0**; that orderly route shutdown does not change the failed capture verdict.

## Standard OpenSSH remote-soak repeat — FAILED, preserved

After the failed run completed, the owned Paramiko route was stopped at approximately **07:37 UTC**. The repeat uses the project's standard `tools.ssh_tunnel.tunnel_command` OpenSSH route, with strict host verification and owned main SSH PID **16656**, forwarding only **127.0.0.1:18889 → board 127.0.0.1:8888**. Its provenance was recorded at **07:37:50 UTC**. No log downloads run during this capture; board logs will be retrieved afterward to isolate ingestion from diagnostic copying.

The separate **`remote-openssh-soak-600s`** capture ran **07:37:51–07:47:55 UTC**, completed its **600.000-second common observation**, and returned **`clean=false`, exit 1**. Production source and freshness thresholds were not changed. Evidence: [OpenSSH route provenance](D:/LetThemCook-builds/dual-esp-20260919T063318Z/openssh-route-provenance.json), [failed repeat report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-soak-600s/final-report.json), [exit-1 process receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-soak-600s/process-result.json), and [progress log](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-soak-600s/progress.log).

| Device | Boot | Generated interval | Generated / BLE received / sent / ACKed | Stale drops / missing ACKs | ACK-sequence anomalies |
| --- | --- | --- | --- | --- | --- |
| 1 | 773972803 | **[15024, 21026)** | **6,002 / 6,002 / 5,997 / 5,997** | **5 / 5** | 3 |
| 2 | 2492093553 | **[7226, 13227)** | **6,001 / 6,001 / 5,973 / 5,973** | **28 / 28** | 10 |

Source generation and BLE receipt remained complete and contiguous, with zero source failures, missing BLE samples, BLE/transport/ACK errors, disconnects, queue overflow or boot changes. Each device retained one BLE/TLS connection; maximum common-window BLE silence was **0.187 / 0.250 seconds**. The progress display's **3 / 10** error counts correspond to source ACK-sequence anomalies, not transport exceptions. The losses are again recorded as pre-send stale discards, totaling **33** samples.

The completed [board-log audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-soak-600s/board-log-audit-v2.json) and [independent full concurrency audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-soak-600s/independent-concurrency-audit-full.json) corroborate **FAILED** clean acceptance: **11,970 accepted IDs out of 12,003 expected**, with exactly **5 device-1 / 28 device-2 IDs missing**, no repeated IDs and no unexpected accepted IDs inside the run bracket. The independent audit verifies the complete post-run byte/offset/hash capture and confirms the IDs actually observed remained in sequence and timestamp order. The frozen auditor's `order_ok=false` denotes failure to equal the complete expected sequence, due to omissions; it is **not evidence of actual reordered reception**.

Both streams nevertheless made board-acceptance progress in **all 599 complete shared UTC one-second bins**, from **07:37:55 through 07:47:53 UTC**. Maximum gaps between observed board acceptance events were **0.998 seconds for device 1** and **1.006 seconds for device 2**. This proves concurrent progress during the measured overlap, not complete delivery: the audit's overall verdict remains failed because the 33 expected IDs are missing.

Because this repeat failed over standard OpenSSH with **no during-run log downloads**, attributing the failure solely to the one-off relay or SFTP traffic is unsupported. Both failed runs remain distinct evidence. Post-run board-log retrieval/audits and the subsequent per-packet stage-timing diagnostic below are complete. The diagnostic identifies ACK waiting and queue aging in the current stop-and-wait sender; it does not isolate the network/server cause of each delayed ACK. No successful long remote acceptance is claimed.

## Per-packet ACK timing diagnostic — failed capture, actionable timing evidence

**07:56:03–07:58:07 UTC:** a separate **120-second** physical diagnostic used standard OpenSSH port **18889**, production revision **`f058ef0`**, and external per-packet stage instrumentation. It completed with **`clean=false`, exit 1**, no capture exception and no trace overflow. It remains a failed delivery run, not a fix-validation result.

| Measurement | Device 1 | Device 2 |
| --- | --- | --- |
| Generated / BLE received | **1,202 / 1,202** | **1,201 / 1,201** |
| Sent / ACKed | **1,098 / 1,098** | **1,091 / 1,091** |
| Stale discards / missing ACKs | **104 / 104** | **110 / 110** |
| Recorded frame-write durations | **0–0.016 s** | **0–0.016 s** |
| ACK-wait p99 / maximum | **0.453 / 2.375 s** | **0.500 / 1.984 s** |
| Maximum queue age when dequeued | **4.188 s** | **3.812 s** |

Source intervals were **[21026, 22228)** for device 1, boot **773972803**, and **[13227, 14428)** for device 2, boot **2492093553**. Both were fully received over BLE with no source failures, BLE gaps, disconnects, transport/ACK errors or queue overflow; each retained one BLE/TLS connection. Nevertheless, sequential waits for individual ACKs allowed queued samples to age beyond the unchanged **two-second freshness limit**. The first stale samples were already **2.016 / 2.187 seconds** old when dequeued. This Windows monotonic clock uses `GetTickCount64()` with **15.625 ms resolution**: recorded writes of 0–16 ms are at the clock's resolution scale, not proof of a precise 16-ms upper bound. They still distinguish the observed local write timing from the multi-second ACK waits and queue aging, without proving which downstream component caused the ACK latency.

Evidence: [diagnostic final report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-ack-diagnostic-120s/final-report.json), [completed run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-ack-diagnostic-120s/run-state.json), [per-packet timing traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-ack-diagnostic-120s/timing-traces.jsonl), and [timing analysis with trace hash](D:/LetThemCook-builds/dual-esp-20260919T063318Z/remote-openssh-ack-diagnostic-120s/timing-analysis.json).

This evidence supports the authorized change: allow a bounded **32-frame ordered ACK window per device**, retaining independent paths, the existing wire contract, the two-second pre-send freshness limit and no replay of ambiguous writes. The chosen window accommodates approximately **2.4 seconds × 10 samples/second** with headroom. The configuration range is **1–64**, preserving legacy default **1** while dual mode defaults to **32**. The implementation and its completed software verification are recorded below; physical revalidation remains separate, and prior failed evidence remains unchanged.

## Bounded ACK window — software and physical revalidation verified

The implementation, three regression-test files, runbook and specification notes are committed locally as **`5d2e06f2ec9b57d6cd7551d6f39d7d683b032aa3`**. Each device now has a serialized sender and FIFO ACK reader with bounded outstanding frames, exact ordered ACK correlation and send-relative deadlines. Freshness remains two seconds, legacy behavior remains window 1, and dual mode defaults to window 32.

Independent review identified and then re-reviewed a cancellation race during transport retirement. The correction invalidates the old connection and accounts every pending/current frame before cleanup awaits, observes still-running workers with bounded cleanup, and prevents late ACKs from mutating retired state. A deterministic cancellation-during-close regression accompanies the correction. The final focused review found **no remaining Important/Critical issue**; this is code-review evidence, not physical acceptance.

The fresh full suite completed **294 passed, 3 skipped, 0 failed**, exit **0**, in **96.41 seconds**, recorded at **08:10:44 UTC** in [software-regression-window32.json](D:/LetThemCook-builds/dual-esp-20260919T063318Z/software-regression-window32.json). It ran against the reviewed candidate before commit; the receipt's hashes for both production files and all three new test files match the subsequently committed files. It includes delayed-ACK overlap, bounded/FIFO behavior, ambiguity/no-replay, peer independence, final-ACK draining, cancellation cleanup and real local TLS coverage.

The separate [window-32 source-provenance check](D:/LetThemCook-builds/dual-esp-20260919T063318Z/source-provenance-window32.json) passed: **26 checked files** match `5d2e06f`, and all **five raw file hashes** in the full-suite receipt match the committed files. The local physical revalidation uses this implementation; it does not silently substitute different production source for the preserved earlier trials.

The frozen external physical collector **`physical_dual_v4_window.py`** changes the earlier v3 collector only to select `ack_window=32`; its SHA-256 is **`224b3a89a4fe6403020c99461ff6daa109df555f5871354aa554cddd6c49f7ab`**. Its [three-second synthetic harness check](D:/LetThemCook-builds/dual-esp-20260919T063318Z/harness-window32-mock-3s/final-report.json) passed clean, exit 0, with **32 exact generated/received/ACK/result samples per device**, **64** accepted in total. This validates the collector/software path with synthetic input; it does not establish physical reception or the remote route.

All earlier artifacts remain attributed to their original revision and outcomes. New physical results at `5d2e06f` are recorded separately below.

## Window-32 local physical baseline — PASS

**08:11:00–08:11:34 UTC:** the first post-change physical baseline completed a **30-second common observation** through the **local** TLS server and desktop result collector, with **`passed=true`, `clean=true`, exit 0**. Production source was **`5d2e06f`** and the v4 collector selected window 32.

| Device | Boot | Generated interval | Generated / BLE received / ACKed / desktop results | Maximum common-window silence |
| --- | --- | --- | --- | --- |
| 1 | 773972803 | **[22228, 22532)** | **304 / 304 / 304 / 304** | 0.140 s |
| 2 | 2492093553 | **[14428, 14729)** | **301 / 301 / 301 / 301** | 0.187 s |

Both devices supplied 300 notifications during the common timed window, had complete clean source reconciliation and one BLE/TLS connection each, with no anomalies or unfinished work. The local server accepted **605** samples with all anomaly counters zero. Evidence: [new-code local baseline report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-local-baseline-30s/final-report.json), [run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-local-baseline-30s/run-state.json), [literal traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-local-baseline-30s/traces.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-local-baseline-30s/server-metrics.json).

This establishes a finite clean local physical run with the new implementation. The subsequent local fault trials and actual-Ultra96 retry have separate outcomes. It does not establish remote zero loss or native-iPhone delivery after the change.

## Window-32 local TLS interruption — recovery PASS, non-clean capture

**08:12:08–08:13:12 UTC:** the new implementation completed a **60-second local** trial with only the right TLS transport deliberately aborted at **08:12:27.441 UTC**, 15 seconds into observation. The recovery checks passed, **exit 0**, while overall **`clean=false`** correctly preserves the induced interruption and ambiguous sample.

- **Device 1:** **602 exact generated/BLE/ACK/desktop-result samples**, boot **773972803**, source interval **[22532, 23134)**, with all anomalies zero and maximum ACK gap **0.125 seconds**.
- **Device 2:** **602 generated/BLE-received samples** but **601 ACKs/results**, boot **2492093553**, source interval **[14729, 15331)**. One ambiguous drop, one ACK error and one transport error were recorded at the forced abort, with two TLS connections and one uninterrupted BLE connection. No other source loss, stale discard or queue drop was reported.
- The right ACK gap was **0.656 seconds**; **six healthy-left ACKs** arrived during the gap, and **451 right ACKs** followed TLS reconnection. The local server accepted **1,203** samples with no duplicate/rejected inputs or other server anomalies.

Evidence: [window-32 TLS-fault report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-tls-60s/final-report.json), [run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-tls-60s/run-state.json), [literal traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-tls-60s/traces.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-tls-60s/server-metrics.json). This is local recovery evidence, not a zero-loss fault result. The completed reset trial, passing independent local audit and completed actual-Ultra96 revalidation follow separately below.

## Window-32 local right-board reset — recovery PASS, non-clean capture

**08:13:21–08:14:25 UTC:** the 60-second right-board reset regression at `5d2e06f` passed the requested recovery checks, **exit 0**, and correctly retained **`clean=false`**. The old/left board remained clean with **601 exact generated/BLE/ACK/desktop-result samples**, boot **773972803**, source interval **[23134, 23735)** and maximum ACK gap **0.125 seconds**.

The affected board changed boot from **2492093553** to **3761642639** and resumed with a causal new-boot sequence-1 ACK at **08:13:58.097 UTC**. Across the trial it received **428** samples and delivered **427 ACKs/results**; the first new-boot sequence-0 sample was ambiguous and was not replayed. The right ACK gap was **18.000 seconds**, during which the unaffected left stream produced **180 ACKs**. The interrupted right capture cannot form one clean same-boot generated interval.

The local server recorded **1,028 accepted and one rejected** operation. The observed `TimeoutError` at **08:13:45.109 UTC**, five seconds after reset, maps to the pre-fault right socket **127.0.0.1:53776** and precedes causal recovery. The classifier retains **one expected right-fault rejection, zero unexpected exceptions** and two normal shutdown EOFs. It does not erase the rejected count or claim zero loss during the outage.

Evidence: [window-32 reset report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-reset-60s/final-report.json), [run state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-reset-60s/run-state.json), [literal traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-reset-60s/traces.jsonl), and [server counters](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-right-reset-60s/server-metrics.json).

The completed [independent window-32 local audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-local-audit.json) **passed all three new-code runs**, checking literal IDs, causal fault recovery, source/runtime hashes and regression provenance. Its SHA-256 is **`975f072628f00d16ba594963f4e0c7c651ea5fc2a5082fb0e0ae88a549e6408d`**. Both protected firmware images remain the earlier `f058ef0` builds; the ACK-window change is laptop-side at `5d2e06f`.

The reset audit explicitly limits its completeness claim: resetting the affected board destroys the old boot's terminal source snapshot. Old-boot received/ACK/result IDs are contiguous and equal through the last **observed** sequence **15481**, but there is no final old-boot source counter proving that this was the last generated sample before reset. The new boot's final `end_next_seq=277` supplies its upper bound. This limitation neither asserts an additional lost pre-reset sample nor permits an uninterrupted zero-loss claim across the reset.

## Window-32 actual-Ultra96 600-second retest — PASS

The new **`window32-remote-soak-600s`** capture ran **08:14:59–08:25:03 UTC**, using the same strict OpenSSH **18889** ingestion forward, with **no during-run SFTP log downloads**. Its reviewed external CLI wrapper retained the ordinary production final-report schema and recorded only bounded per-packet IDs plus receive/write/validated-ACK monotonic events in memory; trace files were written after the production CLI finished. The completed process exited **0**, and the final report records **`clean=true`**, a **600.000-second common observation**, production revision **`5d2e06f`**, physical input and **ACK window 32**.

| Device | Boot | Generated interval / sequence range | Generated / BLE received / sent / ACKed | Peak / final outstanding frames |
| --- | --- | --- | --- | --- |
| 1 | 773972803 | **[23735, 29740)** / 23735–29739 | **6,005 / 6,005 / 6,005 / 6,005** | **6 / 0** |
| 2 | 3761642639 | **[277, 6278)** / 277–6277 | **6,001 / 6,001 / 6,001 / 6,001** | **6 / 0** |

Both per-device source audits are complete and clean. All reported anomaly counters are zero, with one BLE connection and one TLS connection per device. Evidence: [final remote report](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-soak-600s/final-report.json), [completed process receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-soak-600s/process-result.json), [trace state](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-soak-600s/trace-state.json), and [packet-stage traces](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-soak-600s/packet-stage-traces.jsonl).

The [independent stage audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-soak-600s-stage-audit.json) **passed**, checking all **48,024 events**: every expected ID appeared exactly once in received, write-start, write-complete and accepted-ACK stages, with FIFO ACK correlation, bounded outstanding writes and empty final ledgers. The completed trace state reports no overflow and its recorded hash matches the trace. Both devices made ACK progress in **all 599 complete one-second bins** within their shared ACK interval.

Recorded write-start-to-ACK maxima were **0.562 / 0.578 seconds**, with p99 **0.282 / 0.328 seconds**. Approximate received-hook-to-write maxima were **0.046 / 0.047 seconds**. The received hook runs after cross-thread enqueue, so that latter measurement is approximate; all timings retain the Windows clock's **15.625-ms resolution**. This finite run showed a peak of six outstanding frames on each path, below the configured bound of 32.

At **08:26:57 UTC**, the completed [independent board-log audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-soak-600s/board-log-audit-v2.json) **passed**: all **12,006 expected source IDs** appeared exactly once and in per-device order in the actual Ultra96 accepted logs, with **zero missing, repeated or unrelated IDs** inside the run bracket. The post-run [fetch receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-postrun-log/fetch-state.json) confirms completed byte/offset/hash capture and no cleanup errors; the [snapshot ledger](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-postrun-log/remote-server-log-snapshots.jsonl) and [captured server log](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-postrun-log/remote-server.log) preserve the audit inputs.

A second [independent board concurrency audit](D:/LetThemCook-builds/dual-esp-20260919T063318Z/window32-remote-soak-600s/independent-concurrency-audit.json), completed at **08:27:40 UTC**, also **passed** exact reconciliation of all **12,006 IDs**. Both streams made board-acceptance progress in **all 599 complete shared UTC one-second bins**; maximum gaps between board acceptance events were **0.270 / 0.271 seconds**. The audit SHA-256 is **`f8639d0695add3f6383ed327066f026518f1a0858f44f26b86b1836b2d0807fe`**. These UTC board bins are a separate measurement from the laptop's monotonic ACK bins above.

The finite **two-physical-ESP → laptop → actual-Ultra96** clean-acceptance gate therefore **passes** for this 600-second run at the configured 10 Hz per device. Native-iPhone delivery remains a separate unobserved counted test; ACKs and board ingestion must not be described as Phone result receipt. Neither this successful run nor the new implementation changes the earlier failed artifacts.

After capture and log retrieval, the owned OpenSSH forward was stopped with Ctrl+C and local port **18889** was confirmed to have no listener. The board service and VPN were left unchanged.

The [final verification receipt v2](D:/LetThemCook-builds/dual-esp-20260919T063318Z/final-window32-verification-v2.json) **passes all 39 checks**, covering duration/rate/revision, command paths, exact source/stage/board counts, concurrent progress, current source/test hashes and closed-forward cleanup. Its SHA-256 is **`23f0c69782b9c41fa8969b5f6af247ead0ba91170189b5e55c28ee34c17ac7a5`**. The [initial failed aggregation receipt](D:/LetThemCook-builds/dual-esp-20260919T063318Z/final-window32-verification.json) is preserved: it queried a nonexistent top-level local-audit `passed` field instead of `checks.passed`. Version 2 corrects that aggregation lookup; no underlying test or artifact outcome changed.

## Acceptance status and remaining work

| Gate | Status at this checkpoint | Evidence needed |
| --- | --- | --- |
| Old/new protected firmware (`f058ef0`, unchanged) | Both inspections and initial clean captures passed | Runtime IDs and protected source-statistics evidence linked above. |
| Initial local short capture (`f058ef0`) | **PASS — 30 seconds, 302 exact samples per device** | Completed baseline evidence is linked above. |
| Initial local 600-second soak (`f058ef0`) | **PASS — 6,002 / 6,001 exact samples; exit 0** | Collector and independent literal trace audit both passed; evidence linked above. |
| Initial local TLS recovery (`f058ef0`) | **PASS recovery; non-clean capture with one ambiguous drop** | Six healthy-peer ACKs during affected-path gap; do not present this as a zero-loss fault run. |
| Initial local reset recovery (`f058ef0`) | **Corrected v3 recovery PASS; non-clean capture** | 137 healthy-peer ACKs during 13.765-second recovery; one mapped timeout and one ambiguous drop preserved. Initial failed verdict remains separate. |
| Initial post-fault local clean capture (`f058ef0`) | **PASS — 60 seconds, 602 / 601 exact samples; exit 0** | Independent final-clean and fault audits also passed; hashes and literal traces linked above. |
| Software regression | **Initial `f058ef0`: 285 passed / 3 skipped. Window implementation `5d2e06f`: 294 passed / 3 skipped; both exit 0** | Separate versioned evidence and implementation hashes linked above. |
| Initial actual-Ultra96 baseline (`f058ef0`) | **PASS — verified existing server; 30-second dual capture, 301 / 302 source/BLE/ACK samples** | Independent literal board-log audit passed for all 603 IDs; no native-Phone claim implied. |
| First remote 600-second soak (`f058ef0`) | **FAILED — exit 1; right 6,004 generated/received but 6,003 ACKed** | Preserve one stale discard and missing ID; downstream ACK-delay origin remains unproven. |
| OpenSSH remote 600-second repeat (`f058ef0`) | **FAILED — exit 1; 5 left / 28 right stale discards despite complete BLE receipt** | Completed audits confirm exactly 33 missing IDs, no actual reordering and concurrent progress in 599/599 full bins. |
| ACK timing diagnosis / bounded-window implementation | **Diagnostic complete; implementation `5d2e06f` passes review, software tests, provenance checks and physical remote revalidation** | Initial diagnostic remains failed with 104 / 110 stale discards; its evidence is preserved. |
| Window-32 local baseline (`5d2e06f`) | **PASS — 30 seconds, 304 / 301 exact samples; exit 0** | Independent literal audit passed; local server/desktop scope only. |
| Window-32 local TLS recovery (`5d2e06f`) | **PASS recovery; non-clean capture, one ambiguous drop** | Independent audit passed; healthy peer exact for 602 samples, six peer ACKs during 0.656-second gap. |
| Window-32 local reset recovery (`5d2e06f`) | **PASS recovery; non-clean capture, one ambiguous drop** | Independent audit passed; healthy peer exact for 601 samples, 180 peer ACKs during 18-second gap. Mapped timeout and pre-reset counter limitation retained. |
| Window-32 actual-Ultra96 600-second retest (`5d2e06f`) | **PASS — 6,005 / 6,001 exact source/BLE/sent/ACK samples; exit 0** | Stage audit and independent board audit passed: all 12,006 IDs accepted exactly once in order. Both pre-change failed soaks remain preserved. |
| Native iPhone result delivery | Pending separate counted capture | Establish native Phone subscription, record starting count, and compare its increment and displayed IDs with the actual run. |
| Native Phone network/lock recovery and camera/ARKit | Pending, outside the local regression | Observe actual device lifecycle and UI behavior separately. The installed app's latest-result display/count is not a complete per-packet Phone ledger. |

This report records completed evidence and the remaining native-iPhone gates separately. No unobserved gate is treated as passed.
