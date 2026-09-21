# iPhone recovery and result diagnostics — 21 September 2026

This is the diagnosis and software-fix record. The subsequent
[updated-receiver physical report](phone-post-update-test-2026-09-21.md) records
the completed idle/resume and manual-recovery checks, including the final
12,003-result ten-minute run. Pending steps below describe the earlier handoff.

This follow-up uses the two physical ESPs' existing generated dummy packets at
10 Hz each. Real sensor integration is explicitly outside the requested scope.
The earlier [full-system report](dual-esp-iphone-test-2026-09-21.md)
remains a separate record: its 12,004/12,004 iPhone soak passed, while its first
1,094/1,203 iPhone run retains an unexplained 109-result shortfall.

## Lock, unlock, then Connect

The operator was asked to lock the iPhone for about 20 seconds, unlock, and
return to Unity. The reported state was `paused`. This agrees with the current
native app's deliberate lifecycle behavior: leaving the foreground stops the
connection and clears credentials, so the operator must tap Connect again.
The requested lock interval was not independently measured.

After the operator confirmed a fresh `Subscribed, Received: 0`, the existing
frozen physical capture ran for a common 30-second interval, from
07:48:35.844897 to 07:49:10.505071 UTC including setup and cleanup.

| Boundary | ESP 1 | ESP 2 | Total |
|---|---:|---:|---:|
| Generated, BLE received, TLS sent, validated ACK | 306 | 302 | 608 |
| Board accepted exactly once, in per-device order | 306 | 302 | 608 |
| Operator's final iPhone count | — | — | 608 |

Both ESP streams were clean, with zero gaps, queue/stale drops, transport/BLE
errors or cleanup errors. The independent stage and board audits passed.
The operator's exact final reply was `608 , for now no IDs`. No IDs after sending
stops is consistent with the existing two-second live-display expiry. This
reply does not establish that the operator watched IDs during the run.

Result: **manual recovery after lock passes at aggregate iPhone-count level**.
There is no saved per-ID iPhone receipt ledger. This does not demonstrate
automatic reconnection after backgrounding or recovery of data during an outage.

Evidence is retained under
`D:\LetThemCook-builds\phone-recovery-20260921\phone-after-lock-30s`:
`final-report.json`, `packet-stage-traces.jsonl`, `stage-audit.json`,
`board-log-audit.json`, and the before/after `phone-observation` records.
The board audit consumes an immutable fetched log with SHA-256
`63bf5ab1e2c5ee75cf48e44028620a90864adb17aa36dbf75b0d732ed3f4737e`.

## Optional server diagnostics

The server changes add an opt-in `--event-log-dir NEW_DIRECTORY` argument.
Diagnostics record subscriber generations and accepted result identities through
queueing, expiry, overflow, connection retirement, and write completion or failure.
A server write completion is explicitly **not** proof of iPhone receipt.
Payload values and credentials are excluded. The queue and output size are
bounded; overflow, write failures, or incomplete shutdown invalidate the record.

The transport remains live-only, with one current subscriber, a 32-result queue,
a two-second freshness limit, and the existing ACK protocol. Default invocation
does not enable the new log. This instrumentation improves fault localization;
it does not retroactively explain the earlier 109-result shortfall.

The idle-resume test below reproduced a receiver issue. Its native fix now passes
portable Swift tests; the user still needs to build and install the updated app
on their Mac before the physical retest.

Software verification: the full Python suite passed **322 tests, with three
platform skips**. After the last logger hardening and a regression for late
filesystem publication, the focused server/diagnostics suite passed **29 tests**.
The deployment helper's offline contract check also passed. Receipts and exact
source hashes are in `code-verification-v2.json` and the deployment records under
the evidence root.

At 08:08 UTC the tested package was deployed to the owned Ultra96 source directory
`/var/tmp/cg4002-week7-yanjie-20260907/source-observer-20260921T080754Z`.
The candidate passed an isolated TLS smoke check on ephemeral ports and produced
matching complete logger/file receipts before the previous owned server PID
43932 was stopped. Replacement PID **77743** passed TLS verification on the
existing loopback ports 8888 and 9999. The laptop's existing ingestion tunnel also
verified TLS 1.3 after the handoff. All uploaded Python files matched the locally
tested manifest. Old source and evidence were preserved; rollback was prepared
but was not needed.

