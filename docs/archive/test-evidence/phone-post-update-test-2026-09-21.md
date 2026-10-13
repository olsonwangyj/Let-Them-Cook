# Updated iPhone receiver physical checks — 21 September 2026

This report records physical checks performed after the operator installed the
updated native receiver from the `main` integration that included revision
`def19dd`. The app itself did not expose a build revision, so installation
provenance is the operator's report. The sender remained the two physical ESPs'
existing generated dummy stream at 10 Hz per device. These checks do not cover
real sensor input.

The server-side observer distinguishes accepted results, queue outcomes and
socket write completion. A server write completion is not a per-ID iPhone
receipt. Phone counts and statuses below are operator observations; no Phone ID
ledger or automated screen capture was available.

## Controlled setup

The operator first reported `Subscribed, Received: 0`. Before any controlled
input, the board observer was deliberately finalized and restarted to begin a
fresh ledger. That preflight rotation can force a subscriber disconnect, so it
is excluded from the captures and from the idle-continuity claim. The fresh
observer then recorded one subscriber claim at 13:33:59.610081 UTC and one
completed SUBSCRIBED response at 13:33:59.611498 UTC.

The session record is
`D:\LetThemCook-builds\phone-recovery-20260921\post-update-session.json`.
It records a TLS 1.3 laptop tunnel, physical protected inputs, an initial Phone
count of zero and the instruction not to tap Connect between the two captures.

## Baseline capture

The 60-second baseline process ran from 13:34:44.645466 to
13:35:48.846388 UTC, including setup and cleanup. Both source intervals were
complete and clean:

| Device | Boot ID | Source interval | Generated | BLE received | TLS ACKed |
|---|---:|---:|---:|---:|---:|
| ESP 1 | 2630146223 | 0–601 | 602 | 602 | 602 |
| ESP 2 | 1137140539 | 0–599 | 600 | 600 | 600 |
| **Total** | — | — | **1,202** | **1,202** | **1,202** |

There were no source gaps, identity mismatches, queue or freshness drops,
transport or BLE errors, unfinished work, or cleanup errors. The independent
stage audit passed, with both devices making ACK progress in all 59 complete
one-second bins and no outstanding writes at the end.

The operator reported `1202 subcribed` with status `Subscribed`. The response
arrived after the resume process had started, and the observation instant was
not independently measured. It supports the baseline count but is not a
time-stamped Phone receipt boundary.

## Quiet interval and resume capture

No sender ran between the capture processes. Their process boundaries were
124.907924 seconds apart. The stronger board measurement spans
**129.286175 seconds**, from the last baseline write completion at
13:35:48.435802 UTC to the first resume write completion at
13:37:57.721973 UTC.

The 60-second resume process ran from 13:37:53.754312 to
13:38:58.456295 UTC, including setup and cleanup:

| Device | Boot ID | Source interval | Generated | BLE received | TLS ACKed |
|---|---:|---:|---:|---:|---:|
| ESP 1 | 2630146223 | 602–1203 | 602 | 602 | 602 |
| ESP 2 | 1137140539 | 600–1203 | 604 | 604 | 604 |
| **Total** | — | — | **1,206** | **1,206** | **1,206** |

The boot IDs match the baseline, and each resume interval starts exactly at the
previous interval's end. Both source streams were therefore contiguous across
the quiet period. The resume capture had the same zero-anomaly result as the
baseline, and its stage audit also passed all 59 complete one-second bins.

The finalized board ledger gives direct evidence that the subscriber did not
churn during the quiet interval. Every one of the 2,408 accepted capture IDs was
written on subscriber generation 1. There was no replacement, second claim,
disconnect, `result_no_subscriber`, queue loss, stale drop or send failure. The
only subscriber end was `server_shutdown` at 13:40:50.823152 UTC, after the
operator's final Phone observation and during the deliberate final evidence
rotation.

The operator's final report was `2408 subscribed`. Starting from the reported
fresh count of zero, this exactly equals 1,202 baseline results plus 1,206
resume results. This is a **pass for aggregate iPhone count and board-side
subscriber continuity after more than two minutes without input**. It does not
establish per-ID Phone receipt.

The operator did not explicitly answer whether Unity remained foregrounded for
the entire interval or whether the status ever flashed between observations.
`Subscribed` is established at the recorded observation points. The board's
single uninterrupted subscriber generation and exact write accounting are
independent of that missing operator detail.

## Finalized server evidence

The post-update ledger finalized successfully with 9,635 events:

- one `subscriber_claimed` and one `subscribed_write_complete`;
- 2,408 each of `result_accepted`, `result_enqueued`,
  `result_send_started` and `result_write_complete`; and
