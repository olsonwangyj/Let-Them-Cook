# Detail chapter 3: Laptop relay and operator tools

> This is a detail chapter of [`../communications-handoff.md`](../communications-handoff.md). It was checked against local `main` (commit `25fe4e4`) on 2026-10-14, and brought in line with the hand-off document's later 2026-10-14 update (sections 3.1, 6.4, 7, 8 and 13) at commit `878ebeb`. No laptop, `common/` or tool code changed between the two commits. The code is the source of truth: where this chapter and the code disagree, follow the code.

## Role and boundaries

The laptop is the BLE central for both ESP32 boards. It is also the TLS client of the Ultra96 ingest service. It does four things:

1. It scans for and connects to both boards with `bleak==3.0.1` (the WinRT backend on Windows). It confirms that Windows already holds a bond at the "encryption and authentication" level.
2. It subscribes to each board's sensor notifications. Each notification is one 32-byte packet.
3. It turns each packet into one `SENSOR_BATCH` JSON frame and sends it over TLS to the local SSH forward port. SSH carries it to `127.0.0.1:8888` on the Ultra96. The laptop checks the `INGEST_ACK` for every frame.
4. It reconciles the counts and keeps evidence. Three numbers must be equal: the samples the board generated, the samples the laptop received, and the samples the Ultra96 acknowledged.

Boundaries:

- On the laptop leg, Communications ends at the Ultra96's `INGEST_ACK`. The ACK proves only that the ingest service on the Ultra96 accepted this packet (evidence level 3, see section 4.7 of the hand-off document). It does not prove that a model ran on the sample, or that the phone received a result.
- Gesture results do not come back to the laptop (`laptop/bridge.py:1`). The phone connects over SSH to port `9999` on the Ultra96 by itself.
- The laptop does not pair the left and right gloves, does not build model windows, and does not decide between gesture and idle. These are Wen Ree's work. Each board uses its own path. The only thing that tells the boards apart is the packet's `device_id` (1 = left, 2 = right). Who does what at each hand-over is the table in section 3.1 of the hand-off document: Communications moves data correctly and does nothing else.
- The laptop forwards the int16 values exactly as the board packed them and does not convert them to floats. Decided 2026-10-14: the model gets the 11 values as physical floats, transport stays int16, and Communications restores the floats on the Ultra96 (decode, divide by the scale) before it calls the model's `on_sample`. Any normalisation is Wen Ree's (hand-off document, sections 3.1 and 7.2). Planned, not built.
- The connection path is settled. The laptop connects to the local forward port. OpenSSH takes two hops, `stujump:22` and `Ultra96:22`, to `127.0.0.1:8888` on the Ultra96. `BridgeConfig.host` accepts only `127.0.0.1`. Any other value raises an error at construction (`laptop/bridge.py:54-55`).

### Relation to the teammates' interfaces

The laptop code calls no teammate function. Section 7 of the hand-off document holds the three interfaces to connect (the glove sensor module, the entry and exit points of the model on the Ultra96, and the bridge functions the game calls: the three that exist today, `CommsStart`, `CommsCopyDisplay` and `CommsStop`, plus the planned per-result function `CommsNextResult`). It also holds what must be confirmed with Siqiang, Wen Ree and Jie Ling. This chapter does not repeat them.

**Everything in section 7 is planned, not built.** The call into the glove sensor module, the 38-byte packet, `start`/`on_sample`/`emit`, the thread-safe result hand-back, `CommsNextResult`, and real labels and confidence do not exist in code yet. Only `CommsStart`, `CommsCopyDisplay` and `CommsStop` can be called today. Finished documents are not finished integration (hand-off document, section 1). The dates the teammates were asked for, and the owner's own plan up to the in-person integration session on Tue 2026-10-20, are in section 6.4 of the hand-off document.

Below are only the technical constraints that the laptop-side code imposes.

- **int16 range.** A real data packet scales the 11 values to int16 with the multipliers in section 4.2 of the hand-off document. The laptop decodes and validates them as int16. Every scaled value must lie between −32768 and 32767. Acceleration multiplied by 10000 can represent only ±3.2767 g. Angular rate multiplied by 100 can represent only ±327.67 °/s. Angles multiplied by 100 can represent only ±327.67° (yaw overflows if it runs from 0 to 360). Flex values multiplied by 10000 top out at 3.2767. Section 7.1 of the hand-off document states the range each value must stay within; with the current sensor settings every value fits. The scales are checked against Siqiang's real sample log before they are fixed (hand-off document, section 8, step 1). Scaling, and any handling of out-of-range values, happens in the firmware; the laptop only decodes int16. For a value that still falls outside int16, the recommended rule is to clamp it to the int16 limit and count it, never silently: a clamped value arrives as exactly the limit (for example 32767, that is 3.2767 g). Clamping keeps the sample stream free of gaps. The owner has still to confirm clamp-and-count against dropping that one sample (hand-off document, section 13). Either way it is counted, reported and Wen Ree is told, and no connection is dropped for it.
- **Left and right identity.** The laptop trusts only the packet's `device_id`. It is a compile-time constant in the firmware. `flash.py` sets it by the order in which the boards are plugged in (the first board plugged in is flashed as left). The sensor module does not need to supply it.
- **Coverage is judged against `--rate`.** A two-board capture requires each board's packet count inside the observation window to be at least `0.9 × observation duration × --rate` (`laptop/dual_bridge.py:339-340`). Once real capture is connected, a board that sends nothing at more than one in ten of its send ticks falls below 90% coverage, and the run is judged not clean.
- **Labels.** The laptop relay does not look at labels, and results do not pass through the laptop. Only the diagnostic and rehearsal tools validate results with `ultra96.protocol.validate_message`: `laptop/phone_simulator.py`, `tools/rehearse_comms.py`, `tools/rehearse_remote_comms.py` and `tools/comms_demo.py audit`. That function currently admits only `REST`, `FIST`, `OPEN` and `POINT`, and requires a confidence of exactly 1.0 (`ultra96/protocol.py:4`, `:78-83`). Admitting the model's labels is Communications' own work (hand-off document, section 8, step 5). A change to this function takes effect in these tools at the same time. Which labels exist, how often a label is produced, and whether several identical labels in a row mean one action or several are for Wen Ree and Jie Ling to agree (hand-off document, section 3.1). Communications passes every result through unchanged: it never merges, splits, filters or reinterprets results, so the change only has to admit the agreed labels and a real confidence.
- **One input, one result.** Both rehearsal tools and the `Phone expected increase` line that `demo.py` prints assume that each accepted input produces exactly one result. Once the model produces results per window, these criteria must be redefined (hand-off document, section 8, step 6). How often the model produces a result is for Wen Ree and Jie Ling to agree, and it is one of the questions in the message to Wen Ree (hand-off document, sections 3.1 and 7.2), so the new criteria wait for that answer.
- **Gaps in `seq` that the laptop leaves.** The model sees every laptop-side loss as a gap in `seq` at its entry point (hand-off document, section 7.2). None of these samples is resent: eviction of the oldest packet when the queue is full (64 places under `demo.py`; `queue_dropped`, `laptop/bridge.py:132-134`); packets that waited on the laptop for more than 2 s (`stale_dropped`); on a BLE disconnect, the packets still queued for that glove are discarded (`RawInbox.deactivate`, `laptop/bridge.py:113-120`, counted in `callback_generation_dropped`); on a TLS failure, the frames already written but not acknowledged count as `ambiguous_dropped` (`laptop/bridge.py:484-498`), and they leave a gap on the Ultra96 unless the service had already processed them. A packet dequeued while the TLS connection cannot be opened is lost too; it shows only as `transport_errors` and in `missing_acked`. While a glove is disconnected it makes no samples and `seq` does not advance, so that time shows only as a jump in `uptime_ms`, not as a `seq` gap. The laptop's own `gaps` counter (`StreamTracker`, `laptop/bridge.py:150-171`) counts missing sequence numbers among the packets the writer processed.

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
| `laptop/dual_bridge.py` | Two-board coordinator `DualBridge` and the command line used in the field: common observation window, close and drain order, verdict, progress output. |
| `laptop/source_audit.py` | Parses the 24-byte source statistics. Reconciles the three counts "generated, received, acknowledged" in constant memory. |
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
| `common/sensor.py` | Encoding and decoding of the 32-byte packet, `SensorPacket`, conversion to `SENSOR_BATCH`, the dummy-data formula and the dummy-data table. |
| `common/control.py` | Encoding and decoding of BLE control frames, opcodes, status codes, file metadata, and the value transformation for commands. |
| `demo.py` | Operator entry point: `tunnel`, `run`, `live`, `report`, `service`. |
| `tools/demo_boards.py` | Reads, writes and validates `boards.json`, the map of the left and right boards' Bluetooth addresses. |
| `tools/ssh_tunnel.py` | Builds the two-hop SSH local forward command; optional supervised restart. |
| `tools/comms_demo.py` | Teaching packet example, single-board sender with display, offline log audit. |
| `tools/rehearse_comms.py` | Local full-path rehearsal. Brings its own local TLS service and subscriber. |
| `tools/rehearse_remote_comms.py` | Rehearsal against the real Ultra96 through two existing forward ports. Checks ACKs and results ID by ID. |
| `tools/video_evidence.py` | Picks one "sensor packet and ACK" example pair per board from a capture and validates it. |
| `tests/test_bridge.py` | Queue eviction and generation isolation, sequence tracking, stale drop, ACK validation, tunnel command, native-operation limit, back-off. |
| `tests/test_bridge_ack_window.py` | ACK window: delayed ACKs can overlap, window limit, FIFO, after a failure the whole batch counts as ambiguous and is not resent, drain, the two boards do not take each other's window slots. |
| `tests/test_bridge_ack_window_cleanup.py` | When TLS close is cancelled midway, each frame whose write was attempted is still counted once. |
| `tests/test_ack_window_transport.py` | ACK window over real TLS with ACK propagation delay: the server processes the frames in the window before the ACKs return, and ACKs and results match one by one. |
| `tests/test_bridge_connection_parameters.py` | Timing of the throughput preference: requested after authentication and before reading source statistics, released after disconnect. |
| `tests/test_bridge_disconnect_cleanup.py` | On a dropped link, skips the remote notification stop but still disconnects locally. A cleanup failure records only the operation name and exception type. |
| `tests/test_bridge_shutdown_tail.py` | Tail packets: a late callback arrives before the callback is removed. A lost tail packet, a rejected CCCD write, a changed boot ID and a count drift are all judged not clean. |
| `tests/test_bridge_transport_cleanup.py` | When TLS close hangs or is cancelled, the connection is aborted and the cancellation is preserved. |
| `tests/test_dual_bridge.py` | The two paths progress independently; a normal stop drains and reconciles; startup packets do not count toward coverage; silence verdict; read order of source statistics; the command line exits within bounded time. |
| `tests/test_dual_reporting.py` | The report reservation does not overwrite an existing file; writing is refused if the file was replaced; progress goes to stderr; a failed save forces a non-zero exit. |
| `tests/test_dual_transport.py` | Real local TLS: the exact ID sets of both boards arrive. One TLS disconnect does not affect the other path, but the verdict is failure. |
| `tests/test_ble_connection.py` | Forced uncached GATT discovery; passkey input can be cancelled. |
| `tests/test_ble_parameters.py` | The handle is released whether the preference request succeeds, is denied, is unsupported or is cancelled; unit conversion. |
| `tests/test_ble_shutdown.py` | Returns False on non-Windows or when the native interface is missing. The native write must return SUCCESS explicitly. |
| `tests/test_laptop_controls.py` | Command round-trip validation, commands not retried, file chunk retry and digest check, `FILE_ABORT` on failure, commands use a separate TLS connection, old commands not replayed after reconnect. |
| `tests/test_goodput.py` | Counts only unique valid packets; silent time counts in the denominator; startup and drain do not count. |
| `tests/test_source_audit.py` | Decoding of literal source statistics, malformed input rejected (including `W7S1`), a lost tail packet is detected, uint32 wraparound. |
| `tests/test_sensor.py` | Encoding writes only `LC`; `W7`, `WC`, `lc` and other magics are rejected; round trip of fixed vectors; rejection of truncation, version, device ID and value range; boundaries of the dummy-data formula; session ID validation; host test of the firmware serialization. |
| `tests/test_comms_demo.py` | The packet example in `tools/comms_demo.py` matches the literal bytes; the offline audit goes by ID, not by count; incomplete, duplicated, faulty or too-short evidence cannot pass; the sender's timing verdict. |
| `tests/test_ssh_trust.py` | Uses `ssh -G` to check the effective configuration of both hops: the jump hop has its own strict host-key checking; interactive mode allows a password at the jump host; supervised mode overrides the insecure defaults on both hops; `-i` applies only to the target; the supervisor refuses an interactive proxy. |
| `tests/test_demo_boards.py` | Flash order determines the left/right map; capture is blocked while the map is incomplete; the old file is kept when a write fails. |
| `tests/test_demo_launcher.py` | `demo.py` saves the child process output; default command line; choice of session ID; the various fail conditions; interrupt handling. |
| `tests/test_demo_service.py` | Port-in-use check and strict SSH options in the service start script. Session ID: starts with the requested session, a malicious session ID stays a single argument, an invalid session ID is rejected, the same default rule as capture. |
| `tests/test_demo_simplified.py` | Defaults of `run` and `live`; `report` does not ask for the phone count; `--help` of each subcommand does not touch hardware. |
| `tests/test_rehearsal.py` | A 5-second local rehearsal with a target of 10 packets passes. |
| `tests/test_remote_rehearsal.py` | ID-by-ID correspondence; stops before sending data when the CA is wrong; a run with silence or restarts cannot count as a clean pass. |
| `tests/test_packet_evidence.py` | Evidence files contain no ANSI color codes; console sampling; a slow console does not block, and overflow is counted. |
| `tests/test_video_evidence.py` | Examples must pair by full identity. A corrupt file, conflicting records or a missing board all fail. |
| `tests/test_windows_pairing.py` | The passkey must be 6 digits; a weak bond is rejected; the handler is removed after pairing. |

