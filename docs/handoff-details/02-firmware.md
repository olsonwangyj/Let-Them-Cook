# Detail chapter 2: ESP32 firmware (BLE peripheral)

> This is a detail chapter of [`../communications-handoff.md`](../communications-handoff.md). It was checked against local `main` (commit `25fe4e4`, now `dc582c7` after the history rewrite in hand-off document section 6.2; same files) on 2026-10-14, and updated later that day for the owner's direction, the owner's rules and the schedule in hand-off document sections 3.1, 4.2, 6.4, 8 and 13. On the evening of 2026-10-14 it was updated again for protocol version 3, against the local branch `comms/protocol-v3` (code commits `a34c467`, `57a3fbd`, `a4b907b` and `3b94990`, the last a test fix and the rename of the specification to `co-protocol-v3.md`; not merged into `main`, not pushed; the decisions and their status are in hand-off document section 6.5). The interface shapes and teammate dates there are proposals until the teammates confirm them. The code is the source of truth: where this chapter and the code disagree, trust the code.

## Role and boundaries

- Each glove has one FireBeetle ESP32. The firmware makes the board a BLE peripheral and GATT server. The laptop is the central.
- The firmware does four things. It produces one sample at the configured rate. It packs the sample into a fixed-length, little-endian binary packet (38 bytes, protocol version 3). It hands the packet to the one authenticated laptop through protected BLE notifications. It provides source-side counters and a control channel, which the laptop uses for reconciliation, rate changes and file transfer.
- Upstream boundary: the source of the samples. Today the source is a dummy data table compiled into the firmware (11 `int16` per row, in the version-3 channel order). `main.cpp` has no I2C or ADC code. Siqiang provides the real sensor module, and the Communications firmware calls it. The firmware calls no sensor module yet: this is planned, not built (hand-off document section 7 says the same of every teammate interface). What exists on the Communications side (built 2026-10-14): the 38-byte version-3 packet that carries the 11 values, and the scaling helper `comms_sample.h` that will turn the module's 11 floats into `int16`. The helper is compiled into the board build, but nothing calls it yet. The version-3 layout and its scales are provisional (see "Real glove data packet: version 3"). The interface requirements are in section 7.1 of the hand-off document, and who does what at this hand-over is in its section 3.1; both are the owner's proposal of 2026-10-14, final when Siqiang confirms. Siqiang's module and a log of real samples are asked for by Fri 2026-10-16 (a proposed date until Siqiang confirms it), pushed to the team repo on GitHub under `hardware/`, not sent over Telegram (section 6.4). The firmware-side technical constraints are in "Extension point: connecting the real sensor module" in this chapter.
- Downstream boundary: when `esp_ble_gatts_send_indicate` returns `ESP_OK`, the packet counts as "submitted". This is evidence level 1 (source statistics field `submitted`, hand-off document section 4.7). Submission is not delivery. The laptop proves delivery by reconciliation against the source statistics ([detail chapter 3](03-laptop-relay-and-tools.md)).
- Pairing left and right samples, building model windows, deciding gesture or idle, and producing labels belong neither to the firmware nor to Communications. They are Wen Ree's work on the model side. Label names, how often a label fires, and whether several identical labels in a row mean one action or several are agreed between Wen Ree and Jie Ling; Communications passes every result through unchanged and never merges, splits, filters or reinterprets results (hand-off document sections 3 and 3.1). The two boards do not know about each other.
- The firmware has no network: no Wi-Fi, no SSH, no TLS, and no session ID. The VPN, `stujump`, and the Ultra96's ingest port 8888 and gateway port 9999 have nothing to do with the firmware.
- This chapter also covers the host-side `flash.py`, `tools/check_board.py`, `tools/demo_boards.py`, `tools/generate_dummy_fixtures.py`, `common/dummy_fixtures.json` and their tests.

## Components and files

| File | Responsibility |
|---|---|
| `firmware/esp32/platformio.ini` | Build configuration: platform `espressif32`, board `firebeetle32`, Arduino framework, serial 115200, `CORE_DEBUG_LEVEL=0`, four build environments (the default environment is `firebeetle32`). Comments name the optional flags `COMMS_FIXTURE_SEED`, `COMMS_INITIAL_RATE_HZ` and `COMMS_OUT_OF_RANGE_DROP`. |
| `firmware/esp32/src/main.cpp` | The only source file: BLE initialization, security configuration, GATT and GAP callbacks, main loop, serial command `erase-bonds`. It includes `comms_sample.h`, so the scaling helper is compiled into the board build, but it does not call it yet (`main.cpp:13-15`). |
| `firmware/esp32/include/comms_packet.h` | Version-3 constants (`kPacketVersion` 3, `kPacketHeaderSize` 16, `kChannelCount` 11, `kPacketSize` 38) and byte-by-byte serialization of the 38-byte sensor packet. `serializePacket` takes exactly 11 values (a shorter array does not compile); `serializeFixturePacket` sends a row of the dummy table. Also `writeUint32Le`, which the other headers use. |
| `firmware/esp32/include/comms_sample.h` | New on 2026-10-14. `scaleSample`: 11 physical floats to the 11 `int16` of the packet, with the scale factors `kChannelScale`, rounding half away from zero; NaN and infinity refused; an out-of-range value clamped (default) or the whole sample refused (`COMMS_OUT_OF_RANGE_DROP=1`); counts in `SampleScaleStats`. For the coming sensor module; not called yet. |
| `firmware/esp32/include/comms_fixtures.h` | Generated file: the dummy data table `kDummyFixtures[][11]`. Do not edit it by hand; `tools/generate_dummy_fixtures.py` rewrites it. |
| `firmware/esp32/include/comms_source_stats.h` | Source statistics: sequence allocation, success and failure counts, 24-byte serialization with the marker `LCS3`. |
| `firmware/esp32/include/comms_security.h` | Portable policy functions: authentication-bit check, notification gate, sensor minimum MTU (41, packet size plus 3, `sensorFitsMtu`), control-write gate (`canAcceptControl`). |
| `firmware/esp32/include/comms_gatts_control.h` | Safely parses two kinds of write from the union parameter of the GATTS callback: MTU probe requests and control frames. |
| `firmware/esp32/include/comms_control.h` | Control channel state machine `ControlEngine`: command echo (one version-3 packet in, a 52-byte response out), rate change, file receive, response cache. The control minimum MTU (64, `controlFitsMtu`), the chunk capacity (`controlChunkCapacity`), the file metadata size (`kFileMetadataSize`, 36) and the output buffer floor (`kControlMinOutput`, 52) are also here. |
| `firmware/esp32/test/host_packet.cpp` | Host test: packet serialization, the fixture send path, authentication bits, notification gate, sensor MTU 40 and 41. Prints two hex lines for Python to compare with the golden vectors. |
| `firmware/esp32/test/host_sample.cpp` | Host test (new on 2026-10-14): `scaleSample` scales, rounding, exact limits, clamping or refusal, NaN and infinity, null pointers. Built twice, once per out-of-range policy. |
| `firmware/esp32/test/host_source_stats.cpp` | Host test: sequence numbers and counts, 24-byte layout with `LCS3`, `uint32` wrap, invalid arguments leave the buffer untouched. |
| `firmware/esp32/test/host_events.cpp` | Host test: non-WRITE events are not parsed; a wrong handle is ignored; malformed writes are rejected; a 52-byte command frame is accepted. |
| `firmware/esp32/test/host_control.cpp` | Host test: control gate truth table, table dummy data, full flows for command, rate change and file, frame boundaries, wrong packet magic, version-2 payloads, the 52-byte output floor. |
| `common/dummy_fixtures.json` | Editable dummy data source: 4 rows now (at rest, a chop-like row, a fast-rotation row and an `int16`-boundary row), 11 `int16` per row, already in wire units. |
| `tools/generate_dummy_fixtures.py` | Reads the JSON (validated by `load_fixtures` in `common/sensor.py`) and writes `comms_fixtures.h` with `CHANNEL_COUNT` (11) columns. |
| `flash.py` | Generates the dummy data header, builds the left and right protected environments, flashes one board at a time, derives the Bluetooth address from the factory MAC and saves the left/right mapping. Also has `--ports`, `--boards`, `--pair` and `--monitor`. |
| `tools/check_board.py` | New on 2026-10-14. Checks one flashed board over real BLE against a service started on the laptop: rate, commands, a normal stop and source reconciliation. No SSH, Ultra96 or phone. See "`tools/check_board.py`" below. |
| `tools/demo_boards.py` | Validates, reads and atomically writes the left/right board address mapping `.comms-local/boards.json`, and holds the built-in default addresses `DEFAULT_BOARDS`. `flash.py`, `demo.py` and `tools/check_board.py` use it. |
| `tests/test_firmware_control.py` | Compiles and runs `host_control.cpp` with the local C++ compiler. |
| `tests/test_firmware_events.py` | Compiles and runs `host_events.cpp`. |
| `tests/test_firmware_source_stats.py` | Compiles and runs `host_source_stats.cpp`. |
| `tests/test_firmware_sample.py` | Compiles and runs `host_sample.cpp` twice: as is (clamp policy) and with `-DCOMMS_OUT_OF_RANGE_DROP=1` (drop policy). |
| `tests/test_flash.py` | Tests every mode and failure path of `flash.py` with fake PlatformIO, fake serial ports and fake input. |
| `tests/test_demo_boards.py` | Tests that the flash order is written as a persistent mapping, that the mapping drives `demo.py run` and `--pair`, that an unfinished mapping blocks capture, the factory MAC conversion, and that a failed write keeps the old file. |
| `tests/test_check_board.py` | Tests the pass/fail rules of `tools/check_board.py` (`verdict`) without hardware. |
| `tests/test_sensor.py` (`test_firmware_serializer_and_security_policy_on_host`, lines 145 to 157) | Compiles and runs `host_packet.cpp` and compares its output line by line with the hex in `tests/fixtures/comms-golden.json`. |
| `tests/test_co_contracts.py` (`test_fixture_header_matches_editable_json`, lines 37 to 41) | Checks that `comms_fixtures.h` is exactly what the generator produces from the JSON, and that it declares `kDummyFixtures[][11]`. |

Related files that exist on this machine but are not in Git are listed in the status table under "Cautions and known limitations".

## Data formats and constants

**GATT service and characteristics.** All UUIDs end in `-7a45-4dc4-b678-3f2d5a9c1001` (`main.cpp:41-48`). The service reserves 32 handles when it is created (7 characteristics plus 4 CCCDs, `main.cpp:427-428`). Version 3 did not change the GATT table.

| UUID prefix | Code constant | Properties | Permissions in the protected build | Value | Purpose |
|---|---|---|---|---|---|
| `6e1c0001` | `kServiceUuid` | Primary service | — | — | Put in the advertising packet |
| `6e1c0002` | `kCounterUuid` | Notify + CCCD | Characteristic `READ_ENC_MITM`; CCCD `READ_ENC_MITM` plus `WRITE_ENC_MITM` | 4-byte `uint32` little-endian counter | Diagnostic counter stream |
| `6e1c0003` | `kMtuControlUuid` | Write | `WRITE_ENC_MITM` | Exactly 2 bytes, `uint16` little-endian: the requested probe length | MTU probe request |
| `6e1c0004` | `kMtuProbeUuid` | Notify + CCCD | Same as 0002 | N bytes; byte i equals the low 8 bits of i | MTU probe reply |
| `6e1c0005` | `kSensorUuid` | Notify + CCCD | Same as 0002 | 38-byte version-3 sensor packet | Data stream |
| `6e1c0006` | `kSourceStatsUuid` | Read | `READ_ENC_MITM` | 24-byte source statistics | Reconciliation |
| `6e1c0007` | `kControlUuid` | Write | `WRITE_ENC_MITM` | Control frame of 14 to 194 bytes | Control requests |
| `6e1c0008` | `kResponseUuid` | Notify + CCCD | Same as 0002 | Response of 14, 16, 50 or 52 bytes | Control responses |