- one `subscriber_ended`, caused by the deliberate server shutdown.

The exact-fate audit passed both capture windows independently: 1,202 of 1,202
baseline IDs and 1,206 of 1,206 resume IDs had exactly one write-complete fate.
There were no accepted IDs outside the supplied capture windows. The finalized
status reports zero callback errors, lost or dropped events, overflow, file-cap
drops and writer errors. Its event file SHA-256 is
`41bc17b9be3366b5bba8800c6bd527325c5bd88b09e93f4ec445a9804eeaec4e`.
The separate `subscriber-continuity-audit.json` passed all 12 stated checks and
records the full-precision monotonic quiet gap of 129.28617471689358 seconds.

Evidence is retained under:

- `D:\LetThemCook-builds\phone-recovery-20260921\post-update-baseline-60s`;
- `D:\LetThemCook-builds\phone-recovery-20260921\post-update-idle-resume-60s`;
- `D:\LetThemCook-builds\phone-recovery-20260921\post-update-finalized-baseline-idle`;
- `D:\LetThemCook-builds\phone-recovery-20260921\post-update-source-comparison.json`; and
- `D:\LetThemCook-builds\phone-recovery-20260921\post-update-session.json`.

The controlled preflight rotation is separately preserved under
`post-update-preflight-rotate`. The final rotation occurred after the Phone
count was recorded. Neither rotation is part of the continuity interval.

## Manual recovery after a Phone VPN cycle

After being asked to disable and restore the Phone VPN, the operator reported
`paused 2408`. The switching action was not separately confirmed or timed.
This observation is saved in `post-update-vpn-pause-observation.json`. Because
the app was paused, the operator used the documented explicit Connect flow,
entered the required credentials and confirmed `Subscribed, Received: 0`
before controlled input. This was a manual foreground recovery; it was not an
automatic reconnect and no packets were sent or measured during the outage.
The VPN switch and its duration were not independently measured.

The subsequent 30-second physical capture ran from 13:45:39.380691 to
13:46:15.518902 UTC, including process setup and cleanup:

| Device | Boot ID | Source interval | Generated | BLE received | TLS ACKed |
|---|---:|---:|---:|---:|---:|
| ESP 1 | 2630146223 | 1204–1522 | 319 | 319 | 319 |
| ESP 2 | 1137140539 | 1204–1505 | 302 | 302 | 302 |
| **Total** | — | — | **621** | **621** | **621** |

Both source reports were complete and clean. There were no source gaps,
identity mismatches, queue or freshness drops, transport or BLE errors,
unfinished work, or cleanup errors. The stage audit passed with ACK progress
from both ESPs in all **30 of 30** complete one-second bins and no outstanding
writes.

The operator then reported `621 subscribed`, exactly matching the capture total
from the fresh count of zero. This is a **pass for manual foreground recovery
and aggregate iPhone count after the requested VPN cycle**. It does not prove
automatic VPN recovery, background operation, outage replay or per-ID Phone
receipt. The finalized server audit later found exactly one write-complete fate
for all 621 expected IDs, all on stable subscriber generation 2.

Capture evidence is under
`D:\LetThemCook-builds\phone-recovery-20260921\post-update-vpn-recovery-30s`,
including the clean final report, 30-bin stage audit and before/after operator
observations.

## Final after-lock 600-second soak

The operator was asked to lock the Phone for 20 seconds, unlock it and use the
explicit Connect flow. Before the soak, the operator reported
`Subscribed, Received: 0 after locking/unlocking`. The actual lock duration was
not independently measured. This establishes the operator-reported start state.

The 600-second physical process ran from 13:49:50.131204 to
13:59:55.362229 UTC, including setup and cleanup. Its common observation window
was 600.016 seconds:

| Device | Boot ID | Source interval | Generated | BLE received | TLS ACKed |
|---|---:|---:|---:|---:|---:|
| ESP 1 | 2630146223 | 1523–7524 | 6,002 | 6,002 | 6,002 |
| ESP 2 | 1137140539 | 1506–7506 | 6,001 | 6,001 | 6,001 |
| **Total** | — | — | **12,003** | **12,003** | **12,003** |

Both device reports were complete and clean, with no gaps, identity mismatches,
drops, BLE or transport errors, unfinished work, or cleanup errors. The stage
audit passed: both devices made ACK progress in all **600 of 600** complete
one-second bins. Each device reached at most seven outstanding writes and ended
with zero. ACK latency p99 was 0.344 seconds for both devices; the maximum was
0.609 seconds for ESP 1 and 0.610 seconds for ESP 2.