Adjacent files that this chapter does not cover: `common/tls.py`, `common/wire.py`, `tools/demo_service.py`, `tools/generate_comms_pki.py`, `ultra96/protocol.py`, `flash.py`. This chapter cites only their interfaces.

## Data formats and constants

### GATT characteristics the laptop uses

All UUIDs end in `-7a45-4dc4-b678-3f2d5a9c1001`.

| UUID prefix | Code constant | Operation | Content |
|---|---|---|---|
| `6e1c0001` | `SERVICE_UUID` | Scan filter | Service |
| `6e1c0005` | `SENSOR_UUID` | Notify | 32-byte sensor packet |
| `6e1c0006` | `SOURCE_STATS_UUID` | Read | 24-byte source statistics |
| `6e1c0007` | `CONTROL_UUID` | Write with response | Control request |
| `6e1c0008` | `RESPONSE_UUID` | Notify | Control response |
| `6e1c0002` | Only in `ble_counter_receiver.py` | Notify | 4-byte little-endian counter |
| `6e1c0003` / `6e1c0004` | Only in `mtu_probe.py` | Write / Notify | 2-byte requested length / payload whose byte i equals `i mod 256` |

### Sensor packet (current, 32 bytes, `<2sBBIII8h`, little-endian)

| Offset | Length | Field | Type | Values |
|---:|---:|---|---|---|
| 0 | 2 | magic | ASCII | `LC` (`4C 43`), the only accepted value |
| 2 | 1 | version | uint8 | 1 or 2 |
| 3 | 1 | device_id | uint8 | 1 or 2 |
| 4 | 4 | boot_id | uint32 | 0 to 0xFFFFFFFF |
| 8 | 4 | seq | uint32 | 0 to 0xFFFFFFFF, wraps |
| 12 | 4 | uptime_ms | uint32 | 0 to 0xFFFFFFFF |
| 16 | 16 | values[0..7] | 8 × int16 | −32768 to 32767 |

- A length other than 32 is rejected with `sensor packet must contain exactly 32 bytes` (`common/sensor.py:75`).
- A magic other than `LC` is rejected with `invalid sensor packet magic; expected LC` (`common/sensor.py:77-78`).
- In version 1, the 8 values must equal `(seq % 2000) - 1000 + 10 * i`. Otherwise the packet counts as `malformed` (`laptop/bridge.py:408-409`).
- Version 2 accepts any valid int16.
- At connection the ATT MTU must be at least 35 (`laptop/bridge.py:719`).

### Source statistics (24 bytes, `<4sB3xIIII`, little-endian)

| Offset | Length | Field | Values |
|---:|---:|---|---|
| 0 | 4 | magic | `LCS1`, the only accepted value |
| 4 | 1 | device_id | 1 or 2 |
| 5 | 3 | reserved | must be all 0 |
| 8 | 4 | boot_id | uint32 |
| 12 | 4 | next_seq | the next sequence number to assign |
| 16 | 4 | submitted | number of successful notification submissions |
| 20 | 4 | failures | number of failed notification submissions |

The parser checks length, reserved bytes, magic, then device ID, in that order (`laptop/source_audit.py:44-54`). A wrong magic reports `invalid source statistics magic; flash this board with the current firmware` (`laptop/source_audit.py:50-51`).

### BLE control frame (one frame per write or per notification)

Header, 14 bytes, `<2sBBBBII`:

| Offset | Length | Field | Values |
|---:|---:|---|---|
| 0 | 2 | magic | `B7` (the team number B07, not Week 7) |
| 2 | 1 | version | 1 |
| 3 | 1 | opcode | a response is the request value plus 128 (bit 7 set) |
| 4 | 1 | device_id | 1 or 2 |
| 5 | 1 | status | always 0 in a request |
| 6 | 4 | request_id | uint32, 1 to 0xFFFFFFFF |
| 10 | 4 | offset | uint32, 0 to 65536 |
| 14 | 0 to `min(180, MTU-17)` | payload | see the table below |

| opcode | Name | Request payload | Response payload |
|---:|---|---|---|
| 1 | `COMMAND` | A complete 32-byte version 2 packet; `seq == request_id`, `uptime_ms == 0`, `offset == 0` | The 32-byte packet after the board adds 1 to each of the 8 values (32767 wraps to −32768) |
| 2 | `SET_RATE` | uint16 little-endian, 1 to 200 Hz | Echoed unchanged |
| 16 | `FILE_BEGIN` | 36 bytes: uint32 length plus SHA-256; `offset == 0` | None; `offset` must be 0 |
| 17 | `FILE_CHUNK` | File bytes, not empty; `offset` is the start of this chunk | None; `offset` is the next expected offset |
| 18 | `FILE_END` | None; `offset` is the total file length | 36 bytes: the length and SHA-256 the receiver computed; `offset` equals the length |
| 19 | `FILE_ABORT` | None; `offset == 0` | None |

Status codes: 0 `OK`, 1 `INVALID`, 2 `BUSY`, 3 `ORDER`, 4 `INTEGRITY`, 5 `CONFLICT`, 6 `UNSUPPORTED` (`common/control.py:13`). A response with a non-zero status carries no payload. The control channel requires an MTU between 64 and 517 (`common/control.py:30-32`). A file is 1 to 65536 bytes.

### JSON over TLS

A frame is a 4-byte big-endian length followed by UTF-8 JSON. The body is 1 to 16384 bytes (`common/wire.py:7`).

