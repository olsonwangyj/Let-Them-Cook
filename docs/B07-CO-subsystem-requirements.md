# B07 Communications Subsystem Requirements

- Date: 28 September 2026
- Baseline reviewed: `f94b21323383ffa6a64af478e6b0976c855a7dfe`
- Component: **CO — Communications**
- Status: **Requirements and gap assessment; proposed features are not implemented by this document.**

## 1. Purpose and assessment scope

This document translates the instructor's supplied “Individual Full Subsystem Test” guideline into requirements for B07. It identifies what the current implementation provides, what remains to be built or demonstrated, and the acceptance criteria. The source is the guideline supplied in this conversation on 28 September 2026, together with the earlier video submission instructions.

Scope labels preserve the instructor's wording:

- **Live + Video:** required in both demonstrations.
- **Live only / Video only:** explicitly assigned to that format.
- **Unmarked:** required by the guideline, but its demonstration format is not explicitly stated. Do not assume that it is optional.
- **General:** applies across the relevant demonstrations.

The current system is a working transport baseline, not evidence that every item in the newly supplied guideline is complete. The existing [system report](week7-system-technical-report.md), [testing guide](week7-testing-and-demo-guide.md), and [recording guide](B07-CO-subsystem-video-guide.zh-CN.md) describe that baseline. This document adds requirements; it does not retroactively change historical test results.

## 2. Current baseline and delivery boundary

Two ESP32 FireBeetles independently send protected BLE notifications to the Windows laptop. Each device has its own bridge state, input queue, TLS connection, and acknowledgement tracking. The laptop forwards both streams through an SSH local forward to Ultra96. Ultra96 returns `INGEST_ACK` to the laptop and sends `GESTURE_RESULT` to the native iPhone receiver over the phone's own SSH/TLS connection.

The following properties already exist:

- Two concurrent device pipelines implemented with Python `asyncio`; separate tasks can make progress while other tasks await I/O. This does not imply simultaneous radio transmissions or one CPU core per device.
- A 32-byte BLE sensor packet containing magic, version, device ID, boot ID, sequence number, uptime, and eight signed 16-bit values. The current firmware sends at approximately 10 Hz per device.
- Sequence/source accounting, bounded queues, pipelined ingestion ACKs, BLE reconnection, and saved capture logs/reports through `demo.py`.
- BLE authenticated Secure Connections bonding, TLS certificate/hostname verification, SSH host verification, and length-prefixed TCP framing.
- A foreground iPhone receiver that displays results from both devices. Backgrounding or locking pauses its connection; reconnecting through the settings screen is currently manual.

The current dummy sensor values are **deterministic**, not randomly selected: `value[channel] = seq % 2000 - 1000 + 10 * channel`. The board's dummy gesture is also deterministic: `GESTURES[seq % 4]`. A random boot ID does not make either payload random.

The selected reliability scope remains **no missing data during a clean, connected test at an accepted rate**, with independently reported recovery after a fault. It does not include replaying every sample across a power failure, radio outage, or phone pause. Queues and freshness limits can discard data during faults or overload, and the evidence must report those cases honestly.

An ingestion ACK proves board ingestion, not phone receipt. The [21 September iPhone report](phone-post-update-test-2026-09-21.md) records a ten-minute test with an operator-reported phone count of 12,003 matching the source total. That is historical evidence under those conditions, not a maximum-speed measurement or a per-result receipt ledger on the phone.

## 3. Requirements overview

