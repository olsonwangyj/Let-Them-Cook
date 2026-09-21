# Dual ESP32 → Ultra96 → native iPhone test — 2026-09-21

**600-second foreground repeat: native Phone count-level PASS.** Both physical sources generated **6,002 samples each**; all **12,004** were received, sent and ACKed by the laptop, with `clean=true`, and accepted by Ultra96 exactly once in order. The native Unity app's operator-reported count increased from **0 to 12,004**, and the user observed changing gestures and both device-ID prefixes during sending. Independent stage and formal board-log audits passed. Subsequent actual-Ultra96 **device 1 and device 2 transport-recovery tests PASS**, with their intentional fault losses preserved, and the **post-fault clean run PASS** for all **1,209 IDs**. Those three additional runs have no Phone-delivery verdict. The earlier 60-second baseline remains **FAILED at the Phone-count gate: 1,094 / 1,203**, a **109-result shortfall of unknown cause**. Native lifecycle checks remain unobserved; USB screen setup is deferred at the user's request.

This report separates machine-recorded transport evidence from operator observations of the Phone. A laptop ACK or board acceptance log does not prove that the Phone received or displayed a result. These are finite tests under the recorded conditions, not a universal zero-loss guarantee.

## Setup and provenance

- Session began **2026-09-21 05:26:28 UTC / 13:26:28 China Standard Time**. Times below are UTC; add eight hours for local time.
- Reported runtime revision: **`cf1ad08496e71e7c25d5bff4f985c214e7d24db9`** (`cf1ad08`), containing the reviewed bounded-window implementation. The physical capture used **ACK window 32**, the unchanged **10 Hz per-device dummy source**, session **`week7-demo`**, and the default two-second pre-send freshness limit.
- The user reported both laptop/Phone VPNs connected, both ESPs powered, and the installed native Unity app foregrounded. They subsequently confirmed **Subscribed / Received: 0** before the baseline. These are operator observations; no new app build or install was performed for this test.
- Protected BLE identities: old/device 1 **`38:18:2B:19:82:AE`**; new/device 2 **`38:18:2B:18:9D:6A`**. Both advertised the expected service in the session inventory.
- Strict SSH preflight verified the existing Ultra96 server **PID 43932**, hostname **`pynq`**, command `ultra96.server`, working directory **`/var/tmp/cg4002-week7-yanjie-20260907/source-db6769a`**, and owned loopback listeners **8888 / 9999**. The laptop used its ingestion forward on **127.0.0.1:18889**. The board's deployed directory is recorded separately from the laptop revision.
- The native Phone owns its own SSH/TLS result connection to board loopback **9999**. The acceptance target is this installed Unity subscriber, not the historical Python/iSH receiver or a desktop result subscriber.
- Artifacts remain outside Git in [the session evidence directory](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z). Passwords, private keys and BLE passkeys are not reproduced in this report.

Evidence: [session inventory](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/session.json), [verified remote preflight](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-preflight.json), and [operator Phone observations](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-observations.json). The inventory's initial “subscription/count not yet confirmed” state preceded the user's later baseline confirmation. The observation receipt explicitly identifies user text as its source; the assistant did not directly observe the Phone screen.

The [source-provenance check](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/source-provenance.json) **passed for all 26 recorded files** in both the main and observer-import worktrees against revision `cf1ad08` and the prior reviewed inventory. The check records raw hashes separately from normalized content comparisons.

## Foreground baseline — ingestion PASS; Phone count FAILED

**05:27:21–05:28:25 UTC:** the production dual CLI completed a requested **60-second** physical capture, with **60.015 seconds** of common observation. Its process exited **0**, saved the final report, and reported overall/per-device **`clean=true`** with physical input.

| Device | Boot | Generated interval / sequences | Generated / BLE received / sent / ACKed | Common-window notifications | Maximum common-window silence |
| --- | --- | --- | --- | --- | --- |
| 1 | 2922567334 | **[0, 601)** / 0–600 | **601 / 601 / 601 / 601** | 600 | 0.187 s |
| 2 | 3719040663 | **[0, 602)** / 0–601 | **602 / 602 / 602 / 602** | 600 | 0.188 s |

The complete same-boot source intervals reconcile to **1,203 total ACKed samples**, including their first and last IDs. Source submission failures, missing IDs, sequence/identity/boot anomalies, malformed packets, BLE/transport/ACK errors, disconnects, queue/stale/ambiguous drops and cleanup errors were all zero. Each device used one BLE connection and one TLS connection; no work remained unfinished.