Further live recovery tests await the updated iPhone app; this file does not
claim they pass. Server diagnostics initially wrote to the exclusive directory
`evidence/observer-live-20260921T080754Z` under the same owned deployment root.

## Instrumented 60-second baseline

After the operator confirmed a fresh connection with `done`, the physical capture
ran from 08:22:46.912448 to 08:23:51.053581 UTC, including setup and cleanup.
ESP 1 generated/received/sent/ACKed **603** packets; ESP 2 **601**, for **1,204**.
Both streams were clean, with zero gaps, drops, transport errors or cleanup errors.
The independent stage audit passed, with ACK progress from both ESPs in all 59
complete one-second intervals.

A read-only snapshot of the running board's diagnostic log contained exactly one
acceptance, enqueue, send-start and write-complete event for every expected ID.
All 1,204 writes belong to subscriber generation 78. The operator subsequently
reported **1,204**, matching the complete source total. The finalized ledger and
matching server shutdown receipt also passed independent validation. This is a
**pass at aggregate iPhone-count level**; no per-ID phone ledger was collected.

The first snapshot attempt failed during jump-host SSH banner negotiation before
reading any remote file. A separate read-only check found the jump host reachable
and the existing ingestion forward still using TLS 1.3; the second snapshot
attempt succeeded. Both attempts are preserved. This error occurred after the
physical capture completed and is not a failure recorded by its packet trace.

Evidence directories under `D:\LetThemCook-builds\phone-recovery-20260921` are
`observer-phone-baseline-60s`, `baseline-observer-snapshot` (incomplete attempt),
and `baseline-observer-snapshot-retry` (complete live prefix snapshot).

## Idle-resume failure: 16 results arrived without a subscriber

The next capture started at 09:34:31.520743 UTC, 4,240.467 seconds after the
previous capture ended. No manual Connect was requested. The operator confirmed
Unity had stayed on screen and reported a final count of **1,800**, with status
cycling between Subscribed, Disconnected and Connecting.

The capture used a common 30-second observation window and finished at
09:35:06.622192 UTC including cleanup.
ESP 1 generated/received/sent/ACKed **311** packets and ESP 2 **301**, totaling
**612**, with both streams clean and all 29 complete one-second intervals showing
ACK progress from both devices. The phone count increased by **596**, leaving
**16 missing results** in this run. This is a failed idle-resume phone check,
even though laptop ingestion passed.

ESP 2's boot identifier changed from `3719040663` in the baseline to `3951396182`
in this capture, and its sequence restarted at zero. The reset's time and cause
were not observed; no controlled reset was injected. Both captures were clean
within their own source windows, but the gap is not a measured ESP reboot test.
The missing identities were ESP 1 boot `2922567334`, sequences 9320–9332 (13),
and ESP 2 boot `3951396182`, sequences 0–2 (3). The complete identity list is saved
as `observer-finalized-baseline-idle/idle-missing-result-identities.json`.

The finalized server ledger accounts for every expected ID: **16** terminal
`result_no_subscriber` events and **596** `result_write_complete` events, all
writes on subscriber generation 453. The first acceptance was at 09:34:35.260933
UTC; the first completed phone-connection write was at 09:34:36.472244 UTC.
The operator's count increase exactly matches the written total. There were no
unexplained IDs, duplicates, diagnostic overflow, logger errors, queue expiry or
queue drops in these captures.

The native receiver's timer explains this behavior. After the first valid result,
it imposed a five-second deadline even before the next frame's first byte.
Healthy quiet connections therefore closed and entered retry backoff. In the
baseline log, quiet subscriptions lasted about 5.06 seconds; later retry/setup
gaps were about six seconds. Restarting producers during such a gap loses results
because the selected live-only server does not replay them. The fix separates
idle waiting from the incomplete-frame deadline. This reproduction identifies
the 16-result failure; it does **not** retroactively prove the cause of the earlier
109-result shortfall.