| ID | Requirement | Current status | Remaining work |
|---|---|---|---|
| CO-01 | Demonstrate both network channels and two concurrent ESP streams | Implemented baseline; retain and revalidate after extensions | Explain the existing route and repeat delivery tests after protocol changes |
| CO-02 | Randomly select editable dummy packets in the actual sensor format | Missing random selection; deterministic fixtures exist | Update firmware, laptop, and board generation/validation together |
| CO-03 | Keyboard → ESP modification → laptop → Ultra96 → phone | Missing application command/response flow; a narrow BLE MTU probe exists | Add downlink messages, correlation, transformation, timeouts, and integration with concurrent uplinks |
| CO-04 | Generate a random dummy AI event at Ultra96 | Missing; gesture currently follows sequence number | Update board generation and supported result validators; rebuild the native iPhone receiver |
| CO-05 | Display measured transmission speed in kbps | Counts and duration exist; selected live output lacks kbps | Measure actual byte counts and time intervals per device and in aggregate |
| CO-06 | Maximize and demonstrate sustainable dual-device speed | Fixed 10 Hz baseline; maximum not established | Add adjustable source rate and perform hardware benchmarking with loss accounting |
| CO-07 | Transfer a file through the BLE communication path | Not implemented; deployment file copying is unrelated | Add chunking, bounded storage, flow control, integrity verification, and interruption handling |
| CO-08 | Use colored, readable packet logs and saved evidence | Live counts/reports exist; selected dual path lacks full decoded packet logging and connection colors | Add decoded/color output and saved evidence while preserving reception performance |
| CO-09 | Prove independent power-reset and out-of-range recovery | Reconnection code exists; full controlled physical evidence still required | Conduct and record both physical faults with independently powered devices |
| CO-10 | Walk through encryption in every channel | Security mechanisms exist; complete rubric-focused video walkthrough remains | Explain actual configuration and verification code for each channel |
| CO-11 | Explain laptop/Ultra96 concurrency using diagrams, FSMs, and readable source | Relevant code exists; complete presentation material remains | Document task ownership, dependencies, and recovery states accurately |
| CO-12 | Preserve correct framing and validation for all message types | Existing TCP framing is implemented | Extend schemas and regression tests for added message types |
| CO-13 | Prepare compliant hardware setup and submission | Launcher and recording guide exist; setup/coverage updates needed | Update documentation, arrange independent power, and rehearse the complete demonstration |

## 4. Functional and demonstration requirements

### CO-01 — Channel operation and concurrent device isolation

**Scope:** laptop ↔ Ultra96 and Ultra96 ↔ phone: Live + Video; two-FireBeetle concurrency: Unmarked; sensor streaming for over one minute: Live only.

The system shall retain successful communications on both network channels and keep two physical BLE connections active concurrently. Receiving, forwarding, acknowledging, and reconnecting one device shall not unnecessarily block the other device's pipeline. The demonstration shall explain BLE GATT notifications, TLS-framed application messages, the selected SSH route, and the separate ACK/result paths.

**Acceptance:**

- Use two independently powered physical FireBeetles with distinct device IDs. Show both connections and both devices' advancing sequence/count information during an overlapping interval longer than one minute.
- For a clean source-audited interval, reconcile each device's generated, received, and board-ACKed records; require no missing records, validation errors, or queue/staleness drops. Report duplicates/retries separately and reject unexplained duplication.
- With the phone subscribed before transmission, compare its count increase with the accepted result total and demonstrate result IDs from both devices. Label manual phone observations as manual; do not infer phone receipt from laptop ACKs.
- Re-run this baseline after protocol changes. A transport-only pass does not satisfy the new keyboard loop, randomization, or file-transfer requirements.

### CO-02 — Random, editable, schema-valid dummy sensor packets

**Scope:** General; the keyboard-triggered use is Live only.

The demonstrator shall provide multiple dummy sensor payloads using the actual sensor/game packet schema and randomly select among them during the demo. It shall be possible to edit the dummy values, rebuild where necessary, and rerun during the live assessment. Real sensor acquisition is outside this task's scope.

**Acceptance:**

- Preserve valid field types, lengths, ranges, device identity, sequence tracking, and boot/session identity. Do not replace structured packets with plain text or a single integer.
- Record the selected fixture or the exact source payload so that a received packet can be compared with what was sent. For keyboard commands, also retain the expected transformed response.
- Show multiple eligible fixtures and the random-selection code. Random choice may select the same fixture repeatedly; every consecutive packet is not required to differ.
- Demonstrate one fixture edit followed by the required rebuild/rerun, and show the updated decoded values downstream.
- Retain a reproducible fixture/seed mode for automated tests as an engineering aid. Remove formula-specific assumptions only when replacement payload validation and tests are ready.

**Implementation impact:** firmware serialization/generation, `common.sensor`, laptop validation/mock inputs, Ultra96 sensor validation, tests, and documentation. A payload-contract update must reach all participating components together; version the contract if fields or semantics become incompatible.

### CO-03 — Keyboard-triggered bidirectional full pipeline

**Scope:** Live only.

Each accepted demo keystroke shall select a random valid dummy packet, send it from the relay laptop to a chosen FireBeetle over BLE, and cause that FireBeetle to modify the payload. The modified packet shall return over BLE, pass through the laptop to Ultra96, trigger a dummy AI event, and reach the phone.

**Acceptance:**