The reviewed external instrumentation retained production forwarding decisions and recorded packet IDs and monotonic stages in bounded memory. Its trace state completed with **2,404 / 2,408 events**, **no overflow**, and CLI exit 0. The [independent stage audit](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-baseline-60s/stage-audit.json) **passed** all **4,812 events / 1,203 expected IDs**: exact received/write-start/write-complete/accepted-ACK stages, FIFO ACKs, peak **four outstanding frames per device**, and empty final ledgers. Both devices made ACK progress in **all 59 complete one-second bins**. The audit SHA-256 is **`9c2c68c2a04214f7f689d10ed22193752f01186b9e54c8b676feb0c31c06a682`**.

The completed [formal board-log audit](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-baseline-60s/board-log-audit.json) also **passed**: exactly **1,203 expected IDs**, **601 / 602** per device, appeared in order with zero missing, repeated or unrelated IDs and no audit failures. Its SHA-256 is **`775cd3523c6def50858ceb331e9b4c4d649ce6230531612b9ab0709148db3a1e`**. Root verification matched the audit input hashes and source totals to the clean final report. This audit does not expose subscriber-drop/reconnect metrics or establish that the server had zero errors. It closes the baseline's ingestion/ACK/board-correlation checks, not the Phone-count gate.

Evidence: [baseline final report](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-baseline-60s/final-report.json), [process receipt and initial Phone observation](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-baseline-60s/process-result.json), [live progress](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-baseline-60s/progress.log), [trace state](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-baseline-60s/trace-state.json), and [packet-stage traces](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-baseline-60s/packet-stage-traces.jsonl).

| Phone observation | Current evidence |
| --- | --- |
| Before capture | User reported **Subscribed / Received: 0**. |
| After capture | User reported **Received: 1,094**, **No live result**, and frequent changes among Connecting, Disconnected and Subscribed. The timing of those changes relative to active sending is unknown. |
| Count comparison | Expected **1,203**, observed increment **1,094**, shortfall **109**: **FAILED**. Automatic reconnects retain the count; a new explicit Connect resets it and requires separate accounting. No exact missing Phone ID ledger is available. |
| Displayed identities/gestures | **Unobserved during capture.** The user explicitly said they did not watch during the test. The ending “No live result” observation does not establish whether live labels appeared during sending. |

The installed app maintains an aggregate count of accepted unique results and only the latest result for rendering. Matching the observed count increment establishes **count-level Phone delivery**; it does not create a saved per-device Phone ID ledger or prove every intermediate label was rendered. Board logs independently establish ingestion order, not Phone application receipt.

Idle result clearing and reconnects after sending stops can explain the ending UI state, but do **not** reconcile the 109-result shortfall. The available evidence does not locate those missing results at startup, during a reconnect, or elsewhere on the result path. The failed baseline remains preserved independently of subsequent runs.

The retained [baseline server log](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/baseline-board-log/remote-server.log) contains only **27,368 INFO acceptance records**, with this run's **1,203 IDs at lines 26,166–27,368**; it has no subscriber-lifecycle or delivery-error records, and no server-metrics snapshot was saved, so it cannot locate the 109 missing Phone results.

## Foreground 600-second repeat — transport/stage PASS; Phone count-level PASS

**05:35:20.935–05:45:26.209 UTC:** the separate repeat completed its requested **600 seconds**, with **600.000 seconds** of common observation, exit **0**, and overall/per-device **`clean=true`** on revision `cf1ad08`, ACK window 32. The user confirmed a fresh **Subscribed / Received: 0** before launch. That confirmation was written into the observation receipt at **05:35:44 UTC**; its recording time is not the time of the original observation or the capture start.

| Device | Boot | Source interval / sequences | Generated / BLE received / sent / ACKed |
| --- | --- | --- | --- |
| 1 | 2922567334 | **[601, 6603)** / 601–6602 | **6,002 / 6,002 / 6,002 / 6,002** |
| 2 | 3719040663 | **[602, 6604)** / 602–6603 | **6,002 / 6,002 / 6,002 / 6,002** |

Both devices had zero reported BLE, transport, ACK, identity, sequence, source, drop and cleanup anomalies, one BLE/TLS connection each, empty final queues and no unfinished work. Each had **6,000 common-window notifications**, with maximum common-window silence **0.250 seconds**.