| Message | Direction | Fields |
|---|---|---|
| `SENSOR_BATCH` | laptop → Ultra96 | `v` (1 or 2), `type`, `session_id`, `device_id`, `boot_id`, `seq`, `uptime_ms`, `values` (8 integers). With `v=2` it adds `request_id`: `null` for the data stream, a uint32 equal to `seq` for a command. |
| `INGEST_ACK` | Ultra96 → laptop | `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `status` (`accepted` or `duplicate`). With `v=2` it adds `request_id`. |

The ACK's key set must be exactly the one above. Each value's type and value must match the packet sent. Otherwise the ACK is handled as a transport error (`laptop/bridge.py:375-386`).

### `BridgeConfig` (`laptop/bridge.py:33-77`)

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

### Other constants

| Item | Value | Location |
|---|---|---|
| Two-board ACK window (command-line default; `demo.py` always passes 32) | 32 | `laptop/dual_bridge.py:414`, `demo.py:81` |
| TLS read buffer limit | 32768 bytes | `laptop/bridge.py:352` |
| TLS handshake timeout | `io_timeout` (5 s) | `laptop/bridge.py:353` |
| Per-frame ACK deadline | send time plus `io_timeout` | `laptop/bridge.py:605-613` |
| TLS close wait | 1.0 s, then `abort()` on timeout | `laptop/bridge.py:360` |
| Reconnect back-off (BLE and TLS counted separately) | starts at 0.5 s, doubles each time, capped at 5.0 s | `laptop/bridge.py:660-670`, `684`, `948` |
| Limit on unfinished native BLE operations | 2 | `laptop/bridge.py:329-335` |
| Notification stop budget | 0.75 s each | `laptop/bridge.py:816`, `878` |
| Disconnect budget | 1.0 s, counted separately | `laptop/bridge.py:918` |
| Tail-packet wait | at most 0.5 s, polled every 0.01 s | `laptop/bridge.py:846-857` |
| Two-board startup, drain and shutdown timeouts | 30 s, 10 s, 25 s | `laptop/dual_bridge.py:26-28` |
| Coverage threshold | packets received in the observation window greater than 0 and at least `0.9 × duration × expected rate` | `laptop/dual_bridge.py:339-340` |
| Silence threshold | largest gap in the observation window no more than `freshness` | `laptop/dual_bridge.py:341` |
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

Each capture gets one folder: `.comms-local/B07-<UTC timestamp, format %Y%m%dT%H%M%S%fZ>-<8 hex digits>/` (`demo.py:233-236`).

| File | Written by | Format |
|---|---|---|
| `report.json` | the `laptop.dual_bridge` child process | Single-line JSON. At start it exclusively creates a placeholder file (run metadata plus `"status": "incomplete"` and `reservation_id`, permissions 0600). At the end it replaces the file atomically. Before replacing it checks that the file was not swapped for another file and that the placeholder content is unchanged (`laptop/reporting.py:49-84`, `87-120`). |
| `report-readable.json` | `demo.py` | The same content, indented by 2 spaces. Written only when `run` or `live` ends; `demo.py report` does not write it (`demo.py:176-178`). |
| `packets.jsonl` | `PacketEvidence` | One event per line: `timestamp_utc`, `monotonic_seconds`, `type`, `device_id`, plus each event's own fields. A `sensor` event includes the 8 values and `raw_hex`. |
| `packets.log` | `PacketEvidence` | The same events as `key=value` text, without color codes. |
| `live.log` | `demo.py` | The raw stdout and stderr of the child process (`demo.py:243`). |
| `exit-code.txt` | `demo.py` | The child process's exit code, one line (`demo.py:263`). |

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
- `run` (`laptop/dual_bridge.py:470-485`, `528-530`): `started_at_utc`, `finished_at_utc`, `mode`, `requested_duration_seconds`, `expected_rate_hz`, `source_rate_requested_hz`, `keyboard`, `file_device`, `seed`, `queue_capacity`, `freshness_seconds`, `ack_window`, `session_id`, `revision`, `worktree_dirty`, `workspace_source_sha256`.
- The source fingerprint (`laptop/reporting.py:13-37`) covers only `demo.py`, `firmware/esp32/platformio.ini`, and the `.py`, `.json`, `.h`, `.cpp`, `.cs` and `.swift` files in these 8 folders: `common`, `laptop`, `ultra96`, `phone`, `tools`, `firmware/esp32/include`, `firmware/esp32/src`, `ios-visualizer/CommsNative/Sources`. It excludes `flash.py` and any file with `tests` in its path. Each of the two `git` calls is limited to 1 second. On failure, `revision` or `worktree_dirty` is `null` (`git status` at `laptop/reporting.py:31-36`, `git rev-parse` at `123-132`).
- These fields describe only the laptop's working tree. The evidence does not record which build the boards were flashed with, nor which source folder the service on the Ultra96 runs.

**Per-board fields (`devices["1"]`, `devices["2"]`):**

- Counts: `received`, `malformed`, `stale_dropped`, `generation_dropped`, `sent`, `acked`, `duplicate_acks`, `ack_errors`, `ambiguous_dropped`, `transport_errors`, `transport_connections`, `ble_connections`, `ble_errors`, `cleanup_errors`, `identity_mismatches`, `source_stats_errors`, `disconnects`, `queue_dropped`, `callback_generation_dropped`, `queue_size`, `gaps`, `duplicates`, `out_of_order`, `new_boots`.
- State and verdict: `clean`, `runtime_failures`, `unfinished`, `expected_samples`, `coverage_ratio`, `sustained_coverage`, `silence_ok`, `protected_ble`, `input`, `source_issue`.
- Timing: `first_received_at`, `last_received_at`, `max_receive_silence`, `callback_received`, `observation_received`, `observation_max_silence`.
- `sensor_goodput`, `commands` (`accepted`, `rejected`, `completed`, `failed`, `pending`), `controls` (`response_errors`, `duplicate_responses`, `notification_dropped`, `native_pending`).
- `configuration`: `address`, `negotiated_att_mtu`, `source_rate_requested_hz`, `source_rate_confirmed_hz`, `connection_parameters`, `ack_window`, `queue_capacity`, `freshness_seconds`, `fixture_seed`.
- `source`: `complete`, `clean`, `device_id`, `boot_id`, `start_next_seq`, `end_next_seq`, `generated`, `source_submitted`, `source_failures`, `source_consistent`, `received`, `acked`, `missing_received`, `missing_acked`, `first_received_seq`, `last_received_seq`, `first_acked_seq`, `last_acked_seq`, `sequence_anomalies`, `ack_sequence_anomalies`, `identity_mismatches`, `boot_mismatches`, `interruptions`, `snapshot_errors`.

**`received` has three meanings. Do not mix them up.** The per-board `received` is the number of packets the writer task has dequeued and processed (`laptop/bridge.py:399`). The number of BLE callbacks is in `callback_received` (`laptop/bridge.py:301`). `source.received` is the number of packets that decoded and whose identity and boot ID matched. In the progress line, `received=` prints the callback count, and `processed=` is the one that matches the report's `received` (`laptop/dual_bridge.py:145-146`). A packet evicted from the queue counts only in the callback count. In a clean capture the three numbers are equal.

**Conditions for `source.clean`** (`laptop/source_audit.py:150-168`): both the start and the end snapshot exist; the boot ID is the same; `generated` equals `submitted` plus `failures`; `generated` is greater than 0; `failures` is 0; `received` and `acked` both equal `generated`; sequence anomalies, ACK sequence anomalies, identity mismatches, boot mismatches, interruptions and snapshot errors are all 0. Without a start snapshot, `source_issue` is `source statistics unavailable or incompatible; install updated dual-source firmware`. Without an end snapshot it is `final source statistics unavailable; capture is incomplete` (`laptop/bridge.py:983-987`).

**`diagnostic` values of `connection_parameters`** (`laptop/ble_parameters.py`): `unsupported_platform`, `baseline_rate_no_preference_requested`, `preference_request_denied_or_unavailable`, `actual_parameter_change_observed`, `actual_parameters_unavailable`, `accepted_without_observed_parameter_change`, `preference_status_unresolved`, `preference_unavailable:<exception name>`. "Request accepted" (`request_accepted`) and "actual parameters changed" (`actual_parameters_changed`) are recorded separately.

**Progress lines** (stderr; under `demo.py`, one line per board per second, `laptop/dual_bridge.py:548-562`):

```text
progress mode=<physical or synthetic> phase=<startup, observation, shutdown, drain, complete> device=N received= processed= acked= queue= drops= errors= BLE_sensor_kbps_rolling= BLE_sensor_kbps_average=
progress combined_BLE_sensor_kbps_rolling= combined_average_kbps= boundary=laptop_reception bytes=sensor_packet_including_header excludes=BLE_TLS_SSH_controls_files
```

`drops` is the sum of queue evictions, stale drops, both kinds of generation drop, and ambiguous drops. `errors` is the sum of the error counts, disconnects, sequence problems and source statistics anomalies (`laptop/dual_bridge.py:128-142`). Progress is only an in-flight display. The final word is the source statistics reconciliation.

### Goodput definition (`laptop/goodput.py`)

- It counts only the "unique and valid" sensor packets the laptop received. Within one `(device_id, boot_id)` the sequence number must advance. Version 1 values must match the dummy-data formula. Counting happens in the BLE callback.
- Bytes equal packets times 32 (`PACKET_SIZE`, including the 16-byte application header). BLE, TLS and SSH overhead is excluded, and so are commands and files.
- The denominator is the duration of the common observation window. Silent time counts; startup and drain do not.
- `average_kbps = bytes × 8 ÷ duration ÷ 1000`. The two-board total is the sum of both boards.
- `tracking_overflow` is incremented when more than 128 `(device_id, boot_id)` pairs are tracked, or when the rolling window holds more than 20000 timestamps (`laptop/goodput.py:58-60`, `69-71`). It makes the run not clean.

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
| | `--rate` | 10 (1 to 200) |
| | `--file`, `--file-device` | none / 1 |
| | `--seed` | none |
| `report` | `path` (optional, a folder or `report.json`), `--output-root` | the `B07-*` folder under `.comms-local/` with the newest modification time |
| `service` | `--start`, `--session-id` | Without `--start` it only inspects. `--session-id` defaults to the environment variable `LTC_COMMS_SESSION`, otherwise `ltc-comms`, and is used only with `--start` (`demo.py:68-71`, `292`). Details are in [chapter 4](04-ultra96-service-and-certificates.md) |

`live` also requires an interactive terminal, because it turns on `--keyboard`.

The child process that `run` and `live` actually start (`demo.py:75-90`):

```text
python -u -m laptop.dual_bridge --ca … --port … --left-address … --right-address … --duration … --session-id … --ack-window 32 --progress-interval 1 --report <folder>/report.json --evidence <folder>/packets.jsonl [--keyboard] --rate … [--seed …] [--file …] --file-device …
```

`demo.py` sets `PYTHONIOENCODING=utf-8` for the child process (`demo.py:242`).

`demo.py service --start` first prints the deployment folder and the line `Session: <name> (the capture and the phone must use the same one)`. Then it asks for Enter to confirm. Any other input cancels and returns 130 (`tools/demo_service.py:54-60`). The session ID is first validated by `validate_session`, then inserted into the start command on the Ultra96 with `shlex.quote` (`tools/demo_service.py:29-30`, `50`). The SSH account, the Ultra96 host name and the deployment folder on the Ultra96 are hard-coded in `tools/demo_service.py`. No option changes them. The session ID can be changed.

### Other command lines

| Command | Options (defaults) |
|---|---|
| `python -m laptop.dual_bridge` | `--ca` (required), `--left-address`, `--right-address`, `--port` (18888), `--session-id` (`ltc-comms`), `--duration` (600), `--queue-capacity` (64), `--ack-window` (32), `--freshness` (2.0), `--expected-rate` (10.0), `--startup-timeout` (30), `--drain-timeout` (10), `--progress-interval` (1.0, 0 turns it off), `--report`, `--evidence`, `--console-sample` (10), `--keyboard`, `--file`, `--file-device` (1), `--rate`, `--seed`, `--mock`, `--diagnostic-unprotected` |
| `python -m laptop.bridge` | `--ca` (required), `--port` (18888), `--session-id` (`ltc-comms`), `--duration` (60), `--target` (0), `--queue-capacity` (64), `--freshness` (2), `--address`, `--mock`, `--diagnostic-unprotected` |
| `python -m laptop.windows_pairing` | `--address` (without it, scans by service UUID for 8 seconds and connects to the first board found) |
| `python -m tools.ssh_tunnel` | `--jump`, `--target`, `--local-port` (18888), `--remote-port` (8888), `--identity`, `--run` |
| `python -m tools.comms_demo packet` | none |
| `python -m tools.comms_demo sender` | `--ca` (required), `--port` (18888), `--session-id` (`ltc-comms`), `--address`, `--duration` (60), `--target` (100) |
| `python -m tools.comms_demo audit <log>` | `--phone-results`, `--minimum-count` (100), `--session-id` (`ltc-comms`) |
| `python -m tools.rehearse_comms` | `--pki-dir` (required), `--duration` (60), `--target` (100), `--ble`, `--diagnostic-unprotected` |
| `python -m tools.rehearse_remote_comms` | `--ca` (required), `--ingest-port` (18888), `--gateway-port` (19999), `--session-id` (`ltc-comms`), `--duration` (40), `--target` (100), `--ble`, `--address`, `--confirmed-remote-topology` |
| `python -m laptop.phone_simulator` | `--ca` (required), `--host` (`127.0.0.1`), `--port` (19999), `--session-id` (`ltc-comms`), `--count` (0), `--reconnect` |
| `python -m laptop.ble_counter_receiver` | `--target-received` or `--duration-seconds` (one of the two is required), `--require-reconnect`, `--scan-timeout-seconds` (5.0), `--reconnect-delay-seconds` (1.0), `--queue-size` (128) |
| `python -m laptop.mtu_probe` | `--scan-timeout-seconds` (5.0), `--notification-timeout-seconds` (2.0) |

When `laptop.dual_bridge` is given `--rate`, the expected rate is `--rate`, and coverage is judged against it. With `--mock`, the synthetic source runs at `--expected-rate`. Any of `--keyboard`, `--file` or `--rate` enables the control channel. Then `--mock` and `--diagnostic-unprotected` cannot be used (`laptop/dual_bridge.py:449-451`).

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
- `tools/demo_service.py` builds its command with the same function. It removes `-N`, `-T` and `-L`, adds `-tt`, and runs a script on the Ultra96 (`tools/demo_service.py:15-26`).

### Extension point: real glove packet (decided, not yet implemented)

| Offset | Length | Field | Type | Multiplier |
|---:|---:|---|---|---|
| 0 | 16 | header (magic, version, device_id, boot_id, seq, uptime_ms) | same as now | — |
| 16 | 6 | ax, ay, az | 3 × int16 | ×10000 |
| 22 | 6 | gx, gy, gz | 3 × int16 | ×100 |
| 28 | 6 | yaw, pitch, roll | 3 × int16 | ×100 |
| 34 | 4 | flex1, flex2 | 2 × int16 | ×10000 |

The total is 38 bytes. The notification needs an ATT MTU of at least 41. The order of the 11 values follows sections 4.2 and 7.1 of the hand-off document.

Decided 2026-10-14, planned, not built (hand-off document, sections 8 step 1 and 13):

- **It is protocol version 3**, a new version, so no receiver can read it with the old 8-value layout. Firmware, laptop and Ultra96 parsers change together. On the laptop's TLS leg the version shows too: the `v` of `SENSOR_BATCH` is the packet's version (`common/sensor.py:50`), and the Ultra96 accepts only `v` 1 and 2 (`ultra96/protocol.py:42-43`). A laptop that sends version 3 to an old service is disconnected without a reason (see the note after the failure path table).
- **Transport stays int16.** `SENSOR_BATCH` carries the int16 values unchanged; the Ultra96 restores the physical floats for the model (hand-off document, sections 3.1 and 7.2).
- **The multipliers are checked against Siqiang's real sample log before they are fixed.**
- **Out-of-range values:** recommended clamp to the int16 limit and count, never silent; awaiting the owner's confirmation against dropping that one sample (see "int16 range" above).
- In the owner's proposed plan this work starts on Thu 10-15, before the in-person integration session on Tue 10-20 (hand-off document, section 6.4).

## Workflow

### One-time setup

1. Install the dependencies: `python -m pip install -r laptop/requirements.txt`.
2. Board map: `python flash.py` flashes the boards in the order they are plugged in and writes `.comms-local/boards.json` (the first board plugged in is left). This laptop already has the map (see "Local state" under "Cautions and known limits").
3. Pairing: run `python flash.py --pair left`, then `python flash.py --pair right` (with no value it pairs both). For each board it runs `python -m laptop.windows_pairing --address <address>` (`flash.py:125-133`). On first pairing, run `python flash.py --monitor COMx` in another terminal to read the passkey from that board's serial port.
4. The pairing program opens the device by address through WinRT. For a device that is already paired, it only checks the level. For an unpaired device it starts pairing with `PROVIDE_PIN` and `ENCRYPTION_AND_AUTHENTICATION`. The 6-digit passkey is typed hidden in the console (digits only, at most 6, backspace works, Ctrl+C cancels). It waits at most 90 seconds.
5. On success it prints `{"authenticated_bond": true, "address": …}`. A bond level other than 3 (encryption and authentication) reports `authenticated Windows bond required; run laptop.windows_pairing first` (`laptop/windows_pairing.py:22-25`). An existing weak bond is not upgraded automatically: remove the board in Windows first, then pair again. A pairing failure reports `authenticated passkey pairing failed (<status>); deliberate bond recovery may be needed`.

### Normal path (`python demo.py run`)

1. Terminal A runs `python demo.py tunnel`. It starts an ssh child process that forwards local `127.0.0.1:18889` to `127.0.0.1:8888` on the Ultra96. Keep this terminal open.
2. Terminal B runs `python demo.py run` (`--ca` can be left out when the default local CA path exists). Without addresses it reads the board map and prints `Board mapping: LEFT / ID 1 = …; RIGHT / ID 2 = …`. Then it checks that the CA file exists, that the two addresses differ, that standard input is a terminal when `--keyboard` is set, and that the `--file` size is between 1 and 65536 bytes. If any check fails, it ends with exit code 2 and creates no capture folder (`demo.py:216-230`).
3. `demo.py` creates the folder `B07-…` and starts the child process `laptop.dual_bridge`. It writes the child's output line by line into `live.log` and shows it in the terminal.
4. The child first reserves `report.json` (`status: incomplete`). If the path already exists, it prints `report reservation failed: …` and ends with exit code 2 without touching hardware (`laptop/dual_bridge.py:486-495`).
5. The child creates one `PacketEvidence` (background thread named `packet-evidence`) and two `Bridge` objects. All coroutines run in one asyncio event loop.
6. Each board starts two tasks, `writer-N` and `input-N`. With controls enabled it adds `commands-N`. `demo.py` always passes `--rate`, so controls are always enabled.
7. `input-N` scans. It filters advertisements by service UUID, then by address (case-insensitive), for at most 8 seconds (`laptop/bridge.py:702-706`).
8. Connect: `make_ble_client` does not use the cached service table. At most 20 seconds.
9. It checks that the sensor characteristic supports Notify and that `mtu_size` is at least 35. Otherwise it abandons this connection (`laptop/bridge.py:715-720`).
10. It checks that the Windows bond level is "encryption and authentication" (`laptop/bridge.py:722-724`).
11. It requests the throughput preference, but only on Windows and only when `--rate` is above 10. The default 10 Hz makes no request, and the report records `baseline_rate_no_preference_requested`.
12. It reads the source statistics as the start snapshot. A wrong length, reserved bytes, magic or `device_id` fails (`laptop/bridge.py:737-757`). On reconnect it reads them again, but the start point does not change; it records one interruption.
13. Control channel: it checks both control characteristics, requires an MTU of at least 64, subscribes to the response characteristic, sends `SET_RATE` and checks the echo (`laptop/bridge.py:758-772`).
14. It enables the receive queue (the generation equals this connection's number), subscribes to the sensor characteristic, and marks this board "active" (`laptop/bridge.py:773-782`).
15. Once both boards are active, the common observation window starts. Startup waits at most 30 seconds.
16. Each notification is handled in the BLE callback (`laptop/bridge.py:284-309`). The callback records the arrival time and copies the bytes into the queue (when the queue is full, it drops the oldest and counts it). Then it decodes the packet once for goodput and hands a `sensor` or `sensor_invalid` record to the evidence thread. Last, it updates the callback count and the observation window's silence statistics. The callback does no network operations. A lock protects the queue, and `call_soon_threadsafe` wakes the writer.
17. The sender side of `writer-N` first takes an ACK slot (at most 32), then takes a packet from the queue.
18. It validates the packet: decoding, identity, sequence number, connection generation, freshness. A packet that stayed on the laptop for more than 2 seconds is dropped and counted as `stale_dropped` (`laptop/bridge.py:398-427`).
19. If there is no TLS connection, it connects to `127.0.0.1:<port>` now and verifies the certificate against the fixed server name `ultra96.week7.internal`. After connecting, it checks generation and freshness again (`laptop/bridge.py:565-577`).
20. It writes one `SENSOR_BATCH` frame. The write timeout is the smaller of `io_timeout` and the remaining freshness. A written frame enters the pending-ACK queue.
21. The receiver side of `writer-N` reads ACKs in FIFO order and compares each one only with the head of the queue. On a match it increments `acked` and releases a slot. Each frame's ACK must arrive within 5 seconds of its send time.
22. When the observation window ends, it first stops the keyboard, the file transfer and the commands. Then it tells both boards to stop at the same time.
23. Each board does its tail handling independently (see the next section).
24. It waits for both boards' queues and in-flight frames to empty, for at most 10 seconds. Then it cancels the writer tasks and closes TLS.
25. It computes the verdict, writes `report.json` atomically, and prints the same JSON to stdout. A clean run exits 0; otherwise the exit code is 1.
26. `demo.py` writes `exit-code.txt` and reviews the report. It prints a "generated, received, acknowledged" table per board and one packet example pair per board. Only if everything passes does it print `CAPTURE PASSED: physical ESP input through Ultra96 ingestion ACKs.` and `Phone expected increase: N`. N is the sum of both boards' `generated` plus the number of completed commands (`demo.py:209-212`). The phone count is compared by hand; the tool does not check it.

### Tail handling at shutdown (`laptop/bridge.py:805-935`)

When shutdown starts, an overall deadline is set: the current time plus `connect_timeout` (20 seconds, `laptop/bridge.py:811`). Steps b to f are all bound by this deadline.

- a. It detaches the control channel and stops notifications on the response characteristic (0.75 s).
- b. Only on a normal stop, while subscribed, still connected and with source statistics enabled, it writes the sensor characteristic's CCCD to NONE through WinRT (at most 0.75 s). The local callback stays. On non-Windows, or without the native interface, this step returns False, and c and d are skipped (`laptop/ble_shutdown.py:12-23`).
- c. It reads the source statistics again without the cache to get the "quiesced snapshot". The boot ID must equal the start. The expected received count equals the increase in `submitted`.
- d. It waits for the processed packet count to reach the expected value, for at most 0.5 s. On timeout it records one `source_tail_drain` (`validation=timeout`) and one `source_stats_errors`.
- e. `stop_notify` removes the local callback (0.75 s). This step is skipped when the native operation from b has not finished.
- f. It reads the source statistics once more as the end snapshot (uncached if c ran). It must equal the quiesced snapshot exactly. Otherwise it reports `source changed after notifications were quiesced`.
- g. The queue stops accepting new callbacks. Only on a normal stop where e succeeded are the queued tail packets kept for the writer to send. Otherwise the queue is cleared and the packets count in `callback_generation_dropped` (`laptop/bridge.py:910`).
- h. It refreshes the connection parameter record, disconnects (its own 1.0 s), and releases the throughput preference handle.

### Commands, rate setting, files

1. Key `1` targets device 1 (left) and key `2` targets device 2 (right). Each key press creates a version 2 packet: the values are a random row from `common/dummy_fixtures.json`, `uptime_ms=0`, and `seq` is a new request ID. When the command queue is full (8 entries) or the board is not connected, the command is rejected and logged as `command_rejected`. `rejected` does not affect the verdict.
2. A board has only one control transaction at a time. After writing a request, the laptop waits for the response, with `io_timeout` as the timeout.
3. A command's response must have the same `device_id`, `boot_id` and `seq`, and each of the 8 values must be exactly 1 higher (`laptop/controls.py:185-198`).
4. After validation, the laptop opens a separate TLS connection for this command. It sends one `SENSOR_BATCH` frame with `request_id`, waits for one ACK, then closes. `status` must be `accepted`. The command does not use the data stream's sequence numbers or ACK counts (`laptop/bridge.py:263-282`).
5. A command that times out is not retried. It is recorded as failed.
6. The request ID (shared by commands, rate setting and files) starts at a random number between 1 and 0x7FFFFFFE and increments. 0xFFFFFFFF itself can be used. Only taking the next one reports `control request identity space exhausted; restart capture` (`laptop/controls.py:40`, `64-69`).
7. File transfer steps: send `FILE_BEGIN`. Then split the file into chunks of `min(180, MTU-17)` bytes and wait for each chunk's confirmation; the confirmation's `offset` must equal the start of the next chunk. Finally send `FILE_END`. The length and SHA-256 the receiver returns must match the sender's. On any failure, the laptop tries to send `FILE_ABORT` while the same connection is still up.

Time limits, exclusivity and retry boundaries of the file transfer:

- The transfer starts when the common observation window starts (`laptop/dual_bridge.py:181-183`). If it has not finished when the window ends, it is cancelled and recorded as `file:interrupted`, and the run is not clean. After cancellation the laptop still tries to send `FILE_ABORT`.
- The whole transfer holds the control channel's serial lock (`laptop/controls.py:223`). Key commands wait until the file finishes. The command queue holds only 8 entries; further presses are rejected.
- A chunk is retried only after a timeout, at most 2 more times. When the board returns a non-zero status (for example 2 `BUSY`), the laptop does not retry. It fails and aborts at once, and `controls.response_errors` increases by 1 (`laptop/controls.py:126-134`).
- After a retry, if the first attempt's response arrives late, it is recorded as `duplicate_responses` or `response_errors`. The run is then not clean either.
- A BLE reconnect midway does not resume the transfer. It reports `file interrupted by BLE disconnect`.
- A successful result is written to `file_transfer` in `report.json`: `transfer_id`, `bytes`, `sha256`, `elapsed_seconds`, `sender_bytes`, `sender_sha256`, `receiver_bytes`, `receiver_sha256`, `file_payload_kbps`, `verified`.
- The command line reads at most 65537 bytes to tell whether the file is too long (`laptop/dual_bridge.py:456-464`).
- Only 4096 bytes have been tested (23 chunks, once on each board). 65536 bytes is about 365 chunks, and each chunk is one write with response plus one notification. Whether that finishes under the default 60 seconds, 10 Hz and no throughput preference has not been tested.

### Failure paths

| Situation | Behavior | What the report shows |
|---|---|---|
| Not found by the scan, connection failure, MTU too small, bond level too low | This attempt ends. `ble_errors` increases by 1, and `live.log` has `BLE attempt failed: …` (`laptop/bridge.py:804`). Retry after back-off | If the board does not become active within 30 seconds, `runtime_failures` contains `startup:TimeoutError` and the observation window duration is 0 |
| Source statistics unreadable or malformed | Does not subscribe to the sensor. `source_stats_errors` and `ble_errors` each increase by 1. Retry after back-off | `source_issue` asks for a firmware update |
| The board still runs Week 7 firmware (sends `W7` and `W7S1`) | Reading the source statistics reports `invalid source statistics magic; flash this board with the current firmware`. This connection is abandoned and retried after back-off. The board never becomes active and never reaches the "malformed packet" step | `ble_errors` and `source_stats_errors` grow, `runtime_failures` contains `startup:TimeoutError`, and `source_issue` asks for a firmware update. Only the single-board tools that do not read source statistics record `W7` packets as `malformed` |
| The BLE link drops during the run | `disconnects` increases by 1. The remote notification stop is skipped, but the local disconnect still happens. The queue is cleared and counted in `callback_generation_dropped`; those samples are not resent, so the Ultra96 sees a gap in `seq`. While disconnected the board makes no samples, so that time shows only as a jump in `uptime_ms`. Reconnect waits until the previous native operation ends | `source.interruptions` is greater than 0, and this board is not clean. The other board continues |
| The board reboots | After reconnect the boot ID has changed | `new_boots`, `boot_mismatches`. The start and end snapshots have different boot IDs, and `generated` is `null` |
| TLS cannot connect (tunnel not open, certificate expired, host name mismatch) | This packet was dequeued but not written, so it does not count in `ambiguous_dropped`. The next packet triggers a reconnect after back-off | `transport_errors` grows, `acked` is 0, and later packets become `stale_dropped` or `queue_dropped`. In the reconciliation, `missing_acked` is greater than 0 |
| TLS disconnect, write timeout, ACK timeout or mismatched ACK | This TLS connection is discarded. All in-flight frames and frames whose write was attempted count as `ambiguous_dropped` and are not resent; any of them the Ultra96 had not processed leaves a gap in `seq` there. The connection is closed, and the next packet triggers a reconnect after back-off | `transport_errors`; on an ACK timeout or mismatch, `ack_errors` also increases by 1; `ambiguous_dropped` |
| ACKs are slow | Once the 32 slots are full, the sender waits. A packet that stays in the queue for more than 2 seconds is dropped | `stale_dropped` |
| Queue full | Drops the oldest | `queue_dropped` |
| Malformed packet or wrong `device_id` | Not forwarded | `malformed`, `identity_mismatches` |
| At shutdown the tail packet does not arrive, or the end snapshot changed | Records an error and hides nothing | `source_stats_errors`; `source.clean` is false |
| The writer task ends permanently (ACK window greater than 1) | The writer loop catches only `_PipelineTransportError` (`laptop/bridge.py:665`). Three other cases raise `_PipelineCleanupError`, which nothing catches: a worker coroutine of the old TLS generation (`epoch` in the code) did not exit within 0.2 s (`laptop/bridge.py:523-531`, `651`); a pending frame belongs to another generation (`:604`); a worker coroutine ended without a reason (`:645`). Then `writer-N` ends and is not restarted. Until the capture ends, this board's later packets only enter the queue and are evicted | `runtime_failures` contains `writer:_PipelineCleanupError`, usually also `drain:timeout` and `queue_dropped` |
| Shutdown hangs | The input task is cancelled after 25 seconds, then waited on for 0.5 s more. Drain waits 10 seconds. The writer task waits another 25 seconds. Final event-loop cleanup waits only 0.1 s (`laptop/dual_bridge.py:565-584`) | `shutdown:timeout`, `drain:timeout`, `writer:timeout` |
| The evidence queue overflows or a disk write fails | Does not block packet reception | When `evidence.dropped`, `write_errors` or `unfinished` is non-zero, the overall `clean` becomes false |
| The report save fails | stdout still prints the JSON | `report_saved` is false, `report_error` is the exception name, and the exit code is non-zero |
| The operator presses Ctrl+C | `demo.py` terminates the child it started (force kill after 5 seconds) and writes 130 to `exit-code.txt` | The report stays at `incomplete`, and the review fails |
| The SSH tunnel drops | Shows up as a TLS failure. Run `demo.py tunnel` again in terminal A | Same as a TLS disconnect |

**Neither end records why something was rejected.** On the laptop, a TLS connect or handshake failure increments only `transport_errors`. An ACK timeout or a mismatched ACK increments both `ack_errors` and `transport_errors`. None of these records a reason (`laptop/bridge.py:466-470`, `665-666`). Only BLE failures write `BLE attempt failed: …`. On the Ultra96, a bad frame, a session mismatch, an identity conflict or exhausted capacity also only closes the connection and increments `rejected` (see [chapter 4](04-ultra96-service-and-certificates.md)). The consequence: no log on either side says why. On the laptop, an expired certificate and an unreachable port look the same (only `transport_errors` grows), and a mismatched session ID and mismatched protocol versions between the two ends (for example, only one end upgraded to 11 values) look the same (the Ultra96 closes the connection after the frame, so both `ack_errors` and `transport_errors` grow). During the 38-byte migration (decided as protocol version 3, hand-off document section 8, step 1), upgrading one end first shows up as a "silent disconnect". Both ends must be upgraded together.

### Complete list of `runtime_failures` markers (`laptop/dual_bridge.py`)

| Marker | Meaning | Lines |
|---|---|---|
| `startup:<exception name>` | did not become active within 30 seconds | 171 |
| `input:stopped`, `input:<exception name>` | the input task ended early inside the observation window | 199-203 |
| `writer:stopped`, `writer:<exception name>` | the writer task ended inside the observation window, or ended with an exception during shutdown | 204-212, 310-313 |
| `writer:timeout` | the writer task did not exit within 25 seconds during shutdown | 300 |
| `keyboard:error` | the keyboard task failed; recorded on device 1 whichever key was pressed | 192-193 |
| `file:shutdown_timeout`, `file:interrupted`, `file:<exception name>` | the file transfer did not finish its cleanup, was cancelled, or failed | 227, 230, 232 |
| `commands:drain_timeout`, `commands:shutdown_timeout` | the command queue was not drained within 10 seconds; the command task did not exit within 25 seconds | 245, 252 |
| `shutdown:<exception name>`, `shutdown:timeout` | the input task's shutdown failed or timed out | 265, 268 |
| `drain:timeout` | the queue or the in-flight frames did not empty within 10 seconds | 292 |
| `transport_close:<exception name>` | the final TLS close failed | 321 |

### Verdict: `clean`

The overall `clean` is true only when all of these hold (`laptop/dual_bridge.py:329-362`, `525-545`): both boards became active within 30 seconds; the progress callback never raised an exception (`progress_error` is false); both boards are `clean`; the evidence `dropped`, `write_errors` and `unfinished` are all 0; the report was saved.

Each board's `clean` is true only when:

- `runtime_failures` is empty.
- `source.clean` is true.
- Coverage and silence both pass, `protected_ble` is true, and `unfinished` is false.
- These 18 fields are all 0: `malformed`, `stale_dropped`, `generation_dropped`, `duplicate_acks`, `ack_errors`, `ambiguous_dropped`, `transport_errors`, `ble_errors`, `cleanup_errors`, `identity_mismatches`, `source_stats_errors`, `disconnects`, `queue_dropped`, `callback_generation_dropped`, `gaps`, `duplicates`, `out_of_order`, `new_boots`.
- `commands.failed` and `commands.pending` are 0 (`commands.rejected` does not matter).
- The four `controls` counts `response_errors`, `duplicate_responses`, `notification_dropped` and `native_pending` are all 0.
- `sensor_goodput.tracking_overflow` is 0.

Easy to miss: a single `INGEST_ACK` whose `status` is `duplicate` makes the board not clean. `duplicate` proves that the Ultra96 received the packet (level 3), and it also makes the run not clean. The two do not contradict each other.

`demo.py` adds its own criteria on top (`demo.py:143-159`) and requires the packet example review to pass (`demo.py:205-208`). See "How to run and verify".

## Why it is designed this way

Records cited: [Selected design] = `docs/archive/design/week7-selected-design-2026-09-06.md`; [Dual-board spec] = `docs/archive/design/specs/2026-09-17-dual-esp-reception.md`; [Dual-board plan] = `docs/archive/design/plans/2026-09-17-dual-esp-reception.md`; [09-19 test] = `docs/archive/test-evidence/dual-esp-physical-test-2026-09-19.md`; [09-28 test] = `docs/archive/test-evidence/co-live-deployment-2026-09-28.md`; [v2 protocol] = `docs/co-protocol-v2.md`; [Architecture draft] = `docs/archive/design/architecture-and-interface-draft-v0.1.md`; [Features plan] = `docs/archive/design/plans/2026-09-28-co-features.md`. The "rejected" options in the archived records are history only. They are not proposals to reopen now.

1. **Bounded queue, drop oldest when full, freshness 2 seconds.** Stale gesture data is useless. Memory must not grow however long a fault lasts. Rejected at the time: an unbounded queue; replaying the backlog after a disconnect. Source: [Selected design] item 10; [Architecture draft] section 11, "Drop stale sensor records rather than replaying old gestures." This 2 s is only how long a sample may wait on the laptop. The Ultra96 has its own 2 s limit on how long a result may wait on the board (queue plus write to the phone's connection, `ultra96/server.py` `get_timed` and `_send_results`), and the phone has its own 2 s display window counted from when it received a result. None of them is an end-to-end latency bound or a promise that the phone receives a result (hand-off document, sections 7.2 and 9.2).
2. **Frames written but not acknowledged are not resent.** The laptop cannot know whether the other end already processed the frame. A resend could produce a second result. Rejected at the time: automatic retransmission. Source: [Selected design] item 10; the implementation notes in [Dual-board spec].
3. **One independent path per board (its own BLE link, queue and TLS connection).** One board's stuck ACK or reconnect must not block the other board. Rejected at the time: one writer shared by both boards. Source: [Dual-board spec] "Scope and acceptance", point 2.
4. **ACK window of 32.** With stop-and-wait per packet, a single ACK wait on the remote route was measured at up to 2.375 seconds. Packets queued behind it waited more than 2 seconds and were dropped. Two 600-second remote tests lost 1 packet and 33 packets. 32 is roughly 2.4 seconds times 10 Hz, plus margin. Rejected at the time: keeping stop-and-wait (kept as window 1); relaxing the 2-second freshness. Source: [09-19 test] "Per-packet ACK timing diagnostic"; the implementation notes in [Dual-board spec].
5. **Read the source statistics once before subscribing and once after stopping.** A successful notification submission does not mean delivery. Looking only at the first and last received sequence numbers cannot detect a lost first or last packet. The sequence number is assigned before submission, so a sample whose submission failed also uses a sequence number. Rejected at the time: counting only the received packets. Source: [Dual-board spec] "Scope and acceptance", points 5, 6 and 7.
6. **At shutdown, turn notifications off on the remote side first, keep the local callback, then wait for the tail packet.** The ordinary `stop_notify` removes the callback as soon as it has written the CCCD. In a 100 Hz probe, the ordinary stop lost the last packet in 3 of 12 runs; the new method lost it in none of 12. Rejected at the time: using only `stop_notify`; adding a loss tolerance to the reconciliation. Source: [09-28 test] "Fresh post-fault baseline and regression checks" and "Final software verification".
7. **The disconnect has its own 1-second budget.** Two notification-stop timeouts once used up a shared 1 second, leaving the disconnect only 1 millisecond, and native resources were not released. Rejected at the time: one deadline shared by all cleanup. Source: [09-28 test] "Initial rate failure and investigation".
8. **GATT discovery does not use the cache.** A bonded Windows session once reported a cached MTU of 23 when the real value was 517. The cost is a slightly slower connection. Rejected at the time: using the cache by default. Source: [Selected design] item 17.
9. **Own WinRT pairing code.** `pair()` in Bleak 3.0.1 uses `CONFIRM_ONLY`, which can lower the protection level. Rejected at the time: Bleak's built-in pairing; Just Works; an extra HMAC or AES-GCM layer over BLE. Source: [Selected design] items 13 and 14; `laptop/windows_pairing.py:1-7`.
10. **At most 2 unfinished native BLE operations, and no reconnect before they finish.** WinRT operations may ignore cancellation; without a limit they pile up. The cost is that reconnect pauses when the native stack is stuck (`laptop/bridge.py:688-692`). Rejected at the time: starting a new connection right after a timeout. Source: [Selected design] item 19.
11. **SSH uses an explicit `ProxyCommand`, not `-J`.** Strict host-key checking, timeouts and `BatchMode` must each take effect on both hops. Interactive mode uses 20 seconds and 60 seconds because the time spent typing the password at the jump host counts against the target's connect time limit. Rejected at the time: `-J`; 10 seconds on both hops. Source: [Selected design] items 18 and 25.
12. **TLS runs inside SSH, with a fixed server name check and no plaintext mode.** The laptop connects to a local forward port, and it must still confirm that the other end is that Ultra96. Rejected at the time: verifying against `localhost`; turning verification off; mutual TLS. Source: [Selected design] item 11.
13. **Commands use a separate TLS connection and are not retried on timeout.** This way they do not use the data stream's sequence numbers or ACK counts. A retry could produce a second event. Rejected at the time: sharing the connection with the data stream; automatic retry. Source: [Features plan] "Architecture" paragraph and "Contracts"; `laptop/bridge.py:264`.
14. **The throughput preference is requested only above 10 Hz and is released with the connection.** It costs power and the number of devices that can be connected at once. An accepted request does not mean the parameters actually changed, so the two are recorded separately. Rejected at the time: always requesting it; treating "accepted" as "in effect". Source: [v2 protocol] "Protected BLE controls"; [09-28 test].
15. **The report is reserved first and replaced atomically, and never overwrites an existing file.** An interrupted capture is not mistaken for a finished one and does not overwrite another capture. Rejected at the time: writing directly at the end. Source: [Dual-board plan] "Approved live-progress and report follow-up — 2026-09-17".
16. **Results do not come back to the laptop.** The laptop is not a result relay; the phone dials out by itself. Rejected at the time: the laptop forwarding results to the phone. Source: [Architecture draft] section 4.2; [Selected design] item 7.
17. **Coverage threshold 90%, silence threshold equal to freshness.** This tolerates scheduling jitter at the start and stop edges, and still detects a stream that stops midway. The 90% applies only to the rate; the reconciliation still requires every packet. Rejected at the time: looking only at totals. Source: [Dual-board spec] "Scope and acceptance", point 10.

## Cautions and known limits

### Week 7 traces kept on purpose

These names were kept on purpose when the compatibility was removed (hand-off document, section 6.2):

- The TLS server name `ultra96.week7.internal` (`common/tls.py:4`). It is written into the server certificate, and every client verifies against it. It cannot change.
- The default `--ca` path of `demo.py` contains the dated folder name `cg4002-week7-20260906` (`demo.py:49-50`). This folder really exists on this laptop. On another machine, pass `--ca` explicitly.
- The deployment folder on the Ultra96 that `demo.py service` uses is also dated (`tools/demo_service.py:11-12`). It really exists on the Ultra96. `BOARD_SOURCE` now points to the September 28 snapshot. If it is not changed after a redeploy, `demo.py service --start` still starts the old code.

### Usage cautions

- **Port defaults differ.** `demo.py` uses 18889. `laptop.bridge`, `laptop.dual_bridge`, `tools.ssh_tunnel`, `tools.comms_demo` and `tools.rehearse_remote_comms` use 18888. The tunnel and the capture must use the same port.
- **Personal defaults are in the code.** The `--jump` default of `demo.py tunnel` contains the original operator's account. The account, the Ultra96 host name and the path on the Ultra96 used by `demo.py service` are hard-coded, and nobody else can change them by option (the session ID can be changed with `--session-id`). `tools/demo_boards.py:10` holds the built-in default addresses of the two boards.
- **A leftover `LTC_COMMS_SESSION`.** This environment variable affects `demo.py run`, `demo.py live` and `demo.py service --start` together. `--session-id` on the command line takes precedence. The variable is read once, when the options are parsed (`demo.py:54-55`, `70-71`). The phone's session ID is compiled into the app as `ltc-comms` and does not read this variable (the one in use is `IntegrationController.swift:74`; the form text in `SetupViewController.swift:51` repeats it, so both change together). Documents from the transition period taught setting `LTC_COMMS_SESSION=week7-demo`. If the terminal still has it, the laptop and a newly started service both use `week7-demo`. ACKs are normal and `CAPTURE PASSED` appears as usual, but the service closes the phone's connection at once, and the phone keeps showing `Disconnected: connection closed; retrying`. When troubleshooting, first confirm that this variable is not set.
- **`demo.py run` always enables the control channel.** `--rate` defaults to 10 and is always passed to the child. So both boards must have the control characteristics, and the MTU must be at least 64.
- **`demo.py` does not expose `--ack-window` or `--queue-capacity`.** It fixes 32 ACK slots and 64 queue places. At 50 Hz that is only 0.64 seconds in flight plus 1.28 seconds queued. The 50 Hz test on 09-28 passed with the 32-byte dummy packet; real 38-byte data has not been measured. On 09-19 an ACK wait of 2.375 seconds was measured on the remote route.
- **The physical path works only on Windows.** The bond check imports `winrt`. Passkey input and keyboard commands use `msvcrt`. On non-Windows the throughput preference is not requested, and the remote notification stop returns False.
- **`bleak` must stay pinned at 3.0.1.** The remote notification stop uses the `obj` attribute of Bleak's characteristic object and the WinRT native method `write_client_characteristic_configuration_descriptor_with_result_async`. Without them the function silently returns False and falls back to the ordinary stop, and the tail-packet protection is gone (`laptop/ble_shutdown.py:12-23`). The client is created with caching off through `winrt={"use_cached_services": False}` (`laptop/ble_connection.py:5-8`). Pairing and connection parameters call the `winrt` packages directly (`laptop/windows_pairing.py:55-56`, `92`, `103`; `laptop/ble_parameters.py:135-139`). These packages come in as Windows dependencies of `bleak` 3.0.1 and are not listed separately in `laptop/requirements.txt`. Before upgrading Bleak, run the shutdown tail-packet probe on real hardware.
- **The result port has only one subscriber.** `laptop/phone_simulator.py` and `tools/rehearse_remote_comms.py` displace the phone as soon as they subscribe. Do not run them during a demo or joint testing.
- **`python -m laptop.bridge` (the single-board command line) is not the field entry point.** Its ACK window is 1. It has no source statistics reconciliation and no control channel.
- **Three traps shared by the diagnostic and rehearsal tools.**
  - No board selection: `laptop.ble_counter_receiver`, `laptop.mtu_probe` and `tools.rehearse_comms --ble` have no address option (`laptop/ble_counter_receiver.py:336`, `laptop/mtu_probe.py:153`, `tools/rehearse_comms.py:29-30`). Neither does `laptop.windows_pairing` without `--address`. They scan by service UUID and connect to the first board found. Both boards have the same advertised name and service UUID, so power only one board when using these tools. `tools.comms_demo sender` and `tools.rehearse_remote_comms` have `--address`.
  - No rate setting: the firmware keeps its last rate after a disconnect. Only `demo.py` and `laptop.dual_bridge` with `--rate` send the rate command (`laptop/bridge.py:770-772`). The single-board tools inherit whatever rate the board last had, yet judge against 10 Hz, and their ACK window is also 1.
  - Packet version: `tools.comms_demo packet` prints a version 1 example without `request_id` (`tools/comms_demo.py:19`), while the firmware sends version 2 by default. The synthetic input of `tools.rehearse_remote_comms` is also version 1, and it enters the real service on the Ultra96 as device 1 (`tools/rehearse_remote_comms.py:129-137`).
- **`tools/comms_demo.py audit` validates the `result` lines in a log as `v=1`.** It requires the label to equal `GESTURES[seq % 4]` (`ultra96/protocol.py:78-79`). The default synthetic input of `tools.rehearse_remote_comms` is version 1, so a log recorded with it passes. In a log recorded with `--ble`, the results are version 2. The service on the Ultra96 picks a random label for version 2, so each result has only a one-in-four chance of equalling `GESTURES[seq % 4]`, and the audit fails.
- **Implicit input requirements of `demo.py report`.** It requires both `exit-code.txt` and `packets.jsonl` next to `report.json`. A report from running `python -m laptop.dual_bridge --report …` directly has no `exit-code.txt` and is judged `CAPTURE NOT PASSED: missing, incomplete or unreadable evidence (…)` (`demo.py:171-174`). Without a path, it takes the `B07-*` folder under `--output-root` with the newest modification time, even if that run was interrupted (`demo.py:269-275`). Terminal colors apply only to `demo.py`'s own output: lines containing `disconnected`, `failed` or `rejected` are yellow, device 1 is cyan, device 2 is magenta. `live.log` has no colors (`demo.py:104-116`).
- **Evidence content.** The evidence contains BLE addresses and all sensor values. It contains no passkey, password or private key.
- **The measured limits apply to the 32-byte dummy packet.** "70 Hz passed" means the 70 Hz setting: it delivered about 66 packets per second per board to the laptop, about 33.8 kbps for both boards together, and the run passed. The 75 Hz setting failed ([09-28 test]). Real 38-byte data has not been measured at any rate: 38 bytes × 50 Hz × 2 boards = 30.4 kbps is below the measured figure, but that is arithmetic, not a measurement (hand-off document, section 8, step 3).
- **The server certificate is valid for only 30 days** (`tools/generate_comms_pki.py:47`). The copy saved on the laptop, which is the certificate deployed to the Ultra96 in September, expired on 2026-10-06 15:11:29 UTC. Only this laptop copy was checked; whether the Ultra96's certificate was replaced later has not been checked. The CA is valid until 2027-09-06, and its SHA-256 matches the fingerprint pinned in the phone source. For how the laptop behaves on expiry, see the "TLS cannot connect" row of the failure path table. To renew, run `python -m tools.generate_comms_pki --renew-server-from <original CA folder> --output-dir <new empty folder outside the repository>`. It signs a new server private key and certificate with the original CA, and the CA does not change (`tools/generate_comms_pki.py:75-101`). The steps are in section 6.3 of the hand-off document.

### Local state (2026-10-14)

- `.comms-local/` now holds only `boards.json` (created 2026-10-14 03:05, `version` 1, `status` `ready`, byte-for-byte identical to `.week7-local/boards.json`). Capture uses this map. There is no need to reflash to get the map.
- There are no `B07-*` capture folders under `.comms-local/` yet. So `python demo.py report` without a path prints `Demo could not complete: No B07 captures in …; run a capture first.` and ends with exit code 2 (`demo.py:269-273`, `294-296`).
- Old captures are under `.week7-local/`: 17 capture folders (`B07-*`, 2026-09-28 to 10-01), all recorded with Week 7 firmware. In 11 of them, `packets.jsonl` has `sensor` records with `raw_hex`; all of these start with `5737` (`W7`), and none is `LC`. The newest (2026-10-01) has 7038 of them. Another 4 have no `packets.jsonl`, and 2 have no `sensor` records with `raw_hex`. `python demo.py report "<old folder>"` does not pass even with a path: the packet example review decodes `raw_hex`, and the decoder accepts only `LC`. The result is `PACKET EXAMPLES NOT PASSED: …` plus `CAPTURE NOT PASSED: packet evidence could not be verified.` (`tools/video_evidence.py:91-93`, `116-118`). To review old captures, use the code at commit `ec398b6`. Keep `.week7-local/`; do not delete it (hand-off document, section 9.1).
- The left board was flashed with the current firmware on 10-14 and verified locally: local loopback 100/100 packets; in another run 349 packets, the source statistics reconciliation passed, a rate change to 20 Hz was confirmed, and all 3 commands made the round trip (hand-off document, section 6.1). The right board still runs Week 7 firmware, so a two-board capture times out at startup because its source statistics magic is rejected. Flashing it, renewing the server certificate and redeploying the Ultra96 service are in the owner's proposed plan for Thu 10-15 (hand-off document, section 6.4). The current code accepts only `LC`, `LCS1` and `ltc-comms`, and it has not yet done a real two-board capture through the Ultra96. The repository cannot confirm the actual code snapshot, session ID or certificate of the service on the Ultra96 (hand-off document, section 6.3).

### Extension points (Communications' own work, not yet implemented)

The order of these steps is section 8 of the hand-off document; the owner's proposed dates up to the in-person integration session on Tue 2026-10-20 are in its section 6.4. All of them are planned, not built.

- **38-byte real data packet.** Decided 2026-10-14: protocol version 3, with the scales checked against Siqiang's real sample log before they are fixed (see "Extension point: real glove packet" above). Proposed start: Thu 10-15. Places on the laptop side that hard-code "8 values, 32 bytes": `common/sensor.py:11` (struct), `:36` (value count), `:33` and `:79` (version), `:84-87` (dummy-data formula); `laptop/bridge.py:719` (MTU 35); `common/control.py:119-121` (the value transformation for commands); `common/dummy_fixtures.json` (8 values per row); `tools/comms_demo.py:34` (`ble_bytes=32`). `laptop/goodput.py:10` imports `PACKET_SIZE` from `common.sensor` to count bytes, so byte counting follows a change in packet length automatically. Only the version 1 check at `:49` needs review. For the Ultra96 side, see `ultra96/protocol.py:67`.
- **Real data cannot use version 1.** The laptop requires version 1 values to equal the dummy-data formula (`laptop/bridge.py:408-409`).
- **Admitting model labels and real confidence.** `ultra96/protocol.py:4` lists only four labels, and `:82-83` requires a confidence of 1.0. The laptop's diagnostic tools share this function, so a change to it applies to them as well. The labels to admit are the ones Wen Ree and Jie Ling agree (hand-off document, section 3.1). Proposed date: Fri 10-16, in all four checks together (hand-off document, sections 6.4 and 8, step 5).
- **The "one input, one result" criteria.** `tools/rehearse_remote_comms.py` requires the acknowledged ID set to equal the result ID set exactly. `tools/rehearse_comms.py` requires the result count to equal the acknowledged count minus the duplicate acknowledgements. `demo.py`'s `Phone expected increase` also counts one result per packet. Once the model produces results per window, these checks must be redefined. How often results are produced is for Wen Ree and Jie Ling to agree (hand-off document, section 3.1).

### Where design records and documents disagree with the code (follow the code)

- The tool names in old records, `rehearse_week7`, `rehearse_remote_week7`, `week7_demo`, `generate_week7_pki` and `Week7Server`, are now `tools/rehearse_comms.py`, `tools/rehearse_remote_comms.py`, `tools/comms_demo.py`, `tools/generate_comms_pki.py` and `CommsServer`.
- `docs/week7-runbook.md:298` says "One writer owns one request/ACK at a time." Two-board mode actually uses a window of 32. That runbook is out of date as a whole.
- [Selected design] item 12 gives the local forward port as 18888. `demo.py` defaults to 18889.
- In archived records (for example [Dual-board spec]), the source statistics magic is `W7S1`, the packet magic is `W7` and the session ID is `week7-demo`. Those were the names at the time. The code now accepts only `LCS1` and `LC`, and the session defaults to `ltc-comms`.
- `docs/communications-quickstart.md` and `docs/co-protocol-v2.md` were rewritten in `7479e2e`. They now accept only `LC` and `LCS1`, no longer read `.week7-local/`, and default the session ID to `ltc-comms` everywhere. They agree with the code.

### History and removed items

On 2026-10-14, compatibility with the old Week 7 version was removed (commits `d2fff21` and `5f2c12a`, merged into local `main` by `4c2b078`). On the laptop side, this removed:

- The old packet magic `W7`. Encoding and decoding now use only `LC` (`common/sensor.py:13`, `:77-78`). The related "command packet magic follows the board" logic was removed too: `ControlChannel.attach` no longer has a `packet_magic` parameter (`laptop/controls.py:75-82`, `laptop/bridge.py:763`).
- The old statistics magic `W7S1`. Only `LCS1` is accepted now (`laptop/source_audit.py:13`, `:50-51`).
- The fallback read of the old folder `.week7-local`. The board map reads only `.comms-local/boards.json` (`tools/demo_boards.py:9`, `21-24`). `demo.py report` looks only in `.comms-local/` (`demo.py:269-275`). `flash.py --boards` no longer mentions the old folder (`flash.py:151-154`).
- The session ID `week7-demo` hard-coded in the start script on the Ultra96. It is now an option with the default `ltc-comms` (`tools/demo_service.py:50`, `54`; `demo.py:70-71`, `292`).

The matching tests were updated at the same time. In the tests, `W7` and `W7S1` now appear only in `tests/test_sensor.py:24` and `tests/test_source_audit.py:25`, which assert that they are rejected.

## How to run and verify

The commands and numbers in this section come from the code and existing records. No script, test or hardware was run while writing this chapter.

### Prerequisites

- Windows, Python 3.10 or later, Bluetooth on.
- The laptop is connected to the NUS VPN.
- Both boards are flashed with the current firmware and each is powered. The Ultra96 ingest service is running. All three parties use the same session ID (`ltc-comms`). As of 2026-10-14 these conditions are not met:
  - The right board still runs Week 7 firmware.
  - The server certificate deployed to the Ultra96 in September expired on 2026-10-06. Only the laptop's copy of it was checked. The repository has no record of a later replacement, and whether the Ultra96's certificate was replaced has not been checked.
  - The service on the Ultra96 is most likely still the September 28 code snapshot with session `week7-demo`. That process was not started by `demo.py service --start`. The untracked `.week7-local/co_deploy.py` started it in the background (`subprocess.Popen` with `start_new_session=True`; output in `BOARD_ROOT/evidence/`, PID in `BOARD_ROOT/evidence/server.pid`). It does not depend on any SSH session and may still be running. Use that PID file to find the old process during the redeploy (see [chapter 4](04-ultra96-service-and-certificates.md)).

  One redeploy round following section 6.3 of the hand-off document is needed before `demo.py run` can pass. The owner's proposed plan does it on Thu 10-15 and a full dry run on Mon 10-19, the day before the in-person integration session (hand-off document, section 6.4).
- You have the public CA certificate file. The laptop needs no private key.
- Every step that logs in to the jump host or the Ultra96 (`demo.py tunnel`, `demo.py service`) is done by olsonwangyj in their own terminal (hand-off document, section 9).

### Field steps

```powershell
python -m pip install -r laptop/requirements.txt
python flash.py --boards                      # show the left and right board addresses
python flash.py --pair left                   # first time only; read the passkey only on the local serial port
python flash.py --pair right
python demo.py service                        # read-only look at the Ultra96 service (see chapter 4)
# Terminal A, keep it open
python demo.py tunnel --jump '<your account>@stujump.comp.nus.edu.sg' --target '<Ultra96 account>@<Ultra96 host name>'
# iPhone: tap Communications Connect, wait for Subscribed, note Received
# Terminal B
python demo.py run  --ca '<CA certificate path>'       # 60 s, 10 Hz
python demo.py live --ca '<CA certificate path>'       # 120 s; press 1 or 2 to send commands
python demo.py report                         # review the latest; a folder or report.json also works
```

The phone must reach `Subscribed` before the capture starts. When there is no subscriber, the service on the Ultra96 discards results and does not resend them later. `Subscribed` means only that the subscription handshake with the Ultra96 succeeded; it does not prove that results are flowing. Only the increase in the phone's `Received` count after the capture shows that results arrived.

### What counts as a pass

- Terminal B exits with code 0.
- The output contains `Exit=0  clean=True  mock_input=False  report_saved=True`.
- In the table, both boards have Generated, Received and ACKed equal, and MissingBLE and MissingACK are both 0.
- `CAPTURE PASSED` appears. It is evidence level 3: it proves that the service on the Ultra96 validated and accepted every input. It does not prove that a model ran or that the phone received anything.
- A final line `Phone expected increase: N` appears. Compare it with the before-and-after difference of the phone's `Received` count. This is level 5 evidence and relies on a manual comparison. `Received` counts every distinct result, even though the display text shows only the latest one and can lose results between polls (hand-off document, section 4.6).

`demo.py`'s pass conditions (`demo.py:143-159`): the child exits 0; the report has `clean` true, is not synthetic input, and was saved; each board has `clean` and `protected_ble` true and `unfinished` false; source statistics `complete` and `clean` are both true; `generated` is a positive integer and equals `source_submitted`, the source-side `received` and `acked`, and the board-level `received`, `sent` and `acked`; `missing_received` and `missing_acked` are both 0. After that, the packet example review must pass: each board has at least one pair of `sensor` and `sensor_ack` records with exactly the same identity, and the decoded `raw_hex` matches the recorded fields (`tools/video_evidence.py`).

### Checks without hardware

```powershell
python -m pip install -r laptop/requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider
python -m tools.comms_demo packet                               # prints a version 1 packet and an example of each frame
python -m tools.generate_comms_pki --output-dir '<new empty folder outside the repository>'   # one-off certificates for local rehearsal only
python -m tools.rehearse_comms --pki-dir '<that folder>' --duration 30 --target 100
```

- Install `laptop/requirements.txt` first. The modules that `laptop/tests/` and `tests/test_ble_connection.py` import do `import bleak` at file top level (`laptop/ble_connection.py:2`, `laptop/mtu_probe.py:11`, `laptop/ble_counter_receiver.py:13`). Without `bleak`, these tests fail at collection. `requirements-dev.txt` does not include `bleak`.
- Do not run `pytest` without paths from the repository root. It collects `fpga/hls/export_conv1d_test.py`, which rewrites a tracked file as soon as it is imported.
- The certificate tool refuses folders inside a Git repository or working tree, and refuses non-empty folders (`tools/generate_comms_pki.py:27-36`).
- `rehearse_comms` starts a local TLS service, runs the single-board path with synthetic data, and receives the results with a subscriber. Pass conditions: the acknowledged count reaches the target; the result count equals the acknowledged count minus the duplicate acknowledgements; there are no duplicate results and no receive errors; all error counts are 0. It does not go through SSH, the real Ultra96 or the phone. Only `--ble` uses a real board (without board selection). It prints one JSON line, and `passed` should be `true`.
- Two-board synthetic check: in another terminal run `python -m ultra96.server --cert '<folder>/server-cert.pem' --key '<folder>/server-key.pem' --ingest-port 18888 --gateway-port 19999`. Then run `python -m laptop.dual_bridge --ca '<folder>/ca-cert.pem' --mock --duration 10 --report '<new file in an existing folder>.json'`.

### What each rehearsal and simulation tool verifies

| Tool | What it verifies | What it does not verify |
|---|---|---|
| `tools/rehearse_comms.py` | The path, frame format, TLS verification, ACK check and result count close the loop locally | SSH, the real Ultra96, the phone |
| `tools/rehearse_remote_comms.py` | Through two existing forward ports (18888 and 19999), it starts sending data only after receiving `SUBSCRIBED`. The acknowledged IDs equal the result IDs one by one. With `--target 0` it requires a count of at least `ceil(duration × 10 × 0.9)`, and no gap in ACKs or results longer than 5 seconds. Only one TLS connection and one subscription (with `--ble`, also only one BLE connection) | Whether the forward ports really reach that Ultra96 (only the operator can declare it, with `--confirmed-remote-topology`); the phone |
| `tools/comms_demo.py sender` | Real BLE from one board. Prints the bytes and JSON of every acknowledged packet. Requires the acknowledged count to reach at least the target (`ceil(duration × 9)` with `--target 0`), only one BLE connection and one TLS connection, and gaps between acknowledgements of no more than 5 seconds | Whether results are delivered |
| `tools/comms_demo.py audit` | Offline check of the IDs in a saved log (at most 200,000 lines and 64 MiB; each line at most 65536 characters) | Any live connection or physical source |
| `laptop/phone_simulator.py` | The result port can be subscribed to and delivers valid results | A real phone; it displaces the phone's subscription |
| `laptop/mtu_probe.py` | 20 bytes and MTU−3 bytes arrive unchanged; MTU−2 bytes do not | The sensor path |
| `laptop/ble_counter_receiver.py` | Continuity and reconnection of counter notifications | The sensor path |
| `tools/video_evidence.py` | Each board in a capture has at least one packet and ACK pair with exactly the same identity | Completeness of the whole capture; the phone |
