# Week 7 teacher demonstration — 3–5 minutes

Before speaking, complete the [operator checklist](README.md). Open [the brief](teacher-brief.html) or [printable PDF](teacher-brief.pdf), [packet walkthrough](packet-walkthrough.md), one fresh 100-packet log and the saved 600-second evidence. The pack carries [a recorded 100-packet desktop example](recorded-demo100.jsonl) with [provenance and hashes](evidence-index.json); use the checklist's relative-path audit command if presenting that saved example. Keep password and serial-passkey terminals off the shared screen. Choose the truthful endpoint wording below.

## Talk track

**0:00–0:35 — State what is being demonstrated.**

“Week 7 tests the communication chain using predictable dummy data. This ESP32 sends a fixed packet over protected BLE to the Laptop. The Laptop sends it to the actual Ultra96, which creates a deterministic result for an independent viewer. The values and gesture labels are test data; we are demonstrating transport and correlation, not sensor accuracy or AI inference.”

For the verified desktop mode: “Today's receiving endpoint is a separate desktop subscriber. The final planned endpoint is a real Phone with our teammate's visualizer, which still needs physical integration.”

Use Phone wording only after the device test: “This Phone owns its own SSH connection to the Ultra96, and the received result is displayed here.” State separately whether this is the Python JSON display or the teammate's integrated visualizer.

**0:35–1:15 — Point along the connections.**

“The Laptop's ingestion path and the viewer's result path use separate SSH processes through `stujump.comp.nus.edu.sg`. Ultra96 exposes only SSH on TCP 22. Ingestion port 8888 and result port 9999 are loopback services on the board; the clients reach them through local forwarding. SSH checks both host keys, and the inner TLS connection checks our CA and the service name `ultra96.week7.internal`. The Laptop's bridge receives acknowledgements; results use the independent viewer connection.”

Point to the verified current server source/loopback bindings and the two current tunnel owners. A local port listing alone does not prove execution on the Ultra96.

**1:15–2:00 — Explain one packet.**

“Each BLE notification is exactly 32 bytes at approximately 10 Hz. It contains the `W7` marker, version, device ID, boot ID, sequence number, uptime and eight signed dummy values. For sequence 42, the values are `[-958,-948,-938,-928,-918,-908,-898,-888]`. The Laptop decodes those bytes and sends a length-prefixed `SENSOR_BATCH` JSON frame. Ultra96 validates it, acknowledges acceptance and emits `OPEN`, selected by sequence modulo four.”

Use [the packet example](packet-example.json): “The example trace `1:7:42` means device 1, boot 7, sequence 42. This is an explanatory fixture. In the live run, we inspect the actual boot and sequence IDs.” Confidence `1.0` is a dummy constant, not measured model confidence. BLE's packet fields are little-endian; the network JSON length prefix is four-byte big-endian.

**2:00–3:05 — Run and inspect the live 100.**

Start the prepared protected BLE command from the checklist. Show `subscribed`, a live ACK and its matching result ID. In actual Phone mode, show the Phone's readiness and display and start only the logging bridge sender.

“The ACK tells us that the board accepted the input. The result tells us that the independent viewer received an output. They can arrive in either order because they travel on separate streams, so we compare the complete ID sets. We require 100 unique matches, with no missing, unexpected or repeated result IDs.”

Show the final clean summary and saved-log audit. Report what the current run actually produced. If the run fails, keep that result visible and explain the failing check; the saved successful run remains historical evidence.

**3:05–3:50 — Show sustained evidence.**

“We also ran the protected ESP-to-Ultra96 path with an independent desktop viewer for 600.563 seconds. It produced 5,965 accepted ACKs and 5,965 exactly matching results, exceeding the 5,400 minimum. Both client streams and the Ultra96 acceptance log agree. There was one BLE connection, one ingestion connection and one viewer connection, with no reboot or checked stream/transport errors. One late callback was discarded during shutdown and remains recorded.”

Show the saved soak's audit, not a claim that the current short presentation has run for ten minutes. Maximum recorded ACK/result gaps were 0.375/0.500 seconds; these are stream activity gaps, not synchronized end-to-end latency measurements.

**3:50–4:30 — State the limits and next gate.**

“Separate tests interrupted ingestion SSH, viewer SSH, the Ultra96 process and an automated ESP reset. Fresh data resumed; those fault records correctly remain failures of the clean-run criteria. After the user's later USB reconnection and RESET, a fresh 100-packet check passed in 14.110 seconds, followed by 1,768 matching results over 180.469 seconds. Those captures did not observe a new live USB interruption.”

“The remaining final-path work is a real Phone run and the teammate's visualizer integration, including its ten-minute run and lifecycle behavior. The portable C# core has been compiled and tested; the Unity component and actual Android app still need their target environment. The demonstrated scope is one ESP, dummy values, deterministic results and the measured communication paths.”