- Define explicit command and response types, target-device selection, request identity, payload format, and a documented modification rule before implementation. The rule must preserve valid field ranges and make verification unambiguous.
- Use individual designated key events rather than waiting for an entire line followed by Enter, and keep keyboard input from blocking BLE reception or network forwarding.
- Demonstrate the complete loop for each of the two ESPs. Show the original payload, the ESP's changed payload, board ingestion, and the corresponding phone event with traceable correlation.
- Maintain both BLE connections while issuing commands. Use bounded command queues and explicit rejection/backpressure if the operator exceeds supported input rate; do not silently drop accepted keystrokes.
- Handle a missing response, wrong device/request ID, duplicate response, and disconnect explicitly. Define whether a timed-out request is retried or failed and prevent duplicate game/event effects.
- Keep BLE pairing/authentication requirements on the new writable path. A working MTU-probe write alone is insufficient evidence of this application pipeline.

**Dependencies:** CO-02 payload contract, CO-04 event contract, CO-08 tracing, CO-12 message validation. Existing independent uplinks must remain usable. This requires firmware and laptop changes, board integration, and coordinated phone validation where the event schema changes.

### CO-04 — Random dummy AI events

**Scope:** part of the Live-only full pipeline.

Ultra96 shall select a random valid event when it accepts a new relevant dummy input. This is a communications demonstration using dummy AI output; no trained AI model is required.

**Acceptance:**

- Select from a documented event set, preserve the input's trace identity, and validate event fields/ranges at every receiver.
- Replace the current `seq % 4` assumption in the board and phone validators consistently. The existing `confidence = 1.0` may remain if documented; random confidence is not required by the guideline.
- A repeated input identity shall not create a second independent random event effect. Define duplicate handling and test it.
- Demonstrate valid randomly selected events on the actual installed iPhone app. Repeated event labels are allowed.

**Implementation impact:** `ultra96/server.py`, `ultra96/protocol.py`, native Swift result validation/tests, and any supported Python/C# consumers. The selected iPhone route requires building and installing the updated native receiver on a Mac when its validator changes.

### CO-05 — Measured throughput statistics

**Scope:** Live only.

Live output and the final report shall show measured per-device and combined throughput in decimal **kbps**. Every metric shall name its measurement boundary and time interval.

**Acceptance:**

- At minimum, report BLE sensor-packet goodput at laptop reception: `unique valid sensor packet bytes × 8 / elapsed seconds / 1000`. Label the numerator as sensor-packet bytes, including the application's packet header, excluding BLE/TLS/SSH overhead.
- Provide a rolling display and a whole-run average with documented timing rules and a monotonic clock. Include zero-traffic periods; separate connection startup and final draining from the steady-state observation interval.
- Report received and board-ACKed counts alongside the rates. Retransmissions, duplicate packets, and protocol overhead shall not silently inflate useful-data throughput.
- Distinguish any additional file-transfer or command rate from sensor-stream rate. If wire throughput is reported, identify which layer and bytes were actually measured.
- Verify byte/time arithmetic with controlled inputs, then record a physical dual-device run.

At the current nominal 10 Hz and 32 bytes, the arithmetic baseline is **2.56 kbps per device / 5.12 kbps combined**, excluding transport overhead. These are calculated nominal rates, not measured results or maximum BLE capacity.

### CO-06 — Maximum sustainable concurrent speed

**Scope:** Unmarked; the complete-pipeline exemption explicitly retains the dual-FireBeetle maximum-speed demonstration.

The project shall provide a controlled method to adjust the actual ESP generation/transmission rate and establish the highest tested sustainable two-device operating point under recorded conditions.

**Acceptance:**

- Record firmware/software revisions, each source rate, BLE adapter, negotiated MTU, relevant connection settings, ACK window, queue limits, device placement, and measurement duration.
- Increase actual source rates in controlled steps and evaluate both devices concurrently. `--expected-rate` currently changes expectations/mock behavior; it does not change the physical firmware's rate.
- Use the CO-05 rate measurements and CO-01 clean-delivery checks. Document device fairness, queue occupancy, errors/drops, and relevant latency measurements at each candidate rate.
- Hold the selected operating point for longer than one minute after startup. Keep the known-good baseline available if the next rate fails.
- Report the highest **tested sustainable** rate and the tested limit/bottleneck. If no failing boundary is reached, call the result a tested lower bound rather than the hardware's absolute maximum.

Performance tuning may involve firmware pacing, BLE connection parameters, MTU, and ACK pipelining. Larger queues or a larger ACK window alone are not evidence of increased source throughput or loss-free operation.

