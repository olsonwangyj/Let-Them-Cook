# iPhone recovery and result diagnostics — 21 September 2026

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

No native iPhone code has been changed for this follow-up. If a later receiver
change becomes necessary, the user will build and install it on their Mac.

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

Further live recovery tests are in progress; this file does not yet claim they
pass. Server diagnostics initially write to the exclusive remote directory
`evidence/observer-live-20260921T080754Z` under the same owned deployment root.