The [soak stage audit](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-soak-600s/stage-audit.json) **passed** all **48,016 events / 12,004 exact IDs**, with peak outstanding frames **seven per device**, empty final ledgers and both devices making ACK progress in **all 599 complete one-second bins**. Audit SHA-256: **`20862342d6215eca17bccfab47c45a156f7fc4b194f7be3c71852955dcd2205d`**. Evidence: [soak final report](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-soak-600s/final-report.json) and [process receipt](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-soak-600s/process-result.json).

The completed [soak board-log audit](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-soak-600s/board-log-audit.json) **passed**: all **12,004 expected source IDs**, **6,002 per device**, were accepted exactly once in order, with zero missing, repeated or unrelated IDs and no audit failures. Audit SHA-256: **`59c1aa025896df912667893cabc1196e9c7743a29422d751da72dda52b404cc3`**. Root independently checked report/stage/board input hashes and the matching Phone observation. As with the baseline audit, this is an ingestion-ID check, not a per-packet Phone ledger or a claim about unexposed subscriber metrics.

During active sending, the user confirmed Subscribed status, an increasing Received count, changing gestures, and many displayed IDs beginning with **`1:` and `2:`**. After capture, without a new explicit Connect, the user reported **Received: 12,004**. The observation receipt records **0 → 12,004**, matching the **12,004 expected results** with **zero count shortfall**: **count-level Phone delivery PASS**, plus operator-observed live output from both devices. This is not a saved per-packet Phone ledger or proof that every intermediate label rendered. No app or production-code change was made between these captures, and the passing repeat does not resolve or replace the failed baseline.

The [immutable soak Phone-observation snapshot](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/phone-soak-600s/phone-observation.json) preserves the initial, active-period and final user reports. The [overall soak verification](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/overall-soak-verification.json) **passed all 12 checks**, including physical/clean capture, exit 0, duration/rate/window/revision, exact 12,004 counts, both audits, matching Phone count and audit-input hashes. Verification SHA-256: **`cfb7a4f321e20c55c60f864640b710323d1719bec475701411f15372970d39ea`**. This receipt retains the same count-level Phone scope.

## Additional actual-route tests — both fault recoveries PASS; post-fault clean PASS

After the user deferred USB setup, the [additional-test preflight](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/additional-tests-preflight.json) found both expected BLE identities/services and verified actual Ultra96 **TLS 1.3** through the existing ingestion forward. It sent no application frames and opened no result subscriber. The completed [test plan](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/additional-test-plan.json) comprised separate device 1 and device 2 transport aborts, each 15 seconds into a 60-second common observation with a 1.5-second reconnect hold, followed by a clean 60-second capture. It forbade replacement of the Phone subscriber and made no new Phone-delivery claim.

The [external fault helper](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote_fault_capture.py) aborts only the selected Bridge's owned TLS transport and delays only its reconnect. Its final reviewed SHA-256 is **`f330da4595d1cabc54f647306869f8213ebd83be07e29476573f42d751eacb53`**. It retains the unchanged production report and raw production exit; supervisor completion is not a recovery PASS. Production revision remains `cf1ad08`.

**Device 1 fault capture completed, 06:42:16–06:43:20 UTC:** common observation **60 seconds**, raw production exit **1**, **`clean=false`** as required for an observed outage. The [final report](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device1-fault-60s/final-report.json) records:

| Device / role | Source / BLE received / sent / ACKed | Transport observations |
| --- | --- | --- |
| 1 / fault target | **601 / 601 / 601 / 599** | Two ambiguous drops; two TLS connections; one transport error and one ACK error. |
| 2 / healthy peer | **604 / 604 / 604 / 604** | One TLS connection; clean with zero reported errors/drops. |

Both used one BLE connection, had zero cleanup errors and finished with no outstanding work. The [fault record](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device1-fault-60s/fault.json) records one successful abort targeting device 1 and a fresh accepted ACK on connection ordinal **2**, sequence **6754**, **1.906 seconds** after injection. The audit confirmed **18 accepted device 2 ACKs** between injection and that fresh ACK, and **450 target ACKs from recovery onward**. The [process receipt](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device1-fault-60s/process-result.json) preserves raw CLI exit 1. The fault-aware recovery verdict is **PASS**; zero-loss and additional native-Phone acceptance are not claimed for this fault.