- The write characteristics have only `PROPERTY_WRITE` (write with response). Prepared writes and non-zero offsets are not supported.
- The diagnostic build (`COMMS_UNPROTECTED_DIAGNOSTIC=1`) sets none of these permissions.
- Notification gate: the firmware sends a notification only when four conditions all hold: connected, the characteristic is subscribed, authenticated (the diagnostic build does not require authentication), and no bond erase in progress (`main.cpp:98-100`, `comms_security.h:16-19`).

**Advertising and device name.**

| Item | Value |
|---|---|
| Device name | `LTC-COMMS` (the same on both boards; they are told apart by Bluetooth address and by the `device_id` in the packet) |
| Advertising content | Service UUID `6e1c0001-…`; scan response enabled |
| Advertising interval, transmit power | Not set by the firmware; library defaults |
| Simultaneous connections | 1. While a connection exists, a new connection is disconnected immediately |
| Advertising start and stop | Stops when a connection is established; the main loop restarts it after a disconnect; no advertising during a bond erase |

**Security parameters (protected build, `main.cpp:242-256`).**

| Parameter | Value | Meaning |
|---|---|---|
| `ESP_BLE_SM_AUTHEN_REQ_MODE` | `ESP_LE_AUTH_REQ_SC_MITM_BOND` | LE Secure Connections, MITM, bonding |
| `ESP_BLE_SM_IOCAP_MODE` | `ESP_IO_CAP_OUT` | Display only (DisplayOnly); the laptop enters the passkey |
| `ESP_BLE_SM_MAX_KEY_SIZE` | 16 | Key length 16 bytes |
| `ESP_BLE_SM_SET_INIT_KEY`, `ESP_BLE_SM_SET_RSP_KEY` | `ESP_BLE_ENC_KEY_MASK` plus `ESP_BLE_ID_KEY_MASK` | Distribute the encryption key and the identity key |
| `ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH` | Enabled | Pairing below the mode above is not accepted |
| `kRequiredAuthMode` | `0x0d` (`comms_security.h:10`) | Application-level gate: all three bits must be set: SC `0x08`, MITM `0x04` and bond `0x01`. `main.cpp:35-36` uses `static_assert` to confirm that it equals the SDK's `ESP_LE_AUTH_REQ_SC_MITM_BOND` |
| Passkey | 6 decimal digits, generated fresh by the stack for each pairing | Printed only to the local serial port: `PAIR LOCALLY: enter NNNNNN on Windows (do not record)` |

Each parameter is set with its own call to `esp_ble_gap_set_security_param`, and each return value is checked. If any one fails, the firmware prints `ble_security_configuration_failed` and aborts start-up.