### CO-07 — File transfer and integrity verification over BLE

**Scope:** Unmarked, under two-way FireBeetle communications.

The system shall transfer an actual file through the FireBeetle BLE path and verify that the receiver's reconstructed bytes match the sender's bytes. Copying a deployment file over SSH/SCP does not meet this BLE requirement.

The guideline does not specify file size, direction, or storage medium. The proposed B07 scope is a laptop-to-ESP transfer with authenticated BLE acknowledgement and receiver-computed digest; the exact size/storage limits shall be recorded before implementation. A reverse-direction round trip is an optional stronger demonstration.

**Acceptance:**

- Define transfer metadata and begin/chunk/end messages containing a transfer ID, total length, chunk ordering/offset, and bounded chunk length. Choose chunks that fit the negotiated transport limits or implement explicit fragmentation.
- Transfer a nontrivial file requiring multiple BLE messages. Declare the tested size and enforce supported limits without assuming unlimited ESP RAM or storage.
- Reconstruct the byte sequence at the receiver, either into bounded storage or as an ordered stream, and compare total length and a whole-file digest such as SHA-256. Log both endpoints' results.
- Handle duplicate, missing, corrupted, out-of-order, and interrupted chunks through explicit retry/rejection/abort rules. An incomplete transfer must never print success.
- Preserve the second device's connection and account for its traffic during the file test; record any deliberate mode/rate changes.

Resumable transfer across power loss is an optional extension, not part of the previously selected connected-session guarantee. A clean abort followed by a new verified transfer is acceptable under this proposed scope.

### CO-08 — Readable logs, connection colors, and evidence

**Scope:** General.

The selected dual-device demonstration path shall display distinguishable connection colors and device labels, readable decoded packets, progress, and a final report. Saved logs shall remain useful outside a colored terminal.

**Acceptance:**

- Show timestamps, direction, device identity, message type, sequence/request/transfer identity, relevant sensor/event fields, and validation outcome. Record raw bytes only where they help investigation.
- Describe the integrity mechanisms actually present. Do not label a fabricated field as CRC when the current packet does not carry an application CRC.
- Preserve plain-text or structured logs without ANSI escape noise, along with run configuration, final counters, and process exit status. Continue the simple `demo.py` entry-point approach when adding modes.
- Keep the console readable at high rates using a bounded summary or sampled display. Separate console sampling from packet accounting; report evidence-log overflow if it occurs.
- Do not record passwords, pairing passkeys, private keys, or other secret material in the video/report.

The existing launcher already saves `live.log`, `report.json`, and `exit-code.txt` for captures; these artifacts need extension rather than a second unrelated logging system. Historical single-device packet-printing tools do not automatically provide decoded evidence for the selected dual-device run.

### CO-09 — Independent physical disconnection and recovery

**Scope:** power reset and out-of-range tests: Live only.

The live assessment shall demonstrate loss and recovery of one physical ESP while the other remains connected and productive. Perform power-reset and out-of-range trials separately.

**Acceptance:**

- Use independent power sources. For a power-reset trial, remove power from only the chosen ESP, observe disconnection, restore power, and show reconnection plus its new boot identity and subsequent data.
- For a range trial, walk one powered ESP out of radio range, confirm an actual BLE disconnect, and return it. Keep the other ESP near the relay laptop and the network/phone route available.
- Record fault times, disconnect/reconnect evidence, affected-device downtime, and the healthy peer's continuing reception/ACKs. Radio range depends on the environment; no unsupported fixed-distance guarantee is required.
- Keep fault-run results separate from clean-run acceptance. Missing/unavailable source evidence after a reboot shall be marked unknown/not applicable where appropriate, not converted to zero loss.
- Complete a fresh clean capture after recovery. Do not claim that data produced during disconnection was replayed unless a future implementation explicitly supports and verifies replay.

The existing idle/resume and manual phone lock/VPN recovery tests remain useful additional regressions. They do not replace the two physical ESP fault demonstrations.

### CO-10 — Encryption walkthrough for every communication channel

**Scope:** Video only.

The video shall identify and walk through the actual security configuration and verification code for all three communication links:

| Channel | Existing mechanisms and source to explain |
|---|---|
| ESP ↔ laptop | [BLE authentication policy](../firmware/esp32/include/week7_security.h), [firmware security callbacks/configuration and GATT access](../firmware/esp32/src/main.cpp), and laptop pairing/connection flow |
| Laptop ↔ Ultra96 | [TLS CA/hostname verification and server credentials](../common/tls.py), [SSH host verification and forwarding](../tools/ssh_tunnel.py), and their use by bridge/server |
| Ultra96 ↔ iPhone | Board TLS configuration, native [TLS/client setup](../ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift) and [SSH trust checking](../ios-visualizer/Week7Native/Sources/Week7Transport/Trust.swift) |

**Acceptance:** explain where encryption starts/ends, which peers/keys/certificates are trusted, how incorrect trust is rejected, and where application validation occurs. Show readable code for the checks, not just the names “BLE,” “TLS,” and “SSH.” Preserve those checks on added message paths. Cryptography is provided by the relevant libraries/stacks; custom encryption is not required.

### CO-11 — Concurrency diagrams, protocol FSMs, and source walkthrough

**Scope:** laptop/Ultra96 concurrency code walkthrough: Video only; concurrency block diagram and protocol FSMs: General/video guidance.

The documentation/video shall contain code-aligned diagrams and readable source explaining task ownership and state transitions.

**Acceptance:**

- Draw the two laptop input/queue/forwarding pipelines, their send/ACK tasks, shared resources, and bounded queues. Label exchanged data and any ordering/backpressure dependencies.
- Show Ultra96's connection accept tasks, per-client ingestion work, and subscriber send/monitor work. Explain that an asynchronous task is not necessarily an operating-system thread.
- Explain that the current gateway permits one active phone subscriber and can replace an older subscriber; do not run a desktop result subscriber alongside the iPhone during acceptance.
- Provide FSMs for BLE connection/authentication/subscription/retry, network session/framing/recovery, and phone subscription/pause/reconnect. Extend the diagrams for command/file-transfer states when those features exist.
- Comment the relevant source and show it at readable font size. Explain failure transitions and shutdown as well as the success path.

### CO-12 — Framing, validation, and compatibility

**Scope:** General; applies to existing and added message types.

TCP data shall be parsed as a stream. The existing four-byte big-endian length prefix and bounded JSON frame reader shall continue to handle partial and coalesced reads correctly. BLE commands/files shall have their own explicit size/order rules rather than assuming TCP framing solves BLE fragmentation.

**Acceptance:**

- Verify fragmented headers/bodies, multiple frames in one read, invalid/oversized lengths, malformed payloads, truncated streams, and duplicate or unexpected fields for the relevant implementations.
- Preserve correct idle behavior: a healthy subscribed phone may remain idle without repeatedly reconnecting; a partially received frame must still obey its deadline.
- Update sender, board, phone, fixtures, and tests consistently when introducing message types or changing validation semantics. Document protocol/version compatibility and reject unsupported peers clearly.
- Inventory active Python, native Swift, and Unity/C# consumers before migration; do not update only the primary sender while leaving a supported receiver dependent on deterministic sentinels.

### CO-13 — Setup, deployment, and submission

**Scope:** FireBeetle setup: Video only; device IDs and packet types/formats: Live + Video; power/display/deployment rules: General.

**Acceptance:**

- During the assessed demonstration, neither FireBeetle shall have a USB cable connected to the relay laptop, including a USB data connection while powered separately. Use two independent suitable power sources, such as two power banks that stay on at the devices' low current draw, or an allowed separate power source/laptop.
- Show FireBeetle setup in the video. Programming/pairing can be prepared beforehand, but clearly distinguish prior setup from the fresh live run.
- Explain device IDs and packet types/formats in both the live and video demonstrations. Show successful BLE connection and the data route.
- Keep application services on Ultra96. The current design does not require adding a message broker. If one is introduced, follow the instructor's Ultra96-hosting or reverse-tunnel constraint.
- Preserve the selected SSH route unless deployment changes justify direct TCP. The general guideline permits direct TCP to a reachable Ultra96 server; the present deployment exposes SSH and binds application services to board loopback.
- Name the video **`B07_CO_subsystem.mp4`**, use English narration and readable source, and upload it to YouTube as **Unlisted**. Slides are not required. Chapters are optional.
- Cover all Video/Live + Video items. Plan the Unmarked items explicitly. Do not omit the mandatory encryption and laptop/Ultra96 concurrency code walkthroughs.

## 5. Implementation sequence and dependencies