**Device 2 fault capture completed, 06:43:42–06:44:46 UTC:** the [final report](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device2-fault-60s/final-report.json) preserves **`clean=false`**, with raw CLI exit **1**. Target device 2 generated/received **601**, sent/ACKed **600**, and recorded **one ambiguous drop**, two TLS connections, one transport error and zero ACK errors. Healthy device 1 reconciled **606 source/BLE/sent/ACK samples**. The [fault record](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device2-fault-60s/fault.json) shows recovery after **1.735 seconds**; the audit confirmed **17 healthy-peer accepted ACKs** during that interval and **450 target ACKs from recovery onward**. The fault-aware verdict is **PASS**, with the one missing result preserved.

**Post-fault clean capture completed, 06:45:25–06:46:29 UTC:** the [final report](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-post-fault-clean-60s/final-report.json) has exit **0**, **`clean=true`**, and exact source/BLE/sent/ACK counts **601 / 608**, total **1,209**. Its [stage audit](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-post-fault-clean-60s/stage-audit.json) passed **4,836 events**, with both devices making ACK progress in **all 59 complete one-second bins**.

The completed board-ID audits use the [retained additional-test server log](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/additional-tests-board-log/remote-server.log), **3,913,528 bytes**, SHA-256 **`3a1d96237d7b74db9bb9cdda4bdeef38f9cde8a5748d12e975a5368b67d35345`**:

| Capture | Board accepted / generated | Exact-ID result |
| --- | --- | --- |
| [Device 1 fault](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device1-fault-60s/board-log-audit-final.json) | **1,204 / 1,205** | Missing **`1:2922567334:6753`**. Clean zero-loss criteria fail, as preserved. |
| [Device 2 fault](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device2-fault-60s/board-log-audit-final.json) | **1,206 / 1,207** | Missing **`2:3719040663:7358`**. Clean zero-loss criteria fail, as preserved. |
| [Post-fault clean](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-post-fault-clean-60s/board-log-audit-final.json) | **1,209 / 1,209** | **PASS**, exact complete source-ID set. |

The base auditor's exact expected-order check also fails when an expected ID is absent; that does not establish actual out-of-order receipt. A [first audit-wrapper attempt timed out after 30 seconds](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/board-audit-first-attempt-timeout.json) while the frozen auditor waited for missing IDs. That attempt is preserved. The follow-up used the same frozen auditor's final mode against the immutable completed snapshot, with validation before and after; no physical capture was rerun to replace the evidence.

Both final independent fault-aware audits **passed after review and self-checks**, with earlier drafts retained: [device 1 audit v2](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device1-fault-60s/independent-fault-audit-v2.json), SHA-256 **`6d1b1e5193edea7f8608e3169b36a504501b237cc1d88783e24cb428247abfa6`**; [device 2 audit v2](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/remote-device2-fault-60s/independent-fault-audit-v2.json), SHA-256 **`54a4cb4b60054ea17dc2ed1cfbd738d5ea3993fb8a406d19fe8dd1e7a7c79316`**. Their PASS concerns isolation, recovery and loss accounting; the base clean criteria remain failed for both fault runs. In device 1's run, **`1:2922567334:6752`** was accepted by the board without a received ACK, while **`1:2922567334:6753`** was absent from the board. Device 2's missing ID was **`2:3719040663:7358`**. These reconcile the two-versus-one ambiguous-drop counts without claiming replay or zero loss.

The [independent root ID reconciliation](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/additional-tests-root-id-reconciliation.json) and [final verification](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/additional-tests-final-verification.json) confirm the completed results. Final verification **passed all 29 checks**, including current audit/artifact hashes, exact clean-run **1,209 IDs**, unchanged source revision `cf1ad08`, and closed owned tunnel/PID. Its SHA-256 is **`8f46385a3f852782c14a9d9f6dec1c70cb03d9ae74a76edfe0732e1e15bbb17f`**.

All three captures finished, and [owned-forward cleanup](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/additional-tests-cleanup.json) completed afterward: Ctrl+C stopped owned tunnel PID **31912**, with wrapper exit **1** due to the requested KeyboardInterrupt; port **18889** had no listener and the owned PID was gone. The board server and user VPN were unchanged. No result subscriber was created or stopped, and no Phone observations were recorded for these three runs; they establish no additional native-Phone delivery verdict.

## Post-soak USB inspection — screen access not established

The final count was recorded before USB inspection. No USB change during this soak was reported. Afterward, Windows detected **Apple iPhone** and **Apple Mobile Device USB Composite**. The [pre-install USB diagnostic](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/usb-preflight-before-apple-install.json) recorded an unreachable usbmux service; no Apple Mobile Device service or port 27015 listener was available at that checkpoint. The isolated `pymobiledevice3` **11.15.5** diagnostic environment was installed outside Git.