**Sensor packet: 38 bytes, little-endian, protocol version 3 (`kPacketSize = 38`, `comms_packet.h:11-15`).** The Python format is `<2sBBIII11h` (`common/sensor.py:20`). Version 3 is the only version the firmware produces and the only one any receiver accepts (the owner's rule; hand-off document sections 4.2 and 8, step 1). The layout is provisional (see "Real glove data packet: version 3").

| Offset | Length | Type | Field | Values |
|---|---|---|---|---|
| 0 | 2 | ASCII | Packet magic | `LC` (`4C 43`) |
| 2 | 1 | `uint8` | Version | Always 3 (`kPacketVersion`). The version byte says nothing about whether the values are dummy rows or real readings |
| 3 | 1 | `uint8` | `device_id` | 1 means left, 2 means right; any other value makes serialization fail |
| 4 | 4 | `uint32` | `boot_id` | Taken once per power-up with `esp_random()` |
| 8 | 4 | `uint32` | `seq` | Starts at 0, increases by 1 for each generated sample, wraps modulo 2^32 |
| 12 | 4 | `uint32` | `uptime_ms` | `millis()` at the start of this main-loop pass; the two boards are not synchronized |
| 16 | 22 | 11 × `int16` | Channels 0 to 10 | −32768 to 32767, in the order below |

| Channel | Offset | Field | Physical value from the sensor module | Wire value = physical value × | Representable range |
|---|---|---|---|---|---|
| 0, 1, 2 | 16, 18, 20 | `ax` `ay` `az` | g, gravity removed | 10000 | ±3.2767 g |
| 3, 4, 5 | 22, 24, 26 | `gx` `gy` `gz` | °/s, bias removed | 100 | ±327.67 °/s |
| 6, 7, 8 | 28, 30, 32 | `yaw` `pitch` `roll` | degrees | 100 | ±327.67° |
| 9, 10 | 34, 36 | `flex1` `flex2` | 0.0 to 1.0 | 10000 | ±3.2767 |

- The factors are `kChannelScale` in `comms_sample.h:22-24` and `SCALES` in `common/sensor.py:18`. The board service divides by `SCALES` to give the model physical floats, so the two lists must stay identical. They are provisional until checked against Siqiang's real sample log.
- Today the 11 values are a whole row `kDummyFixtures[randomWord % kDummyFixtureCount]` (`comms_packet.h:49-55`). The rows are already in wire units, so no scaling is applied, and the row is chosen independently of `seq`.
- `serializePacket` (`comms_packet.h:27-45`) takes a reference to an array of exactly 11 values, so a caller with fewer values does not compile. It returns false for a null output, a capacity below 38, or a device ID other than 1 or 2. Each value is written as the low byte then the high byte of its `uint16` representation.
- The notification payload limit is MTU − 3, so the sensor stream needs an ATT MTU of at least 41 (`sensorFitsMtu`, `comms_security.h:21-22`, which follows `kPacketSize`).
- The golden vectors are in `tests/fixtures/comms-golden.json`, with the binary copies `comms-dummy.bin` and `comms-boundaries.bin`. They are hand-specified 38-byte version-3 packets, never regenerated by the codec under test, and each also carries the matching `SENSOR_BATCH` message (`v` 3, `request_id` null). `comms-dummy.bin` is device 2, `boot_id` `0x78563412`, `seq` 42, `uptime_ms` `0x01020304`, with dummy row 1 as values (`1200, -300, -8500, 4000, -2000, 1500, 1250, -3000, 600, 6000, 5500`): `4c430302123456782a00000004030201b004d4feccdea00f30f8dc05e20448f4580270177c15`. `comms-boundaries.bin` is device 1, `boot_id` and `seq` both `0xffffffff`, `uptime_ms` 0, values `-32768, 32767, -1, 0, 1, 255, 256, -256, 32766, -32767, 4660`: `4c430301ffffffffffffffff000000000080ff7fffff00000100ff00000100fffe7f01803412`. `host_packet.cpp` holds a literal copy of row 1 (`host_packet.cpp:17-19`), so editing `common/dummy_fixtures.json` never moves the golden vector.

**Source statistics record: 24 bytes, little-endian (`kSourceStatsSize = 24`, `comms_source_stats.h:10`).** The Python format is `<4sB3xIIII`.

| Offset | Length | Type | Field | Notes |
|---|---|---|---|---|
| 0 | 4 | ASCII | Statistics magic | `LCS3` (`comms_source_stats.h:43-46`); it was `LCS1` in version 2 |
| 4 | 1 | `uint8` | `device_id` | 1 or 2 |
| 5 | 3 | — | Reserved | Always 0 |
| 8 | 4 | `uint32` | `boot_id` | The same as in the sensor packet |
| 12 | 4 | `uint32` | `next_seq` | The next sequence number to be allocated, which is also the number of samples generated since this power-up |
| 16 | 4 | `uint32` | `submitted` | Number of successful sensor packet submissions |
| 20 | 4 | `uint32` | `failures` | Number of failed sensor packet submissions |

All three counters wrap as `uint32`. Only sensor packets count. Submissions of the counter, the probe and control responses do not count. Apart from the marker, the format did not change with version 3. The marker follows the packet version: `static_assert(kPacketVersion == 3)` (`comms_source_stats.h:11`) stops the build whenever `kPacketVersion` changes, as a reminder to update the `LCS3` marker and the assert together. It does not read the marker itself. A board still running version-2 firmware answers `LCS1`, and the laptop refuses it before subscribing with `invalid source statistics magic; flash this board with the current firmware` (`laptop/source_audit.py:53`).

**Control frame header: 14 bytes, little-endian (`<2sBBBBII`).** Requests are written to 0007. Responses are notified on 0008. One BLE write carries exactly one frame. There is no TCP-style framing.

| Offset | Length | Field | Rule |
|---|---|---|---|
| 0 | 2 | Magic | ASCII `B7` (the team number B07, not Week 7). No response when it is not `B7` |
| 2 | 1 | Control version | Must be 1, otherwise status 6 |
| 3 | 1 | Opcode | The response opcode is the request opcode with the top bit set (plus `0x80`) |
| 4 | 1 | `device_id` | Must equal this board's ID, otherwise status 1 |
| 5 | 1 | Status | Must be 0 in a request, otherwise status 1; for responses see the status code table |
| 6 | 4 | `id` | `uint32`; must not be 0, otherwise status 1; returned unchanged in the response |
| 10 | 4 | `offset` | `uint32`; must be 0 for command, rate change, file begin and file abort |
| 14 | 0 to 180 | Payload | The whole frame is at most 194 bytes, and not more than MTU − 3 |

`ControlEngine::process` (`comms_control.h:65-103`) first returns 0, with no response, for a null input or output, a frame shorter than 14 bytes, an output buffer smaller than `kControlMinOutput` (52 bytes), or a magic other than `B7`. It then checks the control version, then frame length, `device_id`, status and `id`, and finally it dispatches on the opcode.

| Opcode | Name | Request payload | Success response | Rules |
|---|---|---|---|---|
| `1` | Command | 38-byte version-3 sensor packet (the request frame is 52 bytes) | 52 bytes: header plus the transformed packet | The payload must be exactly 38 bytes (`kPacketSize`) and `offset` must be 0. The payload's packet magic must be `LC`, its version 3 (`kPacketVersion`), its `device_id` and `boot_id` this board's current values, and its `seq` must equal `id`; otherwise status 1. A 32-byte version-2 payload therefore gets status 1, whatever its version byte. These checks run before the cache lookup and the transform, so a rejected command changes no state (`comms_control.h:129-133`). If the same `id` is already in the cache: identical content returns the cached response unchanged, with no second transform; different content gives status 5. If `id` is not greater than the highest `id` handled in this connection: status 5. Otherwise the firmware adds 1 to each of the 11 channels (wrapping as `uint16`, so 32767 plus 1 becomes −32768), replaces `uptime_ms` with this pass's `millis()`, stores the result in the cache and returns it (`comms_control.h:127-160`). |
| `2` | Rate change | 2 bytes, `uint16` little-endian, in Hz | 16 bytes: header plus the rate now in effect | The payload must be exactly 2 bytes, `offset` 0, and the value from 1 to 200; otherwise status 1. Takes effect immediately (`comms_control.h:84-92`). |
| `0x10` | File begin | 36 bytes (`kFileMetadataSize`): `uint32` total length plus 32-byte SHA-256 | 14 bytes | The payload must be exactly 36 bytes, `offset` 0, and the total length from 1 to 65536; otherwise status 1. Resent with the same `id`: if length and digest match, the reply is success and the response `offset` is the number of bytes received (also when the file is already complete); if they differ, status 5. Another file not yet complete: status 2. The previous file already complete: it is discarded and the new file starts. Memory allocation fails: status 2 (`comms_control.h:170-189`). |
| `0x11` | File chunk | 1 to 180 bytes | 14 bytes; `offset` is the next expected offset | Payload length outside 1 to 180: status 1. `id` is not the current file, there is no file, or `offset` is greater than the bytes received (a gap): status 3. `offset` plus length exceeds the total length: status 1. `offset` is less than the bytes received (an old chunk resent): status 3 if the chunk crosses the received position, status 5 if its content differs from what was received, accepted if it is identical. `offset` equals the bytes received: the chunk is written (`comms_control.h:190-207`). |
| `0x12` | File end | None | 50 bytes: header plus `kFileMetadataSize` (`uint32` length plus 32-byte digest) | The payload must be empty, otherwise status 1. Wrong `id`, `offset` not equal to the total length, or not all bytes received: status 3. On the first end the firmware computes SHA-256; a mismatch gives status 4. Another end after success returns the same 50 bytes without recomputing (`comms_control.h:208-222`). |
| `0x13` | File abort | None | 14 bytes | `offset` must be 0 and the payload empty, otherwise status 1. A file exists with a different `id`: status 3. Otherwise the file is discarded and success is returned; success is also returned when there is no file (`comms_control.h:96-100`). |
| Other | — | — | 14 bytes, status 6 | — |

| Status code | Enum name | Meaning |
|---|---|---|
| 0 | `ControlOk` | Success |
| 1 | `ControlInvalid` | Invalid field, length or value (including a command payload whose packet magic is not `LC`, whose version is not 3, or whose length is not 38) |
| 2 | `ControlBusy` | Control queue full, another file in transfer, or out of memory |
| 3 | `ControlOrder` | Order error: a gap, an end before all bytes arrived, an `id` mismatch |
| 4 | `ControlIntegrity` | SHA-256 mismatch |
| 5 | `ControlConflict` | Same `id` with different content, or a command `id` not greater than the highest one handled |
| 6 | `ControlUnsupported` | Unsupported control version or opcode; or rejected directly in the callback because the MTU is too small or the frame is longer than MTU − 3 |

**Capacities, timeouts and other constants.**

| Constant | Value | Location |
|---|---|---|
| `kPacketVersion` | 3 | `comms_packet.h:11` |
| `kPacketHeaderSize` | 16 | `comms_packet.h:12` |
| `kChannelCount` | 11 | `comms_packet.h:13` |
| `kPacketSize` | 38 = 16 + 11 × 2, checked by a `static_assert` | `comms_packet.h:14-15` |
| `kChannelScale` | 10000, 10000, 10000, 100, 100, 100, 100, 100, 100, 10000, 10000 (provisional) | `comms_sample.h:22-24` |
| `kControlHeaderSize` | 14 | `comms_control.h:11` |
| `kControlMaxFrame` | 194 | `comms_control.h:12` |
| `kControlMaxChunk` | 180 | `comms_control.h:13` |
| `kControlMaxFile` | 65536 bytes (held in heap memory) | `comms_control.h:14` |
| `kFileIdleTimeoutMs` | 30000 ms: an incomplete file with no activity for longer than this is discarded | `comms_control.h:15`, `60-63` |
| `kFileMetadataSize` | 36: `uint32` total length plus 32-byte SHA-256; the file-begin payload and the file-end response payload | `comms_control.h:16` |
| `kControlMinOutput` | 52 = 14 + max(38, 36): the largest response, a command echo. `process` returns 0 for a smaller output buffer; a `static_assert` keeps it within one 194-byte frame. It was the literal 50 in version 2 | `comms_control.h:17-21` |
| Control channel minimum MTU | 64 | `controlFitsMtu`, `comms_control.h:31` |
| Chunk capacity | `min(MTU − 3 − 14, 180)`; 47 at MTU 64, 180 at MTU 517 | `controlChunkCapacity`, `comms_control.h:32-36` |
| `kControlQueueSize` | 4 frames (from the callback to the main loop), each up to 194 bytes | `main.cpp:76-78` |
| Command response cache | 8 entries, overwritten as a ring; cleared on every connect and every disconnect, together with the highest handled `id` | `comms_control.h:52-59`, `116`, `156-157` |
| Sensor minimum MTU | 41 (`kPacketSize` + 3) | `sensorFitsMtu`, `comms_security.h:22` |
| Local MTU | `ESP_GATT_MAX_MTU_SIZE` (517 in the SDK installed on this machine) | `main.cpp:423` |
| Initial connection MTU | `ESP_GATT_DEF_BLE_MTU_SIZE` (23 in the SDK installed on this machine) | `main.cpp:61`, `137`, `161` |
| MTU probe maximum payload | `ESP_GATT_MAX_MTU_SIZE − 3` | `main.cpp:49` |
| Rate range and default | 1 to 200 Hz; default 10 Hz | `main.cpp:27-29`, `38-39`; `comms_control.h:45` |
| `kReportIntervalMs` | 1000 ms | `main.cpp:37` |
| Serial baud rate | 115200 | `main.cpp:404`, `platformio.ini:8` |
| Serial command buffer | 32 bytes (at most 31 characters) | `main.cpp:373` |
| Dummy data table rows | The generator requires 2 to 64 rows (`common/sensor.py:105`); the firmware requires more than 1 row (`comms_packet.h:52`) | — |
| Dummy data per row | Exactly 11 integers from −32768 to 32767: each row of the JSON is validated as a version-3 `SensorPacket` (`common/sensor.py:46-49`, `107`), so a generated header has 11 values in every row. The firmware build fails if `comms_fixtures.h` declares a column count other than 11 (`static_assert`, `comms_packet.h:16-17`), and a row with more than 11 values is a compile error (too many initialisers). A row with fewer than 11 values in a hand-edited header compiles and is padded with zeros; only `tests/test_co_contracts.py:37-41` (the header must equal `render_header()`) catches it | — |

**Compile switches.**

| Macro | Default | Effect |
|---|---|---|
| `COMMS_DEVICE_ID` | 1 | This board's identity; only 1 or 2 (`static_assert`, `main.cpp:34`). |
| `COMMS_INITIAL_RATE_HZ` | 10 | Rate at power-up, 1 to 200 (`static_assert`, `main.cpp:39`). |
| `COMMS_UNPROTECTED_DIAGNOSTIC` | 0 | Set to 1 for the unprotected diagnostic build. |
| `COMMS_OUT_OF_RANGE_DROP` | 0 | Out-of-range policy of `scaleSample` (`comms_sample.h:11-13`, `17`). 0 clamps a channel value that does not fit `int16` to the limit, counts it and keeps the sample; 1 refuses the whole sample. Provisional until agreed with Wen Ree. No build environment sets it, and nothing calls `scaleSample` yet, so today it does not change what a board sends. |
| `COMMS_FIXTURE_SEED` | Undefined | When defined, the row is chosen from the linear congruential sequence `state = state×1664525 + 1013904223`, using `state >> 8`; the result is reproducible. When undefined, `esp_random()` is used (`main.cpp:86-95`). |
| `CORE_DEBUG_LEVEL` | 0 | Turns off Arduino framework logs (the library prints the passkey at INFO level). |

`COMMS_LEGACY_DUMMY` no longer exists; it was removed with version 3 (see "History and removed items").

| Build environment | Extra flags | Purpose |
|---|---|---|
| `firebeetle32` (`default_envs`) | None | Protected build, ID 1 (because `COMMS_DEVICE_ID` defaults to 1) |
| `firebeetle32-left` | `-DCOMMS_DEVICE_ID=1` | Left board, used by `flash.py` |
| `firebeetle32-right` | `-DCOMMS_DEVICE_ID=2` | Right board, used by `flash.py` |
| `firebeetle32-unprotected-diagnostic` | `-DCOMMS_UNPROTECTED_DIAGNOSTIC=1` | Unprotected comparison, ID 1 |

`platformio run` without `-e` builds the default environment `firebeetle32`. Flashing that build onto a board makes the board ID 1, so the right board must be built and flashed with `-e firebeetle32-right`. On 2026-10-14 both `firebeetle32-left` and `firebeetle32-right` were built from the version-3 source; the right build uses 7.5 % of RAM (39948 bytes) and 85.4 % of flash (1119853 bytes).

**Serial output (each item is one line of text).**

| Line starts with | When it appears |
|---|---|
| `comms_ready device_id= packet_bytes=38 packet_version=3 rate_hz= protected= control_version=1 file_max_bytes=65536` | `setup()` finished successfully. The length and version are printed from `kPacketSize` and `kPacketVersion` (`main.cpp:449-451`) |
| `alive boot_id= sequence= uptime_ms=` | Every 1000 ms |
| `comms_stats protected= authenticated= sensor_submitted= next_seq= mtu= mtu_suppressed= security_suppressed= submission_errors= rate_hz= control_queue_rejected=` | Every 1000 ms |
| `ble_local_mtu_configured mtu= return_code=` | At start-up |
| `ble_security=UNPROTECTED_DIAGNOSTIC not_protected_evidence` | At start-up of the diagnostic build |
| `ble_security_configuration_failed parameter= return_code=` | Setting a security parameter failed |
| `b07_control_state_allocation_failed`, `ble_state_mutex_create_failed` | Start-up failed |
| `ble_connected boot_id= uptime_ms= security=pending` (`security=UNPROTECTED_DIAGNOSTIC` in the diagnostic build) | Connection established |
| `ble_security_request_failed return_code=` | Starting encryption failed |
| `PAIR LOCALLY: enter NNNNNN on Windows (do not record)` | The passkey is shown during a first pairing |
| `ble_security_complete success= auth_mode= approved= current_peer= reason=` | Pairing or encryption finished; `reason=0` on success |
| `ble_mtu_changed conn_id= negotiated_mtu= uptime_ms=` | MTU negotiation finished |
| `ble_disconnected boot_id= counter= uptime_ms=` | Disconnected |
| `ble_advertising_restarted boot_id= counter= uptime_ms=` | Advertising restarted |
| `ble_notify_submitted boot_id= counter= uptime_ms=` | Each 0002 counter notification sent |
| `b07_rate_changed device_id= rate_hz=` | A rate change took effect |
| `b07_control_rejected reason=malformed bytes=` | Malformed control write |
| `mtu_probe_submitted requested_length= negotiated_mtu= allowed_length= boot_id= uptime_ms=` | MTU probe submitted |
| `mtu_probe_rejected reason=malformed request_bytes=`; `reason=pending` or `reason=not_ready` with `requested_length=` (the main loop's `reason=not_ready` line also carries `negotiated_mtu= allowed_length=`); without `reason`, `requested_length= negotiated_mtu= allowed_length=` | MTU probe write malformed, a probe already pending, not ready, or length above MTU − 3 |
| `erase_bonds_requested count=` | Bond erase requested |
| `erase_bonds_complete remaining=0 remove_Windows_bond_then_pair_again` | Bond erase finished |
| `erase_bonds_failed return_code= restart_required=1`, `erase_bonds_failed remaining= failures= restart_required=1` | Bond erase failed; a restart is required |
| `erase_bonds_rejected disconnect_Windows_first_or_wait_for_erasure` | `erase-bonds` received while connected or while an erase is in progress |
| `serial_command_unknown supported=erase-bonds` | Unknown serial command received |

The firmware prints no line about sample scaling yet: `SampleScaleStats` is not used by `main.cpp` (see the extension point below).

**`flash.py` command line (the four options are mutually exclusive; no option means a full flash).**

| Option | Effect |
|---|---|
| (none) | Generate the dummy data header, build the left and right environments, flash one board at a time, save the mapping |
| `--ports` | Only list the current COM ports (port name, description, hardware ID) |
| `--boards` | Show the saved left and right Bluetooth addresses. Without a mapping file, show the built-in default addresses and print `Using built-in defaults; flash.py records new upload order.` (`flash.py:148-154`) |
| `--pair [left or right or both]` | For each selected board in turn, run `python -m laptop.windows_pairing --address <address>`; stop at the first failure; no value means `both` |
| `--monitor COMx` | Run `platformio device monitor --port COMx --baud 115200 --no-reconnect` and show it in this terminal; no log is saved |

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 130 | Cancelled by typing `q` or pressing Ctrl+C |
| The subprocess's exit code (1 if that code is 0) | A generate, build, port-list, MAC-read, flash, pairing or monitor subprocess failed |
| 2 | MAC read timed out (30 seconds); or `OSError`, `ValueError` or `EOFError`, including PlatformIO tools not found, invalid port name, MAC not unique, both boards with the same address, and mapping incomplete. `argparse` also exits with 2 on conflicting options, without doing anything |

Exit codes are handled in `flash.py:166-177`.

Mapping file: `.comms-local/boards.json` (`tools/demo_boards.py:9`). Its content is `{"version": 1, "status": "ready" or "incomplete", "left": address, "right": address}`; with `incomplete`, `right` is `null`. It is written as a temporary file in the same folder followed by `os.replace` (`tools/demo_boards.py:41-58`), so a failed write leaves the old file unchanged. On read (`tools/demo_boards.py:21-38`): if the file does not exist, the built-in `DEFAULT_BOARDS` is returned (`tools/demo_boards.py:10`, the original operator's two boards). `incomplete` raises `Board setup is incomplete; finish python flash.py before pairing or capture.`. A wrong version, status or address format, or identical left and right addresses, raise an error. An address must be a non-zero unicast address.

**`tools/check_board.py` (new on 2026-10-14): `python -m tools.check_board left|right`.** It checks one flashed board after a flash, without SSH, the Ultra96 or the phone.

| Item | Behaviour |
|---|---|
| Which board | Only the named board, by its address from `.comms-local/boards.json` (or the built-in defaults when there is no file) and with the expected `device_id` 1 or 2 (`tools/check_board.py:154-155`). The other board may stay powered. The board needs its Windows bond; pair it first with `python flash.py --pair left` (or `right`) if it has none |
| What it runs | A `CommsServer` on the laptop (system-chosen ports) with a throwaway certificate set, generated into a temporary folder unless `--pki-dir` is given, and the built-in dummy model; a local subscriber with session `ltc-comms`; and one laptop `Bridge` with source audit, ACK window 32, controls enabled and the requested rate (`tools/check_board.py:62-109`, `156-163`) |
| Options | `--rate` (default 50, 1 to 200), `--duration` (default 65 s, 5 to 3600), `--commands` (default 3, 0 to 8), `--pki-dir`, `--report FILE` (also writes the summary JSON) (`tools/check_board.py:145-153`) |
| Sequence | Once the board has confirmed the rate, it waits 2 s, then sends the commands one at a time, 0.5 s apart. At the end of the duration it waits for the command sender and the command queue, then stops the BLE stream normally (notifications off, final source statistics read), so the source statistics can reconcile (`tools/check_board.py:98-125`) |
| Pass rule (`verdict`, `tools/check_board.py:34-59`) | The source statistics are clean and complete; something was acknowledged; generated = received = acknowledged; none of `malformed`, `ack_errors`, `transport_errors`, `ble_errors`, `cleanup_errors`, `queue_dropped`, `stale_dropped`, `gaps`, `duplicates`, `out_of_order` and `identity_mismatches` is non-zero; the rate is confirmed; the ATT MTU is at least 41; the dummy-model results equal the acknowledged samples; every command completed and got its `cmd:` result; the subscriber saw no error |
| Output | The summary JSON, then one line `CHECK PASSED` or `CHECK FAILED`, the board, `generated=`, `received=`, `acked=` and `commands=`, followed by each failed criterion. Exit code 0 when passed, 1 otherwise (`tools/check_board.py:164-178`) |

### Real glove data packet: version 3 (built; layout provisional)

The direction of olsonwangyj, the Communications owner (2026-10-14; proposed to the teammates and final when they confirm): the 11 values are sent as 11 `int16` with fixed scale factors, in a new protocol version, version 3 (hand-off document sections 4.2, 8 step 1 and 13). **This is in the code since the evening of 2026-10-14 (branch `comms/protocol-v3`): built, and verified on the right board (see the status table below).** The layout and the factors are in "Data formats and constants" above. What is still open or worth knowing:

- **The layout is provisional.** It is frozen only after Siqiang and Wen Ree answer whether the glove's IDLE/MOVING state travels in V1 (asked for Thu 2026-10-15): an extra field changes the length, the MTU floor and `on_sample`.
- **Measured so far: one board.** Application-level byte rate: 38 bytes × 50 Hz × 2 boards = 30.4 kbps. One board sending the 38-byte packet at the 50 Hz setting was clean for a 65 s check on 2026-10-14 (2934 samples; status table below). Two boards together with the 38-byte packet, and any setting above 50 Hz with it, have not been measured. The 32-byte version-2 dummy packet was measured clean at 33.8 kbps combined (the 70 Hz setting, which delivered about 66 packets/s per board; hand-off document section 6.1).
- **Only the newest version is supported (the owner's rule, 2026-10-14).** A new version number means no receiver reads the new layout with the old 8-value one. There is no interoperability between versions: each component accepts only version 3, and an upgrade means reflashing both boards, redeploying the Ultra96 service and reinstalling the phone app together. Version 3 therefore replaced versions 1 and 2 everywhere, including the dummy test data (now 11 values per row) and the formula dummy (removed); there is no transition period (hand-off document section 8, step 1). The laptop carries the packet version into the `v` field of `SENSOR_BATCH` (`common/sensor.py:60`), and the Ultra96 service writes `v` 3 into every `GESTURE_RESULT` (`ultra96/server.py:281`, `315`), so the phone's result checks see version 3 too.
- **The scales are checked before they are fixed (the owner's direction, 2026-10-14).** The factors are checked against the log of real samples that Siqiang pushes to the team repo (asked for by Fri 2026-10-16, a proposed date; hand-off document section 6.4) before they are fixed. A change of factors changes `kChannelScale` and `SCALES` together.
- **Values outside the `int16` range (to be agreed with Wen Ree; asked in the message).** The two options are: clamp the value to the `int16` limit, or drop that one sample. The firmware now supports both: `scaleSample` clamps by default, and a build with `-DCOMMS_OUT_OF_RANGE_DROP=1` drops the sample instead (provisional; decision D13 in hand-off document section 6.5). Either way Communications counts it (`SampleScaleStats`) and never drops a connection or a whole gesture. Where those counts are reported (the `comms_stats` serial line, or the source statistics, which would change the 24-byte `LCS3` format) is still open (hand-off document section 13). A clamped value cannot be told apart from a real value at the limit (3.2767 g can be either); if the model needs to know which samples were clamped, a per-sample flag is needed, which changes the packet and `on_sample` again. Neither option guarantees that a gesture is still recognised (hand-off document sections 8 step 1 and 13).
- **The model gets physical floats (the owner's direction, 2026-10-14; final when Wen Ree confirms).** The transport stays `int16`. On the Ultra96, Communications decodes each value and divides it by the same factor (`physical_values`, `common/sensor.py:92-98`; built), so the model receives the 11 values in the agreed physical units; any normalisation is Wen Ree's (hand-off document section 7.2). Restoring cannot recover precision lost when packing: acceleration and flex keep 4 decimal places, angular rate and angles 2.
- Ranges that can be read from the reference sketch `hardware/gloves/29_sept/imu_v7.ino`: the accelerometer is set to ±2 g and the gyroscope to ±250 °/s; the flex value is the 12-bit ADC reading divided by 4095; `getEulerAngles` computes the angles with `atan2f` and `asinf`, so yaw and roll are within ±180° and pitch within ±90°. Acceleration has gravity removed, so one axis can in theory reach about ±3 g, still within ±3.2767 g, with a margin of only about 0.28 g (this is an inference). So in normal use every value is expected to fit, but that is not guaranteed: the final value depends on the module's processing, not only on the sensor's range (for example the sketch subtracts the gyro calibration bias from each reading, `imu_v7.ino:584-594`). Which sketch is authoritative, and the actual range of each value, are settled by Siqiang's answer to hand-off document section 7.1 and by the real sample log.

## Workflows

**A. Build and flash (`python flash.py` with no options, `flash.py:90-122`)**

1. Run `python -m tools.generate_dummy_fixtures`. It rewrites `firmware/esp32/include/comms_fixtures.h` from `common/dummy_fixtures.json`.
2. Build `firebeetle32-left`, then `firebeetle32-right`. Only after both succeed does the script ask for a board to be connected. PlatformIO is taken from `~/.platformio/penv/Scripts/platformio.exe` first, and from `platformio` on PATH if that is missing (`flash.py:16-21`).
3. Prompt to connect the first board. The operator must press Enter and nothing else. Any other input is an error and exits; `q` cancels.
4. Run `platformio device list --serial --json-output` to list the serial ports. A port name must be `COM` plus digits; a duplicate or a bad format is an error. With one port, it is used. With several ports, the operator must type the port name, and it must be in the list.
5. Using PlatformIO's own interpreter and `esptool.py` (`~/.platformio/penv/Scripts/python.exe` and `~/.platformio/packages/tool-esptoolpy/esptool.py`), run `--chip esp32 --port COMx read_mac` with a 30-second limit. The output must contain exactly one factory MAC. The Bluetooth address is the factory MAC with 2 added to its last byte (`flash.py:68-87`).
6. First board: write the mapping as `incomplete` first (only `left`), then flash `firebeetle32-left`. This way, the old mapping can no longer be used for capture before the flash changes the board's identity.
7. Prompt to unplug the left board and connect the second board. Repeat steps 4 and 5. If the address equals the first board's, the script reports an error and exits without flashing. Then flash `firebeetle32-right`.
8. After both boards are flashed, write the complete mapping (`status: ready`), print `Board mapping saved: <path>`, `LEFT=…` and `RIGHT=…`, and finally print `Both uploads succeeded. …`.
9. Failure paths: any subprocess failure stops the script at once and returns that subprocess's exit code. No serial port, an invalid port name, no unique MAC read, a MAC last byte above 253, PlatformIO tools not found, and a MAC read timeout all return 2. A failure before the first board's MAC is read (for example a build failure or a MAC read failure) leaves the existing mapping unchanged. A failure after it is read (including a failed left or right flash) leaves the mapping at `incomplete`; `flash.py --pair` and `demo.py run` are then blocked until a full `python flash.py` run completes.

A single board can also be flashed without `flash.py` (see "Reflash one board" under "How to run and verify"), and checked afterwards with `python -m tools.check_board`.

**B. Power-up (`setup()`, `main.cpp:403-452`)**

1. Open serial at 115200. Set `boot_id = esp_random()` and write it into the source statistics too.
2. Create `ControlEngine(device ID, boot_id, SHA-256 function, initial rate)` with `new (std::nothrow)`, then create the state mutex `connectionStateMutex`.
3. Call `BLEDevice::init("LTC-COMMS")`. Set the security parameters (the diagnostic build only prints `ble_security=UNPROTECTED_DIAGNOSTIC not_protected_evidence`). Register the custom GAP and GATTS callbacks. Set the local MTU to `ESP_GATT_MAX_MTU_SIZE` and print `ble_local_mtu_configured`. A failure to set the MTU does not abort start-up; only the return code is printed.
4. Create the service and the 7 characteristics, start the service, advertise the service UUID with scan response on, set `bleReady`, and print `comms_ready …`.
5. Failure paths: if the `ControlEngine` allocation fails, the mutex cannot be created, or any security parameter fails, `setup()` returns directly. `bleReady` stays false, the main loop only idles, and the board does not advertise.

**C. Connection and authentication**

1. The laptop connects, and `onConnect` runs (`main.cpp:125-151`). If a connection already exists or a bond erase is in progress, the new connection is disconnected at once. Otherwise the firmware records the connection ID and the peer address, sets `authenticated` to false, clears the subscriptions, the control queue, the command cache, the file and any pending MTU probe, resets the MTU to 23, stops advertising and prints `ble_connected …`.
2. Protected build: the firmware itself calls `esp_ble_set_encryption(peer, ESP_BLE_SEC_ENCRYPT_MITM)`. On failure it prints `ble_security_request_failed` and disconnects.
3. A security request from the peer (`onSecurityRequest`) is accepted only when there is a current connection and no bond erase is in progress.
4. First pairing: the stack generates a 6-digit passkey, `onPassKeyNotify` prints it to serial, and the operator enters it on Windows with the input hidden. With an existing bond, the link is encrypted directly and no passkey appears.
5. `onAuthenticationComplete` (`main.cpp:195-208`) sets `authenticated` only when all four hold: the peer address equals the current connection's, the result is success, `auth_mode` contains the three bits of `0x0d`, and no bond erase is in progress. It then prints `ble_security_complete …`. The callback structure contains key material; the firmware does not print it.
6. After MTU negotiation, `onMtuChanged` updates `negotiatedMtu` only for the current connection ID and prints `ble_mtu_changed`.
7. The laptop subscribes by writing each CCCD. While connected, `CccdCallbacks` sets the four subscription flags to each CCCD's current value.
8. Failure paths: if the authentication result belongs to the current peer but does not meet the requirement, the firmware disconnects the peer. If the peer asks the firmware to enter a passkey (`onPassKeyRequest`), the firmware returns the invalid value `UINT32_MAX`, so that pairing fails. Numeric-comparison confirmation (`onConfirmPIN`) is always refused.

**D. Each main-loop pass (`loop()`, `main.cpp:454-558`)**

1. Record `nowMs = millis()`. If `bleReady` is false, only call `delay(1)` and return.
2. Read serial commands.
3. Check whether the bond erase has finished. Restart advertising if needed and print `ble_advertising_restarted`.
4. Take the mutex. It is held from here through step 10 (`main.cpp:482-546`). First discard an incomplete file that has been idle for more than 30 seconds.
5. Send tick check: continue only if `micros()` is at least `1000000 / rate` microseconds after the last send, and set "last send" to the current time (`main.cpp:484-487`).
6. Protected build, connected but not authenticated: increment `security_suppressed`. The notification gate is closed, and no data is sent.
7. 0002 subscribed and gate open: send the 4-byte counter. Only a successful submission increments the counter and prints `ble_notify_submitted`.
8. 0005 subscribed and gate open: if the MTU is below 41, increment `mtu_suppressed` and allocate no sequence number. Otherwise allocate `seq` first, then serialize, then submit, and finally increment `submitted` or `failures` according to the result (`main.cpp:499-510`). The sample is produced at `main.cpp:502-505`: `serializeFixturePacket(…, fixtureRandomWord())` takes the 11 values of one dummy-table row. The real sensor module's "read one sample", followed by `scaleSample`, goes here; a sample that cannot be read or is refused must then take no `seq` (see the extension point below). When 0005 is not subscribed or the gate is closed, no sequence number is allocated.
9. Control queue not empty, 0008 subscribed and gate open: take the frame at the head of the queue and pass it to `ControlEngine::process` with a 194-byte response buffer; if there is a response, notify it. This step is not bound by the sensor send tick, but it handles at most one frame per pass. If the rate changed, reset "last send" to the current time and print `b07_rate_changed` (`main.cpp:514-526`).
10. A pending MTU probe: if 0004 is not subscribed or the gate is closed, print `reason=not_ready`. If the length exceeds MTU − 3 or `ESP_GATT_MAX_MTU_SIZE − 3`, print a rejection. Otherwise send the N-byte probe packet and, on success, print `mtu_probe_submitted`.
11. Release the mutex. If 1000 ms have passed since the last report, print `alive` and `comms_stats`. Finally call `delay(1)`.

**E. Reading source statistics (the laptop reads 0006)**

1. The callback copies `sensorStats` under the mutex, serializes it to 24 bytes and uses that as the read response (`main.cpp:222-234`). The read itself changes no counter.
2. The read permission is `READ_ENC_MITM`. The stack rejects unencrypted reads.
3. The laptop reads once before subscribing to 0005 and once after stopping notifications. It refuses a marker other than `LCS3`, and it reconciles using `next_seq` and `boot_id` from the two reads ([detail chapter 3](03-laptop-relay-and-tools.md)).

**F. Control writes (the laptop writes 0007; handled in the GATTS callback on the Bluetooth task, `main.cpp:270-304`)**

1. Only real WRITE events on the 0007 handle are processed. If the length is outside 14 to 194, `offset` is non-zero, it is a prepared write, or the value is empty: print `b07_control_rejected reason=malformed bytes=…` and send no response.
2. Checks: no bond erase in progress; the write's connection ID equals the current connection; connected; 0008 subscribed; authenticated; MTU at least 64; frame length not above MTU − 3; queue not full. If all hold, the whole frame is copied into the queue.
3. Otherwise increment `control_queue_rejected`. If the write came from the current connection, which is authenticated and has subscribed to 0008, and the frame starts with `B7`, the firmware immediately replies with a 14-byte rejection: status 2 when frame length and MTU are both acceptable (that is, the queue is full), status 6 when they are not. The rejection frame keeps the request's `id` and `offset`. In all other cases (not authenticated, 0008 not subscribed, a write from another connection) there is no response.
4. The stack sends the ATT-level write response. It only says that the write arrived, not that the application accepted it. Application acceptance is shown only by the response on 0008 (comment at `main.cpp:291-292`).

**G. MTU probe writes (the laptop writes 0003, `main.cpp:305-325`)**

1. Only real WRITE events on the 0003 handle are processed. The write must be exactly 2 bytes, with `offset` 0, not a prepared write, and a non-empty value; otherwise print `mtu_probe_rejected reason=malformed request_bytes=…`.
2. If the write comes from the current connection, 0004 is subscribed, the gate is open and no probe is pending, record the requested length; the main loop sends the probe (see D, step 10). Otherwise print `mtu_probe_rejected reason=pending` or `reason=not_ready`.

**H. Disconnect and reconnect**

1. `onDisconnect` (only for the current connection ID, `main.cpp:153-167`) clears authentication, the subscriptions, the control queue, the command cache and the highest handled `id`, and the file. It resets the MTU to 23, marks advertising for restart when no bond erase is in progress, and prints `ble_disconnected`.
2. The next main-loop pass restarts advertising and prints `ble_advertising_restarted`.
3. No samples are produced while disconnected, `seq` does not advance, and there is no offline buffer. `boot_id` does not change; after reconnecting, sequence numbers continue from where they stopped. The rate keeps its pre-disconnect value until a restart or another rate change.
4. Seen downstream, a reconnect can still leave gaps in `seq`. On a BLE disconnect the laptop discards that glove's queued samples (`laptop/bridge.py:908`, `114-120`), and on a TLS reconnect samples already written but not acknowledged count as ambiguous drops and are not resent ([detail chapter 3](03-laptop-relay-and-tools.md)). The disconnected time itself shows only as a jump in `uptime_ms`, because the board makes no samples then (hand-off document section 7.2).

**I. Bond erase (type `erase-bonds` plus Enter on serial, `main.cpp:337-370`, `460-469`)**

1. Connected or already erasing: print `erase_bonds_rejected …` and do nothing.
2. Otherwise enter the erase state: set `authenticated` to false, stop restarting advertising, stop advertising, list the bonds, call `esp_ble_remove_bond_device` for each one, print `erase_bonds_requested count=N`, and wait for the stack's completion callbacks (`gapCallback`).
3. When all completion callbacks have arrived, no bonds remain and there were no failures: leave the erase state, resume advertising and print `erase_bonds_complete remaining=0 remove_Windows_bond_then_pair_again`. When the board has no bonds, this path is taken too.
4. Failure paths: if listing the bonds fails, print `erase_bonds_failed return_code=… restart_required=1`. If a removal fails or bonds remain, print `erase_bonds_failed remaining=… failures=… restart_required=1`. In both cases the erase state is not cleared, authentication and advertising stay off, and the board must be restarted.
5. Serial input is handled line by line: `\r` is ignored; an empty line gets no response; a line longer than 31 characters, or any line other than `erase-bonds`, prints `serial_command_unknown supported=erase-bonds`.

## Why it is designed this way

1. **A fixed length (38 bytes in version 3), written byte by byte in little-endian order.** C++ and Python then get the same result from the same bytes, independent of struct alignment and host byte order. A fixed length plus a version number exposes a format mismatch; for the same reason the 38-byte real-data layout is a new version, 3. `serializePacket` takes an array of exactly 11 values, so a wrong channel count is a compile error rather than an out-of-bounds read (comment at `comms_packet.h:25-26`). Rejected: application-level fragmentation, CRC and compression, because BLE already provides link integrity. Source: `docs/archive/design/week7-selected-design-2026-09-06.md` item 3; `docs/archive/test-evidence/week7-packet-firmware-evidence.md`.
2. **If the MTU is too small, nothing is sent, and this is counted separately (`mtu_suppressed`).** The notification payload limit is MTU − 3, and a truncated packet is meaningless. Rejected: silent truncation, or fragmentation by the firmware itself. Source: selected design item 3.
3. **No offline backlog; no samples are generated while disconnected.** An old gesture sent late would be treated as a new live action. Rejected: buffering on the ESP and sending later. Source: selected design item 4; "Scope and acceptance" in `docs/archive/design/specs/2026-09-17-dual-esp-reception.md` ("No offline history or retransmission protocol").
4. **Allocate the sequence number first, then try to submit.** A sample whose submission fails still uses up a sequence number, so a loss cannot be hidden by reusing the number. Rejected: incrementing the sequence only after a successful submission. That was the old rule in selected design item 4, and the dual-board specification replaced it. Source: dual-board specification "Scope and acceptance". (A sample that the sensor module cannot deliver, or that scaling refuses, is not a loss in transport and will take no number; see reason 21.)
5. **A separate 24-byte source statistics characteristic.** The laptop reads it once before subscribing and once after stopping, and reconciles over the range `[start.next_seq, end.next_seq)`, so the first and last samples can be checked too. A successful submission alone does not prove delivery. Source: dual-board specification "Scope and acceptance".
6. **SC, MITM and bonding; the passkey is shown only on the local serial port; the characteristics and CCCDs all require encryption with MITM; the application also gates on the authentication result.** These are two layers of protection. The attribute permissions block unencrypted access. The application gate blocks a "success" callback after a downgrade. Rejected: Just Works, automatic downgrade and automatic bond deletion. Source: selected design items 13 and 24.
7. **No `setStaticPIN()`.** This Arduino helper overwrites the authentication mode. The firmware calls `esp_ble_gap_set_security_param` for each parameter instead and checks every return value. Source: the comment at `main.cpp:248-249`; the firmware evidence document.
8. **No extra HMAC, HKDF or AES-GCM on top of BLE.** The authenticated BLE link plus the SSH and TLS legs after it already cover the whole path. Another key and nonce protocol that nobody has reviewed would only add burden. Rejected: the application-level encryption scheme in section 10.1 of the architecture draft. Source: selected design item 14; `docs/archive/design/architecture-and-interface-draft-v0.1.md` section 10.1.
9. **`esp_ble_gatts_send_indicate` sends to the current connection only.** `BLECharacteristic::notify()` broadcasts and returns no result, so it cannot support submission counts. `BLEServer::getGattsIf()` is private in Arduino 2.0.17, so the firmware takes the interface number from the `ESP_GATTS_REG_EVT` registration event. Source: the comments at `main.cpp:102-103` and `260-261`; the firmware evidence document.
10. **Write fields are read only for a real WRITE event with a matching handle.** The GATTS callback parameter is a union. The bytes of another event (for example EXEC_WRITE) must not be parsed as a write. The cost: prepared writes and execute writes are not supported. Source: selected design item 20.
11. **Policy logic lives in portable C++11 headers.** Serialization, security policy, event parsing, sample scaling and the control state machine can then be tested on the host without flashing a board. Source: dual-board specification "Interfaces and boundaries".
12. **Left and right identity is a compile-time constant, in two build environments.** The identity travels with the firmware and is not guessed at run time. Source: dual-board specification "Scope and acceptance".
13. **A board's physical identity is the Bluetooth address derived from the factory MAC, not the COM port number.** With one programming cable, two boards connected one after the other can get the same COM number. The firmware uses `static_assert(CONFIG_ESP32_UNIVERSAL_MAC_ADDRESSES == 4)` to guarantee that the "factory base plus 2" conversion holds. Source: the comments at `flash.py:69-71` and `103`; `main.cpp:560-562`. The same rule applies when one board is flashed by hand (decision D1 in hand-off document section 6.5).
14. **The control channel uses two separate protected characteristics and does not touch the sensor stream's sequence numbers.** Commands, rate changes and files are counted separately and do not affect throughput reconciliation. Files only go from the laptop into ESP memory; resuming after power loss is not supported. Source: "Contracts" in `docs/archive/design/plans/2026-09-28-co-features.md`; "Protected BLE controls" and "Files" in `docs/co-protocol-v3.md`.
15. **The callback only copies control frames into a 4-frame queue; the main loop handles one frame per pass.** The sensor send tick runs first, so bulk work cannot delay the timing. Source: the comment at `main.cpp:512-513`. The design records do not name a rejected alternative.
16. **The command cache holds 8 entries; `id` must increase within one connection; an old `id` pushed out of the cache is always rejected.** Resending the same command gets the same response, with no second transform. An old request cannot have a new effect. The firmware prevents repeats only within one connection; preventing repeated game effects across connections is the job of the command record on the Ultra96 (comment at `comms_control.h:53-54`). Source: "Contracts" in the CO features plan; `docs/co-protocol-v3.md`.
17. **The dummy data header is generated from editable JSON.** The laptop's simulated source and the firmware use the same data. Changing the data is a build step and does not change the wire format. Source: "Decisions" in the CO features plan.
18. **The unprotected build is a separate, explicitly named environment.** It is available when a comparison is needed, but the normal build is always protected. The diagnostic build states on serial that it cannot serve as protection evidence. Source: selected design item 13.
19. **`CORE_DEBUG_LEVEL=0`.** The Arduino BLE library prints the passkey at INFO level. With framework logs off, the only interactive output left is the firmware's own line. Source: `platformio.ini:9-11`; the firmware evidence document.
20. **Only version 3; the formula dummy went with versions 1 and 2; the statistics marker follows the version.** The owner's rule is that only the newest version is supported. The formula dummy (old version 1) could be told apart from table data only by its version byte, so it could not survive a single version; reproducible dummy data stays available with `-DCOMMS_FIXTURE_SEED`. The marker `LCS3` makes the laptop refuse a board with version-2 firmware before it subscribes, with a clear message, instead of failing packet by packet. Source: decisions D4 and D7 in hand-off document section 6.5.
21. **Scaling in a portable helper, with the out-of-range policy as a build flag; NaN and infinity always refused; no `seq` for a refused sample.** Either answer from Wen Ree (clamp or drop) becomes a build flag, not a code change. Rounding is done in `double`, where a `float` times an integer factor is exact, so the result does not depend on `float` rounding or the FPU rounding mode (comment at `comms_sample.h:48-49`). A refused sample takes no sequence number, so it never appears downstream as a false gap, only as a longer `uptime_ms` step. Source: decision D13 in hand-off document section 6.5; the comment at `comms_sample.h:31-35`.

## Cautions and known limitations

- **What is sent today is not sensor data.** The 11 values come from `common/dummy_fixtures.json` (4 rows, already in wire units). The row is chosen at random, and the same row may repeat.
- **Editing the JSON does not change a board that is already flashed.** Regenerate the header, build and flash. `flash.py` rewrites the Git-tracked `comms_fixtures.h` every time.
- **A successful submission is not delivery.** `submitted` only means the stack accepted the submission. It is evidence level 1.
- **The two failure counters count different things.** The serial `submission_errors` counts failed submissions on every characteristic (counter, sensor, probe, control response). The source statistics `failures` counts sensor packets only. Use the source statistics for reconciliation.
- **The rate is not reset on disconnect.** `ControlEngine::disconnect()` does not change `rateHz_`. Only a restart or another rate-change command changes it.
- **At high rates the actual packet rate is below the setting.** When the send tick check passes, "last send" is set to the current time, and each pass also has `delay(1)`, so the period is rounded up. A 70 Hz setting measured about 66 packets/s per board, which matches the code (this is an inference). A 50 Hz setting measured about 49.98 packets/s. The highest clean setting measured is 70 Hz (about 66 packets/s delivered), with the 32-byte version-2 dummy packet. With the 38-byte version-3 packet only one board at the 50 Hz setting has been measured (clean, 2026-10-14); higher settings and two boards together have not. 75 Hz failed because the right board had 260 source submissions rejected by the stack, not because of downstream loss. 100 Hz also failed (`docs/archive/test-evidence/co-live-deployment-2026-09-28.md`).
- **The mutex is held over a wide range.** `connectionStateMutex` is held for all of `main.cpp:482-546`, and the BLE callbacks also need it. A slow operation added in this range in future (for example an I2C read) will block the callbacks.
- **A received file stays in memory** until the next file begin, an abort or a disconnect. The firmware does not use the file content; it only checks the digest. After a digest mismatch (status 4), the incomplete file still holds the slot. Abort it, wait 30 seconds or disconnect before starting another file.
- **A changed GATT table needs re-pairing.** After the control characteristics were added on 28 September, a targeted bond recovery was done on the Windows side (deployment record). Version 3 did not change the GATT table, and reflashing the application does not erase the bonds: on 2026-10-14 Windows kept its authenticated bond with the right board through two reflashes.
- **Bond recovery is a manual procedure.** The firmware never deletes bonds automatically and never lowers the protection level.
- **The 0002 counter stream prints one serial line per notification.** Subscribe to it only for diagnosis.
- **The single-board diagnostic tools cannot choose a board.** `laptop.ble_counter_receiver` and `laptop.mtu_probe` scan by service UUID and connect to whichever board they find first. Both boards advertise the same name, so power only one board when using these tools. They also do not set a rate; the board keeps its last rate. `tools.check_board` is different: it connects by the board's address and sets the rate.
- **The platform version is not pinned.** `platformio.ini` says `platform = espressif32`. The verified combination is Espressif32 7.1.0 with Arduino-ESP32 2.0.17 (package version `3.20017.241212`), and this is also what is installed on this machine. In the local SDK, `ESP_GATT_MAX_MTU_SIZE` is 517, `ESP_GATT_DEF_BLE_MTU_SIZE` is 23 and `CONFIG_ESP32_UNIVERSAL_MAC_ADDRESSES` is 4.
- **`flash.py` works only on Windows.** A port name must be `COM` plus digits, and the interpreter path for `esptool` is `.platformio\penv\Scripts\python.exe`.
- **Reading the MAC resets the board.** `esptool read_mac` goes through the ROM. It does not flash and does not read the application's serial output.
- **The board connected first becomes LEFT (ID 1).** If the order is swapped on a reflash, the left and right identities swap, and the mapping is written in the new order. Label the two boards LEFT and RIGHT after flashing. When one board is flashed by hand, its factory MAC decides whether `-e firebeetle32-left` or `-e firebeetle32-right` is used, never the COM number.
- **Without a mapping file, the default addresses hard-coded in the code are used.** `DEFAULT_BOARDS` in `tools/demo_boards.py` holds the original operator's two boards. After changing boards, run `python flash.py` first.
- **The firmware does not report its own version or commit.** `comms_ready` carries only the device ID, packet length, packet version, rate, protection, control version and file limit; a version-3 board prints `packet_bytes=38 packet_version=3`. Without a serial port, tell a version-3 board by its source statistics marker `LCS3`. Older firmware makes the laptop report `invalid source statistics magic; flash this board with the current firmware` (`laptop/source_audit.py:53`). The capture report's `workspace_source_sha256` covers the firmware sources (`firmware/esp32/platformio.ini`, `include/` and `src/`), but it describes the laptop's working copy and does not prove which version is flashed on the board (`laptop/reporting.py:13-37`).
- **No Week 7 names remain in the firmware.** No TLS host name, no `Week7*` symbol and no dated folder appears in the firmware source. The control frame magic `B7` and the serial prefix `b07_` refer to the team number B07. The `W7` packet marker in `host_control.cpp:68` is a negative test that must be rejected.

### Status of the two boards and the local files (2026-10-14, late evening)

Nothing of version 3 has run on the Ultra96, on the phone, or with both boards together. The right board was checked only against a service on the laptop.

| Item | Status |
|---|---|
| Left board | **Version-2 firmware**, flashed early on 2026-10-14 (the build in the attic row below) and verified then: local loopback 100/100 packets; another run of 349 packets with source statistics reconciliation passing, a rate change to 20 Hz confirmed, and all 3 commands round-tripped (hand-off document section 6.1). Not connected on the evening of 2026-10-14. The version-3 laptop refuses it when it reads the source statistics (`LCS1`), reporting `invalid source statistics magic; flash this board with the current firmware`; that board is not subscribed, and start-up times out after 30 seconds (hand-off document section 9.2). **It must be reflashed** with `-e firebeetle32-left` and checked with `python -m tools.check_board left` (see "Reflash one board"; hand-off document section 6.3, step 2). Whether Windows then needs to pair it again is not known (hand-off document section 13). |
| Right board | **Version 3, verified.** Identified by factory MAC `38:18:2b:18:9d:68` (Bluetooth `38:18:2B:18:9D:6A` = RIGHT) on COM3, a CH340 port. At about 22:20 on 2026-10-14 it was flashed with the then-current version-2 firmware (`firebeetle32-right`, local `main` `c42b386`) and checked against a service on the laptop with a script kept with the evidence: 20 Hz for 30 s, 495 generated = 495 received = 495 acknowledged, 3/3 commands; 50 Hz for 65 s, 3019 = 3019 = 3019, ATT MTU 517, connection interval 15 ms, longest receive silence 63 ms, 3/3 commands (evidence `.comms-local/checks/2026-10-14-right-board-v2/`). About half an hour later it was reflashed with the version-3 firmware of branch `comms/protocol-v3` (`firebeetle32-right`; no firmware file changed after that build: neither `a4b907b` nor `3b94990` touched any firmware file). Boot line: `comms_ready device_id=2 packet_bytes=38 packet_version=3 rate_hz=10 protected=1 control_version=1 file_max_bytes=65536`. `python -m tools.check_board right --rate 50 --duration 65 --commands 3`: `CHECK PASSED`; `boot_id` 3866582580; `LCS3` source statistics clean and complete; 2934 generated = 2934 received = 2934 acknowledged (`seq` 0 to 2933); ATT MTU 517; 50 Hz confirmed; connection interval 15 ms; longest receive silence 63 ms; 3/3 commands (38-byte packets in 52-byte control frames) with their 3 `cmd:` results; 2934 samples to the built-in dummy model and 2934 results back; slowest model call 0.387 ms; no errors (evidence `.comms-local/checks/2026-10-14-right-board-v3/`). A short run after the review fix to `check_board` (`--duration 10 --commands 8`, 50 Hz, board not reflashed, same `boot_id`) also passed: 320 = 320 = 320 (`seq` 2934 to 3253), 8/8. Its JSON report went only to the console and was not saved; its numbers are in the `README.txt` of the same evidence folder. Windows kept its authenticated bond through both reflashes; no new pairing was needed. |
| `.comms-local/boards.json` (ignored by Git) | Exists; written 2026-10-14 03:05; `version` is 1 and `status` is `ready`. The left and right addresses are the same as the built-in `DEFAULT_BOARDS` and the old `.week7-local/boards.json`. So there is no need to rerun `python flash.py` for the mapping; `tools.check_board` reads its board address from here. There is no capture folder under `.comms-local/` yet; `.comms-local/checks/` holds the evidence of 2026-10-14: the right-board checks (`2026-10-14-right-board-v2`, `2026-10-14-right-board-v3`) and the WSL test of the deploy tool (`2026-10-14-deploy-wsl`). This holds for the owner's two boards only. Siqiang's gloves are other boards (flashing them is proposed for Sat 10-17 or Sun 10-18, Mon 10-19 morning at the latest, until Siqiang confirms; hand-off document section 6.4): flash them with the full `python flash.py`, which records their addresses and replaces this mapping. The owner's boards can still be captured afterwards by giving both `--left-address` and `--right-address` to `demo.py run` or `live`. Once a glove runs the Communications firmware, Siqiang's own Bluetooth recording script can no longer connect to it (hand-off document section 7.1). |
| `.week7-local/boards.json` | Still present, but the code no longer reads it. |
| `.week7-local/flashed-firmware-2026-09-29/left/firmware.bin`, `right/firmware.bin` | Archive copies of the firmware flashed on 29 September. They used to match the 29 September builds under `firmware/esp32/.pio/`, but those builds were replaced on 2026-10-14 (next row), so these are now the only copies. Keep them; do not delete them (hand-off document section 9.1, item 6). |
| `firmware/esp32/.pio/` (main working copy, ignored by Git) | Version-3 builds of `firebeetle32-left` and `firebeetle32-right`, made on 2026-10-14 at 22:48 from branch `comms/protocol-v3`. Judging by the time, the right one is the build that was uploaded to the right board. The left one has not been flashed. `platformio run` and `python flash.py` rebuild from the current source, so do not flash a `firmware.bin` from here directly. |
| `D:\LetThemCook-attic\2026-10-14\flashed-firmware-left-2026-10-14\` (copied from the build folder of the removed `comms-cleanup` worktree) | Built 2026-10-14 02:51 (version 2). Judging by the time, this is the build used for the flash of the left board that it still runs. The `firmware/` folder it was built from is the same as in local `main` and in the team main after PR #18; after `d2fff21` (now `28db0b3`), the only change under `firmware/` was to the test file `host_control.cpp`. |

### Extension point: connecting the real sensor module (scaling helper built; the call waits for the module)

The division of work is the owner's proposal of 2026-10-14, final when Siqiang confirms it (hand-off document sections 3.1 and 7.1). Siqiang delivers a working sensor module (initialization, read one sample, a description of the data format). olsonwangyj, the Communications owner, calls it from the Communications firmware and is responsible for scaling to `int16`, packing, BLE sending and connection management. Capture algorithms, calibration and sensor problems belong to Siqiang.

The interface requirements (functions, shapes, and what the other side must state) are maintained only in hand-off document section 7.1: initialization `bool gloveBegin()`, an optional periodic update `void gloveUpdate()`, and read one sample `bool gloveRead(float out[11])`. These are suggested shapes; Siqiang chooses the names. None of these functions exists yet, and the firmware calls none of them. What the Communications side already has is the scaling helper `comms_sample.h` (item 8) and the 38-byte packet it feeds. This section records the technical constraints that come from the Communications firmware code itself, and their reasons.

1. **Initialization must return on failure.** Initialization is called in `setup()`. If any step in `setup()` does not return before `advertising->start()` and `bleReady = true` are reached, the board never advertises and the main loop only idles (`main.cpp:403-452`, `456`).
2. **Reading a sample must not block or call `delay()`.** The code that takes the sample today runs while `connectionStateMutex` is held (`main.cpp:482-546`). The BLE callbacks for connect, disconnect, MTU change, authentication complete, CCCD write, source statistics read, control write and MTU probe write all wait for this lock with `portMAX_DELAY`. A slow sample read stalls all of these callbacks.
3. **Time spent per loop pass lowers the actual rate.** The send tick is checked once per pass, the period counts from the start of the pass that sent (`main.cpp:484-487`), and each pass ends with `delay(1)`. So the period rounds up to whole passes: a longer pass (for example a `gloveUpdate()` on every pass) increases the rounding, and a read longer than the interval delays the next packet. With the version-2 firmware, a 70 Hz setting gave about 66 packets/s (2026-09-28). The version-3 firmware has the same loop timing, so the same is expected (an inference), but it has not been measured above 50 Hz.
4. **How often the periodic update is called.** If `gloveUpdate()` is needed, the main loop calls it once per pass. A pass takes about 1 ms plus that pass's work. When `bleReady` is false, the main loop does nothing.
5. **The serial port belongs to the Communications firmware.** The firmware calls `Serial.begin(115200)` itself, the main loop reads serial input to find `erase-bonds`, and the passkey is printed only on serial. So the module must not call `Serial.begin` again, must not read serial input, and must not print per sample.
6. **The radio belongs to the Communications firmware.** The firmware uses `BLEDevice` (BLE). The reference sketch `hardware/gloves/29_sept/imu_v7.ino` sends CSV text over Bluetooth Classic `BluetoothSerial` and has its own `setup()` and `loop()`, so the two cannot be linked together as they are.
7. **Identity and time are filled in by the Communications firmware.** Left and right identity comes from `COMMS_DEVICE_ID`, `seq` from `allocateSampleSequence`, and `uptime_ms` is `millis()` at the start of the pass. The module does not provide these.
8. **Scaling is done in the Communications firmware, by `scaleSample` (`comms_sample.h:36-65`; built and host-tested under both policies, compiled into the board build, not called yet).** It converts the 11 floats into `int16` with the factors in `kChannelScale` (the table under "Sensor packet"), rounding half away from zero in `double` (`comms_sample.h:48-51`). It refuses the whole sample, leaves the output untouched and counts one rejection for a null pointer or for any NaN or infinity, under either policy; the planned module contract also says `out[]` must not contain NaN (hand-off document section 7.1). A value outside `int16` is clamped to the limit and counted per channel (`clamped`) by default; with `-DCOMMS_OUT_OF_RANGE_DROP=1` the whole sample is refused and counted (`rejected`) instead. Which policy V1 uses is still to be agreed with Wen Ree (see the version-3 section). On the Ultra96, Communications divides by the same factors to give the model physical floats (hand-off document section 7.2).
9. **A sample that is not delivered takes no sequence number.** At each send tick the order will be: read one sample, `scaleSample`, and only on success `allocateSampleSequence`, `serializePacket` and submit. A `false` from the read, or a refused sample, sends nothing and takes no `seq`, so it never appears as a gap downstream, only as a longer `uptime_ms` step. A submission that fails after the number was allocated still uses up its number (design reason 4).

**Places the Communications firmware itself must change when the module is connected (planned):**

| Location | Today | Change |
|---|---|---|
| `setup()`, `main.cpp:403-452` | No sensor initialization | Call the module's initialization (suggested `gloveBegin()`) before advertising starts; it must return on failure (item 1) |
| `loop()`, `main.cpp:454-558` | No periodic sensor call | Call the optional periodic update (suggested `gloveUpdate()`) once per pass, if the module needs one (items 3 and 4) |
| `main.cpp:502-505` | `allocateSampleSequence`, then `serializeFixturePacket` with a dummy row | Read one sample (suggested `gloveRead`), `scaleSample`, and only on success `allocateSampleSequence`, `serializePacket` and submit (items 8 and 9) |
| `SampleScaleStats` | Defined in `comms_sample.h`, not used by `main.cpp` | Keep one instance and report `clamped` and `rejected`: on the `comms_stats` serial line, or in the source statistics, which would change the 24-byte `LCS3` format. Decide before the module is connected (hand-off document section 13) |
| `platformio.ini` | Default 10 Hz; no out-of-range flag | For 50 Hz, `-DCOMMS_INITIAL_RATE_HZ=50`, or set the rate at run time (`--rate 50`). Add `-DCOMMS_OUT_OF_RANGE_DROP=1` to the left and right environments only if Wen Ree chooses drop |
| Build sources | `src/main.cpp` and `include/` only | The module is asked for as one `.h` and one `.cpp` file under `hardware/`, which is Siqiang's path and is not edited by Communications. How the firmware build picks the two files up is not decided yet |

Already done for version 3 (2026-10-14 evening, built): the 38-byte packet with 11 channels and version 3 (`comms_packet.h`), the MTU floor 41 (`comms_security.h`), the `comms_ready` line printed from the constants (`main.cpp:449-451`), the 52-byte command and the output floor (`comms_control.h`), the `LCS3` marker (`comms_source_stats.h`), the 11-value dummy rows (`common/dummy_fixtures.json`, `tools/generate_dummy_fixtures.py`, `comms_fixtures.h`), and the 38-byte golden vectors and host tests.

The matching laptop, Ultra96 and phone changes are listed in hand-off document section 8, steps 1 and 5 (done in code on 2026-10-14: the Python built and tested; in `phone/unity/CommsPhoneCore.cs` only the changed part compiled, with the C# 5 compiler, and its 88 contract checks passed, the rest of the file not compiled; the Swift part written, not compiled; none of it deployed to the Ultra96 or the phone). The firmware does not depend directly on any interface of Wen Ree's or Jie Ling's. Its scale factors are shared with the Ultra96 decoder (`SCALES`), which restores physical floats for the model (see the version-3 section).

**Planned dates for the firmware part.** These come from hand-off document section 6.4. Teammate dates are the owner's proposals, as asked in the messages, until the teammates confirm them; the owner's own plan is proposed too. Teammates deliver code by pushing it to the team repo on GitHub, not over Telegram. The team meets in person on Tue 2026-10-20 to integrate.

| Date | Who | What |
|---|---|---|
| Thu 10-15 | Siqiang | Answers to the questions in the message (hand-off document section 7.1); with Wen Ree, whether the glove's IDLE/MOVING state travels in V1, which freezes the version-3 layout |
| Thu 10-15 | olsonwangyj | Flash the right board with the current firmware; start the version-3 38-byte packet in firmware, laptop and Ultra96, with golden vectors and tests. **Done ahead of time on Wed 10-14 evening** (below) |
| Fri 10-16 | Siqiang | The sensor module (`gloveBegin` / `gloveUpdate` / `gloveRead`, suggested names, in one `.h` and one `.cpp` file) and a CSV log of real samples from each glove, pushed to the team repo under `hardware/` |
| Fri 10-16 | olsonwangyj | Build the firmware with the module. The owner's boards have no IMU or flex sensors, so on them check only that it compiles, that `gloveBegin()` returns false without blocking, and that the board still advertises; check the scales against the sample log before fixing them. Real readings are first tested on the gloves (Sat 10-17 or Sun 10-18) |
| Sat 10-17 or Sun 10-18 (Mon 10-19 morning at the latest) | Siqiang | Both gloves, so the owner can flash and test them, and if possible left with the owner until Tuesday for the Monday dry run |
| Sun 10-18 | olsonwangyj | Flash both gloves (full `python flash.py`) and test with Siqiang |
| Mon 10-19 | olsonwangyj | Full dry run from the gloves to the game; keep the evidence and list the problems for Tuesday |
| Tue 10-20 | Siqiang | Both gloves, charged, with USB cables, for the in-person session |

**Progress (2026-10-14, late evening).** Done ahead of time: the right board was flashed (version 2, then version 3) and checked; the version-3 packet is in the firmware, the laptop and the Ultra96 service code, with golden vectors and tests (built; the firmware is on the right board only; the left board still runs version 2, and the Ultra96 service and the phone app are not updated); the scaling helper for the module is ready (built; not called). Still open on the firmware side: flash and check the left board with version 3 (hand-off document section 6.3, step 2), and connect the module once it arrives.

If time runs short, Siqiang's module comes after renewing the certificate and redeploying the Ultra96 service (hand-off document section 6.4). If the module is late, the rest of the chain can still be tested with dummy data, which is already in the version-3 format with 11 values per row (the `common/dummy_fixtures.json` row above).

### History and removed items

- From 2026-10-08 (commit `d227a84`), the firmware's magic values changed from `W7` and `W7S1` to `LC` and `LCS1`. At that time the command payload still accepted `W7`.
- On 2026-10-14, `d2fff21` (now `28db0b3` after the history rewrite in hand-off document section 6.2; same files) removed that compatibility and the fallback read of `.week7-local`. The same day at 03:14, `4c2b078` (now `5db56ad`) merged it into local `main`. The command payload now accepts only `LC` (`comms_control.h:130`), and `host_control.cpp:67-73` asserts that commands with magic `W7`, `WC` or `L7` all get status 1. The board mapping is read and written only at `.comms-local/boards.json` (`tools/demo_boards.py:9`, `21-24`, `55`).
- Until the evening of 2026-10-14 the right board still ran the Week 7 firmware and sent `W7` packets and `W7S1` statistics, which the laptop refused (`invalid source statistics magic; flash this board with the current firmware`). It was flashed with the version-2 firmware at about 22:20 that evening, then with version 3 (status table above).
- **Protocol versions 1 and 2 were removed on the evening of 2026-10-14** (commits `a34c467` and `57a3fbd`; decision D4 in hand-off document section 6.5). Before that, the sensor packet was 32 bytes with 8 `int16` channels (`<2sBBIII8h`); version 2 carried a dummy-table row of 8 values and was the default; version 1 (`COMMS_LEGACY_DUMMY=1`, `serializeDummyPacket`) carried the formula dummy, channel i = `(seq % 2000) − 1000 + 10×i`, which the laptop and the Ultra96 service checked (`laptop/bridge.py:408` and `ultra96/protocol.py:70-71` at `c42b386`), so real data could never use version 1. The other version-2 values were: statistics marker `LCS1`, sensor MTU floor 35, a command payload of 32 bytes with a 46-byte response, and a control output floor written as the literal 50. The golden vectors were 32-byte version-1 packets. Version 3 replaced all of this; reproducible dummy data remains with `-DCOMMS_FIXTURE_SEED=<n>`.
- The 17 old captures recorded with the Week 7 firmware (in `.week7-local/`) contain `W7` packets, and the current `demo.py report` no longer passes them. To review the old evidence, use the team main commit `880abba`. It replaced `ec398b6` when the history was rewritten (hand-off document section 6.2) and has the same files. Captures made with version-2 firmware (32-byte packets, `LCS1`) are likewise refused by the version-3 tools; check them with `c42b386` or the team main `5a004c6`.
- The "Firmware and pairing" section of `docs/week7-runbook.md` is still written the old way: it builds and uploads only the default environment `firebeetle32` (ID 1), hard-codes the original operator's PlatformIO path, and mentions `W7`. The current procedure is `flash.py`, or "Reflash one board" below.

## How to run and verify

Run every command below from the repository root in Windows PowerShell.

**Flashing and pairing**

```powershell
python flash.py --ports            # list COM ports
python flash.py                    # generate the header, build, flash LEFT then RIGHT, save the mapping
python flash.py --boards           # show the saved left and right addresses
python flash.py --monitor COMx     # watch serial in a second terminal (the passkey appears here; no log is saved)
python flash.py --pair left        # first pairing, one board at a time
python flash.py --pair right
python -m tools.check_board left   # check each board alone after flashing
python -m tools.check_board right
```

- Label the two boards LEFT and RIGHT after flashing. When you reflash later to change the dummy data, connect LEFT first and RIGHT second.
- Build without flashing: `platformio run -d firmware/esp32 -e firebeetle32-left` (use `-right` for the right board). If `platformio` is not on PATH, use `~\.platformio\penv\Scripts\platformio.exe`.
- Regenerate only the dummy data header: `python -m tools.generate_dummy_fixtures`.

**Reflash one board (hand-off document sections 4.3 and 6.3, step 2)**

```powershell
python flash.py --ports
& "$HOME\.platformio\penv\Scripts\python.exe" "$HOME\.platformio\packages\tool-esptoolpy\esptool.py" --chip esp32 --port COMx read_mac
platformio run -d firmware/esp32 -e firebeetle32-left -t upload --upload-port COMx    # -e firebeetle32-right for the right board
python -m tools.check_board left                                                      # or right
```

- Plug in only the board you mean to flash. The laptop has one programming cable, so the COM number says nothing about which board is attached: read the factory MAC first (close any serial monitor; reading the MAC resets the board). The Bluetooth address is the MAC with 2 added to its last byte: left `38:18:2b:19:82:ac` → `38:18:2B:19:82:AE`, right `38:18:2b:18:9d:68` → `38:18:2B:18:9D:6A`. Compare it with `python flash.py --boards`, and use `-e firebeetle32-left` only for the left address and `-e firebeetle32-right` only for the right one.
- The upload neither reads the MAC nor changes `.comms-local/boards.json`. The Bluetooth address comes from the factory MAC and does not change on a reflash, so the mapping stays valid as long as it is the same board. A full `python flash.py` run also works: connect the left board first, then the right board.
- After the upload, `python flash.py --monitor COMx` should show `comms_ready device_id=1 packet_bytes=38 packet_version=3 …` (`device_id=2` on the right board). Close the monitor before the check.
- `python -m tools.check_board left` (or `right`) then checks that board alone (see "`tools/check_board.py`" above). It must print `CHECK PASSED`. Defaults: 50 Hz, 65 s, 3 commands; `--report FILE` also writes the summary JSON. Keep the output with the evidence under `.comms-local/checks/`.
- If Windows says the bond needs authentication after the flash, follow "Bond recovery" below, then run `python flash.py --pair left` (or `right`). On 2026-10-14 the right board needed no new pairing after two reflashes.

**What serial should show**

1. Start-up: `comms_ready device_id=1 packet_bytes=38 packet_version=3 rate_hz=10 protected=1 control_version=1 file_max_bytes=65536` (`device_id=2` on the right board).
2. Every second: `alive …` and `comms_stats …`.
3. Successful pairing or reconnect: `ble_security_complete success=1 auth_mode=13 approved=1 current_peer=1 reason=0`.
4. After the laptop starts a capture: `authenticated=1` in `comms_stats`; `sensor_submitted` and `next_seq` grow each second by about the rate; `mtu_suppressed` and `submission_errors` do not grow. The MTU measured in past runs, including the version-3 check of 2026-10-14, is `mtu=517`.

**Bond recovery**

1. Stop every laptop client for this board, and wait for `ble_disconnected` on serial.
2. Type `erase-bonds` plus Enter on serial, and wait for `erase_bonds_complete remaining=0 …`. Neither `erase_bonds_rejected` nor `erase_bonds_failed` counts as done; the latter requires a board restart.
3. In Windows Bluetooth settings, remove only this board.
4. Run `python flash.py --pair left` (or `right`) again in a new process. Pairing repeatedly in the same process after the bonds changed was measured to fail (selected design item 24).

**Host tests (no hardware needed; they need `g++` or `clang++` on PATH, otherwise the C++ tests are skipped)**

```powershell
python -m pytest tests/test_firmware_control.py tests/test_firmware_events.py tests/test_firmware_source_stats.py tests/test_firmware_sample.py tests/test_flash.py tests/test_demo_boards.py tests/test_check_board.py tests/test_sensor.py tests/test_co_contracts.py -q -p no:cacheprovider
```

- On 2026-10-14 (late evening, branch `comms/protocol-v3`, `g++` on PATH) this gave 120 passed, none skipped.
- All tests: `python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider`. Do not run `python -m pytest` without paths from the repository root (`AGENTS.md` rule 4).
- Compiler options: `-std=c++11 -Wall -Wextra -Werror -I firmware/esp32/include`; `tests/test_firmware_sample.py` builds `host_sample.cpp` a second time with `-DCOMMS_OUT_OF_RANGE_DROP=1`.
- There are five host programs. Four of them require their program to print one line: `PASS B07 command, rate, bounded file and validation`, `PASS GATT event/union and malformed-write regression`, `PASS source statistics accounting, serialization, wrap, and validation`, and `PASS sample scaling, rounding, limits and refusals (clamp policy)` (`(drop policy)` for the second build). `host_packet.cpp` prints no PASS line. It prints two hex lines instead, which `tests/test_sensor.py` compares line by line with the golden vectors.

**What the host-side tests cover**

| Test | Coverage |
|---|---|
| `host_packet.cpp` | Version-3 layout constants (38 bytes, 11 channels, version 3); hex of the two golden packets; capacity 37, device 0 and 3, and a null pointer all fail; the fixture send path: for twice the number of rows, `serializeFixturePacket` equals `serializePacket` of the selected row and writes version 3, and capacity 37 fails; `auth_mode` missing SC (`0x05`), missing MITM (`0x09`), missing bond (`0x0c`), and a failed result are each rejected; notification gate truth table; MTU 23, 35 and 40 rejected, 41 and 517 accepted |
| `host_sample.cpp` | The 11 scale factors; ordinary values in every unit; zero and negative zero; exact halves round away from zero (0.125 °/s → 13, −0.125 → −13), and `0.005f`, slightly below 0.005, rounds to 0; exact limits are not clamped (3.2767 g → 32767, −3.2768 g → −32768, ±327.67 and −327.68 → 32767 and −32768); values just over the limits and large finite values (`1e30`, `-FLT_MAX`) are clamped and counted (clamp policy: 6 clamps) or refuse the sample with the output untouched (drop policy: 2 refusals); NaN, +infinity and −infinity at channels 0, 5 and 10 refuse the sample under either policy, with no clamp counted and the output untouched; null pointers are refused and counted; counters accumulate and a later ordinary sample still succeeds |
| `host_source_stats.cpp` | A failed sample takes sequence 0 and a successful sample takes sequence 1; byte-by-byte comparison of the 24 bytes, starting with `LCS3`; all three counters wrap from `UINT32_MAX` to 0; null pointer, capacity 23, and device 0 and 3 return false and leave the buffer unchanged |
| `host_events.cpp` | Non-WRITE events, null parameters and a wrong handle are ignored; an MTU probe write must be exactly 2 bytes (1 and 3 are rejected), and prepared, `offset` 1 and empty value are judged malformed; a 52-byte control write (a command frame) is accepted; control writes of 13 and 195 bytes, `offset` 1, prepared and empty value are judged malformed |
| `host_control.cpp` | Control gate, 6 combinations; table dummy data version 3, different random numbers choose different rows, modulo wrap, capacity 37 fails; commands with packet magic `W7`, `WC` or `L7` get status 1 (lines 67 to 73); a command's plus-1 wrap on all 11 channels and `uptime` replacement in a 52-byte response; a resend gets the same response; same `id` with different content conflicts; wrong boot, wrong device, wrong sequence and packet version 1 or 2 in the payload all get status 1; a 32-byte payload (version byte 2 or 3) and a 39-byte payload get status 1, and these refusals leave the cache intact; after 10 new commands push it out of the cache, an old `id` conflicts; accepted again after a disconnect; rate change 200 accepted, 201, 0 and `offset` 1 rejected; file begin, concurrency, out of order, resend, conflict, early end, abort after a digest mismatch, repeated abort, oversize 65537, cleared on disconnect, 30-second timeout; null pointers, too-short input, an output buffer of 13 or 51 bytes and a non-`B7` magic all return 0 with no response, while 52 bytes is enough; a frame with control version 2 and a frame with opcode `0x7f` get status 6; `id` 0, wrong device, non-zero status and a 181-byte chunk get status 1; MTU 63 and 64, chunk capacity 47 and 180 |
| `tests/test_flash.py` | Both environments are built before the board prompt; two boards on the same COM port one after the other; with several ports the port must be chosen by hand; an invalid choice does not flash; cancel; bad port data; a failed subprocess returns its real exit code 7; `--ports`, `--pair`, `--monitor`, an invalid monitor port, mutually exclusive options, `--help` run from outside the repository |
| `tests/test_demo_boards.py` | The flash order is written as the mapping and drives `demo.py run` and `--pair`; the same board connected twice is rejected before the right flash, and the mapping stays `incomplete` and blocks capture; a failed left or right flash never publishes `ready`; built-in default addresses and configuration validation; a failed write keeps the old file; the factory MAC plus 2 conversion and invalid output; the exact `read_mac` command; `--boards` is read-only; a failed identity read does not flash and keeps the mapping; explicit address arguments to `demo.py` can still override the mapping |
| `tests/test_check_board.py` | A clean summary passes; each failure is named: source statistics not clean, generated different from acknowledged, a gap, an unconfirmed rate, an ATT MTU of 40, a missing model result, a missing command result, an incomplete command, a subscriber error, nothing acknowledged |
| `tests/test_co_contracts.py:37-41` | `comms_fixtures.h` exactly equals the output of `render_header()` and declares `kDummyFixtures[][11]` |

**Verifying the diagnostic characteristics with the laptop tools** (details in [detail chapter 3](03-laptop-relay-and-tools.md)): `python -m laptop.ble_counter_receiver` uses 0002; `python -m laptop.mtu_probe` uses 0003 and 0004. Power only one board when using them.