1. **Freeze the intended packet contracts and evidence boundaries.** Define editable fixtures, command/response identity and transformation, event validation, and the proposed file direction/size. Preserve the tested 10 Hz baseline as a reference.
2. **Add observability and prepare explanations.** Extend decoded/color logs and measured kbps; draft the existing security/concurrency/FSM walkthrough. These are useful early improvements and support later debugging.
3. **Coordinate dummy-data and event changes.** Implement random fixture selection and random board events with matching validators and test fixtures. Rebuild/install the native receiver where required, then repeat clean two-device delivery tests.
4. **Implement the keyboard command/response pipeline.** Add protected BLE downlink, modification/correlation, timeout/duplicate handling, and the complete board/phone path. Test each hop and then both devices together.
5. **Implement bounded BLE file transfer.** Reuse appropriate framing/validation mechanisms while keeping bulk-transfer state distinct from sensor/command state. Verify bytes/digest and interrupted-transfer behavior.
6. **Tune actual source rate and benchmark concurrent goodput.** Use measured rates and loss accounting to select a sustainable operating point. Repeat with the final logging/security configuration enabled.
7. **Perform physical faults and prepare final evidence.** Run power/range recovery with independent supplies, repeat the clean baseline, update diagrams/recording instructions to match the final code, and record the submission.

Documentation, local validators, fixture tests, throughput arithmetic, and mocked fault/framing tests can be developed without two attached ESPs. Actual BLE writes, radio throughput, range recovery, independent-power operation, and the installed iPhone result path require physical verification. Mocked success shall be labeled as mocked.

## 6. Main source areas affected

| Area | Existing source | Expected work |
|---|---|---|
| ESP packets/security/counters | [main.cpp](../firmware/esp32/src/main.cpp), [week7_packet.h](../firmware/esp32/include/week7_packet.h), [week7_source_stats.h](../firmware/esp32/include/week7_source_stats.h) | Random fixtures, rate control, protected command/file handlers, source accounting |
| Sensor/framing contracts | [common/sensor.py](../common/sensor.py), [common/wire.py](../common/wire.py) | Fixture/schema alignment; preserve bounded TCP framing |
| Laptop streams | [bridge.py](../laptop/bridge.py), [dual_bridge.py](../laptop/dual_bridge.py) | Downlink coordination, validation, per-device rates/logging, fairness and recovery evidence |
| Existing BLE write probe | [mtu_probe.py](../laptop/mtu_probe.py) | Reference for current write/notify support; not an existing application command/file protocol |
| Board ingestion/results | [server.py](../ultra96/server.py), [protocol.py](../ultra96/protocol.py) | Random events, matching contracts, duplicate semantics, evidence |
| Native phone | [Protocol.swift](../ios-visualizer/Week7Native/Sources/Week7Core/Protocol.swift), [Week7Client.swift](../ios-visualizer/Week7Native/Sources/Week7Transport/Week7Client.swift) | Result-contract update, tests, Mac build and iPhone installation |
| Other receiver paths | [Python receiver](../phone/receiver.py), [Unity C# receiver](../phone/unity/Week7PhoneReceiver.cs) | Confirm supported paths and shared validation dependencies before migration |
| Demo launcher/evidence | [demo.py](../demo.py), [recording guide](B07-CO-subsystem-video-guide.zh-CN.md) | Simple entry points for new modes, saved reports, final rubric-complete recording instructions |

These are impact areas, not instructions to put all new code into existing large files. Implementation can introduce focused protocol/transfer modules once their contracts are defined.

## 7. Completion evidence and limits

Each requirement shall be marked implemented, physically verified, or still pending separately. Keep a traceability record from requirement ID to code revision, relevant automated checks, physical test artifact, and video chapter where applicable.

For physical runs, save configuration/revisions, source/receiver/ACK counters, decoded traces as appropriate, measured rates, error/drop indicators, and clear pass/fail reasons. Include file length/digest evidence for CO-07 and timed fault/recovery evidence for CO-09. State whether phone evidence is a manual count/observation or an actual captured per-result receipt record.

The instructor allows a successful full-pipeline demo to replace separate channel demos, except for the concurrent two-FireBeetle maximum-speed demonstration. It does not remove the encryption/concurrency walkthrough, packet-format explanation, or applicable setup/reliability requirements.

Do not describe the subsystem as “perfect.” Report that the listed requirements passed at the recorded rates, durations, hardware configuration, and failure scenarios. Do not claim arbitrary-rate losslessness, unlimited buffering, outage replay, or phone receipt solely from an ingestion ACK.
