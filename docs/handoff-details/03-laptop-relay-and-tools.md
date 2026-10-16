# Detail chapter 3: Laptop relay and operator tools

> This is a detail chapter of [`../communications-handoff.md`](../communications-handoff.md). It describes protocol version 3 as built on the branch `comms/protocol-v3` at `4c6ab4c` (2026-10-16; merged into `main` and pushed to the fork on 2026-10-16, where both are at `e555f77`, whose code is that of `4c6ab4c`; its code-only copy `comms/protocol-v3-team`, at `44d0f71`, is the team pull request #19, not merged; hand-off document, section 6.2). The version-3 work of 2026-10-14 is `a34c467` (core), `57a3fbd` (all components, tools and tests), `a4b907b` (review fixes), `3b94990` (the Linux deploy test from a Windows checkout and the specification rename) and `15de82e` (deploy tool SSH errors, `paramiko` listed). The work of 2026-10-15 is `6583f9d` (the Swift package builds on Linux), `5d2e52f` (movement gating, 36-byte source statistics, the Ultra96 ingest idle limit, `tools/export_capture.py`), `17012b8` (merge of team main `51593be`: Siqiang's glove sensor module), `e24f8ea` (his module built into the `-glove` firmware environments, `tools/sync_glove_module.py`) and `d582ce6` (`flash.py --glove`). Early on 2026-10-16 (+08:00) the branch gained `4c6ab4c`: the capture report's source fingerprint also covers the copies of Siqiang's module, with a test, and the copies' `README.md` is corrected. Every line number in this chapter was re-read at `d582ce6`; `4c6ab4c` changed only `laptop/reporting.py`, `tests/test_laptop_controls.py` and that `README.md`, and the `laptop/reporting.py` citations were re-read at `4c6ab4c`. Later on 2026-10-16 the Swift client was built and tested on the owner's Mac (steps 3 and 4 of section 6.3 of the hand-off document, in a separate clone at `e555f77`, whose code is that of `4c6ab4c`); in this chapter that run changed only the statements on the Swift build status, and it changed no laptop code. That run's only file change besides the documents, one line in the Unity export's `Package.resolved` (its stale origin hash), is in the commit with these documents, which is not pushed. The "not pushed" notes under "History and removed items" give the state at the time. Earlier copies of this chapter describe the 24-byte statistics of 2026-10-14 (code at `3b94990`) or the 32-byte version-2 code (local `main` `dc582c7`, with no laptop, `common/` or tool change up to `c42b386`); the fork's history was rewritten on 2026-10-14 to drop attribution lines (hand-off document, section 6.2), so the oldest copies cite `dc582c7` as `25fe4e4`. Status words follow section 6.5 of the hand-off document: **verified** (run or measured; the place is named), **built** (compiled and tested on the laptop only), **written, not compiled**, **provisional** (waits for a teammate). Nothing of version 3 has run on the Ultra96, on the phone, or with both gloves together. The movement gating and the `-glove` firmware are built; neither has run on a board. The code is the source of truth: where this chapter and the code disagree, follow the code.

## Role and boundaries

The laptop is the BLE central for both ESP32 boards. It is also the TLS client of the Ultra96 ingest service. It does four things:

1. It scans for and connects to both boards with `bleak==3.0.1` (the WinRT backend on Windows). It confirms that Windows already holds a bond at the "encryption and authentication" level.
2. It subscribes to each board's sensor notifications. Each notification is one 38-byte version-3 packet.
3. It turns each packet into one `SENSOR_BATCH` JSON frame and sends it over TLS to the local SSH forward port. SSH carries it to `127.0.0.1:8888` on the Ultra96. The laptop checks the `INGEST_ACK` for every frame.
4. It reconciles the counts and keeps evidence. Three numbers must be equal: the samples the board generated, the samples the laptop received, and the samples the Ultra96 acknowledged.

Boundaries:

- On the laptop leg, Communications ends at the Ultra96's `INGEST_ACK`. The ACK proves only that the ingest service on the Ultra96 accepted this packet (evidence level 3, see section 4.7 of the hand-off document). It does not prove that a model ran on the sample, or that the phone received a result.
- Gesture results do not come back to the laptop (`laptop/bridge.py:1`). The phone connects over SSH to port `9999` on the Ultra96 by itself.
- The laptop does not pair the left and right gloves, does not build model windows, and does not decide between gesture and idle. These are Wen Ree's work. Whether a glove sends a sample at all is decided on the glove by Siqiang's movement detector, which the Communications firmware calls (since 2026-10-15; built, not yet run on a board); the laptop only reads the result in the source statistics. Each board uses its own path. The only thing that tells the boards apart is the packet's `device_id` (1 = left, 2 = right). Who does what at each hand-over is the table in section 3.1 of the hand-off document: Communications moves data correctly and does nothing else.
- The laptop forwards the int16 values exactly as the board packed them and does not convert them to floats. The owner's direction (2026-10-14), final when Wen Ree confirms: the model gets the 11 values as physical floats, transport stays int16, and Communications restores the floats on the Ultra96 (decode, divide by the scale) before it calls the model's `on_sample`. Any normalisation is Wen Ree's (hand-off document, sections 3.1 and 7.2). Built on 2026-10-14: `physical_values` in `common/sensor.py:92-98` divides each value by its scale, and the model interface calls it at `ultra96/model.py:155`. Not deployed; the function names are provisional until Wen Ree confirms them (see [chapter 4](04-ultra96-service-and-certificates.md)).
- The connection path is settled. The laptop connects to the local forward port. OpenSSH takes two hops, `stujump:22` and `Ultra96:22`, to `127.0.0.1:8888` on the Ultra96. `BridgeConfig.host` accepts only `127.0.0.1`. Any other value raises an error at construction (`laptop/bridge.py:55-56`).

### Relation to the teammates' interfaces

The laptop code calls no teammate function. Section 7 of the hand-off document holds the three interfaces to connect (the glove sensor module, the entry and exit points of the model on the Ultra96, and the bridge functions the game calls: `CommsStart`, `CommsCopyDisplay`, `CommsStop` and the per-result function `CommsNextResult`). It also holds what must be confirmed with Siqiang, Wen Ree and Jie Ling. This chapter does not repeat them.

**What exists (branch `comms/protocol-v3` at `4c6ab4c`, 2026-10-16).** The Communications side of sections 7.1 and 7.2 is built and tested on the laptop: the 38-byte version-3 packet on every component; the firmware's glove interface `comms_glove.h` (`gloveBegin`, `gloveUpdate`, `gloveRead`, `gloveShouldSend`) with a built-in dummy module, scaling of each sample that is read and MOVING, and sending only while the glove module reports MOVING; the 36-byte source statistics that report the skipped ticks; the model interface on the Ultra96 (`start(emit)`, `on_sample`, the thread-safe `emit`, `--model`) and its ingest idle limit; model labels with real confidence in `ultra96/protocol.py` and `phone/receiver.py`. The C# reference `phone/unity/CommsPhoneCore.cs` compiled and its self-test passed (113 checks, PowerShell 7); it was compiled at C# 7.0 against the .NET 10 libraries, not Unity's .NET Standard 2.1, and the Unity file `CommsPhoneReceiver.cs` was checked by reading only. The Swift client, with its checks and `CommsNextResult` (7.3), compiled and tested on Linux in a Swift 6.1 container (72 tests, every test that builds on Linux; the macOS-only `PythonBoardTests` and the iOS-only sources, `IntegrationController.swift` and `SetupViewController.swift`, were not compiled there). On 2026-10-16, on the owner's Mac, it passed 73 tests on macOS (`PythonBoardTests` included), its preview app built for the iOS Simulator (compiling the iOS-only sources) and passed 34 transport tests and 1 UI test, and the Week 7 Unity export built with it as an unsigned iPhone app; that app is not signed or installed (see [chapter 5](05-phone-and-week7-receiver.md)). **On the teammates' side, only Siqiang's sensor module exists.** He pushed it to the team main on 2026-10-15 (`51593be`, `hardware/gloves/integration_files/`). The firmware builds byte-identical copies of it in the `firebeetle32-left-glove` and `firebeetle32-right-glove` environments: built (compiles and links); not run on a glove. There is no model module and no game script calling the bridge. **Nothing of version 3 is deployed on the Ultra96 or the phone:** the Ultra96 should still run the 28 September version-2 code and the phone the Week 7 build (session `week7-demo`). **No board runs the current firmware.** The left board runs version 2. The right board should still hold the 2026-10-14 version-3 build with 24-byte statistics; it was unplugged before the gated build could be flashed, and that flash may have been interrupted, so its state is not certain. The current laptop code refuses both at connection (hand-off document, section 6.3). Finished documents are not finished integration (hand-off document, section 1). The dates the teammates are asked for, and the owner's own plan up to the in-person integration session on Tue 2026-10-20, are in section 6.4 of the hand-off document.

Below are only the technical constraints that the laptop-side code imposes.

- **int16 range.** A version-3 packet carries the 11 values as int16, scaled with the multipliers in `common/sensor.py:18` (`SCALES`; hand-off document, section 4.2). The laptop decodes and validates them as int16. Every scaled value must lie between −32768 and 32767. Acceleration multiplied by 10000 can represent only ±3.2767 g. Angular rate multiplied by 100 can represent only ±327.67 °/s. Angles multiplied by 100 can represent only ±327.67° (yaw overflows if it runs from 0 to 360). Flex values multiplied by 10000 top out at 3.2767. Section 7.1 of the hand-off document states the range each value must stay within. In normal use every value is expected to fit, but that is not guaranteed: the final value depends on the sensor module's processing (for example the gyro calibration bias it subtracts), not only on the raw sensor range. Siqiang's module, read but not measured, keeps every value inside these limits: it sets the accelerometer to ±2 g and the gyro to ±250 °/s (the range registers at `hardware/gloves/integration_files/glove_sensor.cpp:454-455`, with the matching scales at `:27-28`); linear acceleration is the reading minus a unit gravity vector, so at most 3 g per axis (`:278-289`); the angles come from `atan2f` and `asinf`, so yaw and roll stay within ±180° and pitch within ±90° (`:255-276`); flex is the ADC value divided by 4095, so 0 to 1 (`:522-523`). The gyro fits while the calibration bias it subtracts stays below about 77 °/s. The scales are provisional: they are checked against Siqiang's real sample log before they are fixed (hand-off document, section 8, step 1). Scaling happens in the firmware at each send tick whose sample is read and MOVING (`prepareSample`, which calls `scaleSample`, `firmware/esp32/include/comms_sample.h:94-114`; an IDLE or unread tick is never scaled; built and host-tested, not yet run on a board; see [chapter 2](02-firmware.md)); the laptop only decodes int16. The out-of-range policy is provisional until Wen Ree answers: the firmware clamps to the int16 limit by default, and a build with `-DCOMMS_OUT_OF_RANGE_DROP=1` refuses that one sample instead. Either way the firmware counts it, and it never drops a connection or a whole gesture for it. A refused sample (a non-finite value, or an out-of-range value under the drop policy) is counted in the source statistics as `refused`, which the laptop reports as `source_refused`. A clamped value is counted only on the serial line (`comms_stats … clamped=`, the number of values clamped in samples that were sent). A clamped value arrives as exactly the limit (for example 32767, that is 3.2767 g) and cannot be told apart from a real value at the limit; if the model needs to know, a per-sample flag is needed, which changes the packet and `on_sample` again. Neither option guarantees that the gesture is still recognised (hand-off document, sections 8 step 1 and 13).
- **Left and right identity.** The laptop trusts only the packet's `device_id`. It is a compile-time constant in the firmware. `flash.py` sets it by the order in which the boards are plugged in (the first board plugged in is flashed as left), with or without `--glove`. The sensor module does not need to supply it. Siqiang confirmed (2026-10-15) that left and right run the same module code, and that the 12th value `SENS_GL_LEFT`/`SENS_GL_RIGHT` and the Bluetooth names `SENSOR_GLOVE_LEFT`/`SENSOR_GLOVE_RIGHT` of his own sketches were only for his PC; Communications does not use them, and the boards advertise as `LTC-COMMS`.
- **Coverage is judged against `--rate`, and a gated board by its ticks.** An ungated board must deliver at least `0.9 × observation duration × --rate` packets inside the observation window. A gated board (one whose source statistics carry the gated flag: the `-glove` firmware unless built with `-DCOMMS_GLOVE_SEND_ALL=1`, or the dummy built with `-DCOMMS_DUMMY_IDLE_MS` above 0; `kGloveGated`, `firmware/esp32/include/comms_glove.h:63-64`) sends only while its glove module reports MOVING, so its packet count cannot show whether it stalled. Its `generated` plus `source_idle` ticks must instead reach `0.9 × source_ticking_seconds × --rate`, where `source_ticking_seconds` is the span from its first sensor subscription to the quiesce read at shutdown; its silence is not judged once it has reported an idle tick (`board_coverage`, `laptop/dual_bridge.py:391-416`; details under "Gating in the report"). Unread and refused ticks (the module had no valid sample, or the firmware refused it) count against coverage on both kinds of board, and so does a send tick the firmware skips because one loop pass ran longer than the send interval (20 ms at 50 Hz); such a tick is not counted anywhere. A board that misses more than one in ten of its ticks this way is judged not clean.
- **Labels.** The laptop relay does not look at labels, and results do not pass through the laptop. Only the diagnostic, check and rehearsal tools validate results with `ultra96.protocol.validate_message`: `laptop/phone_simulator.py`, `tools/check_board.py`, `tools/rehearse_comms.py`, `tools/rehearse_remote_comms.py` and `tools/comms_demo.py audit`. Since version 3 that function admits a `GESTURE_RESULT` with `v` 3, all 10 keys (including `request_id`), any label of 1 to 32 characters from `A–Z a–z 0–9 _ -`, and any confidence that is a finite JSON number from 0 to 1 (`ultra96/protocol.py:11-12`, `:31-40`, `:93-99`). Built in Python; the same rule is in every receiver (the C# reference compiled against the .NET 10 libraries and its self-test passed, 113 checks under PowerShell 7; the Swift client compiled and tested on Linux in a Swift 6.1 container, 72 tests, without its macOS-only test and iOS-only sources, and on 2026-10-16 on macOS, 73 tests, and on the iOS Simulator, but not installed on the phone; [chapter 5](05-phone-and-week7-receiver.md); hand-off document, sections 4.2 and 6.5, D8). A change to this function takes effect in these tools at the same time. Which labels exist, how often a label is produced, and whether several identical labels in a row mean one action or several are for Wen Ree and Jie Ling to agree (hand-off document, section 3.1). Communications passes every result through unchanged: it never merges, splits, filters or reinterprets results, and it does not know the label set.
- **One input, one result.** `demo.py`'s `Phone expected increase`, the verdicts of `tools/check_board.py`, `tools/rehearse_comms.py` and `tools/rehearse_remote_comms.py`, and the ID match of `tools/comms_demo.py audit` all assume that each accepted input produces exactly one result. The built-in dummy model of the Ultra96 service keeps that true: one result per accepted sample, plus the service's own `cmd:` result per command (hand-off document, section 6.5, D11 and D12). `demo.py` now prints a line under `Phone expected increase` saying the count holds only for the dummy model (`demo.py:213-217`), and both rehearsal tools say the same in their docstrings (`tools/rehearse_comms.py:4`, `tools/rehearse_remote_comms.py:6-7`). Once Wen Ree's model produces results per window, these criteria must be redefined (hand-off document, section 8, step 6). Not done: how often the model produces a result is for Wen Ree and Jie Ling to agree, and the new criteria wait for that answer.
- **Gaps in `seq` that the laptop leaves.** The model sees every laptop-side loss as a gap in `seq` at its entry point (hand-off document, section 7.2). None of these samples is resent: eviction of the oldest packet when the queue is full (64 places under `demo.py`; `queue_dropped`, `laptop/bridge.py:133-135`); packets that waited on the laptop for more than 2 s (`stale_dropped`); on a BLE disconnect, the packets still queued for that glove are discarded (`RawInbox.deactivate`, `laptop/bridge.py:114-121`, counted in `callback_generation_dropped`); on a TLS failure, the frames already written but not acknowledged count as `ambiguous_dropped` (`laptop/bridge.py:487-502`), and they leave a gap on the Ultra96 unless the service had already processed them. A packet dequeued while the TLS connection cannot be opened is lost too; it shows only as `transport_errors` and in `missing_acked`. While a glove is disconnected it makes no samples and `seq` does not advance, so that time shows only as a jump in `uptime_ms`, not as a `seq` gap. The same holds for every send tick that sends nothing (built; not yet run on a board): an idle tick while a gated glove is still, an unread tick, and a sample the firmware refuses (a non-finite value, or an out-of-range value under the drop policy). None of them takes a `seq` (hand-off document, section 4.3). So a pause between two gestures of a gated glove is one `uptime_ms` jump between consecutive sequence numbers, and the two gloves pause independently. The laptop's own `gaps` counter (`StreamTracker`, `laptop/bridge.py:151-172`) counts missing sequence numbers among the packets the writer processed.

## Components and files

| File | Responsibility |
|---|---|
| `laptop/__init__.py` | Package marker. |
| `laptop/requirements.txt` | One line only: `bleak==3.0.1`. The version must stay pinned; "Cautions and known limits" says why. |
| `laptop/ble_connection.py` | `make_ble_client()`: creates a `BleakClient` and forces `winrt={"use_cached_services": False}`. |
| `laptop/windows_pairing.py` | Windows passkey pairing and bond-level check. It also runs as a command-line program. |
| `laptop/ble_parameters.py` | Above 10 Hz, asks Windows for "throughput-optimized" connection parameters. Reads back the actual connection interval, peripheral latency and supervision timeout. |
| `laptop/ble_shutdown.py` | At stop, writes the remote CCCD to NONE directly through WinRT and keeps the local notification callback. |
| `laptop/bridge.py` | Single-board path `Bridge`: receive queue, validation, TLS send and ACK, BLE lifecycle, synthetic data source, single-board command line. |
| `laptop/dual_bridge.py` | Two-board coordinator `DualBridge` and the command line used in the field: common observation window, close and drain order, verdict (with `board_coverage`, the coverage and silence rules for gated and ungated boards), progress output. |
| `laptop/source_audit.py` | Parses the 36-byte source statistics (marker `LCS3`, gated flag, idle, unread and refused counters). Reconciles the three counts "generated, received, acknowledged" in constant memory, and reports the skipped ticks. |
| `laptop/controls.py` | BLE control channel client: commands, rate setting, file transfer, command queue, keyboard input. |
| `laptop/goodput.py` | Goodput measurement. |
| `laptop/evidence.py` | A background thread writes `packets.jsonl` and `packets.log` and prints a sample to the console. |
| `laptop/reporting.py` | Exclusive reservation and atomic write of the report file; source fingerprint and Git revision. |
| `laptop/phone_simulator.py` | Desktop result subscriber (simulates the phone). For rehearsals only. |
| `laptop/ble_counter_receiver.py` | Early diagnostic: receives the 4-byte counter characteristic `6e1c0002` and checks continuity and reconnection. |
| `laptop/mtu_probe.py` | Early diagnostic: ATT MTU boundary probe. |
| `laptop/bounded_telemetry_queue.py` | Generic "drop oldest when full" queue. Current code does not reference it; only its own test uses it. |
| `laptop/tests/test_ble_counter_receiver.py` | Counter decoding; gaps, duplicates, out-of-order; reconnect generation; cleanup time limit. |
| `laptop/tests/test_bounded_telemetry_queue.py` | Capacity validation, FIFO eviction, no lost item when a waiter is cancelled. |
| `laptop/tests/test_mtu_probe.py` | The three probe lengths; an oversized notification counts as an anomaly; cleanup shares a 1-second grace period. |
| `common/sensor.py` | Encoding and decoding of the 38-byte version-3 packet: `SensorPacket`, `VERSION` (3), `CHANNELS`, `SCALES`, `CHANNEL_COUNT` (11), `PACKET_SIZE` (38), `SENSOR_MTU_FLOOR` (41), conversion to `SENSOR_BATCH`, `physical_values` (int16 / scale, used on the Ultra96), and the dummy-data table with `choose_fixture`. |
| `common/control.py` | Encoding and decoding of BLE control frames, opcodes, status codes, file metadata, and the value transformation for commands (11 values). |
| `common/dummy_fixtures.json` | The 11-value dummy rows the boards, the laptop's commands and the synthetic sources send (4 rows). |
| `demo.py` | Operator entry point: `tunnel`, `run`, `live`, `report`, `service`. |
| `tools/demo_boards.py` | Reads, writes and validates `boards.json`, the map of the left and right boards' Bluetooth addresses. |
| `tools/ssh_tunnel.py` | Builds the two-hop SSH local forward command; optional supervised restart. |
| `tools/check_board.py` | New on 2026-10-14. Checks one flashed board after flashing: real BLE to the laptop relay, a service started on the laptop with throwaway certificates and the dummy model, and a local subscriber. No SSH, Ultra96 or phone. Since 2026-10-15 its summary line also names `gated`, `idle`, `unread` and `refused`. Verified on the right board on 2026-10-14, with that day's 24-byte statistics (see "Checking one board"). |
| `tools/export_capture.py` | New on 2026-10-15. Writes the glove samples of one capture's `packets.jsonl` as CSV in physical units, one row per sample (see "Recording glove data through the chain"). Built (unit tests); never run on a real capture. |
| `tools/sync_glove_module.py` | New on 2026-10-15. Copies Siqiang's module from `hardware/gloves/integration_files/` into `firmware/esp32/` unchanged; `--check` only compares (see "Flashing the real gloves"). Built. |
| `tools/deploy_service.py` | New on 2026-10-14, the tracked successor of the untracked `.week7-local/co_deploy.py`. Uploads `common/` and `ultra96/` to the Ultra96, optionally installs a renewed server certificate, and swaps the running service with checks and rollback; writes a local record that `demo.py service --start` follows. The board-side program was verified on Linux only; the SSH half has never run (see "Deploying the Ultra96 service"). |
| `tools/comms_demo.py` | Teaching packet example (version 3), single-board sender with display, offline log audit. |
| `tools/rehearse_comms.py` | Local full-path rehearsal. Brings its own local TLS service (with the dummy model) and subscriber. |
| `tools/rehearse_remote_comms.py` | Rehearsal against the real Ultra96 through two existing forward ports. Checks ACKs and results ID by ID. Its synthetic source sends version-3 packets with the dummy rows. |
| `tools/video_evidence.py` | Picks one "sensor packet and ACK" example pair per board from a capture and validates it. Reads only version-3 captures. |
| `tests/test_bridge.py` | Queue eviction and generation isolation, sequence tracking, stale drop, ACK validation, packets that are not version 3 counted as `malformed`, the sensor MTU floor of 41 (38 + 3), tunnel command, native-operation limit, back-off. |
| `tests/test_bridge_ack_window.py` | ACK window: delayed ACKs can overlap, window limit, FIFO, after a failure the whole batch counts as ambiguous and is not resent, drain, the two boards do not take each other's window slots. |
| `tests/test_bridge_ack_window_cleanup.py` | When TLS close is cancelled midway, each frame whose write was attempted is still counted once. |
| `tests/test_ack_window_transport.py` | ACK window over real TLS with ACK propagation delay: the server processes the frames in the window before the ACKs return, and ACKs and results match one by one. |
| `tests/test_bridge_connection_parameters.py` | Timing of the throughput preference: requested after authentication and before reading source statistics, released after disconnect. |
| `tests/test_bridge_disconnect_cleanup.py` | On a dropped link, skips the remote notification stop but still disconnects locally. A cleanup failure records only the operation name and exception type. |
| `tests/test_bridge_shutdown_tail.py` | Tail packets: a late callback arrives before the callback is removed. A gated board reconciles with the idle ticks it counted before the stop. A lost tail packet, a rejected CCCD write, a changed boot ID, a count drift and an idle tick counted after the quiesce read are all judged not clean. |
| `tests/test_bridge_transport_cleanup.py` | When TLS close hangs or is cancelled, the connection is aborted and the cancellation is preserved. |
| `tests/test_dual_bridge.py` | The two paths progress independently; a normal stop drains and reconciles; startup packets do not count toward coverage; silence verdict; read order of source statistics; the command line exits within bounded time. Gating: the `board_coverage` rules for gated and ungated boards; a gated board that is idle half the time passes, while an ungated board with the same gaps fails; a gated board that subscribed early is judged over its own ticking interval, so a stall after the window's share of ticks still fails; the progress line names `gated`. |
| `tests/test_dual_reporting.py` | The report reservation does not overwrite an existing file; writing is refused if the file was replaced; progress goes to stderr; a failed save forces a non-zero exit. |
| `tests/test_dual_transport.py` | Real local TLS: the exact ID sets of both boards arrive. One TLS disconnect does not affect the other path, but the verdict is failure. |
| `tests/test_ble_connection.py` | Forced uncached GATT discovery; passkey input can be cancelled. |
| `tests/test_ble_parameters.py` | The handle is released whether the preference request succeeds, is denied, is unsupported or is cancelled; unit conversion. |
| `tests/test_ble_shutdown.py` | Returns False on non-Windows or when the native interface is missing. The native write must return SUCCESS explicitly. |
| `tests/test_laptop_controls.py` | Command round-trip validation (version-3 packets, 11 values), commands not retried, file chunk retry and digest check, `FILE_ABORT` on failure, commands use a separate TLS connection, old commands not replayed after reconnect. The workspace fingerprint records dirty state and, since `4c6ab4c`, covers the copies of Siqiang's module. |
| `tests/test_goodput.py` | Counts only unique valid packets (any version-3 values); silent time counts in the denominator; startup and drain do not count. |
| `tests/test_source_audit.py` | Decoding of a literal 36-byte `LCS3` value with the gated flag and the three skip counters; the 24-byte `LCS3` and `LCS1` values refused by length with the reflash message; `LCS1`, `LCS2`, `LCS4` and `lcs3` refused by marker with the same message; non-zero reserved bytes, unknown flag bits and other malformed input rejected (including `W7S1`); the skip counters are same-boot deltas that wrap like the sequence counters, are `null` across a reboot, and never affect `clean`; a lost tail packet is detected; uint32 wraparound. |
| `tests/test_sensor.py` | The version-3 layout constants match the specification; encoding writes `LC` and version 3 (38 bytes); `W7`, `WC` and `lc` are rejected; round trip of the fixed vectors; rejection of truncation, trailing bytes, version, device ID and value range; a 32-byte version-2 packet is rejected; `physical_values` divides by the scales and accepts only 11 int16; session ID validation; host test of the firmware serialization and security policy. |
| `tests/test_comms_demo.py` | The packet example in `tools/comms_demo.py` matches the literal bytes; the offline audit goes by ID, not by count; model labels and fractional confidence pass the audit; incomplete, duplicated, faulty or too-short evidence cannot pass; the sender's timing verdict. |
| `tests/test_ssh_trust.py` | Uses `ssh -G` to check the effective configuration of both hops: the jump hop has its own strict host-key checking; interactive mode allows a password at the jump host; supervised mode overrides the insecure defaults on both hops; `-i` applies only to the target; the supervisor refuses an interactive proxy. |
| `tests/test_demo_boards.py` | Flash order determines the left/right map; capture is blocked while the map is incomplete; the old file is kept when a write fails. |
| `tests/test_demo_launcher.py` | `demo.py` saves the child process output; default command line; choice of session ID; the various fail conditions; interrupt handling; the report table's `Gated` and `Idle` columns do not change the verdict. |
| `tests/test_demo_service.py` | The start folder follows the newest deployment record (records that left nothing running, unreadable records and folders outside `BOARD_ROOT` are skipped; without a record, `BOARD_SOURCE`); a start restarts the deployed `--model`/`--model-path` too, and a record whose model is not a module name is not trusted. Port-in-use check and strict SSH options in the service start script. Session ID: starts with the requested session, a malicious session ID stays a single argument, an invalid session ID is rejected, the same default rule as capture. |
| `tests/test_demo_simplified.py` | Defaults of `run` and `live`; `report` does not ask for the phone count; `--help` of each subcommand does not touch hardware. |
| `tests/test_rehearsal.py` | A 5-second local rehearsal with a target of 10 packets passes. |
| `tests/test_remote_rehearsal.py` | ID-by-ID correspondence; the synthetic source sends version-3 fixture packets; stops before sending data when the CA is wrong; a run with silence or restarts cannot count as a clean pass. |
| `tests/test_packet_evidence.py` | Evidence files contain no ANSI color codes; console sampling; a slow console does not block, and overflow is counted. |
| `tests/test_video_evidence.py` | Examples must pair by full identity. An explicit version-3 ACK version is checked. Captures from before version 3 are refused and named as such. A corrupt file, conflicting records or a missing board all fail. |
| `tests/test_check_board.py` | The `check_board` verdict: a clean summary passes; each failure is named (source not clean, generated and received differ, a gap, rate not confirmed, MTU below 41, missing dummy-model or command results, too few completed commands, subscriber errors, nothing acknowledged). The summary line names `gated`, `idle`, `unread` and `refused`; a gated board's idle ticks do not fail the verdict. |
| `tests/test_export_capture.py` | `tools/export_capture.py`: one physical-unit row per sample in arrival order (a repeated sample, a `sensor_invalid` record and a torn last line are skipped); `--device`; the default uses the newest capture (the newest-folder choice itself is not tested); an existing CSV is never overwritten; a record that is not a valid version-3 sample fails the export. |
| `tests/test_glove_module_sync.py` | The firmware's copies equal Siqiang's module in `hardware/gloves/integration_files/` (line endings aside), so this test fails while a copy is stale; `--check` names a stale copy and exits 1; only the two `-glove` environments link the module. |
| `tests/test_deploy_service.py` | The uploaded file set is exactly `common/*.py`, `common/*.json` and `ultra96/*.py`; the manifest hashes each file; the board-side program compiles and its command line survives shell quoting; options and the certificate folder are validated; `--dry-run` connects nothing. One opt-in test (`B07_LINUX_DEPLOY_TEST=1`) runs the board-side program against real processes in Linux or WSL through `tests/linux/deploy_remote_test.sh`; it hands bash a copy of that script with LF endings, so it also runs from a checkout with CRLF endings (`tests/test_deploy_service.py:131-134`, since `3b94990`). |
| `tests/test_windows_pairing.py` | The passkey must be 6 digits; a weak bond is rejected; the handler is removed after pairing. |

Adjacent files that this chapter does not cover: `common/tls.py`, `common/wire.py`, `tools/demo_service.py` (only its start behaviour is described here), `tools/generate_comms_pki.py`, `ultra96/protocol.py`, `ultra96/model.py`, `ultra96/server.py`, `flash.py` (only its pairing and `--glove` steps are described here), and the firmware, including the copies of Siqiang's module in `firmware/esp32/lib/glove_sensor/` ([chapter 2](02-firmware.md)). This chapter cites only their interfaces. The Ultra96 service, its model interface and the board-side half of `tools/deploy_service.py` are in [chapter 4](04-ultra96-service-and-certificates.md).

## Data formats and constants

### GATT characteristics the laptop uses

All UUIDs end in `-7a45-4dc4-b678-3f2d5a9c1001`.

| UUID prefix | Code constant | Operation | Content |
|---|---|---|---|
| `6e1c0001` | `SERVICE_UUID` | Scan filter | Service |
| `6e1c0005` | `SENSOR_UUID` | Notify | 38-byte version-3 sensor packet |
| `6e1c0006` | `SOURCE_STATS_UUID` | Read | 36-byte source statistics (`LCS3`) |
| `6e1c0007` | `CONTROL_UUID` | Write with response | Control request |
| `6e1c0008` | `RESPONSE_UUID` | Notify | Control response |
| `6e1c0002` | Only in `ble_counter_receiver.py` | Notify | 4-byte little-endian counter |
| `6e1c0003` / `6e1c0004` | Only in `mtu_probe.py` | Write / Notify | 2-byte requested length / payload whose byte i equals `i mod 256` |

### Sensor packet (protocol version 3, 38 bytes, `<2sBBIII11h`, little-endian)

Version 3 is the only version (since 2026-10-14, branch `comms/protocol-v3`; built, and verified on the right board on 2026-10-14, see "Checking one board"). Siqiang answered the IDLE/MOVING question on 2026-10-15: the glove sends only while his detector says MOVING and nothing while IDLE, so the state does not travel in the packet and the 11-value layout stays. The layout is still provisional for two things: the scales are checked against Siqiang's real sample log, and Wen Ree agrees to it (hand-off document, sections 4.2 and 13).

| Offset | Length | Field | Type | Values |
|---:|---:|---|---|---|
| 0 | 2 | magic | ASCII | `LC` (`4C 43`), the only accepted value |
| 2 | 1 | version | uint8 | 3, the only accepted value |
| 3 | 1 | device_id | uint8 | 1 or 2 |
| 4 | 4 | boot_id | uint32 | 0 to 0xFFFFFFFF |
| 8 | 4 | seq | uint32 | 0 to 0xFFFFFFFF, wraps |
| 12 | 4 | uptime_ms | uint32 | 0 to 0xFFFFFFFF |
| 16 | 22 | values[0..10] | 11 × int16 | −32768 to 32767 |

The 11 values, in this order (`CHANNELS` and `SCALES`, `common/sensor.py:15-18`; physical value = int16 / scale):

| Index | Names | Unit the sensor module delivers | Scale |
|---:|---|---|---:|
| 0–2 | `ax` `ay` `az` | g, gravity removed | 10000 |
| 3–5 | `gx` `gy` `gz` | °/s, bias removed | 100 |
| 6–8 | `yaw` `pitch` `roll` | degrees | 100 |
| 9–10 | `flex1` `flex2` | 0.0 to 1.0 | 10000 |

- The default firmware environments (`firebeetle32-left` and `-right`, what `python flash.py` builds) send dummy rows from `common/dummy_fixtures.json` (4 rows of 11) through the built-in dummy module. The `-glove` environments (`python flash.py --glove`) send the values of Siqiang's module: built, not run on a glove. No real sensor data has crossed the chain yet.
- A length other than 38 is rejected with `sensor packet must contain exactly 38 bytes` (`common/sensor.py:82-83`). A 32-byte version-2 packet therefore fails here.
- A magic other than `LC` is rejected with `invalid sensor packet magic; expected LC` (`common/sensor.py:85-86`).
- A version other than 3 is rejected with `unsupported sensor packet version` (`common/sensor.py:87-88`). On the laptop each rejected packet counts as `malformed` (`laptop/bridge.py:413-415`). The relay does not check the values beyond the int16 range: the deterministic dummy formula of version 1 is gone.
- At connection the ATT MTU must be at least 41, that is `PACKET_SIZE` + 3 for the ATT notification header (`SENSOR_MTU_FLOOR`, `common/sensor.py:22`; checked at `laptop/bridge.py:722-723`). Otherwise the attempt fails with `current ATT MTU cannot carry 38-byte sensor packet` and is retried after back-off. The negotiated MTU measured on these boards is 517.

### Source statistics (36 bytes, `<4sBB2xIIIIIII`, little-endian)

| Offset | Length | Field | Values |
|---:|---:|---|---|
| 0 | 4 | magic | `LCS3`, the only accepted value |
| 4 | 1 | device_id | 1 or 2 |
| 5 | 1 | flags | bit 0 = gated (the board sends only while its glove module reports MOVING); every other bit must be 0 |
| 6 | 2 | reserved | must be all 0 |
| 8 | 4 | boot_id | uint32 |
| 12 | 4 | next_seq | the next sequence number to assign |
| 16 | 4 | submitted | number of successful notification submissions |
| 20 | 4 | failures | number of failed notification submissions |
| 24 | 4 | idle | send ticks skipped because the glove module said IDLE |
| 28 | 4 | unread | send ticks skipped because the glove module had no valid sample |
| 32 | 4 | refused | send ticks whose sample the firmware refused (a non-finite value, or out of range under the drop policy) |

After the boot ID, the six uint32 fields are totals since boot (`laptop/source_audit.py:12-22`). A tick counts only while the laptop is subscribed to the sensor notifications; idle, unread and refused ticks send nothing and take no sequence number. The firmware commits a tick only if notifications are still on after the glove module answered, so once they are off nothing in this value changes, skip counters included (see [chapter 2](02-firmware.md)). The format changed on 2026-10-15 (`5d2e52f`) from the 24-byte `<4sB3xIIII` of 2026-10-14; the marker stayed `LCS3`, because only the right board ever ran the 24-byte `LCS3`. The parser checks, in this order (`laptop/source_audit.py:61-75`):

1. Length. Anything but 36 bytes reports `source statistics must contain exactly 36 bytes; flash this board with the current firmware`. This is where every older board now fails: the 24-byte `LCS3` of 2026-10-14, the version-2 `LCS1` and the Week 7 `W7S1` are all 24 bytes.
2. Reserved bytes 6 and 7 must be 0.
3. Magic. Anything but `LCS3` reports `invalid source statistics magic; flash this board with the current firmware` (`laptop/source_audit.py:70-71`).
4. Flags. Any bit other than bit 0 reports `source statistics flags contain unknown bits`.
5. Device ID, against the expected one.

So a board with older firmware is refused before the laptop subscribes, with a message that names the cause, instead of producing `malformed` counts packet by packet (hand-off document, section 6.5, D7).

### BLE control frame (one frame per write or per notification)

Header, 14 bytes, `<2sBBBBII`:

| Offset | Length | Field | Values |
|---:|---:|---|---|
| 0 | 2 | magic | `B7` (the team number B07, not Week 7) |
| 2 | 1 | version | 1 (the control version; it did not change with packet version 3) |
| 3 | 1 | opcode | a response is the request value plus 128 (bit 7 set) |
| 4 | 1 | device_id | 1 or 2 |
| 5 | 1 | status | always 0 in a request |
| 6 | 4 | request_id | uint32, 1 to 0xFFFFFFFF |
| 10 | 4 | offset | uint32, 0 to 65536 |
| 14 | 0 to `min(180, MTU-17)` | payload | see the table below |

| opcode | Name | Request payload | Response payload |
|---:|---|---|---|
| 1 | `COMMAND` | A complete 38-byte version-3 packet; `seq == request_id`, `uptime_ms == 0`, `offset == 0`. The whole frame is 52 bytes | The 38-byte packet after the board adds 1 to each of the 11 values (32767 wraps to −32768) and writes its own `millis()` into `uptime_ms`; again a 52-byte frame |
| 2 | `SET_RATE` | uint16 little-endian, 1 to 200 Hz | Echoed unchanged |
| 16 | `FILE_BEGIN` | 36 bytes: uint32 length plus SHA-256; `offset == 0` | None; `offset` must be 0 |
| 17 | `FILE_CHUNK` | File bytes, not empty; `offset` is the start of this chunk | None; `offset` is the next expected offset |
| 18 | `FILE_END` | None; `offset` is the total file length | 36 bytes: the length and SHA-256 the receiver computed; `offset` equals the length |
| 19 | `FILE_ABORT` | None; `offset == 0` | None |

Status codes: 0 `OK`, 1 `INVALID`, 2 `BUSY`, 3 `ORDER`, 4 `INTEGRITY`, 5 `CONFLICT`, 6 `UNSUPPORTED` (`common/control.py:13`). A response with a non-zero status carries no payload. The control channel requires an MTU between 64 and 517 (`common/control.py:30-32`), so a 52-byte command frame always fits. A command's packet must be version 3, for this board and with `seq` equal to the request ID (`common/control.py:54-58`). A file is 1 to 65536 bytes. The firmware's control output floor follows the packet: 14 + 38 = 52 bytes (`kControlMinOutput`; see [chapter 2](02-firmware.md)).

### JSON over TLS

A frame is a 4-byte big-endian length followed by UTF-8 JSON. The body is 1 to 16384 bytes (`common/wire.py:7`).

| Message | `v` | Direction | Fields |
|---|---|---|---|
| `SENSOR_BATCH` | 3 | laptop → Ultra96 | `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `uptime_ms`, `values` (11 integers), `request_id`: `null` for the data stream, a uint32 equal to `seq` for a command (`common/sensor.py:52-69`). |
| `INGEST_ACK` | 3 | Ultra96 → laptop | `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `status` (`accepted` or `duplicate`), `request_id`. |
| `SUBSCRIBE`, `SUBSCRIBED` | 1 | tool → Ultra96, Ultra96 → tool | `v`, `type`, `session_id`. Only the tools that subscribe use them (`laptop/phone_simulator.py`, `tools/check_board.py`, both rehearsal tools). They stay at `v` 1: they never carried the packet version (hand-off document, section 6.5, D5). |
| `GESTURE_RESULT` | 3 | Ultra96 → subscriber | 10 keys: `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `request_id`, `result_id`, `gesture`, `confidence`. The relay never sees it; the tools above validate it (see "Labels"). |

`request_id` is now always present in the three version-3 messages (hand-off document, section 6.5, D6). The Ultra96 accepts only `v` 3 for them and `v` 1 for the subscription messages (`ultra96/protocol.py:22-24`, `:64-66`). The ACK's key set must be exactly the one above. Each value's type and value must match the packet sent, including `v` 3 and the `request_id` (`null` for the stream). Otherwise the ACK is handled as a transport error (`laptop/bridge.py:381-391`).

### `BridgeConfig` (`laptop/bridge.py:34-78`)

| Field | Default | Range and constraints |
|---|---|---|
| `ca_file` | required | CA certificate path |
| `host` | `127.0.0.1` | only this value |
| `port` | 18888 | 1 to 65535 |
| `session_id` | `ltc-comms` | 1 to 128 characters, no control characters (`ultra96.protocol.validate_session`) |
| `queue_capacity` | 64 | 1 to 4096 |
| `freshness` | 2.0 s | positive finite number |
| `io_timeout` | 5.0 s | positive finite number; also the control channel timeout |
| `scan_timeout` | 8.0 s | positive finite number |
| `connect_timeout` | 20.0 s | positive finite number; also bounds subscription, the source statistics read at start and the throughput preference request; also the total budget for source statistics handling at shutdown |
| `address` | none | BLE address; required in two-board physical mode |
| `diagnostic_unprotected` | False | when True, skips the bond check, and the result cannot be judged clean |
| `expected_device_id` | none | 1 or 2 |
| `source_audit` | False | when True, `expected_device_id` must be given |
| `ack_window` | 1 | 1 to 64 |
| `controls_enabled` | False | requires `source_audit=True` and not diagnostic mode |
| `source_rate` | none | integer, 1 to 200 Hz |
| `seed` | none | seed for the random choice of dummy data |

`BridgeConfig` has no MTU field: the sensor MTU floor is the constant below, and the control MTU floor is `MIN_CONTROL_MTU` in `common/control.py:14`.

### Other constants

| Item | Value | Location |
|---|---|---|
| Sensor packet size | 38 bytes (`PACKET_SIZE`, from the struct `<2sBBIII11h`) | `common/sensor.py:20-21` |
| Sensor notification MTU floor | 41 = 38 + 3 (`SENSOR_MTU_FLOOR`); it was 35 for the 32-byte packet | `common/sensor.py:22`, `laptop/bridge.py:722-723` |
| Source statistics size | 36 bytes (`SOURCE_STATS_SIZE`); gated flag `0x01` (`SOURCE_FLAG_GATED`) | `laptop/source_audit.py:14`, `18-20` |
| Control channel MTU floor | 64 (`MIN_CONTROL_MTU`) | `common/control.py:14`, `laptop/controls.py:78-79` |
| Two-board ACK window (command-line default; `demo.py` always passes 32) | 32 | `laptop/dual_bridge.py:450`, `demo.py:81` |
| TLS read buffer limit | 32768 bytes | `laptop/bridge.py:358` |
| TLS handshake timeout | `io_timeout` (5 s) | `laptop/bridge.py:359` |
| Per-frame ACK deadline | send time plus `io_timeout` | `laptop/bridge.py:608-616` |
| TLS close wait | 1.0 s, then `abort()` on timeout | `laptop/bridge.py:366` |
| Reconnect back-off (BLE and TLS counted separately) | starts at 0.5 s, doubles each time, capped at 5.0 s | `laptop/bridge.py:663-673`, `687`, `958` |
| Limit on unfinished native BLE operations | 2 | `laptop/bridge.py:335-341` |
| Notification stop budget | 0.75 s each | `laptop/bridge.py:821`, `884` |
| Disconnect budget | 1.0 s, counted separately | `laptop/bridge.py:928` |
| Tail-packet wait | at most 0.5 s, polled every 0.01 s | `laptop/bridge.py:852-863` |
| Two-board startup, drain and shutdown timeouts | 30 s, 10 s, 25 s | `laptop/dual_bridge.py:26-28` |
| Coverage threshold, ungated board | packets received in the observation window greater than 0 and at least `0.9 × duration × expected rate` | `laptop/dual_bridge.py:411-415` |
| Coverage threshold, gated board | `generated` plus `source_idle` greater than 0 and at least `0.9 × source_ticking_seconds × expected rate` | `laptop/dual_bridge.py:405-409`, `415` |
| Silence threshold | largest gap in the observation window no more than `freshness`; for a gated board, not judged once `source_idle` is above 0 | `laptop/dual_bridge.py:410`, `414` |
| Control response buffer, duplicate record | 32 entries, 64 entries | `laptop/controls.py:93`, `35` |
| Command wait queue | 8 entries per board | `laptop/controls.py:285` |
| File chunk retry | after a timeout, at most 2 more sends, with identical content | `laptop/controls.py:218`, `241-249` |
| Keyboard polling | every 0.02 s, at most 16 keys per round | `laptop/controls.py:353-361` |
| Evidence queue, console sampling | 4096 entries; prints 1 in 10 | `laptop/evidence.py:14` |
| Goodput rolling window | 5.0 s | `laptop/goodput.py:20` |
| Throughput preference observation | at most 2.0 s, polled every 0.05 s | `laptop/ble_parameters.py:109`, `171` |
| Pairing wait | 90 s | `laptop/windows_pairing.py:77-79` |
| SSH keepalive | `ServerAliveInterval=15`, `ServerAliveCountMax=3` | `tools/ssh_tunnel.py:27` |
| SSH connect timeout (interactive mode / supervised mode) | jump host 20 s, target 60 s / 10 s on both hops | `tools/ssh_tunnel.py:30`, `35` |

### Evidence folder and report

Each capture gets one folder: `.comms-local/B07-<UTC timestamp, format %Y%m%dT%H%M%S%fZ>-<8 hex digits>/` (`demo.py:239-242`).

| File | Written by | Format |
|---|---|---|
| `report.json` | the `laptop.dual_bridge` child process | Single-line JSON. At start it exclusively creates a placeholder file (run metadata plus `"status": "incomplete"` and `reservation_id`, permissions 0600). At the end it replaces the file atomically. Before replacing it checks that the file was not swapped for another file and that the placeholder content is unchanged (`laptop/reporting.py:50-85`, `88-121`). |
| `report-readable.json` | `demo.py` | The same content, indented by 2 spaces. Written only when `run` or `live` ends; `demo.py report` does not write it (`demo.py:176-178`). |
| `packets.jsonl` | `PacketEvidence` | One event per line: `timestamp_utc`, `monotonic_seconds`, `type`, `device_id`, plus each event's own fields. A `sensor` event includes `version` (3), `boot_id`, `seq`, `uptime_ms`, the 11 values and `raw_hex` (the 38 bytes); it is written in the BLE callback for every packet that decodes and enters the queue, before the Ultra96 sees it (`laptop/bridge.py:299-302`). `tools/export_capture.py` reads these events. |
| `packets.log` | `PacketEvidence` | The same events as `key=value` text, without color codes. |
| `live.log` | `demo.py` | The raw stdout and stderr of the child process (`demo.py:249`). |
| `exit-code.txt` | `demo.py` | The child process's exit code, one line (`demo.py:269`). |
| `samples.csv` | `tools/export_capture.py`, only when run | The capture's glove samples in physical units (see "Recording glove data through the chain"). |

The complete set of `type` values in `packets.jsonl` (from every `log(` call in `laptop/bridge.py` and `laptop/controls.py`):

- Data: `sensor`, `sensor_invalid`, `sensor_ack`.
- BLE connection: `BLE_connection_parameters`, `BLE_connected`, `BLE_disconnected`.
- Source statistics and tail packets: `source_quiesced`, `source_tail_drain`, `source_quiesce_failed`, `source_final_verified`, `source_final_failed`.
- Control channel: `control_connected`, `control_duplicate`, `control_invalid`, `source_rate`.
- Commands: `command_accepted`, `command_rejected`, `command_original`, `command_modified`, `command_ingested`, `command_failed`.
- Files: `file_begin`, `file_complete`, `file_failed`, `file_abort_requested`, `file_abort_confirmed`, `file_abort_unconfirmed`.

`sensor_ack` records only `direction`, `seq`, `boot_id` and `validation` (the ACK's `status`). It does not record the protocol version, the session ID or `request_id`. `tools/video_evidence.py` prints this point when it reviews the evidence.

Console sampling (`laptop/evidence.py:66`): `sensor` and `sensor_ack` are counted separately per device and type, and 1 in 10 is printed. Every event of the other types is printed. Output goes to stderr. It is colored only when stderr is a terminal (device 1 cyan, device 2 magenta).

The local board map is `.comms-local/boards.json`, format `{"version": 1, "status": "ready" or "incomplete", "left": "<address>", "right": "<address>"}`. `flash.py` writes it (`tools/demo_boards.py:41-58`). An address must be `XX:XX:XX:XX:XX:XX`, non-zero and unicast, and is stored in upper case (`tools/demo_boards.py:13-18`). When the file does not exist, the built-in default addresses are used (see `tools/demo_boards.py:10`). When `status` is `incomplete`, capture and pairing are refused with `Board setup is incomplete; finish python flash.py before pairing or capture.`. `.comms-local/` is already in `.gitignore`.

**Top-level fields of `report.json`:** `clean`, `mock_input`, `session_id`, `common_observation_seconds`, `expected_rate_hz`, `progress_error`, `file_transfer`, `sensor_goodput`, `devices` (keys `"1"` and `"2"`), `evidence`, `run`, `report_saved`. When the save fails, `report_error` is added.

- `evidence`: `written`, `dropped`, `write_errors`, `unfinished`, `console_sample_every`.
- `run` (`laptop/dual_bridge.py:506-521`, `564-566`): `started_at_utc`, `finished_at_utc`, `mode`, `requested_duration_seconds`, `expected_rate_hz`, `source_rate_requested_hz`, `keyboard`, `file_device`, `seed`, `queue_capacity`, `freshness_seconds`, `ack_window`, `session_id`, `revision`, `worktree_dirty`, `workspace_source_sha256`.
- The source fingerprint (`laptop/reporting.py:13-38`) covers only `demo.py`, `firmware/esp32/platformio.ini`, `firmware/esp32/movement_model_params.h`, and the `.py`, `.json`, `.h`, `.cpp`, `.cs` and `.swift` files in these 9 folders: `common`, `laptop`, `ultra96`, `phone`, `tools`, `firmware/esp32/include`, `firmware/esp32/src`, `firmware/esp32/lib`, `ios-visualizer/CommsNative/Sources`. It excludes `flash.py`, `hardware/` and any file with `tests` in its path. The weights header and `firmware/esp32/lib` were added in `4c6ab4c` (2026-10-16), so a change to a copy of Siqiang's module (`firmware/esp32/lib/glove_sensor/src/` or `firmware/esp32/movement_model_params.h`) changes `workspace_source_sha256`. Each of the two `git` calls is limited to 1 second. On failure, `revision` or `worktree_dirty` is `null` (`git status` at `laptop/reporting.py:32-37`, `git rev-parse` at `124-133`).
- These fields describe only the laptop's working tree. The evidence does not record which build the boards were flashed with, nor which source folder the service on the Ultra96 runs. Whether a board is gated is recorded per board (`gated`, below), from the board's own statistics.

**Per-board fields (`devices["1"]`, `devices["2"]`):**

- Counts: `received`, `malformed`, `stale_dropped`, `generation_dropped`, `sent`, `acked`, `duplicate_acks`, `ack_errors`, `ambiguous_dropped`, `transport_errors`, `transport_connections`, `ble_connections`, `ble_errors`, `cleanup_errors`, `identity_mismatches`, `source_stats_errors`, `disconnects`, `queue_dropped`, `callback_generation_dropped`, `queue_size`, `gaps`, `duplicates`, `out_of_order`, `new_boots`.
- State and verdict: `clean`, `runtime_failures`, `unfinished`, `gated`, `source_idle`, `expected_samples`, `coverage_expected`, `coverage_ratio`, `sustained_coverage`, `silence_ok`, `protected_ble`, `input`, `source_issue`.
- Timing: `first_received_at`, `last_received_at`, `max_receive_silence`, `callback_received`, `observation_received`, `observation_max_silence`, `source_ticking_seconds`.
- `sensor_goodput`, `commands` (`accepted`, `rejected`, `completed`, `failed`, `pending`), `controls` (`response_errors`, `duplicate_responses`, `notification_dropped`, `native_pending`).
- `configuration`: `address`, `negotiated_att_mtu`, `source_rate_requested_hz`, `source_rate_confirmed_hz`, `connection_parameters`, `ack_window`, `queue_capacity`, `freshness_seconds`, `fixture_seed`.
- `source`: `complete`, `clean`, `device_id`, `boot_id`, `start_next_seq`, `end_next_seq`, `generated`, `source_submitted`, `source_failures`, `source_consistent`, `gated`, `source_idle`, `source_unread`, `source_refused`, `source_ticks`, `received`, `acked`, `missing_received`, `missing_acked`, `first_received_seq`, `last_received_seq`, `first_acked_seq`, `last_acked_seq`, `sequence_anomalies`, `ack_sequence_anomalies`, `identity_mismatches`, `boot_mismatches`, `interruptions`, `snapshot_errors`.

**`received` has three meanings. Do not mix them up.** The per-board `received` is the number of packets the writer task has dequeued and processed (`laptop/bridge.py:404`). The number of BLE callbacks is in `callback_received` (`laptop/bridge.py:307`). `source.received` is the number of packets that decoded and whose identity and boot ID matched. In the progress line, `received=` prints the callback count, and `processed=` is the one that matches the report's `received` (`laptop/dual_bridge.py:149-150`). A packet evicted from the queue counts only in the callback count. In a clean capture the three numbers are equal.

**Conditions for `source.clean`** (`laptop/source_audit.py:191-198`): both the start and the end snapshot exist; the boot ID is the same; `generated` equals `submitted` plus `failures`; `generated` is greater than 0; `failures` is 0; `received` and `acked` both equal `generated`; sequence anomalies, ACK sequence anomalies, identity mismatches, boot mismatches, interruptions and snapshot errors are all 0. The skip counters (`source_idle`, `source_unread`, `source_refused`) never affect `source.clean`. Because `generated` must be above 0, a gated glove that stays still for the whole capture is not clean. Without a start snapshot, `source_issue` is `source statistics unavailable or incompatible; install updated dual-source firmware` (this is what a board with older firmware produces: its 24-byte statistics are refused). Without an end snapshot it is `final source statistics unavailable; capture is incomplete` (`laptop/bridge.py:996-1000`).

**Gating in the report** (2026-10-15, `5d2e52f`; built, not yet run on a board):

- `source.gated` is the gated flag of the end snapshot, or of the start snapshot when there is no end snapshot; `null` without either (`laptop/source_audit.py:185`, `211`). The per-board `gated` copies it (`laptop/dual_bridge.py:349`).
- `source.source_idle`, `source_unread` and `source_refused` are the increases of the three skip counters between the start and end snapshots, with uint32 wraparound; `source_ticks` is `generated` plus the three, that is every send tick while the laptop listened. All four are `null` when either snapshot is missing or the two have different boot IDs (`laptop/source_audit.py:180-184`). The per-board `source_idle` copies `source.source_idle` (`laptop/dual_bridge.py:350`).
- `source_ticking_seconds` is the span from the first sensor subscription of the capture (`laptop/bridge.py:781-782`) to the uncached quiesce read at shutdown, or, when that read did not happen, to the final read after `stop_notify` (`laptop/bridge.py:904-907`). It is one span: it includes any reconnect gap, when notifications were off, so it can only overstate the time they were on; such a capture is already not clean (`source.interruptions`). It is `null` when either end is missing, for example when the final read failed. The synthetic `--mock` source sets both ends too (`laptop/bridge.py:971-972`, `989`). The firmware counts ticks only while notifications are on, so this is the interval the counters cover. It can start well before the common observation window (while the other board connects), and it ends after it.
- `coverage_expected` is what coverage is judged against: `expected_samples` (the observation window × `--rate`) for an ungated board, `source_ticking_seconds × --rate` for a gated one, `null` for a gated board without a ticking interval. `coverage_ratio` is the covered count divided by it (the packets received in the window for an ungated board, `generated` plus `source_idle` for a gated one), or 0.0 when it is missing or 0 (`laptop/dual_bridge.py:343-355`, `391-416`). Until 2026-10-15 `coverage_ratio` was always `observation_received / expected_samples`.

**`diagnostic` values of `connection_parameters`** (`laptop/ble_parameters.py`): `unsupported_platform`, `baseline_rate_no_preference_requested`, `preference_request_denied_or_unavailable`, `actual_parameter_change_observed`, `actual_parameters_unavailable`, `accepted_without_observed_parameter_change`, `preference_status_unresolved`, `preference_unavailable:<exception name>`. "Request accepted" (`request_accepted`) and "actual parameters changed" (`actual_parameters_changed`) are recorded separately.

**Progress lines** (stderr; under `demo.py`, one line per board per second, `laptop/dual_bridge.py:584-600`):

```text
progress mode=<physical or synthetic> phase=<startup, observation, shutdown, drain, complete> device=N gated=<yes, no or unknown> received= processed= acked= queue= drops= errors= BLE_sensor_kbps_rolling= BLE_sensor_kbps_average=
progress combined_BLE_sensor_kbps_rolling= combined_average_kbps= boundary=laptop_reception bytes=sensor_packet_including_header excludes=BLE_TLS_SSH_controls_files
```

`gated` comes from the board's start snapshot; it reads `unknown` until the first source statistics read succeeds (`laptop/dual_bridge.py:137-148`, `587`). A gated board's counts stand still while the player is still; that is not a stall. `drops` is the sum of queue evictions, stale drops, both kinds of generation drop, and ambiguous drops. `errors` is the sum of the error counts, disconnects, sequence problems and source statistics anomalies (`laptop/dual_bridge.py:128-143`). Progress is only an in-flight display. The final word is the source statistics reconciliation.

### Goodput definition (`laptop/goodput.py`)

- It counts only the "unique and valid" sensor packets the laptop received: packets that decode as version 3 and, within one `(device_id, boot_id)`, whose sequence number advances. Any int16 values count; the version-1 formula check is gone. Counting happens in the BLE callback.
- Bytes equal packets times 38 (`PACKET_SIZE`, imported at `laptop/goodput.py:10`, including the 16-byte application header). BLE, TLS and SSH overhead is excluded, and so are commands and files.
- The denominator is the duration of the common observation window. Silent time counts; startup and drain do not. Only `laptop.dual_bridge` opens that window; `tools/check_board.py` does not, so its goodput fields read 0.
- `average_kbps = bytes × 8 ÷ duration ÷ 1000`. The two-board total is the sum of both boards.
- `tracking_overflow` is incremented when more than 128 `(device_id, boot_id)` pairs are tracked, or when the rolling window holds more than 20000 timestamps (`laptop/goodput.py:56-58`, `67-69`). It makes the run not clean.

### `demo.py` subcommands

| Subcommand | Option | Default |
|---|---|---|
| `tunnel` | `--jump` | see `demo.py:40` (it contains the original operator's account; a different operator must override it) |
| | `--target` | see `demo.py:41` |
| | `--port` | 18889 (local port; the port on the Ultra96 is fixed at 8888, `demo.py:120`) |
| `run` / `live` | `--duration` | 60 / 120 s |
| | `--ca` | `~/.codex/private/cg4002-week7-20260906/ca-cert.pem` (`demo.py:49-50`) |
| | `--left-address`, `--right-address` | from the board map |
| | `--port` | 18889 |
| | `--session-id` | environment variable `LTC_COMMS_SESSION`, otherwise `ltc-comms` (`demo.py:54-55`) |
| | `--output-root` | `<repository>/.comms-local` |
| | `--keyboard` | off for `run` / on for `live` |
| | `--rate` | 10 (1 to 200); pass 50 for the gloves (see "Usage cautions") |
| | `--file`, `--file-device` | none / 1 |
| | `--seed` | none |
| `report` | `path` (optional, a folder or `report.json`), `--output-root` | the `B07-*` folder under `.comms-local/` with the newest modification time |
| `service` | `--start`, `--session-id` | Without `--start` it only inspects. `--session-id` defaults to the environment variable `LTC_COMMS_SESSION`, otherwise `ltc-comms`, and is used only with `--start` (`demo.py:68-71`, `298`). With `--start` it follows the newest local deployment record, model included (below). Details are in [chapter 4](04-ultra96-service-and-certificates.md) |

`live` also requires an interactive terminal, because it turns on `--keyboard`.

The child process that `run` and `live` actually start (`demo.py:75-90`):

```text
python -u -m laptop.dual_bridge --ca … --port … --left-address … --right-address … --duration … --session-id … --ack-window 32 --progress-interval 1 --report <folder>/report.json --evidence <folder>/packets.jsonl [--keyboard] --rate … [--seed …] [--file …] --file-device …
```

`demo.py` sets `PYTHONIOENCODING=utf-8` for the child process (`demo.py:248`).

**Which code `demo.py service --start` starts (changed on 2026-10-14).** It no longer always starts the 28 September folder. `newest_deployment()` (`tools/demo_service.py:27-50`) reads the records that `tools/deploy_service.py` saves in `.comms-local/deployments/deployment-<UTC stamp>.json`, newest first, and takes the first one that left a service running: the folder is that process's working directory (`current.cwd`), and `--model` and `--model-path` are read from that process's own arguments (`current.argv`). A record is skipped when it is unreadable, when nothing was left running (no `current`, as after `failed_nothing_running` or `rollback_failed_nothing_running`), when the folder is not under `BOARD_ROOT`, when the model is not a module name, or when the model path is not an absolute printable path. Without a usable record it falls back to `BOARD_SOURCE`, the 28 September version-2 snapshot, with the built-in dummy model. The start script then runs `cd <folder>` and adds the same `--model`/`--model-path` to `ultra96.server`, each quoted with `shlex.quote` (`tools/demo_service.py:72-98`). So a restart after a reboot runs the deployed model, not silently the dummy one (hand-off document, section 6.5, D16 and D19). Built and unit-tested; it has not run against the real Ultra96, and `.comms-local/deployments/` does not exist yet on this laptop.

Before asking, `--start` prints `Run 'python demo.py service' first. Reuse an existing healthy service.`, `Confirm ESP, board and iPhone versions match this deployment: <folder>`, `Model: <module, or the built-in dummy model>` and `Session: <name> (the capture and the phone must use the same one)`. Then it asks for Enter to confirm. Any other input cancels and returns 130 (`tools/demo_service.py:102-111`). The session ID is first validated by `validate_session`, then inserted into the start command on the Ultra96 with `shlex.quote` (`tools/demo_service.py:73`, `98`). The SSH accounts, the Ultra96 host name and `BOARD_ROOT` are hard-coded in `tools/demo_service.py` (`:13`, `:58-69`); no option changes them. The session ID can be changed. A deployment made by hand, or from another laptop, leaves no record here; `--start` would then start whatever the newest record on this laptop names, or the 28 September code.

### Other command lines

| Command | Options (defaults) |
|---|---|
| `python -m laptop.dual_bridge` | `--ca` (required), `--left-address`, `--right-address`, `--port` (18888), `--session-id` (`ltc-comms`), `--duration` (600), `--queue-capacity` (64), `--ack-window` (32), `--freshness` (2.0), `--expected-rate` (10.0), `--startup-timeout` (30), `--drain-timeout` (10), `--progress-interval` (1.0, 0 turns it off), `--report`, `--evidence`, `--console-sample` (10), `--keyboard`, `--file`, `--file-device` (1), `--rate`, `--seed`, `--mock`, `--diagnostic-unprotected` |
| `python -m laptop.bridge` | `--ca` (required), `--port` (18888), `--session-id` (`ltc-comms`), `--duration` (60), `--target` (0), `--queue-capacity` (64), `--freshness` (2), `--address`, `--mock`, `--diagnostic-unprotected` |
| `python -m laptop.windows_pairing` | `--address` (without it, scans by service UUID for 8 seconds and connects to the first board found) |
| `python -m tools.ssh_tunnel` | `--jump`, `--target`, `--local-port` (18888), `--remote-port` (8888), `--identity`, `--run` |
| `python -m tools.check_board` | `left` or `right` (required), `--rate` (50; 1 to 200), `--duration` (65 s; 5 to 3600), `--commands` (3; 0 to 8), `--pki-dir` (a new throwaway set by default), `--report` (also write the summary JSON there) (`tools/check_board.py:142-153`) |
| `python -m tools.deploy_service` | `--server-cert-dir` (none: keep the board's certificate), `--session-id` (`ltc-comms`), `--model`, `--model-path` (needs `--model`), `--no-event-log`, `--start-timeout` (30 s; 5 to 300), `--jump-user` (`yanjie`), `--board-user` (`xilinx`), `--dry-run` (`tools/deploy_service.py:310-317`, `418-436`) |
| `python -m tools.export_capture` | `capture` (optional: a capture folder or its `packets.jsonl`; default the `B07-*` folder under `.comms-local/` with the newest modification time), `--out` (default `samples.csv` beside `packets.jsonl`), `--device` (1 or 2; default both) (`tools/export_capture.py:78-84`) |
| `python -m tools.sync_glove_module` | `--check` (only compare; exit 1 when a copy differs) (`tools/sync_glove_module.py:52-68`) |
| `python -m tools.comms_demo packet` | none |
| `python -m tools.comms_demo sender` | `--ca` (required), `--port` (18888), `--session-id` (`ltc-comms`), `--address`, `--duration` (60), `--target` (100) |
| `python -m tools.comms_demo audit <log>` | `--phone-results`, `--minimum-count` (100), `--session-id` (`ltc-comms`) |
| `python -m tools.rehearse_comms` | `--pki-dir` (required), `--duration` (60), `--target` (100), `--ble`, `--diagnostic-unprotected` |
| `python -m tools.rehearse_remote_comms` | `--ca` (required), `--ingest-port` (18888), `--gateway-port` (19999), `--session-id` (`ltc-comms`), `--duration` (40), `--target` (100), `--ble`, `--address`, `--confirmed-remote-topology` |
| `python -m laptop.phone_simulator` | `--ca` (required), `--host` (`127.0.0.1`), `--port` (19999), `--session-id` (`ltc-comms`), `--count` (0), `--reconnect` |
| `python -m laptop.ble_counter_receiver` | `--target-received` or `--duration-seconds` (one of the two is required), `--require-reconnect`, `--scan-timeout-seconds` (5.0), `--reconnect-delay-seconds` (1.0), `--queue-size` (128) |
| `python -m laptop.mtu_probe` | `--scan-timeout-seconds` (5.0), `--notification-timeout-seconds` (2.0) |

When `laptop.dual_bridge` is given `--rate`, the expected rate is `--rate`, and coverage is judged against it. With `--mock`, the synthetic source runs at `--expected-rate`. Any of `--keyboard`, `--file` or `--rate` enables the control channel. Then `--mock` and `--diagnostic-unprotected` cannot be used (`laptop/dual_bridge.py:485-487`).

### SSH forward command construction (`tools/ssh_tunnel.py:12-41`, interactive mode)

```text
ssh -N -T -o StrictHostKeyChecking=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o BatchMode=no
    -o Port=22 -o ConnectTimeout=60
    -o ProxyCommand="ssh -o StrictHostKeyChecking=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o BatchMode=no -o ConnectTimeout=20 -W [%h]:%p <jump>"
    -o ExitOnForwardFailure=yes
    -L 127.0.0.1:<local port>:127.0.0.1:<remote port> [-i <identity>] <target>
```

- `<jump>` and `<target>` must be `user@host`, with no spaces or options.
- `-i` applies only to the last hop.
- `--run` (supervised mode) changes `BatchMode` to `yes` and both `ConnectTimeout` values to 10. It can use only a key or an agent; it cannot take a password. The supervisor refuses `-J` and an interactive proxy. After the child exits, it restarts it with a back-off that starts at 0.5 s and is capped at 5 s. On stop it terminates only the child it started (`tools/ssh_tunnel.py:44-80`).
- `python -m tools.ssh_tunnel` without `--run` only prints the command and does not run it. `python demo.py tunnel` runs it directly and waits for password input in the current terminal.
- `tools/demo_service.py` builds its command with the same function. It removes `-N`, `-T` and `-L`, adds `-tt`, and runs a script on the Ultra96 (`tools/demo_service.py:58-69`). `tools/deploy_service.py` does not use OpenSSH; it opens the same two hops with `paramiko` (see "Deploying the Ultra96 service").

### Version 3: the real glove packet (implemented 2026-10-14; layout provisional)

The extension point that earlier copies of this chapter proposed is now implemented as protocol version 3 on branch `comms/protocol-v3` (`a34c467` core, `57a3fbd` every component, tools and tests, `a4b907b` review fixes, `3b94990` the Linux deploy test from a Windows checkout and the specification rename). The layout is the one in "Sensor packet" above. Status: built; verified on the right board alone against a service on the laptop on 2026-10-14, with that day's 24-byte statistics (see "Checking one board"); the packet has not changed since, but the current firmware (36-byte statistics, gating) has not run on a board; not run with both gloves together, through the Ultra96, or to the phone (hand-off document, sections 6.1 and 6.3).

- **Only the newest version is supported (the owner's rule).** There is no interoperability between versions: version 3 replaced versions 1 and 2 everywhere, including the dummy test data (now 11-value rows) and the deterministic formula of version 1, and there is no transition period. Both boards, the laptop, the Ultra96 service and the phone app are upgraded together (hand-off document, section 6.3). On the laptop's TLS leg the version shows too: the `v` of `SENSOR_BATCH` is the packet's version (`common/sensor.py:60`), the new Ultra96 code accepts only `v` 3 for data messages (`ultra96/protocol.py:22-24`, `:64-66`), copies the sample's `v` into the ACK (`ultra96/server.py:337`) and writes `v` 3 into every `GESTURE_RESULT` (`ultra96/server.py:333`, `:367`). **The service now on the Ultra96 is most likely still the 28 September version-2 code with session `week7-demo`:** it refuses a version-3 frame (and an `ltc-comms` session) and closes the connection without a reason, so until the redeploy the laptop sees only `ack_errors` and `transport_errors` (see the note after the failure path table).
- **Transport stays int16.** `SENSOR_BATCH` carries the int16 values unchanged; the Ultra96 restores the physical floats for the model (`physical_values`, built; hand-off document, sections 3.1 and 7.2).
- **The scales are provisional.** They are checked against Siqiang's real sample log before they are fixed.
- **The out-of-range policy is provisional.** The firmware clamps by default and can be built to drop the sample instead; to be agreed with Wen Ree (see "int16 range" above).
- **Where the laptop side follows the packet.** Everything on the laptop takes the packet shape from `common/sensor.py`: `VERSION`, `CHANNELS`, `SCALES`, `CHANNEL_COUNT`, `PACKET_SIZE` and `SENSOR_MTU_FLOOR`. The bridge's MTU check, the command checks (`common/control.py:56`, `laptop/controls.py:185`, `:194`), goodput byte counting, `tools/comms_demo.py` (`ble_bytes`), `tools/check_board.py` (MTU), `tools/export_capture.py` (`CHANNELS`, `physical_values`) and `tools/generate_dummy_fixtures.py` all import them. Siqiang's IDLE/MOVING answer (2026-10-15) adds no field: the gating lives in the firmware and the source statistics, not in the packet. If a later change adds a field, the laptop side changes in `common/sensor.py` and `common/dummy_fixtures.json`; the firmware, the golden vectors and the tests change with it (hand-off document, section 12.6).

## Workflow

### One-time setup

1. Install the dependencies: `python -m pip install -r laptop/requirements.txt` and `python -m pip install -r requirements-dev.txt`. The second file provides `cryptography`, which `tools.check_board` needs for its throwaway certificates (step 6), and `paramiko`, which `tools.deploy_service` needs to connect. `laptop/requirements.txt` holds only `bleak==3.0.1`.
2. Board map: `python flash.py` flashes the boards in the order they are plugged in and writes `.comms-local/boards.json` (the first board plugged in is left). It builds the dummy firmware (`firebeetle32-left` and `-right`). `python flash.py --glove` builds and flashes the real gloves instead and writes the map the same way (see "Flashing the real gloves"). This laptop already has the map of the owner's two boards, which have no glove sensors (see "Local state" under "Cautions and known limits").
3. Pairing: run `python flash.py --pair left`, then `python flash.py --pair right` (with no value it pairs both). For each board it runs `python -m laptop.windows_pairing --address <address>` (`flash.py:129-137`). A board Windows has never paired (for example a glove flashed for the first time) needs this step. On first pairing, run `python flash.py --monitor COMx` in another terminal to read the passkey from that board's serial port.
4. The pairing program opens the device by address through WinRT. For a device that is already paired, it only checks the level. For an unpaired device it starts pairing with `PROVIDE_PIN` and `ENCRYPTION_AND_AUTHENTICATION`. The 6-digit passkey is typed hidden in the console (digits only, at most 6, backspace works, Ctrl+C cancels). It waits at most 90 seconds.
5. On success it prints `{"authenticated_bond": true, "address": …}`. A bond level other than 3 (encryption and authentication) reports `authenticated Windows bond required; run laptop.windows_pairing first` (`laptop/windows_pairing.py:22-25`). An existing weak bond is not upgraded automatically: remove the board in Windows first, then pair again. A pairing failure reports `authenticated passkey pairing failed (<status>); deliberate bond recovery may be needed`.
6. After flashing a board, check it alone: `python -m tools.check_board left` or `right` (see "Checking one board"). Reflashing the application does not erase the bonds: on 2026-10-14 Windows kept its authenticated bond with the right board through two reflashes, and no new pairing was needed. Whether the left board keeps its bond through the version-3 reflash is not yet known. Neither board has been flashed with the current firmware yet (see "Local state").

### Normal path (`python demo.py run`)

1. Terminal A runs `python demo.py tunnel`. It starts an ssh child process that forwards local `127.0.0.1:18889` to `127.0.0.1:8888` on the Ultra96. Keep this terminal open.
2. Terminal B runs `python demo.py run` (`--ca` can be left out when the default local CA path exists). Without addresses it reads the board map and prints `Board mapping: LEFT / ID 1 = …; RIGHT / ID 2 = …`. Then it checks that the CA file exists, that the two addresses differ, that standard input is a terminal when `--keyboard` is set, and that the `--file` size is between 1 and 65536 bytes. If any check fails, it ends with exit code 2 and creates no capture folder (`demo.py:222-236`).
3. `demo.py` creates the folder `B07-…` and starts the child process `laptop.dual_bridge`. It writes the child's output line by line into `live.log` and shows it in the terminal.
4. The child first reserves `report.json` (`status: incomplete`). If the path already exists, it prints `report reservation failed: …` and ends with exit code 2 without touching hardware (`laptop/dual_bridge.py:522-531`).
5. The child creates one `PacketEvidence` (background thread named `packet-evidence`) and two `Bridge` objects. All coroutines run in one asyncio event loop.
6. Each board starts two tasks, `writer-N` and `input-N`. With controls enabled it adds `commands-N`. `demo.py` always passes `--rate`, so controls are always enabled.
7. `input-N` scans. It filters advertisements by service UUID, then by address (case-insensitive), for at most 8 seconds (`laptop/bridge.py:705-709`).
8. Connect: `make_ble_client` does not use the cached service table. At most 20 seconds.
9. It checks that the sensor characteristic supports Notify and that `mtu_size` is at least 41 (`SENSOR_MTU_FLOOR`, the 38-byte packet plus the 3-byte ATT header). Otherwise it abandons this connection (`laptop/bridge.py:718-723`).
10. It checks that the Windows bond level is "encryption and authentication" (`laptop/bridge.py:725-727`).
11. It requests the throughput preference, but only on Windows and only when `--rate` is above 10. The default 10 Hz makes no request, and the report records `baseline_rate_no_preference_requested`.
12. It reads the source statistics as the start snapshot. A wrong length (anything but 36 bytes), reserved bytes, magic (anything but `LCS3`), unknown flag bits or `device_id` fails (`laptop/bridge.py:740-760`). The snapshot's gated flag tells the laptop which coverage rule applies to this board. On reconnect it reads them again, but the start point does not change; it records one interruption.
13. Control channel: it checks both control characteristics, requires an MTU of at least 64, subscribes to the response characteristic, sends `SET_RATE` and checks the echo (`laptop/bridge.py:761-775`).
14. It enables the receive queue (the generation equals this connection's number), subscribes to the sensor characteristic, notes the time of the first sensor subscription (the start of `source_ticking_seconds`), and marks this board "active" (`laptop/bridge.py:776-787`).
15. Once both boards are active, the common observation window starts. Startup waits at most 30 seconds.
16. Each notification is handled in the BLE callback (`laptop/bridge.py:290-315`). The callback records the arrival time and copies the bytes into the queue (when the queue is full, it drops the oldest and counts it). Then it decodes the packet once for goodput and hands a `sensor` or `sensor_invalid` record to the evidence thread. Last, it updates the callback count and the observation window's silence statistics. The callback does no network operations. A lock protects the queue, and `call_soon_threadsafe` wakes the writer.
17. The sender side of `writer-N` first takes an ACK slot (at most 32), then takes a packet from the queue.
18. It validates the packet: decoding, identity, sequence number, connection generation, freshness. A packet that stayed on the laptop for more than 2 seconds is dropped and counted as `stale_dropped` (`laptop/bridge.py:403-430`). A packet that does not decode as version 3 counts as `malformed`.
19. If there is no TLS connection, it connects to `127.0.0.1:<port>` now and verifies the certificate against the fixed server name `ultra96.week7.internal`. After connecting, it checks generation and freshness again (`laptop/bridge.py:568-580`).
20. It writes one `SENSOR_BATCH` frame (`v` 3, `request_id` null). The write timeout is the smaller of `io_timeout` and the remaining freshness. A written frame enters the pending-ACK queue.
21. The receiver side of `writer-N` reads ACKs in FIFO order and compares each one only with the head of the queue. On a match it increments `acked` and releases a slot. Each frame's ACK must arrive within 5 seconds of its send time.
22. When the observation window ends, it first stops the keyboard, the file transfer and the commands. Then it tells both boards to stop at the same time.
23. Each board does its tail handling independently (see the next section).
24. It waits for both boards' queues and in-flight frames to empty, for at most 10 seconds. Then it cancels the writer tasks and closes TLS.
25. It computes the verdict, writes `report.json` atomically, and prints the same JSON to stdout. A clean run exits 0; otherwise the exit code is 1.
26. `demo.py` writes `exit-code.txt` and reviews the report. It prints a "generated, received, acknowledged" table per board, with the columns `Device  Generated  Received  ACKed  MissingBLE  MissingACK  Gated  Idle`, and one packet example pair per board. `Gated` is `yes`, `no` or `N/A`, and `Idle` is `source_idle`, the send ticks a gated glove skipped while still; both are for information and do not change the verdict (`demo.py:181-190`). Only if everything passes does it print `CAPTURE PASSED: physical ESP input through Ultra96 ingestion ACKs.` and `Phone expected increase: N`. N is the sum of both boards' `generated` plus the number of completed commands. Under it, `demo.py` prints `This count holds while the Ultra96 runs the built-in dummy model (one result per accepted sample or command).` (`demo.py:213-217`; see "One input, one result"). The phone count is compared by hand; the tool does not check it.

### Tail handling at shutdown (`laptop/bridge.py:810-945`)

When shutdown starts, an overall deadline is set: the current time plus `connect_timeout` (20 seconds, `laptop/bridge.py:816`). Steps b to f are all bound by this deadline.

- a. It detaches the control channel and stops notifications on the response characteristic (0.75 s).
- b. Only on a normal stop, while subscribed, still connected and with source statistics enabled, it writes the sensor characteristic's CCCD to NONE through WinRT (at most 0.75 s). The local callback stays. On non-Windows, or without the native interface, this step returns False, and c and d are skipped (`laptop/ble_shutdown.py:12-23`).
- c. It reads the source statistics again without the cache to get the "quiesced snapshot". The boot ID must equal the start. The expected received count equals the increase in `submitted`. The time this read returns ends the board's ticking interval (`source_ticking_seconds`; `laptop/bridge.py:844`, `904-907`).
- d. It waits for the processed packet count to reach the expected value, for at most 0.5 s. On timeout it records one `source_tail_drain` (`validation=timeout`) and one `source_stats_errors`.
- e. `stop_notify` removes the local callback (0.75 s). This step is skipped when the native operation from b has not finished.
- f. It reads the source statistics once more as the end snapshot (uncached if c ran). It must equal the quiesced snapshot exactly, all 36 bytes: an idle, unread or refused tick counted after the quiesce read is a change too, because the firmware commits no tick once notifications are off. Otherwise it reports `source changed after notifications were quiesced`. When c did not run, the time of this read ends the ticking interval instead.
- g. The queue stops accepting new callbacks. Only on a normal stop where e succeeded are the queued tail packets kept for the writer to send. Otherwise the queue is cleared and the packets count in `callback_generation_dropped` (`laptop/bridge.py:920`).
- h. It refreshes the connection parameter record, disconnects (its own 1.0 s), and releases the throughput preference handle.

### Commands, rate setting, files

1. Key `1` targets device 1 (left) and key `2` targets device 2 (right). Each key press creates a version-3 packet: the 11 values are a random row from `common/dummy_fixtures.json`, `uptime_ms=0`, and `seq` is a new request ID (`laptop/bridge.py:262-267`). Commands go through the control channel, so a gated glove answers them while it is still too. When the command queue is full (8 entries) or the board is not connected, the command is rejected and logged as `command_rejected`. `rejected` does not affect the verdict.
2. A board has only one control transaction at a time. After writing a request, the laptop waits for the response, with `io_timeout` as the timeout.
3. The request packet must be version 3, for this board and boot, with `uptime_ms` 0. The response must be version 3 with the same `device_id`, `boot_id` and `seq`, and each of the 11 values must be exactly 1 higher, 32767 wrapping to −32768 (`laptop/controls.py:185-198`, `common/control.py:119-121`). The response's `uptime_ms` is the board's clock; it is logged in `command_modified`, not checked.
4. After validation, the laptop opens a separate TLS connection for this command. It sends one `SENSOR_BATCH` frame with `request_id`, waits for one ACK, then closes. `status` must be `accepted`. The command does not use the data stream's sequence numbers or ACK counts (`laptop/bridge.py:269-288`). On the Ultra96 a command never reaches the model; the service answers it with one `cmd:` result of its own (hand-off document, section 6.5, D11).
5. A command that times out is not retried. It is recorded as failed.
6. The request ID (shared by commands, rate setting and files) starts at a random number between 1 and 0x7FFFFFFE and increments. 0xFFFFFFFF itself can be used. Only taking the next one reports `control request identity space exhausted; restart capture` (`laptop/controls.py:40`, `64-69`).
7. File transfer steps: send `FILE_BEGIN`. Then split the file into chunks of `min(180, MTU-17)` bytes and wait for each chunk's confirmation; the confirmation's `offset` must equal the start of the next chunk. Finally send `FILE_END`. The length and SHA-256 the receiver returns must match the sender's. On any failure, the laptop tries to send `FILE_ABORT` while the same connection is still up.

Time limits, exclusivity and retry boundaries of the file transfer:

- The transfer starts when the common observation window starts (`laptop/dual_bridge.py:185-187`). If it has not finished when the window ends, it is cancelled and recorded as `file:interrupted`, and the run is not clean. After cancellation the laptop still tries to send `FILE_ABORT`.
- The whole transfer holds the control channel's serial lock (`laptop/controls.py:223`). Key commands wait until the file finishes. The command queue holds only 8 entries; further presses are rejected.
- A chunk is retried only after a timeout, at most 2 more times. When the board returns a non-zero status (for example 2 `BUSY`), the laptop does not retry. It fails and aborts at once, and `controls.response_errors` increases by 1 (`laptop/controls.py:126-134`).
- After a retry, if the first attempt's response arrives late, it is recorded as `duplicate_responses` or `response_errors`. The run is then not clean either.
- A BLE reconnect midway does not resume the transfer. It reports `file interrupted by BLE disconnect`.
- A successful result is written to `file_transfer` in `report.json`: `transfer_id`, `bytes`, `sha256`, `elapsed_seconds`, `sender_bytes`, `sender_sha256`, `receiver_bytes`, `receiver_sha256`, `file_payload_kbps`, `verified`.
- The command line reads at most 65537 bytes to tell whether the file is too long (`laptop/dual_bridge.py:492-500`).
- Only 4096 bytes have been tested (23 chunks, once on each board). 65536 bytes is about 365 chunks, and each chunk is one write with response plus one notification. Whether that finishes under the default 60 seconds, 10 Hz and no throughput preference has not been tested.

### Failure paths

| Situation | Behavior | What the report shows |
|---|---|---|
| Not found by the scan, connection failure, MTU too small, bond level too low | This attempt ends. `ble_errors` increases by 1, and `live.log` has `BLE attempt failed: …` (`laptop/bridge.py:809`). Retry after back-off | If the board does not become active within 30 seconds, `runtime_failures` contains `startup:TimeoutError` and the observation window duration is 0 |
| Source statistics unreadable or malformed | Does not subscribe to the sensor. `source_stats_errors` and `ble_errors` each increase by 1. Retry after back-off | `source_issue` asks for a firmware update |
| The board still runs older firmware: the version-3 build of 2026-10-14 (24-byte `LCS3`; the right board), version 2 (32-byte `LC` packets, `LCS1`; the left board) or Week 7 (`W7`, `W7S1`) | Reading the source statistics reports `source statistics must contain exactly 36 bytes; flash this board with the current firmware` (all three answer 24 bytes). This connection is abandoned and retried after back-off. The board never becomes active and never reaches the "malformed packet" step | `ble_errors` and `source_stats_errors` grow, `runtime_failures` contains `startup:TimeoutError`, and `source_issue` asks for a firmware update. Only the single-board tools that do not read source statistics record version-2 and Week 7 packets as `malformed` (wrong length); the 2026-10-14 build sends valid 38-byte packets |
| A gated glove stays still for the whole capture, or its sensor failed at boot | Nothing is sent: the ticks count as `idle` (still) or `unread` (no valid sample; a board whose `gloveBegin` failed still advertises and connects). The connection stays up | `generated` is 0, so `source.clean` is false and the run is not clean. For a failed sensor, `source_unread` is close to `source_ticks`, and coverage fails too |
| A gated glove stays still longer than the Ultra96's ingest idle limit (`--ingest-idle-timeout`, default 600 s), or the service closes its quiet connection because all 8 client slots are full and it has waited longest (at least 5 s) | The laptop does not see the close until it sends again: the next frame fails as in the row "TLS disconnect" below, and the laptop reconnects (see [chapter 4](04-ultra96-service-and-certificates.md)). Before 2026-10-15 the service closed an ingest connection after 5 s without a frame, which would have cost frames after every pause of a gated glove; that is why the limit was raised (built; not deployed) | `transport_errors`, `ambiguous_dropped`; the run is not clean |
| The BLE link drops during the run | `disconnects` increases by 1. The remote notification stop is skipped, but the local disconnect still happens. The queue is cleared and counted in `callback_generation_dropped`; those samples are not resent, so the Ultra96 sees a gap in `seq`. While disconnected the board makes no samples, so that time shows only as a jump in `uptime_ms`. Reconnect waits until the previous native operation ends | `source.interruptions` is greater than 0, and this board is not clean. The other board continues |
| The board reboots | After reconnect the boot ID has changed | `new_boots`, `boot_mismatches`. The start and end snapshots have different boot IDs, and `generated` is `null` |
| TLS cannot connect (tunnel not open, certificate expired, host name mismatch) | This packet was dequeued but not written, so it does not count in `ambiguous_dropped`. The next packet triggers a reconnect after back-off | `transport_errors` grows, `acked` is 0, and later packets become `stale_dropped` or `queue_dropped`. In the reconciliation, `missing_acked` is greater than 0 |
| TLS disconnect, write timeout, ACK timeout or mismatched ACK | This TLS connection is discarded. All in-flight frames and frames whose write was attempted count as `ambiguous_dropped` and are not resent; any of them the Ultra96 had not processed leaves a gap in `seq` there. The connection is closed, and the next packet triggers a reconnect after back-off | `transport_errors`; on an ACK timeout or mismatch, `ack_errors` also increases by 1; `ambiguous_dropped` |
| ACKs are slow | Once the 32 slots are full, the sender waits. A packet that stays in the queue for more than 2 seconds is dropped | `stale_dropped` |
| Queue full | Drops the oldest | `queue_dropped` |
| Malformed packet (not 38 bytes, not `LC`, not version 3) or wrong `device_id` | Not forwarded | `malformed`, `identity_mismatches` |
| At shutdown the tail packet does not arrive, or the end snapshot changed | Records an error and hides nothing | `source_stats_errors`; `source.clean` is false |
| The writer task ends permanently (ACK window greater than 1) | The writer loop catches only `_PipelineTransportError` (`laptop/bridge.py:668`). Three other cases raise `_PipelineCleanupError`, which nothing catches: a worker coroutine of the old TLS generation (`epoch` in the code) did not exit within 0.2 s (`laptop/bridge.py:526-534`, `654`); a pending frame belongs to another generation (`:607`); a worker coroutine ended without a reason (`:648`). Then `writer-N` ends and is not restarted. Until the capture ends, this board's later packets only enter the queue and are evicted | `runtime_failures` contains `writer:_PipelineCleanupError`, usually also `drain:timeout` and `queue_dropped` |
| Shutdown hangs | The input task is cancelled after 25 seconds, then waited on for 0.5 s more. Drain waits 10 seconds. The writer task waits another 25 seconds. Final event-loop cleanup waits only 0.1 s (`laptop/dual_bridge.py:603-622`) | `shutdown:timeout`, `drain:timeout`, `writer:timeout` |
| The evidence queue overflows or a disk write fails | Does not block packet reception | When `evidence.dropped`, `write_errors` or `unfinished` is non-zero, the overall `clean` becomes false |
| The report save fails | stdout still prints the JSON | `report_saved` is false, `report_error` is the exception name, and the exit code is non-zero |
| The operator presses Ctrl+C | `demo.py` terminates the child it started (force kill after 5 seconds) and writes 130 to `exit-code.txt` | The report stays at `incomplete`, and the review fails |
| The SSH tunnel drops | Shows up as a TLS failure. Run `demo.py tunnel` again in terminal A | Same as a TLS disconnect |

**Neither end records why something was rejected.** On the laptop, a TLS connect or handshake failure increments only `transport_errors`. An ACK timeout or a mismatched ACK increments both `ack_errors` and `transport_errors`. None of these records a reason (`laptop/bridge.py:469-473`, `668-669`). Only BLE failures write `BLE attempt failed: …`. On the Ultra96, a bad frame, a session mismatch, an identity conflict or exhausted capacity also only closes the connection and increments `rejected` (see [chapter 4](04-ultra96-service-and-certificates.md)). The consequence: no log on either side says why. On the laptop, an expired certificate and an unreachable port look the same (only `transport_errors` grows), and a mismatched session ID and mismatched protocol versions between the two ends look the same (the Ultra96 closes the connection after the frame, so both `ack_errors` and `transport_errors` grow). This is one reason only the newest version is supported and everything is upgraded together (hand-off document, section 8, step 1). **It is the situation right now:** the version-3 laptop code against the version-2 service still on the Ultra96 (hand-off document, section 6.3) shows up only as this "silent disconnect", with no ACK at all. Redeploy the service (`tools/deploy_service.py`) before the first capture. On the BLE side the version mismatch is clear: a board with older firmware is refused by the length or the marker of its source statistics, with a message that names the cause.

### Complete list of `runtime_failures` markers (`laptop/dual_bridge.py`)

| Marker | Meaning | Lines |
|---|---|---|
| `startup:<exception name>` | did not become active within 30 seconds | 175 |
| `input:stopped`, `input:<exception name>` | the input task ended early inside the observation window | 203-207 |
| `writer:stopped`, `writer:<exception name>` | the writer task ended inside the observation window, or ended with an exception during shutdown | 208-216, 314-317 |
| `writer:timeout` | the writer task did not exit within 25 seconds during shutdown | 304 |
| `keyboard:error` | the keyboard task failed; recorded on device 1 whichever key was pressed | 196-197 |
| `file:shutdown_timeout`, `file:interrupted`, `file:<exception name>` | the file transfer did not finish its cleanup, was cancelled, or failed | 231, 234, 236 |
| `commands:drain_timeout`, `commands:shutdown_timeout` | the command queue was not drained within 10 seconds; the command task did not exit within 25 seconds | 249, 256 |
| `shutdown:<exception name>`, `shutdown:timeout` | the input task's shutdown failed or timed out | 269, 272 |
| `drain:timeout` | the queue or the in-flight frames did not empty within 10 seconds | 296 |
| `transport_close:<exception name>` | the final TLS close failed | 325 |

### Verdict: `clean`

The overall `clean` is true only when all of these hold (`laptop/dual_bridge.py:333-370`, `561-581`): both boards became active within 30 seconds; the progress callback never raised an exception (`progress_error` is false); both boards are `clean`; the evidence `dropped`, `write_errors` and `unfinished` are all 0; the report was saved.

Each board's `clean` is true only when:

- `runtime_failures` is empty.
- `source.clean` is true.
- Coverage and silence both pass (`sustained_coverage` and `silence_ok`; for a gated board by the rules under "Gating in the report"), `protected_ble` is true, and `unfinished` is false.
- These 18 fields are all 0: `malformed`, `stale_dropped`, `generation_dropped`, `duplicate_acks`, `ack_errors`, `ambiguous_dropped`, `transport_errors`, `ble_errors`, `cleanup_errors`, `identity_mismatches`, `source_stats_errors`, `disconnects`, `queue_dropped`, `callback_generation_dropped`, `gaps`, `duplicates`, `out_of_order`, `new_boots`.
- `commands.failed` and `commands.pending` are 0 (`commands.rejected` does not matter).
- The four `controls` counts `response_errors`, `duplicate_responses`, `notification_dropped` and `native_pending` are all 0.
- `sensor_goodput.tracking_overflow` is 0.

Easy to miss: a single `INGEST_ACK` whose `status` is `duplicate` makes the board not clean. `duplicate` proves that the Ultra96 received the packet (level 3), and it also makes the run not clean. The two do not contradict each other.

`demo.py` adds its own criteria on top (`demo.py:143-159`) and requires the packet example review to pass (`demo.py:209-212`). See "How to run and verify".

### Checking one board (`python -m tools.check_board left|right`)

Added on 2026-10-14 for checking each board right after it is flashed, without the Ultra96 (hand-off document, section 6.5, D16). It contacts only the named board, by its address in `.comms-local/boards.json` (or the built-in default), so the other board may stay powered (`tools/check_board.py:154-155`).

1. Unless `--pki-dir` is given, it generates a throwaway CA and server certificate in a temporary folder outside the repository (`generate_pki`, which needs `cryptography` from `requirements-dev.txt`) and deletes them afterwards (`tools/check_board.py:156-161`).
2. It starts a `CommsServer` on the laptop on free ports, with the default session `ltc-comms` and the built-in dummy model, and subscribes to it like the phone would (`SUBSCRIBE`/`SUBSCRIBED`, `v` 1) (`tools/check_board.py:64-71`). Every result is validated with `validate_message` and counted as a stream or a `cmd:` result; a repeated `result_id` is an error (`:75-88`).
3. It runs one `Bridge` against that service with source statistics, controls and an ACK window of 32 (`:91-93`). The rate command is sent at connection. Two seconds after the rate is confirmed, it submits the commands one at a time, waiting for each to finish and 0.5 s between them (`:98-105`).
4. After `--duration` it waits for the command sender (at most 10 s + 15 s per command), then for the command queue (10 s), then stops the BLE stream normally, so the remote notifications are turned off and the final source statistics are read (30 s), drains the queue and in-flight frames (10 s) and allows 0.5 s for the last results (`:111-125`). A BLE loop that ends early is an error (`:114-116`).
5. Verdict (`tools/check_board.py:34-59`): the source statistics are clean and complete; something was acknowledged; generated = received = acknowledged; `malformed`, `ack_errors`, `transport_errors`, `ble_errors`, `cleanup_errors`, `queue_dropped`, `stale_dropped`, `gaps`, `duplicates`, `out_of_order` and `identity_mismatches` are all 0; the rate is confirmed; the negotiated MTU is at least 41; the dummy-model results equal the acknowledged samples; completed commands and `cmd:` results both equal `--commands`; the subscriber saw no error.
6. Output: the whole summary as one JSON line (also written to `--report` when given; it includes `server_metrics` with the model counters), then one summary line, then one line per failed criterion. Exit code 0 on a pass, 1 otherwise (`:164-174`). The summary line is (`summary_line`, `:177-187`):

   ```text
   CHECK PASSED RIGHT (device 2): generated=… received=… acked=… commands=n/m gated=<yes, no or unknown> idle=… unread=… refused=…
   ```

   `commands=n/m` is the `cmd:` results received over the commands requested. `idle`, `unread` and `refused` are `source_idle`, `source_unread` and `source_refused`; they read `None` when the source counts are unknown. They are for information: a gated board's idle ticks do not fail the check. It writes no `packets.jsonl` and opens no observation window, so goodput reads 0 and coverage is not judged.

A gated board must still send something: "nothing acknowledged" and an unclean source (`generated` 0) both fail. So a glove flashed with the `-glove` firmware must be moved during the check, and the first part of each movement (a few hundred milliseconds) sends nothing (see "Flashing the real gloves").

What it proves: one board's firmware, bond, MTU, rate setting, control channel and source reconciliation, and the laptop relay against the version-3 service code with the dummy model. What it does not prove: SSH, the real Ultra96, the phone, two boards at once, or real sensor data. Because it runs the dummy model, its "one result per sample" check holds only for that model.

Verified on the right board (2026-10-14, after the version-3 reflash; evidence in `.comms-local/checks/2026-10-14-right-board-v3/`): `python -m tools.check_board right --rate 50 --duration 65 --commands 3` gave `CHECK PASSED`: boot ID 3866582580, `LCS3` statistics clean and complete, 2934 generated = 2934 received = 2934 acknowledged (`seq` 0 to 2933), ATT MTU 517, 50 Hz confirmed, connection interval 15 ms, longest receive silence 63 ms, 3/3 commands in 52-byte control frames with their 3 `cmd:` results, 2934 samples to the dummy model and 2934 results back, slowest model call 0.387 ms, no error of any kind. After the review fixes (`a4b907b`), a short run of 10 s with 8 commands also passed: 320 = 320 = 320, 8/8. Those runs used the firmware and laptop code of 2026-10-14, with 24-byte statistics and no gating. The current code has not been checked on a board: the right board was unplugged on 2026-10-15 before the gated build could be flashed, and the current laptop code refuses the build it holds (24 bytes). The left board has not been checked under version 3: it still runs version-2 firmware (hand-off document, section 6.3).

Not done yet (hand-off document, section 6.3): flash a board with the current firmware and check it as above; then check the gated dummy, built with `$env:PLATFORMIO_BUILD_FLAGS = "-DCOMMS_DUMMY_MOVING_MS=3000 -DCOMMS_DUMMY_IDLE_MS=7000"` set in the PowerShell terminal before flashing (3 s sending, then 7 s idle, repeating from boot; `flash.py` passes the terminal's environment to PlatformIO, `flash.py:24-27`, so clear it afterwards with `Remove-Item Env:PLATFORMIO_BUILD_FLAGS`, or every later build in that terminal gets the switch too), which should pass with `gated=yes` and an `idle` count of about seven tenths of the ticks; and flash a `-glove` build on one of the owner's boards, which has no glove sensor, to confirm that it prints `glove_begin ok=0`, does not block and still advertises. From the code, such a board counts every tick as `unread`, so `tools.check_board` itself fails there with nothing acknowledged.

### Flashing the real gloves (`python flash.py --glove`, `tools/sync_glove_module.py`)

Added on 2026-10-15 (`e24f8ea`, `d582ce6`). Built: the `-glove` environments compile and link, and the tool and the flash order are unit-tested. Nothing of it has run on a glove.

Siqiang's module lives in `hardware/gloves/integration_files/` (team commit `51593be`, 2026-10-15): `glove_sensor.cpp`, `glove_sensor.h` and the weights header `movement_model_params.h`. Communications must not edit that folder, and PlatformIO builds only from `firmware/esp32/`. So the firmware builds unchanged copies:

1. `python -m tools.sync_glove_module` copies the `.cpp` and `.h` to `firmware/esp32/lib/glove_sensor/src/`, and `movement_model_params.h` to both `firmware/esp32/` and `firmware/esp32/lib/glove_sensor/src/` (`tools/sync_glove_module.py:26-32`). The copies are tracked in Git; `firmware/esp32/lib/glove_sensor/README.md` says not to edit them. Run it after the module changes in the team repo.
2. `python -m tools.sync_glove_module --check` changes nothing. It compares content with CRLF read as LF, prints `out of date: <name> (run python -m tools.sync_glove_module)` for each stale copy and exits 1; it exits 0 when all match, and 2 with `FAILED: … not found; merge the team main first` when a source file is missing (`:35-43`, `:57-65`). `tests/test_glove_module_sync.py` fails while a copy differs.
3. Why the header is copied twice: line 4 of `glove_sensor.cpp` includes `"../../../movement_model_params.h"`. From `lib/glove_sensor/src/` that path is `firmware/esp32/`. From where the file lives, it is the repository root, where no such file exists, so the file does not compile in its own folder. `#include "movement_model_params.h"` would fix it, and the second copy makes that form work too. This was reported to the owner; Siqiang's file is untouched.
4. `python flash.py --glove` runs `tools.generate_dummy_fixtures`, then `tools.sync_glove_module --check`, then builds and flashes `firebeetle32-left-glove` and `firebeetle32-right-glove` in the usual plug-in order, and writes `.comms-local/boards.json` like an ordinary flash (`flash.py:90-124`). A stale copy stops it before any build, with `FAILED: command exited with code 1; remaining operations were not run.`. The map then names the gloves, which need their own pairing (`python flash.py --pair`).
5. The `-glove` environments (`firmware/esp32/platformio.ini:42-58`) set `COMMS_GLOVE_MODULE=1`, link the module (every other environment ignores it, `:12-14`) and start at 50 Hz (`COMMS_INITIAL_RATE_HZ=50`). The laptop's rate command still sets the rate at connection (see "Usage cautions").

The send decision is `gloveShouldSend()`, which returns `gloveIsMoving()` (`firmware/esp32/src/glove_module.cpp:10-18`). A `-glove` build is gated: its statistics carry the gated flag, and the laptop judges it by the gated rules. Built with `-DCOMMS_GLOVE_SEND_ALL=1`, it sends every sample, IDLE included, and is not gated, so the ordinary coverage and silence rules apply. The firmware side (`gloveBegin` before BLE, about 5.1 s of calibration with the glove held still; `gloveUpdate` every loop pass; `gloveRead` at each send tick) is in [chapter 2](02-firmware.md).

What the laptop will see from a gated glove (from the code and Siqiang's answers; not yet observed):

- Sending starts some time after a movement starts and stops some time after it ends: his detector judges a 1 s window every 200 ms and says MOVING after two consecutive windows above its threshold, IDLE after three below (`hardware/gloves/integration_files/glove_sensor.cpp:46-50`, `:381-389`). So sending starts no earlier than about 0.2 to 0.4 s after the movement starts, and typically later, depending on how fast the 1 s window crosses the threshold. It stops at least about 0.4 to 0.6 s after the movement ends (three windows below the threshold). These are estimates from the code, not measurements. Samples before the MOVING decision are never sent and cannot be sent later. The two gloves gate independently, so one can be silent while the other sends.
- His module resets its movement classifier after any failed IMU read, any non-finite sample, or more than 100 ms between two `gloveUpdate` calls. `gloveIsMoving()` then stays false for about 1.2 s (the 1 s window refills, then two evaluations 200 ms apart must agree; `glove_sensor.cpp:301-311`, `:396-416`; the figure reported to the owner was about 1.4 s), even in the middle of a gesture, and the board counts idle ticks meanwhile. In the Communications firmware `gloveUpdate` runs every 1 to 2 ms, so only the first call after boot (before any laptop connects) and a transient I2C failure (2 ms timeout) can trigger it. This was reported to the owner.
- His classifier runs only when the weights header defines `MOVEMENT_MODEL_TRAINED` as 1 (`hardware/gloves/integration_files/glove_sensor.cpp:313`, `:395`). The current header does (`hardware/gloves/integration_files/movement_model_params.h:3`). A header with 0 would leave `gloveIsMoving()` false for ever, so a gated glove would send nothing and every capture would fail with `generated` 0; a build with `-DCOMMS_GLOVE_SEND_ALL=1` would still send.

### Recording glove data through the chain (`tools/export_capture.py`)

Added on 2026-10-15 (`5d2e52f`) because Siqiang asked whether he can still record data. His Bluetooth Classic recording script cannot connect to the Communications firmware, which speaks only BLE. He can flash his own sketch for his own recordings, or record through the chain like this. Built (unit tests); never run on a real capture.

1. Flash the gloves with `python flash.py --glove` and pair them. To keep the IDLE samples too, run `$env:PLATFORMIO_BUILD_FLAGS = "-DCOMMS_GLOVE_SEND_ALL=1"` in the PowerShell terminal before flashing (not yet tried), and clear it afterwards with `Remove-Item Env:PLATFORMIO_BUILD_FLAGS`, or the next flash in that terminal keeps sending IDLE samples.
2. Capture with `python demo.py run --rate 50 --duration <seconds>` (or `live`). Pass `--rate 50`: `demo.py` always sends its rate (default 10) at connection, which overrides the 50 Hz the `-glove` firmware starts at. A capture needs both gloves connected within 30 s, and it sends to the Ultra96 through the tunnel like any capture. `tools.check_board` writes no `packets.jsonl`, so it cannot record.
3. Export with `python -m tools.export_capture`. Without arguments it reads the newest capture's `packets.jsonl` and writes `samples.csv` beside it, then prints `<N> samples written to <path>`. `python -m tools.export_capture <capture folder or packets.jsonl> --out data.csv --device 2` picks the capture, the output file and one glove.

The CSV (`tools/export_capture.py:66-75`) has the header `device_id,glove,boot_id,seq,uptime_ms,ax,ay,az,gx,gy,gz,yaw,pitch,roll,flex1,flex2` and one row per sample in arrival order. `glove` is `left` or `right`. The 11 values are int16 / scale, the same `physical_values` the Ultra96 applies before `on_sample`, printed with 4 decimals, in g, °/s, degrees and 0 to 1.

Rules (`tools/export_capture.py:41-63`, `:85-103`):

- Only `sensor` records count. A line that is not JSON, such as the torn last line of an interrupted capture, is skipped.
- A sample seen twice (same device, boot ID and `seq`) is written once.
- Each record is rebuilt as a `SensorPacket`, so a record that is not a valid version-3 sample (for example 8 values from a version-2 capture) stops the export with `FAILED: …` and exit code 2. So do a missing capture and an existing output file (`… exists; choose another --out`): the tool never overwrites. The CSV is opened and its header written before the records are checked (`tools/export_capture.py:66-75`), so a failed export leaves a partial CSV behind; delete it or pass another `--out` before retrying.
- The CSV holds every sample the laptop accepted from BLE, whether or not the Ultra96 acknowledged it. Samples the evidence writer dropped under load are missing; the tool then prints a warning with the count from `report.json` (`evidence.dropped`). Whether the capture lost anything is the report's verdict (`python demo.py report`), not the CSV's.
- In a gated capture, `seq` runs on without a gap across a still period; the pause is the jump in `uptime_ms`.

### Deploying the Ultra96 service (`python -m tools.deploy_service`, laptop half)

Added on 2026-10-14 as the tracked successor of the untracked September script `.week7-local/co_deploy.py` (hand-off document, section 6.5, D15). The owner runs it from the repository root, with the VPN on and the branch to deploy checked out, and types both passwords; nothing is stored. Its board-side program and the statuses it records are described in [chapter 4](04-ultra96-service-and-certificates.md) and in section 6.3, step 1 of the hand-off document. The laptop half:

1. Validates the options before it connects anything: the session ID rule, `--model-path` only with `--model`, `--start-timeout` from 5 to 300 s (`tools/deploy_service.py:310-317`). With `--server-cert-dir`, the folder must hold both `server-cert.pem` and `server-key.pem` (`:320-328`).
2. Collects exactly the files the board runs: `common/*.py`, `common/*.json` and `ultra96/*.py` (`:288-297`), and names a new board folder `BOARD_ROOT/source-co-v3-<UTC stamp>` (`:358-359`). It prints the folder, the file count, the certificate plan and the options. With `--dry-run` it stops here: nothing is connected or changed (`:360-366`).
3. Opens the two SSH hops with `paramiko`: the jump host `stujump.comp.nus.edu.sg` as `--jump-user` (default `yanjie`), then a `direct-tcpip` channel to the Ultra96 (`makerslab-fpga-35.ddns.comp.nus.edu.sg`) as `--board-user` (default `xilinx`). Both hops check host keys strictly against `~/.ssh/known_hosts` (`RejectPolicy`), use only a password typed at a hidden prompt (no key files, no agent), and have a 10 s connect and 15 s authentication limit (`:39-40`, `:331-351`). `paramiko` is imported only here, when the tool connects (`:332`), so a `--dry-run` does not import it. `requirements-dev.txt` lists it since 2026-10-14 (`paramiko>=2.8,<4`); `laptop/requirements.txt` does not. On this laptop it comes with Anaconda, version 2.8.1.
4. Uploads the files over SFTP into the new folder (mode 700), with `source-manifest.json` holding each file's SHA-256, and, with `--server-cert-dir`, the certificate pair into `tls-incoming/` with the key at mode 600 (`:370-382`).
5. Runs the board-side program with `/usr/bin/python3 -c` and waits at most 2 × `--start-timeout` + 120 s for its answer (`:383-387`). If nothing comes back in time, it prints that the board may still be finishing or rolling back, and asks the operator to run `python demo.py service` and read `BOARD_ROOT/evidence/active-deployment.json` before trying again; exit code 1 (`:392-396`).
6. Prints the board's output and saves the board's final record (its last JSON line) as `.comms-local/deployments/deployment-<UTC stamp>.json` (`:400-405`). That record is what `demo.py service --start` follows afterwards (see "Which code `demo.py service --start` starts"). Exit code 0 when the board reports success, 1 when it reports a failure, 2 for a local error such as a bad option or a missing file (`:406-410`, `:432-436`).

Status: the board-side program was verified on Linux only (WSL Ubuntu, Python 3.10, the Ultra96's Python version): 27 of 27 checks through `tests/linux/deploy_remote_test.sh`, including a deploy over a running version-2 service built from `5a004c6`, the team main, whose service code equals `c42b386` (hand-off document, section 6.1; evidence in `.comms-local/checks/2026-10-14-deploy-wsl/`). The SSH half has never connected: it needs the owner's login. No deployment has been made with it yet, so `.comms-local/deployments/` does not exist on this laptop.

## Why it is designed this way

Records cited: [Selected design] = `docs/archive/design/week7-selected-design-2026-09-06.md`; [Dual-board spec] = `docs/archive/design/specs/2026-09-17-dual-esp-reception.md`; [Dual-board plan] = `docs/archive/design/plans/2026-09-17-dual-esp-reception.md`; [09-19 test] = `docs/archive/test-evidence/dual-esp-physical-test-2026-09-19.md`; [09-28 test] = `docs/archive/test-evidence/co-live-deployment-2026-09-28.md`; [v2 protocol] = `docs/co-protocol-v2.md` as of `c42b386` (renamed `docs/co-protocol-v3.md` with the version-3 change); [Architecture draft] = `docs/archive/design/architecture-and-interface-draft-v0.1.md`; [Features plan] = `docs/archive/design/plans/2026-09-28-co-features.md`. The "rejected" options in the archived records are history only. They are not proposals to reopen now.

1. **Bounded queue, drop oldest when full, freshness 2 seconds.** Stale gesture data is useless. Memory must not grow however long a fault lasts. Rejected at the time: an unbounded queue; replaying the backlog after a disconnect. Source: [Selected design] item 10; [Architecture draft] section 11, "Drop stale sensor records rather than replaying old gestures." This 2 s is only how long a sample may wait on the laptop. The Ultra96 has its own 2 s limit on how long a result may wait on the board (queue plus write to the phone's connection, `ultra96/server.py` `get_timed` and `_send_results`), and the phone has its own 2 s display window counted from when it received a result. None of them is an end-to-end latency bound or a promise that the phone receives a result (hand-off document, sections 7.2 and 9.2).
2. **Frames written but not acknowledged are not resent.** The laptop cannot know whether the other end already processed the frame. A resend could produce a second result. Rejected at the time: automatic retransmission. Source: [Selected design] item 10; the implementation notes in [Dual-board spec].
3. **One independent path per board (its own BLE link, queue and TLS connection).** One board's stuck ACK or reconnect must not block the other board. Rejected at the time: one writer shared by both boards. Source: [Dual-board spec] "Scope and acceptance", point 2.
4. **ACK window of 32.** With stop-and-wait per packet, a single ACK wait on the remote route was measured at up to 2.375 seconds. Packets queued behind it waited more than 2 seconds and were dropped. Two 600-second remote tests lost 1 packet and 33 packets. 32 is roughly 2.4 seconds times 10 Hz, plus margin. Rejected at the time: keeping stop-and-wait (kept as window 1); relaxing the 2-second freshness. Source: [09-19 test] "Per-packet ACK timing diagnostic"; the implementation notes in [Dual-board spec].
5. **Read the source statistics once before subscribing and once after stopping.** A successful notification submission does not mean delivery. Looking only at the first and last received sequence numbers cannot detect a lost first or last packet. The sequence number is assigned before submission, so a sample whose submission failed also uses a sequence number. Rejected at the time: counting only the received packets. Source: [Dual-board spec] "Scope and acceptance", points 5, 6 and 7.
6. **At shutdown, turn notifications off on the remote side first, keep the local callback, then wait for the tail packet.** The ordinary `stop_notify` removes the callback as soon as it has written the CCCD. In a 100 Hz probe, the ordinary stop lost the last packet in 3 of 12 runs; the new method lost it in none of 12. Rejected at the time: using only `stop_notify`; adding a loss tolerance to the reconciliation. Source: [09-28 test] "Fresh post-fault baseline and regression checks" and "Final software verification".
7. **The disconnect has its own 1-second budget.** Two notification-stop timeouts once used up a shared 1 second, leaving the disconnect only 1 millisecond, and native resources were not released. Rejected at the time: one deadline shared by all cleanup. Source: [09-28 test] "Initial rate failure and investigation".
8. **GATT discovery does not use the cache.** A bonded Windows session once reported a cached MTU of 23 when the real value was 517. The cost is a slightly slower connection. Rejected at the time: using the cache by default. Source: [Selected design] item 17.
9. **Own WinRT pairing code.** `pair()` in Bleak 3.0.1 uses `CONFIRM_ONLY`, which can lower the protection level. Rejected at the time: Bleak's built-in pairing; Just Works; an extra HMAC or AES-GCM layer over BLE. Source: [Selected design] items 13 and 14; `laptop/windows_pairing.py:1-7`.
10. **At most 2 unfinished native BLE operations, and no reconnect before they finish.** WinRT operations may ignore cancellation; without a limit they pile up. The cost is that reconnect pauses when the native stack is stuck (`laptop/bridge.py:691-695`). Rejected at the time: starting a new connection right after a timeout. Source: [Selected design] item 19.
11. **SSH uses an explicit `ProxyCommand`, not `-J`.** Strict host-key checking, timeouts and `BatchMode` must each take effect on both hops. Interactive mode uses 20 seconds and 60 seconds because the time spent typing the password at the jump host counts against the target's connect time limit. Rejected at the time: `-J`; 10 seconds on both hops. Source: [Selected design] items 18 and 25.
12. **TLS runs inside SSH, with a fixed server name check and no plaintext mode.** The laptop connects to a local forward port, and it must still confirm that the other end is that Ultra96. Rejected at the time: verifying against `localhost`; turning verification off; mutual TLS. Source: [Selected design] item 11.
13. **Commands use a separate TLS connection and are not retried on timeout.** This way they do not use the data stream's sequence numbers or ACK counts. A retry could produce a second event. Rejected at the time: sharing the connection with the data stream; automatic retry. Source: [Features plan] "Architecture" paragraph and "Contracts"; `laptop/bridge.py:270`.
14. **The throughput preference is requested only above 10 Hz and is released with the connection.** It costs power and the number of devices that can be connected at once. An accepted request does not mean the parameters actually changed, so the two are recorded separately. Rejected at the time: always requesting it; treating "accepted" as "in effect". Source: [v2 protocol] "Protected BLE controls"; [09-28 test].
15. **The report is reserved first and replaced atomically, and never overwrites an existing file.** An interrupted capture is not mistaken for a finished one and does not overwrite another capture. Rejected at the time: writing directly at the end. Source: [Dual-board plan] "Approved live-progress and report follow-up — 2026-09-17".
16. **Results do not come back to the laptop.** The laptop is not a result relay; the phone dials out by itself. Rejected at the time: the laptop forwarding results to the phone. Source: [Architecture draft] section 4.2; [Selected design] item 7.
17. **Coverage threshold 90%, silence threshold equal to freshness.** This tolerates scheduling jitter at the start and stop edges, and still detects a stream that stops midway. The 90% applies only to the rate; the reconciliation still requires every packet. Rejected at the time: looking only at totals. Source: [Dual-board spec] "Scope and acceptance", point 10. A gated board is judged by its ticks instead (22).

The next four were decided within Communications on 2026-10-14 (evening) and are recorded with their status in section 6.5 of the hand-off document; they are open to the owner's review.

18. **Only version 3, and the source statistics marker follows it (`LCS3`).** The owner's rule allows one version only, so no laptop path keeps a version branch: one packet size, one field set with `request_id` always present, one value check. A board with older firmware must fail with a clear message at connection rather than as thousands of `malformed` packets, so the marker changed with the version while the 24-byte format stayed. (On 2026-10-15 the format grew to 36 bytes; see 23.) Source: hand-off document, section 6.5, D4, D6 and D7.
19. **The MTU floor and every size come from `common/sensor.py`.** `PACKET_SIZE` and `SENSOR_MTU_FLOOR` are computed from the struct, so a later layout change (for example a field added after the scale check) cannot leave a stale 35 or 32 behind on the laptop. Source: hand-off document, sections 4.2 and 12.6.
20. **A one-board check that needs no Ultra96 (`tools/check_board.py`).** Each board must be checkable right after flashing, while the Ultra96 is still on old code and the other board may be powered; it connects by address and stops the stream normally, so the source reconciliation is as strict as in a capture. Source: hand-off document, section 6.5, D16.
21. **`demo.py service --start` follows the deployment record, model included.** A fixed `BOARD_SOURCE` would silently restart old code after a redeploy, and a restart without the deployed `--model` would silently run the dummy model. The record holds the running process's own folder and arguments, which are validated before use. Source: hand-off document, section 6.5, D16 and D19.

The next four were decided within Communications on 2026-10-15, after Siqiang's answers of that day (hand-off document, section 7.1); they are open to the owner's review.

22. **A gated board is judged by the ticks it counted, over the time it counted them.** Siqiang's glove sends only while it is moving, so its received count cannot tell a still player from a stalled board, and a still player is silent for longer than `freshness`. The board's own idle counter proves that it kept ticking, so `generated` plus `source_idle` stands in for the received count, and silence is not judged once there are idle ticks. The counters cover the whole time notifications were on, which can start well before the common window and ends after it; comparing them with the window would let a board that subscribed early and then stopped ticking pass (`tests/test_dual_bridge.py` shows this). So the expectation uses `source_ticking_seconds`. Unread and refused ticks do not count: they are missing data, not stillness. The board declares itself gated in its own statistics, so the laptop needs no option for it. An ungated board keeps the old rules exactly.
23. **36-byte statistics with the marker kept at `LCS3`.** The laptop needs the gated flag and the three skip counters from the board, and the end snapshot must still prove that nothing changed after the quiesce. The 24-byte `LCS3` ran only on the right board and was never deployed further, so a new marker would add nothing: the length check already refuses every older board with a message that names the cause. Unknown flag bits are refused, so a later flag cannot be silently ignored.
24. **Recording goes through the existing chain, with an exporter.** Siqiang's Bluetooth Classic script cannot reach the BLE firmware, and the connection path is settled, so no second route was added. Every capture already records each sample with its raw bytes in `packets.jsonl`; the exporter only turns that into CSV, with the same `physical_values` the Ultra96 applies before the model, so his recordings and the model's input agree.
25. **Unchanged copies of the glove owner's module, with a check.** The module lives in a teammate's folder that Communications must not edit, and PlatformIO builds only from `firmware/esp32/`. Byte-identical copies, a `--check` mode, a test and the check inside `flash.py --glove` make any drift visible before a glove is flashed. His include path is left as it is; the copies sit where it resolves.

## Cautions and known limits

### Week 7 traces kept on purpose

These names were kept on purpose when the compatibility was removed (hand-off document, section 6.2):

- The TLS server name `ultra96.week7.internal` (`common/tls.py:4`). It is written into the server certificate, and every client verifies against it. It cannot change.
- The default `--ca` path of `demo.py` contains the dated folder name `cg4002-week7-20260906` (`demo.py:49-50`). This folder really exists on this laptop. On another machine, pass `--ca` explicitly.
- The deployment folder on the Ultra96 that `demo.py service` and `tools/deploy_service.py` use is also dated (`BOARD_ROOT`, `tools/demo_service.py:13`). It really exists on the Ultra96. `BOARD_SOURCE` (`:16`) points to the September 28 snapshot and is now only the fallback: after a deployment with `tools/deploy_service.py`, `demo.py service --start` follows the local deployment record instead (see "Which code `demo.py service --start` starts").

### Usage cautions

- **Port defaults differ.** `demo.py` uses 18889. `laptop.bridge`, `laptop.dual_bridge`, `tools.ssh_tunnel`, `tools.comms_demo` and `tools.rehearse_remote_comms` use 18888. The tunnel and the capture must use the same port.
- **Personal defaults are in the code.** The `--jump` default of `demo.py tunnel` contains the original operator's account. The accounts, the Ultra96 host name and `BOARD_ROOT` used by `demo.py service` are hard-coded, and nobody else can change them by option (the session ID can be changed with `--session-id`). `tools/deploy_service.py` has the same host names and `BOARD_ROOT` built in; only its accounts can be changed (`--jump-user`, default `yanjie`; `--board-user`, default `xilinx`). `tools/demo_boards.py:10` holds the built-in default addresses of the two boards.
- **A leftover `LTC_COMMS_SESSION`.** This environment variable affects `demo.py run`, `demo.py live` and `demo.py service --start` together. `--session-id` on the command line takes precedence. The variable is read once, when the options are parsed (`demo.py:54-55`, `70-71`). In the current source (built into an unsigned app on 2026-10-16, not yet installed), the phone's session ID is compiled in as `ltc-comms` and does not read this variable (the one in use is `IntegrationController.swift:74`; the form text in `SetupViewController.swift:51` repeats it, so both change together). The installed Week 7 app still uses `week7-demo`. Documents from the transition period taught setting `LTC_COMMS_SESSION=week7-demo`. If the terminal still has it, the laptop and a newly started service both use `week7-demo`. After the version-3 redeploy and the installation of the rebuilt phone app, ACKs are normal and `CAPTURE PASSED` appears as usual, but the service closes the phone's connection at once, and the phone keeps showing `Disconnected: connection closed; retrying`. (Until the redeploy, the service is version-2 code, and `demo.py service --start` also falls back to the version-2 `BOARD_SOURCE` because no deployment record exists; that code refuses every version-3 frame, so no capture passes, whatever the session.) When troubleshooting, first confirm that this variable is not set.
- **`demo.py run` always enables the control channel.** `--rate` defaults to 10 and is always passed to the child. So both boards must have the control characteristics, and the MTU must be at least 64.
- **Pass `--rate 50` for glove captures.** The `-glove` firmware starts at 50 Hz, the rate of the model's windows (`firmware/esp32/platformio.ini:42-58`), but the rate command at connection overrides it. `python demo.py run` without `--rate` therefore runs the gloves at 10 Hz. `tools.check_board` defaults to 50 Hz. Siqiang's movement detector samples on its own clock, so the gating does not depend on the send rate.
- **`demo.py` does not expose `--ack-window` or `--queue-capacity`.** It fixes 32 ACK slots and 64 queue places. At 50 Hz that is only 0.64 seconds in flight plus 1.28 seconds queued. The 50 Hz test on 09-28 passed on the remote route with the 32-byte dummy packet. The 38-byte version-3 packet passed at 50 Hz on one board on 2026-10-14, but against a service on the laptop (`tools/check_board.py`), so the remote route has not carried version 3 yet. On 09-19 an ACK wait of 2.375 seconds was measured on the remote route.
- **The physical path works only on Windows.** The bond check imports `winrt`. Passkey input and keyboard commands use `msvcrt`. On non-Windows the throughput preference is not requested, and the remote notification stop returns False.
- **`bleak` must stay pinned at 3.0.1.** The remote notification stop uses the `obj` attribute of Bleak's characteristic object and the WinRT native method `write_client_characteristic_configuration_descriptor_with_result_async`. Without them the function silently returns False and falls back to the ordinary stop, and the tail-packet protection is gone (`laptop/ble_shutdown.py:12-23`). The client is created with caching off through `winrt={"use_cached_services": False}` (`laptop/ble_connection.py:5-8`). Pairing and connection parameters call the `winrt` packages directly (`laptop/windows_pairing.py:55-56`, `92`, `103`; `laptop/ble_parameters.py:135-139`). These packages come in as Windows dependencies of `bleak` 3.0.1 and are not listed separately in `laptop/requirements.txt`. Before upgrading Bleak, run the shutdown tail-packet probe on real hardware.
- **The result port has only one subscriber.** `laptop/phone_simulator.py` and `tools/rehearse_remote_comms.py` displace the phone as soon as they subscribe. Do not run them during a demo or joint testing. `tools/check_board.py` and `tools/rehearse_comms.py` subscribe only to their own service on the laptop and do not touch the phone's subscription.
- **`python -m laptop.bridge` (the single-board command line) is not the field entry point.** Its ACK window is 1. It has no source statistics reconciliation and no control channel.
- **Three traps shared by the diagnostic and rehearsal tools.**
  - No board selection: `laptop.ble_counter_receiver`, `laptop.mtu_probe` and `tools.rehearse_comms --ble` have no address option (`laptop/ble_counter_receiver.py:336`, `laptop/mtu_probe.py:153`, `tools/rehearse_comms.py:30-31`). Neither does `laptop.windows_pairing` without `--address`. They scan by service UUID and connect to the first board found. Both boards have the same advertised name and service UUID, so power only one board when using these tools. `tools.comms_demo sender` and `tools.rehearse_remote_comms` have `--address`, and `tools.check_board left|right` connects by the board map's address.
  - No rate setting: the firmware keeps its last rate after a disconnect. Only `demo.py`, `laptop.dual_bridge` with `--rate` and `tools.check_board` send the rate command (`laptop/bridge.py:773-775`). The single-board tools inherit whatever rate the board last had, yet judge against 10 Hz, and their ACK window is also 1.
  - Synthetic input reaches the real service: without `--ble`, `tools.rehearse_remote_comms` sends version-3 packets with the dummy rows into the real service on the Ultra96 as device 1, with a random boot ID (`tools/rehearse_remote_comms.py:131-140`). Each run takes one of the service's 128 `(device_id, boot_id)` slots. (The version-1 example and synthetic input of these tools are gone; see "History and removed items".)
- **`tools/comms_demo.py audit` rebuilds each `ack` and `result` line of a log as a version-3 message with `request_id` null and validates it** (`tools/comms_demo.py:175-191`). Any valid label and confidence pass, so logs recorded with synthetic input and with `--ble` are audited the same way. A log recorded before version 3 (with `v` 1 or 2 results) cannot be audited with the current code; use `c42b386` for it. The audit still matches acknowledged IDs to result IDs one to one, which holds only for the dummy model (see "One input, one result").
- **Implicit input requirements of `demo.py report`.** It requires both `exit-code.txt` and `packets.jsonl` next to `report.json`. A report from running `python -m laptop.dual_bridge --report …` directly has no `exit-code.txt` and is judged `CAPTURE NOT PASSED: missing, incomplete or unreadable evidence (…)` (`demo.py:171-174`). Without a path, it takes the `B07-*` folder under `--output-root` with the newest modification time, even if that run was interrupted (`demo.py:275-281`). Terminal colors apply only to `demo.py`'s own output: lines containing `disconnected`, `failed` or `rejected` are yellow, device 1 is cyan, device 2 is magenta. `live.log` has no colors (`demo.py:104-116`).
- **Evidence content.** The evidence contains BLE addresses and all sensor values. It contains no passkey, password or private key.
- **The rate sweep applies to the 32-byte dummy packet.** "70 Hz passed" means the 70 Hz setting: it delivered about 66 packets per second per board to the laptop, about 33.8 kbps for both boards together, and the run passed. The 75 Hz setting failed ([09-28 test]). The 38-byte packet has been measured only on one board: 50 Hz for 65 s, clean, against a service on the laptop (2026-10-14, see "Checking one board"). Two boards with 38-byte packets have not been measured: 38 bytes × 50 Hz × 2 boards = 30.4 kbps is below the measured figure, but that is arithmetic, not a measurement (hand-off document, section 8, step 3). Real sensor data has not been sent at any rate.
- **The server certificate is valid for only 30 days** (`tools/generate_comms_pki.py:47`). The copy saved on the laptop, which is the certificate deployed to the Ultra96 in September, expired on 2026-10-06 15:11:29 UTC. Only this laptop copy was checked; whether the Ultra96's certificate was replaced later has not been checked. The CA is valid until 2027-09-06, and its SHA-256 matches the fingerprint pinned in the phone source. For how the laptop behaves on expiry, see the "TLS cannot connect" row of the failure path table. To renew, run `python -m tools.generate_comms_pki --renew-server-from <original CA folder> --output-dir <new empty folder outside the repository>`. It signs a new server private key and certificate with the original CA, and the CA does not change (`tools/generate_comms_pki.py:75-101`). This was done on 2026-10-14: the renewed pair is in `~/.codex/private/cg4002-comms-server-20261014/` (valid until 2026-11-13 14:27:35 UTC; verified locally: it chains to the CA, the key matches, and a local TLS 1.3 handshake with `SUBSCRIBE`/`SUBSCRIBED` worked). It is **not on the Ultra96 yet**: `python -m tools.deploy_service --server-cert-dir <that folder>` installs it together with the new code, and refuses a certificate that expires within an hour. The laptop's `--ca` does not change. The steps are in section 6.3 of the hand-off document.

### Local state (2026-10-15)

- `.comms-local/boards.json` (created 2026-10-14 03:05, `version` 1, `status` `ready`, byte-for-byte identical to `.week7-local/boards.json`; left `38:18:2B:19:82:AE`, right `38:18:2B:18:9D:6A`). These are the owner's two boards. Capture and `tools.check_board` use this map. There is no need to reflash to get the map. Flashing Siqiang's gloves with `python flash.py --glove` will replace it with the gloves' addresses.
- `.comms-local/checks/` holds the evidence of 2026-10-14, each folder with a `README.txt`: `2026-10-14-right-board-v2/` (the right board on version-2 firmware: 20 Hz for 30 s, 495 = 495 = 495; 50 Hz for 65 s, 3019 = 3019 = 3019; both with 3/3 commands), `2026-10-14-right-board-v3/` (the version-3 `check_board` run, see "Checking one board"), and `2026-10-14-deploy-wsl/` (the Linux test of the deploy tool's board-side program). Nothing was added on 2026-10-15: no board check ran that day.
- `.comms-local/deployments/` does not exist yet: `tools.deploy_service` creates it with its first record. Until then `demo.py service --start` uses the fallback `BOARD_SOURCE`, the 28 September version-2 code.
- There are no `B07-*` capture folders under `.comms-local/` yet. So `python demo.py report` without a path prints `Demo could not complete: No B07 captures in …; run a capture first.` and ends with exit code 2 (`demo.py:275-279`, `300-302`).
- Old captures are under `.week7-local/`: 17 capture folders (`B07-*`, 2026-09-28 to 10-01), all recorded with Week 7 firmware. In 11 of them, `packets.jsonl` has `sensor` records with `raw_hex`; all of these start with `5737` (`W7`), none is `LC`, and all carry `version` 2. The newest (2026-10-01) has 7038 of them. Another 4 have no `packets.jsonl`, and 2 have no `sensor` records with `raw_hex`. `python demo.py report "<old folder>"` does not pass even with a path: the packet example review now refuses any `sensor` record whose version is not 3 and names it (`sensor version is protocol version 2; this tool reads only version-3 captures (check older captures with the code from before version 3)`, `tools/video_evidence.py:46-52`, `:96`), and their `raw_hex` is not `LC` anyway. The result is `PACKET EXAMPLES NOT PASSED: …` plus `CAPTURE NOT PASSED: packet evidence could not be verified.` (`tools/video_evidence.py:127-129`, `demo.py:210-212`). To review these Week 7 captures, use the code at commit `880abba`, the PR #15 merge on the team main branch, whose code still accepts `W7` (it was `ec398b6` before the 2026-10-14 history rewrite; the file contents are the same). A capture made with version-2 firmware would need `c42b386` or the team main `5a004c6`; none exists on this laptop. Keep `.week7-local/`; do not delete it (hand-off document, section 9.1).
- Boards: neither runs the current firmware. The right board ran the 2026-10-14 version-3 build and passed `tools.check_board right` with it (see "Checking one board"). On 2026-10-15 it was unplugged before the gated build could be flashed; it should still hold the 2026-10-14 build, but that flash may have been interrupted, so its state is not certain. The left board still runs the version-2 firmware flashed earlier on 10-14 (verified then: local loopback 100/100 packets; another run of 349 packets with the source reconciliation passed, a rate change to 20 Hz confirmed and all 3 commands round-tripped). The current laptop code refuses both at connection, because both answer 24-byte statistics, so a two-board capture times out at startup. Both need a reflash with `python flash.py` (the dummy firmware) and a check with `python -m tools.check_board left` and `right` (hand-off document, section 6.3, step 2). Siqiang's gloves have never been flashed with Communications firmware.
- The Ultra96 service and the phone app are untouched: the service should still be the 28 September version-2 snapshot with session `week7-demo`, and the phone runs the Week 7 build. The current laptop code accepts only `LC` version 3, 36-byte `LCS3` statistics and `ltc-comms`, and it has not yet done a real capture through the Ultra96. The repository cannot confirm the actual code snapshot, session ID or certificate of the service on the Ultra96 (hand-off document, section 6.3).

### Extension points (Communications' own work)

The order of these steps is section 8 of the hand-off document; the owner's proposed dates up to the in-person integration session on Tue 2026-10-20 are in its section 6.4. Status on 2026-10-16 (`4c6ab4c`; the work is that of 2026-10-15, `d582ce6`, plus the fingerprint change), for the parts that touch the laptop:

- **38-byte real data packet: done in code (built; the right board verified on 2026-10-14).** Protocol version 3, 38 bytes with the 11 values only (see "Version 3: the real glove packet"). The laptop no longer hard-codes "8 values, 32 bytes" anywhere: the struct, the value count, the version, the MTU floor, the command transformation, the dummy rows and `ble_bytes` all follow `common/sensor.py`. Siqiang's IDLE/MOVING answer (2026-10-15) keeps this layout. **Still open:** the scales are checked against Siqiang's real sample log before they are fixed, and Wen Ree agrees to the layout. A change then touches `common/sensor.py` and `common/dummy_fixtures.json` on the laptop side. For the Ultra96 side, see `ultra96/protocol.py:87-89` (the value count of `SENSOR_BATCH`).
- **Versions 1 and 2 removed: done (built).** Version 3 replaced both everywhere, including the dummy data (11-value rows) and the deterministic formula of version 1. The laptop has no branch on the packet version left (see "History and removed items"). `SUBSCRIBE` and `SUBSCRIBED` stay at `v` 1 (`laptop/phone_simulator.py:23`, `tools/check_board.py:70`, `tools/rehearse_comms.py:35`; `ultra96/protocol.py:22-24`).
- **Admitting model labels and real confidence: done for the checks the laptop tools share (built).** `ultra96/protocol.py` admits any label of 1 to 32 characters from `A–Z a–z 0–9 _ -` and any finite confidence from 0 to 1, so the laptop's diagnostic tools accept model results as they are (see "Labels"). The phone side is in [chapter 5](05-phone-and-week7-receiver.md): `phone/receiver.py` built; `phone/unity/CommsPhoneCore.cs` compiled at C# 7.0 against the .NET 10 libraries (not Unity's .NET Standard 2.1) and its self-test passed (113 checks, PowerShell 7); `Protocol.swift` compiled and tested on Linux in a Swift 6.1 container (72 tests, every test that builds on Linux; the macOS-only `PythonBoardTests` and the iOS-only sources were not compiled there), and on 2026-10-16 on macOS (73 tests) and for the iOS Simulator, and built into an unsigned iPhone app that is not installed (hand-off document, section 8, step 5).
- **The "one input, one result" criteria: not done.** `tools/rehearse_remote_comms.py` requires the acknowledged ID set to equal the result ID set exactly. `tools/rehearse_comms.py` requires the result count to equal the acknowledged count minus the duplicate acknowledgements. `tools/check_board.py` requires as many stream results as acknowledged samples. `tools/comms_demo.py audit` matches IDs one to one. `demo.py`'s `Phone expected increase` counts one result per packet and command. All of them hold only while the Ultra96 runs the built-in dummy model, and they say so (see "One input, one result"). Once the model produces results per window, these checks must be redefined. How often results are produced is for Wen Ree and Jie Ling to agree (hand-off document, section 3.1). The owner's proposed plan redefines them on Sun 10-18, before the Monday dry run, or records that the phone count is not compared in the dry run (hand-off document, section 6.4).
- **Sending only while the glove moves: built, not yet run on a board (2026-10-15).** The firmware skips IDLE ticks and counts them; the 36-byte statistics carry the gated flag and the skip counters; the laptop judges a gated board by its ticks over `source_ticking_seconds`, and shows `gated` and `idle` in the progress line, the report table and `tools.check_board` (see "Gating in the report"); the Ultra96 keeps a quiet ingest connection open for up to 600 s. Next: flash a board and check it, then the gated dummy (see "Checking one board").
- **Siqiang's module in the firmware: built (2026-10-15).** The `-glove` environments compile and link his unchanged module, and `python flash.py --glove` flashes them after checking the copies (see "Flashing the real gloves"). Not run on a glove; the first run is with Siqiang and his gloves.
- **Recording through the chain: built (2026-10-15).** `tools/export_capture.py` turns a capture into physical-unit CSV for Siqiang (see "Recording glove data through the chain"). Not run on a real capture.
- **One redeploy round and the acceptance run: not done (the owner's login).** The board side is now one command, `python -m tools.deploy_service` (see "Deploying the Ultra96 service"); then both boards' reflash and check, signing and installing the phone app (built unsigned on 2026-10-16), and `demo.py run` (hand-off document, section 6.3).

### Where design records and documents disagree with the code (follow the code)

- The tool names in old records, `rehearse_week7`, `rehearse_remote_week7`, `week7_demo`, `generate_week7_pki` and `Week7Server`, are now `tools/rehearse_comms.py`, `tools/rehearse_remote_comms.py`, `tools/comms_demo.py`, `tools/generate_comms_pki.py` and `CommsServer`.
- `docs/week7-runbook.md:300` says "One writer owns one request/ACK at a time." Two-board mode actually uses a window of 32. That runbook is out of date as a whole.
- [Selected design] item 12 gives the local forward port as 18888. `demo.py` defaults to 18889.
- In archived records (for example [Dual-board spec]), the source statistics magic is `W7S1`, the packet magic is `W7`, the packet has 32 bytes and the session ID is `week7-demo`. Those were the names at the time. The code now accepts only `LC` packets of version 3 (38 bytes) and `LCS3` statistics, and the session defaults to `ltc-comms`.
- Records and documents written before 2026-10-14 evening describe the 32-byte packet with 8 values, versions 1 and 2, `LCS1`, an MTU floor of 35, and results restricted to the four dummy labels with confidence 1.0. Those are gone from the code (see "History and removed items"). The four labels and confidence 1.0 remain only as the output of the built-in dummy model and of the service's `cmd:` echo (`DUMMY_GESTURES`, `ultra96/protocol.py:10`; `ultra96/model.py:50`; `ultra96/server.py:333-336`); any valid label and confidence are now accepted (see "Labels").
- Records and copies of this chapter written on 2026-10-14 describe 24-byte `LCS3` statistics, a coverage rule based only on received packets, an open IDLE/MOVING question and no sensor module. Since 2026-10-15 the statistics are 36 bytes with the gated flag and the skip counters, a gated board is judged by its ticks, the glove sends only while MOVING, and Siqiang's module is built into the `-glove` firmware.
- The protocol specification `docs/co-protocol-v2.md` (rewritten in `798438d`, `7479e2e` before the 2026-10-14 history rewrite, for the Week 7 removal) was renamed `docs/co-protocol-v3.md` with the version-3 change. Where it, `docs/communications-quickstart.md` or any other document disagrees with the code, follow the code.

### History and removed items

**Source statistics of 2026-10-14 (replaced 2026-10-15).** `5d2e52f` replaced the 24-byte `LCS3` value (`<4sB3xIIII`: marker, device ID, 3 reserved bytes, boot ID, next sequence, submitted, failures) with the 36-byte value above. The marker stayed `LCS3`; the length now tells the two apart, and the 24-byte value is refused with the reflash message (`laptop/source_audit.py:61-64`). Only the right board ever ran the 24-byte firmware. Coverage was judged only on the packets received in the common window; that rule now applies only to ungated boards (`laptop/dual_bridge.py:411-415`), and `coverage_ratio` follows the rule that applies. The 2026-10-14 check of the right board is the only evidence recorded with the 24-byte value. Every fake board in the tests now serves the 36-byte value; the 24-byte `LCS3` and `LCS1` remain only as refused inputs (`tests/test_source_audit.py:57-64`).

**Protocol version 3 (2026-10-14, evening).** On the local branch `comms/protocol-v3` (`a34c467`, `57a3fbd`, `a4b907b`, `3b94990`; not merged into `main`, not pushed), version 3 replaced versions 1 and 2 everywhere (hand-off document, sections 6.2 and 6.5). On the laptop side, this removed:

- The 32-byte packet with 8 values (`<2sBBIII8h`) and packet versions 1 and 2. `decode_packet` now accepts only 38 bytes and version 3 (`common/sensor.py:81-89`). The sensor MTU floor moved from 35 to 41 (`laptop/bridge.py:722`).
- The deterministic dummy formula of version 1, `dummy_values(seq)` (values `(seq % 2000) - 1000 + 10 * i`), and its two checks: the bridge counted a version-1 packet with other values as `malformed`, and goodput did not count it. The synthetic sources and the commands use the 11-value rows of `common/dummy_fixtures.json`.
- The version-2-only `request_id` branches. `SENSOR_BATCH` always carries `request_id` (`common/sensor.py:68`), and the ACK check always expects it (`laptop/bridge.py:381-384`).
- Version-2 command packets: key commands and the `--mock` source build version-3 packets (`laptop/bridge.py:262-267`, `:976-977`), and the command checks require version 3 (`common/control.py:56`, `laptop/controls.py:185`, `:194`).
- The statistics marker `LCS1`. Only `LCS3` is accepted (`laptop/source_audit.py:17`, `:70-71`).
- The version-1 teaching example of `tools.comms_demo packet` (8 values, gesture `OPEN`, confidence 1.0, no `request_id`). It now prints a version-3 packet, an ACK and a model-style result (`CHOP`, confidence 0.875) (`tools/comms_demo.py:17-42`).
- The audit's version-1 result rule in `tools/comms_demo.py audit` (label equal to `GESTURES[seq % 4]`, confidence 1.0), which made logs recorded with `--ble` fail. It now validates version-3 messages with the general label and confidence rules.
- The version-1 synthetic source of `tools.rehearse_remote_comms`. It now sends version-3 packets with the dummy rows (`tools/rehearse_remote_comms.py:131-140`).
- Versions 1 and 2 in `tools/video_evidence.py`. It reads only version-3 captures and names an older version when it meets one (`tools/video_evidence.py:46-52`).
- The fixed start folder of `demo.py service --start`. It now follows the newest local deployment record and restarts the deployed model; `BOARD_SOURCE` is only the fallback (`tools/demo_service.py:27-50`, `:72-98`).

Captures, logs and evidence recorded before version 3 cannot be checked with the current code; use `c42b386` or the team main `5a004c6` for version 2, and `880abba` for Week 7. The tests keep version-2 material only to prove that it is refused (for example the 32-byte packet in `tests/test_sensor.py:80-87` and `LCS1` in `tests/test_source_audit.py:57-72`) and, in the opt-in Linux deploy test, as the old service being replaced (built from `5a004c6`, the team main, whose service code equals `c42b386`).

**Week 7 compatibility removal (2026-10-14, earlier).** Compatibility with the old Week 7 version was removed (commits `28db0b3` and `b414696`, merged into local `main` by `5db56ad`; before the 2026-10-14 history rewrite these were `d2fff21`, `5f2c12a` and `4c2b078`; merged into the team main by PR #18). On the laptop side, this removed (line numbers are those of the current code):

- The old packet magic `W7`. Encoding and decoding use only `LC` (`common/sensor.py:23`, `:85-86`). The related "command packet magic follows the board" logic was removed too: `ControlChannel.attach` no longer has a `packet_magic` parameter (`laptop/controls.py:75-82`, `laptop/bridge.py:766`).
- The old statistics magic `W7S1`. At the time only `LCS1` was accepted; version 3 later replaced it with `LCS3` (above).
- The fallback read of the old folder `.week7-local`. The board map reads only `.comms-local/boards.json` (`tools/demo_boards.py:9`, `21-24`). `demo.py report` looks only in `.comms-local/` (`demo.py:275-281`). `flash.py --boards` no longer mentions the old folder (`flash.py:157-160`).
- The session ID `week7-demo` hard-coded in the start script on the Ultra96. It is now an option with the default `ltc-comms` (`tools/demo_service.py:98`, `:102`; `demo.py:70-71`, `298`).

The matching tests were updated at the same time. In the tests, `W7` and `W7S1` now appear only in `tests/test_sensor.py:36` and `tests/test_source_audit.py:41`, which assert that they are rejected.

## How to run and verify

The commands and numbers in this section come from the code and the records of 2026-10-14 and 2026-10-15 (hand-off document, sections 6.1 and 6.2, and the evidence under `.comms-local/checks/`). Apart from one run of the test suite at `4c6ab4c` on 2026-10-16 (below) and the run on the owner's Mac on 2026-10-16 that gives the Swift build status (hand-off document, section 6.3, steps 3 and 4; it touched no laptop code and no hardware), no Communications script, test or hardware was run while writing this chapter.

### Prerequisites

- Windows, Python 3.10 or later, Bluetooth on.
- The laptop is connected to the NUS VPN.
- Both boards are flashed with the current firmware (36-byte statistics) and each is powered. The Ultra96 runs the version-3 service. The phone app is a version-3 build. All three parties use the same session ID (`ltc-comms`). As of 2026-10-15 these conditions are not met:
  - Neither board runs the current firmware: the left board runs version 2, and the right board should still hold the 2026-10-14 build with 24-byte statistics (see "Local state"). The current laptop code refuses both.
  - The server certificate deployed to the Ultra96 in September expired on 2026-10-06. Only the laptop's copy of it was checked. A renewed pair exists on the laptop (`~/.codex/private/cg4002-comms-server-20261014/`, valid until 2026-11-13 14:27:35 UTC) but is not on the Ultra96, and whether the Ultra96's certificate was replaced has not been checked.
  - The service on the Ultra96 is most likely still the September 28 version-2 code snapshot with session `week7-demo`, so it refuses every version-3 frame (see the note after the failure path table). That process was not started by `demo.py service --start`. The untracked `.week7-local/co_deploy.py` started it in the background (`subprocess.Popen` with `start_new_session=True`; output in `BOARD_ROOT/evidence/`, PID in `BOARD_ROOT/evidence/server.pid`). It does not depend on any SSH session and may still be running. `tools/deploy_service.py` finds it by its process and ports and replaces it (see [chapter 4](04-ultra96-service-and-certificates.md)).
  - The phone runs the Week 7 build (version-2 results, dummy labels only, session `week7-demo`); it cannot read version-3 results (hand-off document, section 6.3).

  One redeploy round following section 6.3 of the hand-off document is needed before `demo.py run` can pass: `python -m tools.deploy_service --server-cert-dir <renewed folder>` (the owner's login), both boards' reflash and `tools.check_board left` and `right`, then signing and installing the phone app on a Mac with Xcode (on 2026-10-16 the Swift package passed its tests on macOS, 73 tests, and on the iOS Simulator, and the Week 7 Unity export built unsigned for iPhone; [chapter 6](06-tests-operations-extension.md), section C steps 4 and 5). The owner's proposed plan has a full dry run on Mon 10-19, the day before the in-person integration session (hand-off document, section 6.4).
- You have the public CA certificate file. The laptop needs no private key.
- Every step that logs in to the jump host or the Ultra96 (`demo.py tunnel`, `demo.py service`, `tools.deploy_service`) is done by olsonwangyj in their own terminal (hand-off document, section 9).

### Field steps

```powershell
python -m pip install -r laptop/requirements.txt
python -m pip install -r requirements-dev.txt  # cryptography for tools.check_board, paramiko for tools.deploy_service
python flash.py --boards                      # show the left and right board addresses
python flash.py                               # dummy firmware; or: python flash.py --glove for Siqiang's gloves
python flash.py --pair left                   # first time only; read the passkey only on the local serial port
python flash.py --pair right
python -m tools.check_board left              # after flashing; one board, no Ultra96; then the same for right
python -m tools.deploy_service --dry-run      # once per new code or certificate; the real run asks for both passwords
python demo.py service                        # read-only look at the Ultra96 service (see chapter 4)
# Terminal A, keep it open
python demo.py tunnel --jump '<your account>@stujump.comp.nus.edu.sg' --target '<Ultra96 account>@<Ultra96 host name>'
# iPhone: tap Communications Connect, wait for Subscribed, note Received
# Terminal B
python demo.py run  --ca '<CA certificate path>'       # 60 s, 10 Hz
python demo.py live --ca '<CA certificate path>'       # 120 s; press 1 or 2 to send commands
python demo.py run --rate 50 --ca '<CA certificate path>'   # the real gloves: the model's 50 Hz
python demo.py report                         # review the latest; a folder or report.json also works
python -m tools.export_capture                # optional: the latest capture's samples as CSV
```

The phone must reach `Subscribed` before the capture starts. When there is no subscriber, the service on the Ultra96 discards results and does not resend them later. `Subscribed` means only that the subscription handshake with the Ultra96 succeeded; it does not prove that results are flowing. Only the increase in the phone's `Received` count after the capture shows that results arrived.

### What counts as a pass

- Terminal B exits with code 0.
- The output contains `Exit=0  clean=True  mock_input=False  report_saved=True`.
- In the table, both boards have Generated, Received and ACKed equal, and MissingBLE and MissingACK are both 0. `Gated` and `Idle` are for information only. A gated glove must have been moved during the capture: `generated` must be above 0.
- `CAPTURE PASSED` appears. It is evidence level 3: it proves that the service on the Ultra96 validated and accepted every input. It does not prove that a model ran or that the phone received anything.
- A line `Phone expected increase: N` appears, followed by the note that the count holds only while the Ultra96 runs the built-in dummy model. Compare N with the before-and-after difference of the phone's `Received` count. This is level 5 evidence and relies on a manual comparison. `Received` counts every distinct result, even though the display text shows only the latest one and can lose results between polls (hand-off document, section 4.6). With a real model that does not answer every sample, N is not the expected increase (see "One input, one result").

`demo.py`'s pass conditions (`demo.py:143-159`): the child exits 0; the report has `clean` true, is not synthetic input, and was saved; each board has `clean` and `protected_ble` true and `unfinished` false; source statistics `complete` and `clean` are both true; `generated` is a positive integer and equals `source_submitted`, the source-side `received` and `acked`, and the board-level `received`, `sent` and `acked`; `missing_received` and `missing_acked` are both 0. After that, the packet example review must pass: each board has at least one pair of `sensor` and `sensor_ack` records with exactly the same identity, and the decoded `raw_hex` matches the recorded fields (`tools/video_evidence.py`).

### Checks without hardware

```powershell
python -m pip install -r laptop/requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider
python -m tools.sync_glove_module --check                      # the firmware's copies equal Siqiang's module
python -m tools.comms_demo packet                               # prints a 38-byte version-3 packet and an example of each frame
python -m tools.generate_comms_pki --output-dir '<new empty folder outside the repository>'   # one-off certificates for local rehearsal only
python -m tools.rehearse_comms --pki-dir '<that folder>' --duration 30 --target 100
```

- Install `laptop/requirements.txt` first. The modules that `laptop/tests/` and `tests/test_ble_connection.py` import do `import bleak` at file top level (`laptop/ble_connection.py:2`, `laptop/mtu_probe.py:11`, `laptop/ble_counter_receiver.py:13`). Without `bleak`, these tests fail at collection. `requirements-dev.txt` does not include `bleak`.
- Do not run `pytest` without paths from the repository root. It collects `fpga/hls/export_conv1d_test.py`, which rewrites a tracked file as soon as it is imported.
- On 2026-10-16, at `4c6ab4c`, the command above gave 842 passed, 4 skipped (run during the review of this chapter; the one new test is the fingerprint test of `4c6ab4c`). On 2026-10-15, at `d582ce6`, it gave 841 passed, 4 skipped. `tests/test_server_diagnostics.py::test_close_deadline_includes_status_persistence` is timing-sensitive (a 0.01 s close, a 0.2 s wait); it failed once under load and passed on a rerun. On 2026-10-14, at `3b94990`, the command gave 778 passed, 4 skipped; with `B07_LINUX_DEPLOY_TEST=1` set it gave 779 passed, 3 skipped, including 27 of 27 deploy checks (hand-off document, section 6.2). That variable adds the deploy tool's board-side test, which starts and stops `ultra96.server` processes in the local Linux or WSL; never run `tests/linux/deploy_remote_test.sh` on the Ultra96 itself.
- The certificate tool refuses folders inside a Git repository or working tree, and refuses non-empty folders (`tools/generate_comms_pki.py:27-36`).
- `rehearse_comms` starts a local TLS service with the built-in dummy model, runs the single-board path with synthetic version-3 data, and receives the results with a subscriber. Pass conditions: the acknowledged count reaches the target; the result count equals the acknowledged count minus the duplicate acknowledgements; there are no duplicate results and no receive errors; all error counts are 0. It does not go through SSH, the real Ultra96 or the phone. Only `--ble` uses a real board (without board selection). It prints one JSON line, and `passed` should be `true`.
- Two-board synthetic check: in another terminal run `python -m ultra96.server --cert '<folder>/server-cert.pem' --key '<folder>/server-key.pem' --ingest-port 18888 --gateway-port 19999`. Then run `python -m laptop.dual_bridge --ca '<folder>/ca-cert.pem' --mock --duration 10 --report '<new file in an existing folder>.json'`.

### What each rehearsal and simulation tool verifies

| Tool | What it verifies | What it does not verify |
|---|---|---|
| `tools/rehearse_comms.py` | The path, frame format, TLS verification, ACK check and result count close the loop locally (one result per sample: dummy model) | SSH, the real Ultra96, the phone, a real model |
| `tools/check_board.py` | One real board after flashing: bond, MTU of at least 41, rate setting, commands in 52-byte frames, source reconciliation (generated = received = acknowledged), every sample and command answered by the dummy model of a service on the laptop | SSH, the real Ultra96, the phone, two boards together, goodput and coverage, real sensor data |
| `tools/rehearse_remote_comms.py` | Through two existing forward ports (18888 and 19999), it starts sending data only after receiving `SUBSCRIBED`. The acknowledged IDs equal the result IDs one by one, which holds only while the service runs the dummy model. With `--target 0` it requires a count of at least `ceil(duration × 10 × 0.9)`, and no gap in ACKs or results longer than 5 seconds. Only one TLS connection and one subscription (with `--ble`, also only one BLE connection) | Whether the forward ports really reach that Ultra96 (only the operator can declare it, with `--confirmed-remote-topology`); the phone |
| `tools/comms_demo.py sender` | Real BLE from one board. Prints the bytes and JSON of every acknowledged packet. Requires the acknowledged count to reach at least the target (`ceil(duration × 9)` with `--target 0`), only one BLE connection and one TLS connection, and gaps between acknowledgements of no more than 5 seconds | Whether results are delivered |
| `tools/comms_demo.py audit` | Offline check of the IDs in a saved log (at most 200,000 lines and 64 MiB; each line at most 65536 characters), with every ACK and result validated as version 3 | Any live connection or physical source; logs from before version 3 |
| `laptop/phone_simulator.py` | The result port can be subscribed to and delivers valid results | A real phone; it displaces the phone's subscription |
| `laptop/mtu_probe.py` | 20 bytes and MTU−3 bytes arrive unchanged; MTU−2 bytes do not | The sensor path |
| `laptop/ble_counter_receiver.py` | Continuity and reconnection of counter notifications | The sensor path |
| `tools/video_evidence.py` | Each board in a version-3 capture has at least one packet and ACK pair with exactly the same identity | Completeness of the whole capture; the phone; captures from before version 3 (refused by name) |
| `tools/export_capture.py` | Not a check: it writes each `sensor` record of a capture as one physical-unit CSV row, and refuses a record that is not a valid version-3 sample | Completeness of the capture or acknowledgement by the Ultra96 (that is the report's verdict) |