At 09:39:53 UTC the owned diagnostic server was stopped gracefully to finalize
its evidence and restarted with fresh diagnostics as PID **84751**, with the
same source, certificate and loopback ports. The completed capture is stored in
`observer-finalized-baseline-idle`: **8,669 events**, complete matching caller/file
receipts, zero lost events, SHA-256
`9a0922ed153e1ee37a2eae6278f95158e33fc4c8856bd4685a0c97924cd62596`.
`exact-fate-audit.json` passes exact accounting for all **1,816** accepted IDs:
1,800 writes and 16 no-subscriber outcomes. Accounting PASS does not change the
idle-resume phone test's failure. Fresh remote diagnostics use
`evidence/observer-live-20260921T093930Z` under the same deployment root.

## Native idle fix and software verification

The receiver now keeps a healthy subscription open between complete frames,
including before the first result. The first byte of an incomplete result starts
one five-second frame budget; later fragments cannot extend it. A coalesced next
partial frame receives its own budget. Complete frames cancel the timer.
Connection setup remains bounded to ten seconds, and the SUBSCRIBED response
still has its five-second deadline. EOF and transport errors retain reconnect
and capped backoff. Credential clearing on pause, foreground-only operation,
the wire protocol and two-second display expiry are unchanged.

No heartbeat was added. A silent network blackhole can remain undetected until
the operating system reports transport failure. This fix does not promise
replay during outages or automatic background recovery.

The unchanged production code failed the new regressions: **57 tests, eight
expected assertions across three cases**, exit 1. The updated code passed
**54 of 54 tests**, exit 0. Three obsolete tests for an unused deadline-policy
type were removed with that type. The new tests cover clean idle/resume,
first-byte timing, non-extending fragments, coalesced frames, bounded subscription
startup and reconnection after a real local transport close. Independent code
review found no important or critical issues. The iOS export patch checks also
passed **18 tests**.

Swift evidence is in `D:\LetThemCook-builds\native-idle-fix-20260921`.
Both runs used official Swift 6.2.3 on Linux with all eight exact repository
dependency versions and revisions. The 12 included source/test files match the
verified repository bytes. The harness ran Core and Transport; it excluded Apple
Bridge/UI/Xcode and macOS-only PythonBoardTests. These results do not establish
an Apple build or delivery by the updated app on a physical iPhone.

- RED log SHA-256: `d539f7e538b1128abbc4f605b1b945ba246043378825b5d7c832f732e36b51c8`.
- GREEN log SHA-256: `69c7613991b6110c73526f49f6bd17b34660fe66af124869c77675a4527532d0`.
- Receipts: `red/verified-result.json`, `green/verified-result.json`,
  `green-current-snapshot-verification.json`, `root-independent-verification.json`.

## Handoff and remaining physical checks

Use the [Mac update instructions](phone-idle-fix-mac-handoff-2026-09-21.md) to
pull the receiver fix, run the full native suite on macOS, rebuild, sign and
install the Unity app. No ESP firmware update is required for this fix.

After installation, run a fresh two-ESP baseline, leave Unity foregrounded
through a quiet interval, then resume sending without tapping Connect. Compare
the phone count increment with exact source/board totals and record whether the
subscription remained stable. Also repeat VPN recovery, lock/unlock with explicit
Connect, and a final continuous two-ESP run. Outage results remain separate from
connected lossless-delivery acceptance. Camera/ARKit and real sensors are not
part of this dummy-data transport verification.

The owned laptop ingestion SSH tunnel was stopped after testing; PID 39404 and
the 127.0.0.1:18889 listener were confirmed absent. Test containers were removed;
the Swift image cache was retained. The Ultra96 service was left running as
PID 84751, as verified at the last server handoff. Evidence and failed runs were
preserved. Receiver fix `724f399` and these reports are included in the `main`
integration; the Mac must pull the update and install a newly built app before
the physical checks can resume. The earlier ZIP remains a pre-integration
snapshot, rather than the current Git update instructions.