## Evidence to have open

| Claim | Source to show | Exact scope |
|---|---|---|
| Fixed packet, framing and deterministic output | [Selected design](../week7-selected-design-2026-09-06.md), [packet walkthrough](packet-walkthrough.md), [codec](../../common/sensor.py) | W7 v1, 32 bytes, eight dimensionless int16 values, 10 Hz; no real sensor/AI claim. |
| Actual board and independent SSH route | [Latest report: board and deployment](../week7-continuation-report-2026-09-07.md#actual-board-and-deployment), current day-of identity checks | Real Ultra96 `source-db6769a`; only SSH TCP 22 is externally reachable. PID 43932 was the last recorded owner and must be revalidated. |
| Portable recorded 100-packet example | [Included JSONL](recorded-demo100.jsonl), [provenance and hashes](evidence-index.json) | 100/100 in 14.110 s, traces `1:738264655:0` through `:99`. Saved actual ESP/Ultra96/desktop evidence; offline audit is not a new physical run. |
| Clean protected 600-second desktop route | [600-second JSONL](D:/LetThemCook-builds/remote-evidence-20260907/remote-protected600.jsonl), [independent audit](D:/LetThemCook-builds/remote-evidence-20260907/independent-evidence-audit.json), [report](../week7-continuation-report-2026-09-07.md#actual-remote-acceptance-evidence) | 5,965/5,965 in 600.563 s; actual protected BLE and Ultra96, independent desktop subscriber. No Phone claim. |
| Stored-bond recovery after reported user actions | [100-packet capture](D:/LetThemCook-builds/physical-followup-20260907/post-action100.jsonl), [180-second capture](D:/LetThemCook-builds/physical-followup-20260907/live-physical180.jsonl), [follow-up report](../week7-continuation-report-2026-09-07.md#user-operated-usb-reconnection-and-reset-follow-up) | 100/100 in 14.110 s and 1,768/1,768 in 180.469 s. Actions preceded first capture; no additional power-loss/reset transition during the later window. |
| Fault recovery and security negatives | [Recorded fault and live protocol checks](../week7-continuation-report-2026-09-07.md#deliberately-induced-faults), [protected firmware evidence](../week7-packet-firmware-evidence.md) | Intentional faults remain `passed=false`; wrong CA/SAN and invalid input rejected. No durable exactly-once or lossless-outage claim. |
| Phone implementation and remaining final requirement | [Phone guide](../week7-phone-runbook.md), [original goal](../week7-development-plan.md), [current acceptance table](../week7-continuation-report-2026-09-07.md#acceptance-status-and-remaining-work) | Runnable Python receiver and tested portable C# core; supplied Unity component is uncompiled here. Actual Phone, teammate visualizer and full physical Gate M remain pending. |

## Likely questions

**Is the data fake?** The values are intentionally deterministic. With `--ble`, they originate on the physical ESP and cross real protected BLE. A synthetic Laptop run is explicitly labelled; it tests the network path without proving BLE.

**Why does the Phone need a tunnel?** Only Ultra96 SSH port 22 is externally accessible. The Phone's own SSH process forwards its local 19999 to Ultra96 loopback 9999, independently of the Laptop's ingestion connection.

**How do you know the received result belongs to this input?** The trace is `device_id:boot_id:seq`. We compare complete accepted-ACK and result sets, and independently compare the board's acceptance log. Equal totals alone are insufficient.

**Does a Phone log prove uninterrupted delivery and no duplicates?** The receiver saves results after duplicate suppression and includes no per-result timestamps. The audit establishes exact saved-ID correlation. A 600-second Phone continuity claim needs a separately timed on-device display/status observation; zero duplicate saved rows cannot establish zero duplicate wire arrivals. The sender's five-second ACK-silence check covers ingestion, not Phone result timing.

**What happens when a connection drops?** Reconnects use bounded backoff. Queues are bounded and stale data is dropped. The viewer receives fresh live results after re-subscription; disconnected results are not replayed. Loss and ambiguous sends stay visible in the counters.

**Is this secure or production ready?** The selected demo uses authenticated BLE bonding, strict SSH host trust and CA/SAN-validated TLS. Production identity, durable storage, certificate lifecycle automation, real inference and full AR behavior are outside this Week 7 contract.

**Does this finish the original Week 7 goal?** The desktop connection evidence is complete for its stated route. The original plan also requires a real Phone and the teammate's visualizer; those must be demonstrated before claiming that final path. The official written course rubric was not available, so this pack makes no grading or rubric-acceptance claim.

**Can you show a restart?** Yes, as a separately labelled fault experiment after a clean baseline, following the owned-process procedure. Successful recovery does not change a fault record into a clean soak.