The [post-install USB receipt at 06:07:41 UTC](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/usb-post-install-pre-reconnect.json) confirms that **Apple Devices 1.1540.24088.0**, from official Microsoft Store product **9NP83LWLPZ9K**, installed successfully and completed onboarding. The Apple USB multiplex service then listened on **127.0.0.1:27015**, owned by **PID 45752**. However, a fresh count-only `pymobiledevice3` discovery still returned **zero devices**, despite the Windows PnP entries; Apple Devices displayed “Connect an Apple device to get started.”

After the user reported reconnecting, the test operator ran a **60-second discovery poll, 06:29:30–06:30:31 UTC**, which still found **zero devices**. The [USB recognition receipt](D:/LetThemCook-builds/dual-esp-iphone-20260921T052628Z/usb-recognition-20260921T063031Z.json) records the initial observation, unchanged final zero-device state and `screenshot_captured=false`. Separate operator checks found **AppleKmdfFilter** and **AppleLowerFilter** running with exit code 0 and the USB device's **ProblemCode 0**; Apple Devices still requested a connected device. The user then reported that the Phone was **already trusted** and requested proceeding with other tests without screen access. USB screen setup is therefore **deferred at the user's request**, rather than awaiting Trust confirmation. No further installation or reset was performed at this checkpoint. No USB screenshot or assistant screen access has been established. These post-soak observations do not alter the completed count-level result. No production app or source code was changed.

The user has been asked to lock the Phone for 20 seconds, unlock it, report the resulting status, then establish a fresh **Subscribed / Received: 0** for a recovery capture. No response or recovery result has yet been recorded, so lock/return remains **unobserved**.

## Soak and lifecycle gates

| Gate | Status | Required evidence |
| --- | --- | --- |
| Protected dual baseline to Ultra96 | **PASS — 601 / 602 exact source/BLE/sent/ACK samples; exit 0** | Independent stage and formal board-log audits passed for all 1,203 IDs. |
| Native Unity foreground baseline | **FAILED — 1,094 / 1,203 reported received; shortfall 109** | Exact missing Phone IDs and cause unknown; active-period rendering unobserved. |
| Longer native-Phone foreground soak | **PASS at Phone count level — 0 → 12,004 / 12,004** | Source/BLE/sent/ACK, independent stage audit and formal board-log audit passed; both live device prefixes observed. |
| Actual Ultra96 device 1 transport recovery | **PASS — isolation/recovery; intentionally non-clean** | Healthy peer 604 exact; target recovered in 1.906 s; one board-missing ID and one board-accepted/unACKed ID accounted for. No additional Phone verdict. |
| Actual Ultra96 device 2 transport recovery | **PASS — isolation/recovery; intentionally non-clean** | Healthy peer 606 exact; target recovered in 1.735 s; one board-missing ID accounted for. No additional Phone verdict. |
| Post-fault clean actual Ultra96 capture | **PASS — 601 / 608, total 1,209 exact IDs** | Clean source/BLE/sent/ACK/stage/board reconciliation; exit 0. No additional Phone verdict. |
| Native lock/background/return | **Pending** | Observed pause/cleared live result, password re-entry, fresh subscription and new results after return. |
| Native foreground network recovery | **Pending** | Recorded network interruption/restoration and fresh post-return progress. Opening system VPN/Wi-Fi UI can also deactivate Unity and must be identified as a combined lifecycle test. |
| Camera/ARKit behavior | **Unobserved** | Direct device observation; transport success does not establish this behavior. |

The native app deliberately stops reception and clears credentials when deactivated or locked. Returning requires explicit Connect with passwords again; background survival is not the expected behavior. Live results clear after two seconds without a fresh result. Once the session has received its first result, five seconds of input silence can trigger expected network reconnects while retaining the count. Those quiet-tail reconnects must be distinguished from faults during active sending.

At this completion boundary, the foreground count-level soak and additional transport tests are complete, with owned-forward cleanup verified. The failed baseline remains unresolved; native lock/return, network recovery and camera/ARKit behavior remain unobserved, and USB screen setup is deferred. Earlier [September 19 dual-to-Ultra96 evidence](D:/LetThemCook/docs/dual-esp-physical-test-2026-09-19.md) remains separate and did not establish native-Phone delivery.