`post-update-final-source-summary.json` verifies the same boot ID and adjacent
source intervals for each device across all four post-update captures. Their
combined source total is **15,032 packets**, all generated, received and ACKed
within clean capture reports.

After the soak and before the final server rotation, the operator reported
`12003 subscribed`. Starting from the reported fresh zero, this exactly matches
the source total. The finalized server audit found exactly one write-complete
fate for all 12,003 expected IDs, all on subscriber generation 3. That
subscriber was claimed at 13:49:27.429848 UTC, had no lifecycle change during
the capture, and ended only with the intentional server shutdown at
14:02:35.969719 UTC, after the Phone reply. Its observed board write span was
600.031455 seconds.

This is a **pass for manual recovery after lock, the 600-second connected soak,
and aggregate iPhone count**. The Phone evidence remains an aggregate operator
observation rather than a per-ID receipt ledger.

Soak evidence is under
`D:\LetThemCook-builds\phone-recovery-20260921\post-update-after-lock-soak-600s`.
The finalized board evidence and independent audits are under
`D:\LetThemCook-builds\phone-recovery-20260921\post-update-finalized-recovery-soak`.

That second ledger finalized successfully with 50,505 events: three subscriber
claims, three completed SUBSCRIBED responses, 12,624 each of accepted, enqueued,
send-started and write-complete result events, and three subscriber ends. The
first two ends were peer EOFs between operator actions; neither occurred during
a capture. The final end was the intentional server shutdown after the Phone
count. There were no other result fates, outside-window acceptances or duplicate
IDs. The bounded logger reports zero callback, overflow, loss, file-cap or writer
errors. The event file SHA-256 is
`db40b5673fe0fd38e075f54e188c7c7aef77c900d8e96ab12be9d7c786f8558d`.
The independent recovery/soak audit passed all 17 stated checks; its SHA-256 is
`2403ae9bc53f1afddf347aab616509954971e6cc5724df0b04ee974038bd55bb`.

## Relationship to earlier results

The earlier 109-result Phone shortfall remains unexplained. It is retained as a
historical failure and is not reassigned based on this test.

The separate pre-update idle-resume test lost 16 results while no subscriber
was present. That failure reproduced the old clean-idle timeout behavior and
motivated the receiver fix. The 16 results are not failures in the post-update
captures: the post-update baseline/idle ledger has 2,408 write completions and zero
no-subscriber outcomes.

## Completed acceptance and limits

| Capture | Clean source, BLE and ACK total | Both-device stage bins | Operator Phone count | Exact board write fates |
|---|---:|---:|---:|---:|
| Baseline, 60 seconds | 1,202 | 59/59 | 1,202 | 1,202 |
| Idle resume, 60 seconds | 1,206 | 59/59 | 1,206 increment; 2,408 cumulative | 1,206 |
| Manual VPN recovery, 30 seconds | 621 | 30/30 | 621 | 621 |
| After-lock soak, 600 seconds | 12,003 | 600/600 | 12,003 | 12,003 |
| **Total** | **15,032** | — | **15,032 across fresh sessions/increments** | **15,032** |

All requested post-update physical captures were performed and pass within this
scope. The two finalized ledgers account for every expected capture ID with
exactly one server write completion: 2,408 in the baseline/idle ledger and
12,624 in the VPN/soak ledger. The four clean source reports use the same two
boot IDs and adjacent sequence intervals throughout.
`post-update-final-verification.json` independently cross-checks all four source
and stage audits, the exact event identity sets in both ledgers, all 29 combined
continuity checks and the aggregate Phone counts.

This is not a claim of universal perfect delivery. The Phone evidence is exact
only at aggregate-count level; socket write completion does not prove per-ID
Phone receipt. The earlier 109-result shortfall remains unexplained, while the
separate pre-fix 16-result idle failure remains documented rather than erased by
the passing retest.

The VPN and lock tests used explicit Connect after the app paused. They establish
manual foreground recovery, not automatic background reconnection. The live-only
server does not replay outage packets, and zero loss during an outage is not
promised. A silent network blackhole can remain undetected until the operating
system reports transport failure because no heartbeat was added.

The physical inputs were the approved generated dummy streams at 10 Hz from two
ESP32s. Real sensors, ARKit/camera behavior and model accuracy remain outside
this transport acceptance. Apple unit-test, Xcode build and installed-artifact
logs were not collected in this Windows-led retest; the updated app's build
provenance remains the operator's report rather than an extracted app revision.

After evidence finalization, the replacement board service was left running as
PID 90538 with the same code and TLS ports. The owned ingestion SSH session 3980
and PID 43776 were stopped; the PID was absent and no local listener remained on
port 18889. These cleanup facts are recorded in `post-update-cleanup.json`.
