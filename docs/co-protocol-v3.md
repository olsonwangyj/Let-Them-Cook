# CO application protocol version 3

This is the specification of the Communications application protocol: the BLE sensor packet, the source statistics, the JSON messages between the laptop, the Ultra96 service and the phone, the result rules, the board-side model interface, the phone's per-result function, the BLE control channel and file transfer. The transport underneath (BLE GATT, SSH, TLS) and the reasons for the design are in `communications-handoff.md` (section 4 for the transport, section 5 for the reasons) and its detail chapters. Where this document and the code disagree, the code wins.

Version 3 was introduced on 2026-10-14 on the local branch `comms/protocol-v3` (code commits `a34c467`, `57a3fbd` and `a4b907b`, then `3b94990`, a test fix and the rename of this file). The branch is not merged into `main`, not pushed and not deployed; its code-only copy for the team repo, the local branch `comms/protocol-v3-team` (commits `348fc10`, `ed2aa1f` and `ab3c7f6`), is not pushed either (hand-off 6.2). This file was `co-protocol-v2.md` until then. `B07-CO-protocol-explained.zh-CN.md` is a Chinese study companion written for version 2 (its banner lists the version-3 differences); this document governs.

## Status (2026-10-14, late evening)

Status words: **verified** means run or measured (the row says where); **built** means compiled and tested on the laptop only; **written, not compiled** means there is no toolchain for it on the laptop (for C#, the only compiler there is C# 5); **provisional** means it waits for a teammate's answer.

| Part | Status |
|---|---|
| Firmware (`firmware/esp32/`) | Built: the left and right environments compile, and the host tests of the portable headers pass. Verified on the right board only: flashed with version 3 and checked with `python -m tools.check_board right` against a service on the laptop (50 Hz, 65 s): `LCS3` statistics clean, 2934 generated = 2934 received = 2934 ACKed, 3 of 3 commands in 52-byte frames with their `cmd:` results, 2934 samples to the dummy model and 2934 results back. Evidence: `.comms-local/checks/2026-10-14-right-board-v3/`. After the review fixes (`a4b907b`, which changed no firmware), a 10 s run of the fixed `check_board` with 8 commands also passed on the right board (320 = 320 = 320, 8/8); its JSON report went only to the console, and its figures are written in the `README.txt` of the same evidence folder. The left board still runs version-2 firmware |
| Laptop (`laptop/`, `demo.py`, `tools/`) | Built. Verified with the right board in that check: the single-board relay (`laptop/bridge.py` with `laptop/controls.py` and `laptop/source_audit.py`) and `tools/check_board.py`. `demo.py run` and `live` and the two-board relay `laptop/dual_bridge.py` have not run on hardware under version 3. `tools/deploy_service.py`: its board-side half was verified on Linux (WSL, 27 of 27 checks); its SSH half has not run |
| Ultra96 service (`ultra96/`) | Built. It ran on the laptop in the right-board check and on Linux (WSL) in the deploy test, which includes a version-3 end-to-end exchange (27 of 27 checks). Not deployed: the Ultra96 was not touched and should still hold the 28 September version-2 snapshot (session `week7-demo`), which may still be running. Its server certificate expired on 2026-10-06 (read from the laptop's copy; the board's copy is unchecked); the renewed pair (valid to 2026-11-13 14:27:35 UTC) is only on the laptop and is installed by step 1 of "Running the updated software" (`--server-cert-dir`) |
| Phone reference receivers (`phone/`) | `phone/receiver.py` built. `phone/unity/CommsPhoneCore.cs`: the changed result-validation part (`GestureResult` and `PhoneProtocol`) compiled with the C# 5 compiler and passed 88 contract checks; the whole file needs C# 6 or later (it uses exception filters), so the rest of it is written, not compiled |
| Swift client (`ios-visualizer/CommsNative`) | Written, not compiled. The installed phone app is the Week 7 build: it uses session `week7-demo`, so it cannot subscribe to a version-3 service started by `tools.deploy_service` (session `ltc-comms`; the board closes the connection on its `SUBSCRIBE`, `ultra96/server.py:355`). It also accepts only version-1 or version-2 results with the dummy labels `REST`, `FIST`, `OPEN`, `POINT` and confidence 1, so a version-3 result would end its session |
| The 11-value layout (no IDLE/MOVING field), the scales, the out-of-range policy, the model function names, the `CommsNextResult` limits | Provisional |

Nothing of version 3 has run on the Ultra96, on the phone, or with both boards together.

## Version 3 is the only version

Every component produces and accepts only version 3 (the owner's rule of 2026-10-14: only the newest version is supported). There is no compatibility mode. An upgrade means reflashing both boards, redeploying the Ultra96 service and reinstalling the phone app together. What version 3 removed is listed under "History" at the end.

Unchanged by version 3: the BLE service and its UUIDs, the BLE security, the `B7` control framing (control version 1), the network framing, the `SUBSCRIBE` and `SUBSCRIBED` envelopes (`v` 1), the session ID and the ports.

## Sensor packet

Each sample is one BLE notification on characteristic `6e1c0005-7a45-4dc4-b678-3f2d5a9c1001`: 38 bytes, little-endian, Python format `<2sBBIII11h`.

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 2 | Marker | ASCII `LC` (`4C 43`), the only marker accepted |
| 2 | 1 | Version | 3, the only value accepted |
| 3 | 1 | `device_id` | 1 = left, 2 = right (fixed at build time) |
| 4 | 4 | `boot_id` | uint32, drawn at random once per power-up |
| 8 | 4 | `seq` | uint32, from 0 at each power-up, +1 per sample. It is allocated before the notification is submitted, so a failed submission leaves a gap |
| 12 | 4 | `uptime_ms` | uint32, this board's `millis()`. The two boards are not synchronised |
| 16 | 22 | `values` | 11 × int16, in the channel order below |

Channels (physical value = int16 / scale):

| Index | Name | Unit delivered by the sensor module | Scale | int16 range in physical units |
|---|---|---|---|---|
| 0, 1, 2 | `ax`, `ay`, `az` | g, gravity removed | 10000 | ±3.2767 g |
| 3, 4, 5 | `gx`, `gy`, `gz` | °/s, bias removed | 100 | ±327.67 °/s |
| 6, 7, 8 | `yaw`, `pitch`, `roll` | degrees | 100 | ±327.67° |
| 9, 10 | `flex1`, `flex2` | 0.0 to 1.0 | 10000 | at most 3.2767 |

The constants are `VERSION`, `CHANNELS`, `SCALES`, `PACKET_SIZE` (38) and `SENSOR_MTU_FLOOR` (41) in `common/sensor.py:14-22`, and `kPacketVersion`, `kChannelCount` and `kPacketSize` in `firmware/esp32/include/comms_packet.h:11-15`. A 38-byte notification needs a negotiated ATT MTU of at least 41 (firmware `sensorFitsMtu`, `comms_security.h:22`; the laptop refuses a smaller MTU before subscribing). The measured MTU is 517. The application-layer rate at 50 Hz is 38 × 8 × 50 = 15.2 kbps per board.

The laptop counts a notification of any other length, marker or version as `malformed` and does not forward it.

**Provisional.** The layout is frozen only after Siqiang and Wen Ree say whether the glove's IDLE/MOVING state travels with each sample (an extra field would change the length, the MTU floor and `on_sample`), and after the scales are checked against Siqiang's real sample log.

Golden vectors: `tests/fixtures/comms-golden.json` with `comms-dummy.bin` and `comms-boundaries.bin`. They are hand-specified, and `firmware/esp32/test/host_packet.cpp` prints the same bytes. The fixture-row vector is device 2, `boot_id` 0x78563412, `seq` 42, `uptime_ms` 0x01020304 and the values `[1200, -300, -8500, 4000, -2000, 1500, 1250, -3000, 600, 6000, 5500]` (0.12 g, −0.03 g, −0.85 g, 40 °/s, −20 °/s, 15 °/s, 12.5°, −30°, 6°, 0.6, 0.55):

```text
4c43 03 02 12345678 2a000000 04030201 b004 d4fe ccde a00f 30f8 dc05 e204 48f4 5802 7017 7c15
```

### Dummy data

Until Siqiang's sensor module is connected, each sample carries one row of `common/dummy_fixtures.json`, chosen at random and independently of `seq` (`serializeFixturePacket`, called at `firmware/esp32/src/main.cpp:504`). The file holds 2 to 64 rows of exactly 11 int16 values; it holds 4 today. After editing it, run `python -m tools.generate_dummy_fixtures` (or `python flash.py`, which runs it every time, `flash.py:91`) and rebuild the firmware. The generator refuses a row that is not exactly 11 int16 values (`load_fixtures`, `common/sensor.py:101-107`). The firmware build refuses only a stale `comms_fixtures.h` whose rows are not 11 wide (`comms_packet.h:16-17`): running `platformio` directly does not regenerate the header and builds the old rows without an error. Python reads the file when its process starts. The firmware uses ESP randomness; build with `-DCOMMS_FIXTURE_SEED=<n>` for a reproducible choice. `--seed` controls the laptop's and the mock source's choice, not the firmware's. `-DCOMMS_INITIAL_RATE_HZ` sets the firmware's starting rate (default 10, valid 1 to 200).

### Scaling on the board

`firmware/esp32/include/comms_sample.h` turns one sample of 11 physical floats into the 11 int16 of the packet (`scaleSample`, lines 36-65). It is built and host-tested but not called yet: `main.cpp` still sends fixture rows. When the sensor module arrives, the send block becomes "read one sample, then `scaleSample`, then `serializePacket`".

- Each value is multiplied by its scale and rounded half away from zero.
- A NaN or infinity refuses the whole sample.
- A value outside int16 is clamped to the limit and counted (`clamped`) by default. Built with `-DCOMMS_OUT_OF_RANGE_DROP=1`, it refuses the whole sample instead (`rejected`). **This policy is provisional** until Wen Ree answers. A clamped value cannot be told apart from a real value at the limit.
- A refused sample is not sent and takes no `seq`, so it shows only as a longer `uptime_ms` step, never as a gap.

## Source statistics

The read characteristic `6e1c0006-7a45-4dc4-b678-3f2d5a9c1001` returns 24 bytes, `<4sB3xIIII`: marker `LCS3`, `device_id`, three zero bytes, `boot_id`, `next_seq`, `submitted` (successful notification submissions) and `failures` (failed submissions). The marker follows the packet version (`comms_source_stats.h:43-46`, `laptop/source_audit.py:15`); the format is otherwise the one version 2 used with `LCS1`.

The audited relays (`demo.py run` and `live`, through `laptop/dual_bridge.py`, and `tools.check_board`) read the statistics once before subscribing and once after stopping, to reconcile "generated on the board = received by the laptop = acknowledged by the Ultra96". They refuse a board that answers another marker (`LCS1` from version-2 firmware, `W7S1` from Week 7 firmware) before subscribing, with `invalid source statistics magic; flash this board with the current firmware`. The audit is off by default (`BridgeConfig.source_audit`, `laptop/bridge.py:48`): the plain `python -m laptop.bridge` does not read the statistics, so it does not refuse a version-2 board but counts its 32-byte packets as `malformed`.

## JSON messages

Each network frame is a 4-byte big-endian length followed by a strict UTF-8 JSON object of 1 to 16384 bytes (`common/wire.py`). Duplicate keys and non-finite numbers are refused. The set of keys must match exactly. There is no error message: on any error the receiving side closes the connection.

| `type` | `v` | Port, direction | Keys (exactly these) |
|---|---|---|---|
| `SENSOR_BATCH` | 3 | 8888, laptop → board | `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `uptime_ms`, `values`, `request_id` |
| `INGEST_ACK` | 3 | 8888, board → laptop | `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `request_id`, `status` |
| `SUBSCRIBE` | 1 | 9999, phone → board | `v`, `type`, `session_id` |
| `SUBSCRIBED` | 1 | 9999, board → phone | `v`, `type`, `session_id` |
| `GESTURE_RESULT` | 3 | 9999, board → phone | `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `request_id`, `result_id`, `gesture`, `confidence` (10 keys) |

The subscription envelopes stay at `v` 1: they never carried the packet version and did not change. Every peer refuses any other version for each type.

An example result from a model:

```json
{"v":3,"type":"GESTURE_RESULT","session_id":"ltc-comms","device_id":1,"boot_id":305419896,"seq":42,"request_id":null,"result_id":"1:305419896:42","gesture":"CHOP","confidence":0.93}
```

Field rules:

- `session_id`: a string of 1 to 128 characters, none below U+0020 and no surrogates. It must equal the configured session, or the connection is closed. It is configuration, not a password.
- `device_id` is 1 or 2. `boot_id`, `seq` and `uptime_ms` are integers from 0 to 4294967295. `values` is a list of exactly 11 integers from −32768 to 32767, in the packet's channel order.
- `request_id` is always present in the three version-3 messages. It is `null` for ordinary samples and for model results. For a command it is an integer from 1 to 4294967295 and equals `seq`.
- `INGEST_ACK` repeats `device_id`, `boot_id`, `seq` and `request_id` of the `SENSOR_BATCH` it answers. `status` is `accepted` or `duplicate`.
- `result_id` is `device_id:boot_id:seq` in decimal, with the prefix `cmd:` when `request_id` is not null. A receiver refuses a result whose `result_id` does not match its own fields. The phone de-duplicates by `result_id` (the latest 4096).

### Label and confidence rules

- `gesture`: a string of 1 to 32 characters, each from `A–Z a–z 0–9 _ -`. Communications does not know the label set; Wen Ree and Jie Ling agree it. The six model classes `PICKUPHOLD`, `PLACEDOWN`, `CHOP`, `WASH`, `THROW` and `FIREEXT` fit.
- `confidence`: a JSON number, not a boolean, finite, from 0 to 1 inclusive. The integers 0 and 1 are allowed. It is passed on unrounded (a numpy float32 0.93 arrives as 0.9300000071525574).

The same rules are implemented identically in four places: `ultra96/protocol.py:31-40` (used by the board's `emit` before a result is sent, and by the laptop's test subscribers such as `laptop/phone_simulator.py`), `phone/receiver.py`, `phone/unity/CommsPhoneCore.cs` and `CommsCore/Protocol.swift`. A result the phone rejects ends the phone session and clears its passwords, so the board refuses an invalid model result before it is sent. In the adversarial review of 2026-10-14, 11,421 result bodies were validated identically by the board's check, the Python receiver and a compiled C# harness. The Swift check is written, not compiled.

### Session ID

The session ID is `ltc-comms` everywhere by default: `demo.py run` and `live`, `demo.py service --start`, `tools.deploy_service`, the Ultra96 service and the phone source. All three network participants must use the same session. For the `demo.py` commands, `--session-id` or `LTC_COMMS_SESSION` changes it; for `tools.deploy_service`, `--session-id`; the phone app has it compiled in. The Ultra96 service started for Week 7 and the app installed for Week 7 use `week7-demo`, so both are replaced when this source is deployed.

## Results: model results and command echoes

For each `SENSOR_BATCH` the Ultra96 service checks the message, de-duplicates it and then writes the `INGEST_ACK` (`ultra96/server.py:262-287`):

- **A new sample** (`request_id` null) goes to the model's `on_sample` before the ACK is written. Results come only from the model, through `emit`.
- **A new command** (`request_id` set) never reaches the model. Its values are transformed dummy rows and its `seq` comes from the command space, so it would corrupt the model's windows. The service itself publishes one command echo: a random label from `REST`, `FIST`, `OPEN`, `POINT`, confidence 1.0, `request_id` = `seq`, `result_id` `cmd:device_id:boot_id:seq`. Echoes come only from the owner's command tests on the laptop.
- **An exact retry** of an identity already accepted gets `status: duplicate` and reaches neither the model nor the phone. The laptop treats a duplicate ACK for a command as an error. A different payload under an identity already seen closes the connection.

Replay protection lives in memory only. For each `(device_id, boot_id)` the service keeps a high-water mark of `seq` that only rises; it also keeps the latest 4096 sample fingerprints across all pairs together (`ultra96/server.py:122` and `:350-351`), so with two gloves streaming at the same rate each has about 2048. A sample at or below its pair's mark that is not among them is refused and the connection closed. Commands use a separate ledger. One process allows at most 128 `(device_id, boot_id)` pairs and 4096 commands, never evicted; after that the service refuses new ones and must be restarted. Replay protection across a restart needs a fresh session ID.

A model result is checked twice. `emit` checks the shape at once (`normalize_result` and `emit`, `ultra96/model.py:84-100` and `:168-187`): the label and confidence rules, `device_id` 1 or 2, `boot_id` and `seq` uint32; a result that fails is counted on the event loop (`model_results_rejected`). On the event loop the service then refuses a result that names a `(device_id, boot_id)` with no accepted sample in this process, or a `seq` above the highest one accepted for it (`model_results_rejected`), and a result whose `result_id` was already emitted among the latest 4096 (`model_results_duplicate`) (`_model_result`, `ultra96/server.py:296-320`). Otherwise it publishes a `GESTURE_RESULT` with `request_id: null`. A `seq` inside a gap (never received, but below the highest accepted) is not detected. **Each result must name a different sample**; usually the newest one in the model's window, from either glove.

**The dummy model.** Without `--model`, the service uses its built-in dummy model (`ultra96/model.py:38-50`): for every accepted sample it emits one result for that same sample, with a random label from `REST`, `FIST`, `OPEN`, `POINT` and confidence 1.0. These labels are not game actions. With the dummy model every accepted input (sample or command) gives one result on the board, so `demo.py`'s `Phone expected increase` and the rehearsal checks hold. They do not hold for a real model, whose result rate waits for Wen Ree's answer.

Delivery to the phone is unchanged from version 2: one subscriber at a time (a newcomer replaces it), a queue of 32 results with the oldest dropped when full, a 2 s limit on waiting on the board, and results dropped at once when no phone is subscribed. Results are not resent.

## Board-side model interface

The interface is in `ultra96/model.py`; the service calls `on_sample` at `ultra96/server.py:277`. Its full contract, counters and failure behaviour are in `handoff-details/04-ultra96-service-and-certificates.md` (section "The model interface"); the hand-off document (7.2) has the proposal to Wen Ree. **The function names are provisional** until Wen Ree confirms that the model runs inside the service process. If Wen Ree picks other names, only `ultra96/model.py` changes. Status: built.

| Function | Provided by | Contract |
|---|---|---|
| `start(emit)` | The model | Called once at service start, before the ports open. A model that cannot be loaded (import error, `start` or `on_sample` missing or `async def`) or whose `start` raises (including `SystemExit`) makes the service print `{"event": "model_failed", …}` and exit nonzero without opening its ports. On success the service prints `{"event": "model_ready", "model": <name>, "seconds": <how long start took>}` |
| `on_sample(device_id, boot_id, seq, uptime_ms, values)` | The model | Called on the service's single event-loop thread for each newly accepted sample, before that sample's ACK is written. `values` is a tuple of 11 floats in physical units (int16 / scale). **Must return immediately**: inference belongs on another thread or in another process. Exceptions, including `SystemExit`, are counted (`model_errors`) and never close a connection; calls longer than 5 ms are counted (`model_slow_calls`), and `model_max_call_ms` keeps the longest |
| `emit(gesture, confidence, device_id, boot_id, seq)` | Communications | May be called from any thread; numpy-style numbers are converted. Returns `True` when the arguments are valid and the service is running, `False` otherwise. The result then goes through the event-loop checks above. After the service stops, it returns `False` (`model_results_late`) |

The service loads the model with `--model MODULE` (a module with plain functions `start` and `on_sample`; `async def` is refused) and `--model-path DIR` (put first on the import path). `demo.py service --start` restarts the newest deployed source with the same `--model` and `--model-path` that `tools.deploy_service` recorded for the process it left running (checked before use, `tools/demo_service.py:27-50` and `:72-78`), and prints `Model: …` before it starts; without a usable record it falls back to the 28 September version-2 snapshot and passes no model. Status: built. The `stopped` line printed at shutdown includes `model_samples`, `model_results`, `model_errors`, `model_slow_calls`, `model_max_call_ms`, `model_results_rejected`, `model_results_duplicate` and `model_results_late`. If the model leaves non-daemon threads running, the stopped service prints `{"event": "exit_with_model_threads", "threads": n}` and exits anyway.

## Per-result function on the phone: `CommsNextResult`

The game takes results one at a time with a fourth C function of the Swift package (`Sources/CommsBridge/DisplayMailbox.swift:27-47` and `:70-74`, queue in `Sources/CommsCore/DisplayState.swift`). **Status: written, not compiled. Its limits are provisional.** The installed Week 7 app does not have it.

```c
int32_t CommsNextResult(char* buffer, int32_t capacity);
```

In C# (only in the iOS build, so inside `#if UNITY_IOS && !UNITY_EDITOR`): `[DllImport("__Internal")] static extern int CommsNextResult(byte[] buffer, int capacity);`

- Queue: every result the client accepts (version 3, the rules above, a `result_id` not among the latest 4096) is appended with its arrival time. At most 32 wait; when the queue is full, the oldest is dropped and counted (`pendingDropped`). A result that has waited 2 s or more since it reached the phone is dropped and counted (`pendingExpired`) the next time the queue is examined, also when only `CommsCopyDisplay` is polled.
- One call first drops expired results, then looks at the oldest one left:
  - none: returns 0 and writes nothing;
  - the buffer is null or smaller than the result's bytes plus a terminating 0: writes nothing, keeps the result queued and returns −(bytes + 1), the capacity needed;
  - otherwise: writes the result as one compact UTF-8 JSON object plus a terminating 0, removes it from the queue and returns the number of bytes (without the 0).
- The object is `{"result_id":"…","gesture":"…","confidence":…,"device_id":…}`, for example `{"result_id":"1:305419896:42","gesture":"CHOP","confidence":0.93,"device_id":1}`. `confidence` is written as Swift prints the received number (`1.0`, not `1`). With labels of at most 32 characters a result is well under 512 bytes.
- A new Connect and a stop (Disconnect, the app becoming inactive, `CommsStop`) empty the queue; a new Connect also resets the counters. An automatic reconnect keeps the queue, and so does a terminal error, which reports only a status (`DisplayState.clear`); the waiting results still expire.
- It never blocks. Call it on the main thread every frame, in a loop while it returns a positive number. Each result that is not dropped is taken out at most once; results lost before the phone never arrive.

## Protected BLE controls

Controls use the same service: the write characteristic `6e1c0007-7a45-4dc4-b678-3f2d5a9c1001` and the response notifications `6e1c0008-7a45-4dc4-b678-3f2d5a9c1001`. Both require authenticated, encrypted BLE permissions, and the firmware checks that the request comes from the current peer.

Every control message begins with the 14-byte little-endian header `<2sBBBBII` (`common/control.py:16`):

| Field | Meaning |
|---|---|
| Magic/version | `B7`, control protocol 1 |
| Opcode | 1 command; 2 rate; 16 begin file; 17 chunk; 18 end; 19 abort |
| Device | 1 or 2 |
| Status | Request 0; response 0 OK, 1 invalid, 2 busy, 3 ordering, 4 integrity, 5 conflict, 6 unsupported |
| ID | Nonzero uint32 request/transfer identity |
| Offset | uint32 file offset; zero for commands/rate/abort |

A response sets bit 7 of the opcode. Controls require a negotiated ATT MTU of at least 64 (`MIN_CONTROL_MTU` in `common/control.py:14`, `controlFitsMtu` in `comms_control.h:31`). Payloads are at most `min(180, MTU - 3 - 14)` bytes: 47 at the floor, 180 from MTU 197. Each BLE write carries exactly one control message; the network framing does not apply here.

The two MTU floors are separate: sensor notifications need 41, controls need 64.

**Commands.** The payload is exactly one 38-byte version-3 sensor packet, so a command frame is 52 bytes and so is its response. The laptop builds it from a random fixture row: marker `LC`, version 3, this board's `device_id`, the board's current `boot_id` (read from the source statistics), `seq` equal to the request ID, and `uptime_ms` 0. Before the command changes any state, the firmware answers "invalid" to a payload of another length, marker, version, device or boot, or with a `seq` that differs from the request ID (`comms_control.h:129-133`). The response carries the same packet with `uptime_ms` replaced by the board's clock and 1 added to each of the 11 values, 32767 wrapping to −32768. The sensor stream keeps its own sequence and accounting. The firmware needs at least 52 bytes of output space for a response (`kControlMinOutput` = 14 + max(38, 36), `comms_control.h:16-20`).

The laptop stores the original and the expected values, verifies the response, and forwards the returned packet over its own TLS connection as a `SENSOR_BATCH` with `request_id` = `seq`; the Ultra96 answers it with one `cmd:` echo (see "Results"). The firmware caches eight command responses per connection and rejects older evicted requests; IDs increase within a connection. A disconnect clears the local control state. The Ultra96's command ledger stops a repeated command identity from causing another result.

One control transaction is active per device. Keyboard keys `1` and `2` submit a random command to the corresponding device without Enter. Each device has a bounded queue of eight waiting commands. Overload or a disconnect rejects explicitly. Accepted commands finish or are recorded as failed; a timeout is not retried automatically. A board ACK is evidence of ingestion and does not prove phone receipt.

**Rate.** Rate commands carry a uint16 in Hz (1 to 200) and return the accepted rate. They change the board's pacing. These are configurable operating points, not measured maximum-speed claims.

On supported Windows versions, rates above 10 Hz also request the operating system's throughput-oriented BLE connection preference for that connection's lifetime. Reports distinguish request acceptance from the observed interval, peripheral latency and supervision timeout. The preference is released during cleanup; unsupported or denied requests remain visible as diagnostics. This trades power and available concurrent connections for throughput, so sustainable performance still requires a measured two-board capture. ATT MTU alone does not establish the connection interval or the link-layer data length.

## Files

The supported direction is laptop to ESP RAM, 1 to 65536 bytes. Begin carries 36 bytes: the uint32 length and the SHA-256 digest. Ordered chunks contain file bytes at the declared offset. Responses carry the next expected offset. Identical already-received bytes may be retried; missing, out-of-order or conflicting chunks are rejected. End succeeds only after the entire file has arrived and the receiver has computed and matched its digest; its response returns the length plus the computed digest (36 bytes, a 50-byte frame).

The client retries an identical chunk up to twice after a timeout. Failure aborts, and a disconnect or 30 seconds of receiver inactivity discards an unfinished file. Restart with a new transfer ID. Resuming after power loss is not supported. Files and commands use separate accounting from sensor goodput.

## Running the updated software

Version 3 must be at every end before the full chain runs: both boards flashed with the current firmware, the Ultra96 service deployed from this source, and a phone app built from the current `CommsNative`. On 2026-10-14 only the right board has it (flashed and checked, see "Status"); the left board still runs version-2 firmware, the installed phone app is the Week 7 build (session `week7-demo`, no version-3 results), and the Ultra96, not touched, should still hold the version-2 snapshot. The hand-off document (6.3) gives the round in full; in short, with its step numbers:

1. Ultra96 service and certificate (the owner's login; the tool needs `paramiko`): `python -m tools.deploy_service --dry-run`, then `python -m tools.deploy_service --server-cert-dir <renewed certificate folder>`. Without `--server-cert-dir` the tool keeps the board's certificate and refuses to deploy if it has expired or expires within an hour (`tools/deploy_service.py:153`). Add `--model MODULE --model-path DIR` to start a model instead of the dummy one. Its board-side half was verified on Linux (WSL); its SSH half has not run.
2. Left board (the right board already runs version 3 and needs nothing): after confirming it by its factory MAC, `platformio run -d firmware/esp32 -e firebeetle32-left -t upload --upload-port COMx`, or `python flash.py` with both boards (left first). Then `python -m tools.check_board left`: 65 s at 50 Hz with 3 commands, against a service on the laptop with throwaway certificates and the dummy model; it prints `CHECK PASSED` only when everything reconciles. No SSH, Ultra96 or phone is involved.
3. Swift package, on a Mac: `swift test --package-path ios-visualizer/CommsNative` first, because the Swift changes have not been compiled.
4. Phone app, on the Mac with Xcode: build it with the current `CommsNative` and install it.
5. Acceptance: `python demo.py tunnel` and `python demo.py run`, as below.

For step 5, run from the repository, with `python demo.py tunnel` open in another terminal and the phone subscribed. For a teammate machine, add `--ca` with the verified public CA as shown in the [communications quickstart](communications-quickstart.md); these short forms use the original operator's CA path and the `ltc-comms` session default:

```powershell
python demo.py run --duration 90 --keyboard
python demo.py run --duration 90 --rate 50
python demo.py run --duration 90 --file path\to\sample.bin --file-device 2
```

Both device connections continue during command and file work. A board that still runs version-2 firmware is refused at start-up (see "Source statistics"). Repository changes alone do not upgrade installed firmware, the running Ultra96 service or the installed phone app.

`Phone expected increase` assumes one result per accepted sample or command. It holds only while the Ultra96 runs the built-in dummy model, and the run prints a line saying so.

Reports include per-device and combined decimal kbps. The boundary is unique valid 38-byte sensor packets received at the laptop, including application headers and excluding BLE/TLS/SSH overhead, commands and files. Monotonic observation time includes zero-traffic periods and excludes startup and draining. Console sampling is independent of accounting. Captures keep the plain `live.log`, the structured `packets.jsonl`, the decoded `packets.log`, the configuration, `report.json` and the exit status; evidence overflow is reported explicitly. Captures recorded before version 3 are refused by `demo.py report` and `tools/video_evidence.py`; check them with the code of `c42b386` or the team main `5a004c6`.

## History: what version 3 replaced

Version 2 was current until 2026-10-14 and is described in `docs/co-protocol-v2.md` at commit `c42b386`. Version 3 removed:

- The 32-byte sensor packet (`<2sBBIII8h`, the same 16-byte header with eight int16 values) and its version bytes 1 and 2. The sensor MTU floor was 35, a command frame 46 bytes, and the firmware's control output floor 50 bytes.
- Version 1, the deterministic-formula dummy: values computed from `seq` (`dummy_values(seq)` in Python, `dummyValue` and `serializeDummyPacket` in the firmware, selected with `COMMS_LEGACY_DUMMY=1`), the receivers' formula checks, and a result label fixed by `seq % 4`. Reproducible dummy data now comes only from `-DCOMMS_FIXTURE_SEED` and `--seed`.
- The source-statistics marker `LCS1`.
- `SENSOR_BATCH`, `INGEST_ACK` and `GESTURE_RESULT` at `v` 1 (without `request_id`) and `v` 2 (with it); updated receivers had accepted both result versions.
- The fixed result vocabulary: every receiver accepted only `REST`, `FIST`, `OPEN`, `POINT` with confidence 1.0, and every accepted input got one dummy result directly from the service. There was no model interface.
- The server's capacity parameters `max_v2_namespaces` and `max_v2_commands`, now `max_namespaces` and `max_commands` with the same limits (128 and 4096).

Earlier on 2026-10-14 the cleanup merged as PR #18 had already removed the Week 7 markers `W7` and `W7S1`.
