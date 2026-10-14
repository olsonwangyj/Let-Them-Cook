# Detail chapter 2: ESP32 firmware (BLE peripheral)

> This is a detail chapter of [`../communications-handoff.md`](../communications-handoff.md). It was checked against local `main` (commit `25fe4e4`, now `dc582c7` after the history rewrite in hand-off document section 6.2; same files) on 2026-10-14, and updated later that day for the owner's direction, the owner's rules and the schedule in hand-off document sections 3.1, 4.2, 6.4, 8 and 13. The interface shapes and teammate dates there are proposals until the teammates confirm them. No code under the paths this chapter covers changed in between. The code is the source of truth: where this chapter and the code disagree, trust the code.

## Role and boundaries

- Each glove has one FireBeetle ESP32. The firmware makes the board a BLE peripheral and GATT server. The laptop is the central.
- The firmware does four things. It produces one sample at the configured rate. It packs the sample into a fixed-length, little-endian binary packet. It hands the packet to the one authenticated laptop through protected BLE notifications. It provides source-side counters and a control channel, which the laptop uses for reconciliation, rate changes and file transfer.
- Upstream boundary: the source of the samples. Today the source is a dummy data table compiled into the firmware (8 `int16` per row). `main.cpp` has no I2C or ADC code. Siqiang provides the real sensor module, and the Communications firmware calls it. This is planned, not built: the firmware calls no sensor module yet, and the 38-byte real-data packet does not exist either (hand-off document section 7 says the same of every teammate interface). The interface requirements are in section 7.1 of the hand-off document, and who does what at this hand-over is in its section 3.1; both are the owner's proposal of 2026-10-14, final when Siqiang confirms. Siqiang's module and a log of real samples are asked for by Fri 2026-10-16 (a proposed date until Siqiang confirms it), pushed to the team repo on GitHub under `hardware/`, not sent over Telegram (section 6.4). The firmware-side technical constraints are in "Extension point: connecting the real sensor module" in this chapter.
- Downstream boundary: when `esp_ble_gatts_send_indicate` returns `ESP_OK`, the packet counts as "submitted". This is evidence level 1 (source statistics field `submitted`, hand-off document section 4.7). Submission is not delivery. The laptop proves delivery by reconciliation against the source statistics ([detail chapter 3](03-laptop-relay-and-tools.md)).
- Pairing left and right samples, building model windows, deciding gesture or idle, and producing labels belong neither to the firmware nor to Communications. They are Wen Ree's work on the model side. Label names, how often a label fires, and whether several identical labels in a row mean one action or several are agreed between Wen Ree and Jie Ling; Communications passes every result through unchanged and never merges, splits, filters or reinterprets results (hand-off document sections 3 and 3.1). The two boards do not know about each other.
- The firmware has no network: no Wi-Fi, no SSH, no TLS, and no session ID. The VPN, `stujump`, and the Ultra96's ingest port 8888 and gateway port 9999 have nothing to do with the firmware.
- This chapter also covers the host-side `flash.py`, `tools/demo_boards.py`, `tools/generate_dummy_fixtures.py`, `common/dummy_fixtures.json` and their tests.

## Components and files

| File | Responsibility |
|---|---|
| `firmware/esp32/platformio.ini` | Build configuration: platform `espressif32`, board `firebeetle32`, Arduino framework, serial 115200, `CORE_DEBUG_LEVEL=0`, four build environments (the default environment is `firebeetle32`). |
| `firmware/esp32/src/main.cpp` | The only source file: BLE initialization, security configuration, GATT and GAP callbacks, main loop, serial command `erase-bonds`. |
| `firmware/esp32/include/comms_packet.h` | Byte-by-byte serialization of the 32-byte sensor packet; version 1 formula dummy data; version 2 table dummy data. |
| `firmware/esp32/include/comms_fixtures.h` | Generated file: the dummy data table `kDummyFixtures[][8]`. Do not edit it by hand; `tools/generate_dummy_fixtures.py` rewrites it. |
| `firmware/esp32/include/comms_source_stats.h` | Source statistics: sequence allocation, success and failure counts, 24-byte serialization. |
| `firmware/esp32/include/comms_security.h` | Portable policy functions: authentication-bit check, notification gate, sensor minimum MTU (35, `sensorFitsMtu`), control-write gate (`canAcceptControl`). |
| `firmware/esp32/include/comms_gatts_control.h` | Safely parses two kinds of write from the union parameter of the GATTS callback: MTU probe requests and control frames. |
| `firmware/esp32/include/comms_control.h` | Control channel state machine `ControlEngine`: command echo, rate change, file receive, response cache. The control minimum MTU (64, `controlFitsMtu`) and the chunk capacity (`controlChunkCapacity`) are also here. |
| `firmware/esp32/test/host_packet.cpp` | Host test: packet serialization, formula dummy data, authentication bits, notification gate, MTU 34 and 35. Prints two hex lines for Python to compare with the golden vectors. |
| `firmware/esp32/test/host_source_stats.cpp` | Host test: sequence numbers and counts, 24-byte layout, `uint32` wrap, invalid arguments leave the buffer untouched. |
| `firmware/esp32/test/host_events.cpp` | Host test: non-WRITE events are not parsed; a wrong handle is ignored; malformed writes are rejected. |
| `firmware/esp32/test/host_control.cpp` | Host test: control gate truth table, table dummy data, full flows for command, rate change and file, frame boundaries, wrong packet magic. |
| `common/dummy_fixtures.json` | Editable dummy data source: 4 rows now, 8 `int16` per row. |
| `tools/generate_dummy_fixtures.py` | Reads the JSON (validated by `load_fixtures` in `common/sensor.py`) and writes `comms_fixtures.h`. |
| `flash.py` | Generates the dummy data header, builds the left and right protected environments, flashes one board at a time, derives the Bluetooth address from the factory MAC and saves the left/right mapping. Also has `--ports`, `--boards`, `--pair` and `--monitor`. |
| `tools/demo_boards.py` | Validates, reads and atomically writes the left/right board address mapping `.comms-local/boards.json`, and holds the built-in default addresses `DEFAULT_BOARDS`. Both `flash.py` and `demo.py` use it. |
| `tests/test_firmware_control.py` | Compiles and runs `host_control.cpp` with the local C++ compiler. |
| `tests/test_firmware_events.py` | Compiles and runs `host_events.cpp`. |
| `tests/test_firmware_source_stats.py` | Compiles and runs `host_source_stats.cpp`. |
| `tests/test_flash.py` | Tests every mode and failure path of `flash.py` with fake PlatformIO, fake serial ports and fake input. |
| `tests/test_demo_boards.py` | Tests that the flash order is written as a persistent mapping, that the mapping drives `demo.py run` and `--pair`, that an unfinished mapping blocks capture, the factory MAC conversion, and that a failed write keeps the old file. |
| `tests/test_sensor.py` (`test_firmware_serializer_and_security_policy_on_host`, lines 125 to 137) | Compiles and runs `host_packet.cpp` and compares its output line by line with the hex in `tests/fixtures/comms-golden.json`. |
| `tests/test_co_contracts.py` (`test_fixture_header_matches_editable_json`, line 32) | Checks that `comms_fixtures.h` is exactly what the generator produces from the JSON. |

Related files that exist on this machine but are not in Git are listed in the status table under "Cautions and known limitations".

## Data formats and constants

**GATT service and characteristics.** All UUIDs end in `-7a45-4dc4-b678-3f2d5a9c1001` (`main.cpp:42-49`). The service reserves 32 handles when it is created (7 characteristics plus 4 CCCDs, `main.cpp:428-429`).

| UUID prefix | Code constant | Properties | Permissions in the protected build | Value | Purpose |
|---|---|---|---|---|---|
| `6e1c0001` | `kServiceUuid` | Primary service | — | — | Put in the advertising packet |
| `6e1c0002` | `kCounterUuid` | Notify + CCCD | Characteristic `READ_ENC_MITM`; CCCD `READ_ENC_MITM` plus `WRITE_ENC_MITM` | 4-byte `uint32` little-endian counter | Diagnostic counter stream |
| `6e1c0003` | `kMtuControlUuid` | Write | `WRITE_ENC_MITM` | Exactly 2 bytes, `uint16` little-endian: the requested probe length | MTU probe request |
| `6e1c0004` | `kMtuProbeUuid` | Notify + CCCD | Same as 0002 | N bytes; byte i equals the low 8 bits of i | MTU probe reply |
| `6e1c0005` | `kSensorUuid` | Notify + CCCD | Same as 0002 | 32-byte sensor packet | Data stream |
| `6e1c0006` | `kSourceStatsUuid` | Read | `READ_ENC_MITM` | 24-byte source statistics | Reconciliation |
| `6e1c0007` | `kControlUuid` | Write | `WRITE_ENC_MITM` | Control frame of 14 to 194 bytes | Control requests |
| `6e1c0008` | `kResponseUuid` | Notify + CCCD | Same as 0002 | Response of 14, 16, 46 or 50 bytes | Control responses |

- The write characteristics have only `PROPERTY_WRITE` (write with response). Prepared writes and non-zero offsets are not supported.
- The diagnostic build (`COMMS_UNPROTECTED_DIAGNOSTIC=1`) sets none of these permissions.
- Notification gate: the firmware sends a notification only when four conditions all hold: connected, the characteristic is subscribed, authenticated (the diagnostic build does not require authentication), and no bond erase in progress (`main.cpp:99-101`, `comms_security.h:14-17`).

**Advertising and device name.**

| Item | Value |
|---|---|
| Device name | `LTC-COMMS` (the same on both boards; they are told apart by Bluetooth address and by the `device_id` in the packet) |
| Advertising content | Service UUID `6e1c0001-…`; scan response enabled |
| Advertising interval, transmit power | Not set by the firmware; library defaults |
| Simultaneous connections | 1. While a connection exists, a new connection is disconnected immediately |
| Advertising start and stop | Stops when a connection is established; the main loop restarts it after a disconnect; no advertising during a bond erase |

**Security parameters (protected build, `main.cpp:243-257`).**

| Parameter | Value | Meaning |
|---|---|---|
| `ESP_BLE_SM_AUTHEN_REQ_MODE` | `ESP_LE_AUTH_REQ_SC_MITM_BOND` | LE Secure Connections, MITM, bonding |
| `ESP_BLE_SM_IOCAP_MODE` | `ESP_IO_CAP_OUT` | Display only (DisplayOnly); the laptop enters the passkey |
| `ESP_BLE_SM_MAX_KEY_SIZE` | 16 | Key length 16 bytes |
| `ESP_BLE_SM_SET_INIT_KEY`, `ESP_BLE_SM_SET_RSP_KEY` | `ESP_BLE_ENC_KEY_MASK` plus `ESP_BLE_ID_KEY_MASK` | Distribute the encryption key and the identity key |
| `ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH` | Enabled | Pairing below the mode above is not accepted |
| `kRequiredAuthMode` | `0x0d` (`comms_security.h:8`) | Application-level gate: all three bits must be set: SC `0x08`, MITM `0x04` and bond `0x01`. `main.cpp:35-36` uses `static_assert` to confirm that it equals the SDK's `ESP_LE_AUTH_REQ_SC_MITM_BOND` |
| Passkey | 6 decimal digits, generated fresh by the stack for each pairing | Printed only to the local serial port: `PAIR LOCALLY: enter NNNNNN on Windows (do not record)` |

Each parameter is set with its own call to `esp_ble_gap_set_security_param`, and each return value is checked. If any one fails, the firmware prints `ble_security_configuration_failed` and aborts start-up.

**Sensor packet: 32 bytes, little-endian (`kPacketSize = 32`, `comms_packet.h:9`).** The Python format is `<2sBBIII8h`.

| Offset | Length | Type | Field | Values |
|---|---|---|---|---|
| 0 | 2 | ASCII | Packet magic | `LC` (`4C 43`) |
| 2 | 1 | `uint8` | Version | 2 means table dummy data (default); 1 means formula dummy data (`COMMS_LEGACY_DUMMY=1`). Version 3 is the owner's direction for the planned real-data packet (38 bytes with the 11 values only). It will replace versions 1 and 2 everywhere, including the dummy data, and is not in the code (see "Planned, not built: real glove data packet") |
| 3 | 1 | `uint8` | `device_id` | 1 means left, 2 means right; any other value makes serialization fail |
| 4 | 4 | `uint32` | `boot_id` | Taken once per power-up with `esp_random()` |
| 8 | 4 | `uint32` | `seq` | Starts at 0, increases by 1 for each generated sample, wraps modulo 2^32 |
| 12 | 4 | `uint32` | `uptime_ms` | `millis()` at the start of this main-loop pass; the two boards are not synchronized |
| 16 | 16 | 8 × `int16` | Channels 0 to 7 | −32768 to 32767 |

- In version 2, the 8 values are `kDummyFixtures[randomWord % kDummyFixtureCount]` (`comms_packet.h:54-62`).
- In version 1, channel i is `(seq % 2000) − 1000 + 10×i` (`comms_packet.h:17-20`). The laptop and the Ultra96 service both check that version-1 values equal this formula (`laptop/bridge.py:408`, `ultra96/protocol.py:71`). Real data therefore cannot use version 1.
- The notification payload limit is MTU − 3, so the sensor stream needs an ATT MTU of at least 35 (`comms_security.h:19`).
- The golden vectors are in `tests/fixtures/comms-golden.json`. One packet is formula dummy data for device 2, `boot_id` `0x78563412`, `seq` 42, `uptime_ms` `0x01020304`. The other is a boundary-value packet for device 1, with `boot_id` and `seq` both `0xffffffff` and `uptime_ms` 0. Both packets are version 1.

**Source statistics record: 24 bytes, little-endian (`kSourceStatsSize = 24`, `comms_source_stats.h:10`).** The Python format is `<4sB3xIIII`.

| Offset | Length | Type | Field | Notes |
|---|---|---|---|---|
| 0 | 4 | ASCII | Statistics magic | `LCS1` |
| 4 | 1 | `uint8` | `device_id` | 1 or 2 |
| 5 | 3 | — | Reserved | Always 0 |
| 8 | 4 | `uint32` | `boot_id` | The same as in the sensor packet |
| 12 | 4 | `uint32` | `next_seq` | The next sequence number to be allocated, which is also the number of samples generated since this power-up |
| 16 | 4 | `uint32` | `submitted` | Number of successful sensor packet submissions |
| 20 | 4 | `uint32` | `failures` | Number of failed sensor packet submissions |

All three counters wrap as `uint32`. Only sensor packets count. Submissions of the counter, the probe and control responses do not count.

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

`ControlEngine::process` checks in this order: first `B7` (if it is missing, the function returns 0 and no response is sent), then the control version, then frame length, `device_id`, status and `id`, and finally it dispatches on the opcode (`comms_control.h:59-97`).

| Opcode | Name | Request payload | Success response | Rules |
|---|---|---|---|---|
| `1` | Command | 32-byte version-2 sensor packet | 46 bytes: header plus the transformed packet | The payload must be exactly 32 bytes and `offset` must be 0. The payload's packet magic must be `LC`, its version 2, its `device_id` and `boot_id` this board's current values, and its `seq` must equal `id`; otherwise status 1. These checks run before the cache lookup and the transform, so a rejected command changes no state (`comms_control.h:123-127`). If the same `id` is already in the cache: identical content returns the cached response unchanged, with no second transform; different content gives status 5. If `id` is not greater than the highest `id` handled in this connection: status 5. Otherwise the firmware adds 1 to each of the 8 channels (wrapping as `uint16`, so 32767 plus 1 becomes −32768), replaces `uptime_ms` with this pass's `millis()`, stores the result in the cache and returns it (`comms_control.h:121-154`). |
| `2` | Rate change | 2 bytes, `uint16` little-endian, in Hz | 16 bytes: header plus the rate now in effect | The payload must be exactly 2 bytes, `offset` 0, and the value from 1 to 200; otherwise status 1. Takes effect immediately (`comms_control.h:78-86`). |
| `0x10` | File begin | 36 bytes: `uint32` total length plus 32-byte SHA-256 | 14 bytes | The payload must be exactly 36 bytes, `offset` 0, and the total length from 1 to 65536; otherwise status 1. Resent with the same `id`: if length and digest match, the reply is success and the response `offset` is the number of bytes received (also when the file is already complete); if they differ, status 5. Another file not yet complete: status 2. The previous file already complete: it is discarded and the new file starts. Memory allocation fails: status 2 (`comms_control.h:164-183`). |
| `0x11` | File chunk | 1 to 180 bytes | 14 bytes; `offset` is the next expected offset | Payload length outside 1 to 180: status 1. `id` is not the current file, there is no file, or `offset` is greater than the bytes received (a gap): status 3. `offset` plus length exceeds the total length: status 1. `offset` is less than the bytes received (an old chunk resent): status 3 if the chunk crosses the received position, status 5 if its content differs from what was received, accepted if it is identical. `offset` equals the bytes received: the chunk is written (`comms_control.h:184-201`). |
| `0x12` | File end | None | 50 bytes: header plus `uint32` length plus 32-byte digest | The payload must be empty, otherwise status 1. Wrong `id`, `offset` not equal to the total length, or not all bytes received: status 3. On the first end the firmware computes SHA-256; a mismatch gives status 4. Another end after success returns the same 50 bytes without recomputing (`comms_control.h:202-216`). |
| `0x13` | File abort | None | 14 bytes | `offset` must be 0 and the payload empty, otherwise status 1. A file exists with a different `id`: status 3. Otherwise the file is discarded and success is returned; success is also returned when there is no file (`comms_control.h:90-94`). |
| Other | — | — | 14 bytes, status 6 | — |

| Status code | Enum name | Meaning |
|---|---|---|
| 0 | `ControlOk` | Success |
| 1 | `ControlInvalid` | Invalid field, length or value (including a command payload whose packet magic is not `LC`) |
| 2 | `ControlBusy` | Control queue full, another file in transfer, or out of memory |
| 3 | `ControlOrder` | Order error: a gap, an end before all bytes arrived, an `id` mismatch |
| 4 | `ControlIntegrity` | SHA-256 mismatch |
| 5 | `ControlConflict` | Same `id` with different content, or a command `id` not greater than the highest one handled |
| 6 | `ControlUnsupported` | Unsupported control version or opcode; or rejected directly in the callback because the MTU is too small or the frame is longer than MTU − 3 |

**Capacities, timeouts and other constants.**

| Constant | Value | Location |
|---|---|---|
| `kControlHeaderSize` | 14 | `comms_control.h:11` |
| `kControlMaxFrame` | 194 | `comms_control.h:12` |
| `kControlMaxChunk` | 180 | `comms_control.h:13` |
| `kControlMaxFile` | 65536 bytes (held in heap memory) | `comms_control.h:14` |
| `kFileIdleTimeoutMs` | 30000 ms: an incomplete file with no activity for longer than this is discarded | `comms_control.h:15`, `54-57` |
| Control channel minimum MTU | 64 | `controlFitsMtu`, `comms_control.h:25` |
| Chunk capacity | `min(MTU − 3 − 14, 180)`; 47 at MTU 64, 180 at MTU 517 | `controlChunkCapacity`, `comms_control.h:26-30` |
| `kControlQueueSize` | 4 frames (from the callback to the main loop), each up to 194 bytes | `main.cpp:77-79` |
| Command response cache | 8 entries, overwritten as a ring; cleared on every connect and every disconnect, together with the highest handled `id` | `comms_control.h:46-53`, `110`, `150-151` |
| Sensor minimum MTU | 35 | `sensorFitsMtu`, `comms_security.h:19` |
| Local MTU | `ESP_GATT_MAX_MTU_SIZE` (517 in the SDK installed on this machine) | `main.cpp:424` |
| Initial connection MTU | `ESP_GATT_DEF_BLE_MTU_SIZE` (23 in the SDK installed on this machine) | `main.cpp:62`, `138`, `162` |
| MTU probe maximum payload | `ESP_GATT_MAX_MTU_SIZE − 3` | `main.cpp:50` |
| Rate range and default | 1 to 200 Hz; default 10 Hz | `main.cpp:24-26`, `39`; `comms_control.h:39` |
| `kReportIntervalMs` | 1000 ms | `main.cpp:37` |
| Serial baud rate | 115200 | `main.cpp:405`, `platformio.ini:8` |
| Serial command buffer | 32 bytes (at most 31 characters) | `main.cpp:374` |
| Dummy data table rows | The generator requires 2 to 64 rows (`common/sensor.py:94`); the firmware requires more than 1 row (`comms_packet.h:57`) | — |
| Dummy data per row | 8 integers from −32768 to 32767 | `common/sensor.py:96` |

**Compile switches.**

| Macro | Default | Effect |
|---|---|---|
| `COMMS_DEVICE_ID` | 1 | This board's identity; only 1 or 2 (`static_assert`, `main.cpp:34`). |
| `COMMS_INITIAL_RATE_HZ` | 10 | Rate at power-up, 1 to 200 (`static_assert`, `main.cpp:39`). |
| `COMMS_UNPROTECTED_DIAGNOSTIC` | 0 | Set to 1 for the unprotected diagnostic build. |
| `COMMS_LEGACY_DUMMY` | 0 | Set to 1 to send version-1 formula dummy data. |
| `COMMS_FIXTURE_SEED` | Undefined | When defined, the row is chosen from the linear congruential sequence `state = state×1664525 + 1013904223`, using `state >> 8`; the result is reproducible. When undefined, `esp_random()` is used (`main.cpp:87-96`). |
| `CORE_DEBUG_LEVEL` | 0 | Turns off Arduino framework logs (the library prints the passkey at INFO level). |

| Build environment | Extra flags | Purpose |
|---|---|---|
| `firebeetle32` (`default_envs`) | None | Protected build, ID 1 (because `COMMS_DEVICE_ID` defaults to 1) |
| `firebeetle32-left` | `-DCOMMS_DEVICE_ID=1` | Left board, used by `flash.py` |
| `firebeetle32-right` | `-DCOMMS_DEVICE_ID=2` | Right board, used by `flash.py` |
| `firebeetle32-unprotected-diagnostic` | `-DCOMMS_UNPROTECTED_DIAGNOSTIC=1` | Unprotected comparison, ID 1 |

`platformio run` without `-e` builds the default environment `firebeetle32`. Flashing that build onto a board makes the board ID 1, so the right board must be built and flashed with `-e firebeetle32-right`.

**Serial output (each item is one line of text).**

| Line starts with | When it appears |
|---|---|
| `comms_ready device_id= packet_bytes=32 packet_version= rate_hz= protected= control_version=1 file_max_bytes=65536` | `setup()` finished successfully |
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

### Planned, not built: real glove data packet (38 bytes, version 3)

The direction of olsonwangyj, the Communications owner (2026-10-14; proposed to the teammates and final when they confirm): the 11 values are sent as 11 `int16` with fixed scale factors, in a new protocol version, version 3 (hand-off document sections 4.2, 8 step 1 and 13). With the 11 values only, the packet is 38 bytes. The final layout is frozen only after Siqiang and Wen Ree answer whether the glove's IDLE/MOVING state travels in V1 (asked for Thu 2026-10-15): an extra field changes the length, the MTU floor and `on_sample`. The table below is the layout with the 11 values only. It is not in the code yet: today `kPacketSize` is 32, and the laptop's `decode_packet` rejects any packet that is not exactly 32 bytes or whose version is not 1 or 2 (`common/sensor.py:74-80`).

| Offset | Length | Field | Wire value = physical value × | Representable range |
|---|---|---|---|---|
| 0 | 16 | Header | The current 16-byte header layout, with the version byte set to 3 | — |
| 16, 18, 20 | 2 each | `ax` `ay` `az` | g × 10000 | ±3.2767 g |
| 22, 24, 26 | 2 each | `gx` `gy` `gz` | °/s × 100 | ±327.67 °/s |
| 28, 30, 32 | 2 each | `yaw` `pitch` `roll` | degrees × 100 | ±327.67° |
| 34, 36 | 2 each | `flex1` `flex2` | normalized value × 10000 | ±3.2767 |

- A 38-byte notification needs an ATT MTU of at least 41.
- Application-level byte rate: 38 bytes × 50 Hz × 2 boards = 30.4 kbps. The 32-byte dummy packet was measured clean at 33.8 kbps combined (the 70 Hz setting, which delivered about 66 packets/s per board). The 38-byte packet has not been measured at all (hand-off document section 13).
- **Version 3, and only the newest version is supported (the owner's rule, 2026-10-14).** A new version number means no receiver reads the new layout with the old 8-value one. There is no interoperability between versions: each component accepts only the current version, and an upgrade means reflashing both boards, redeploying the Ultra96 service and reinstalling the phone app together. Version 3 therefore replaces versions 1 and 2 everywhere, including the dummy test data, which moves to the 11-value format; there is no transition period (hand-off document section 8, step 1, which also explains why keeping an old version on the result path would not help). Firmware, laptop, Ultra96 and phone change together: the laptop carries the packet version into the `v` field of `SENSOR_BATCH` (`common/sensor.py:50`), and the Ultra96 copies the sample's version into `GESTURE_RESULT.v` (`ultra96/server.py:264`), so the phone's result checks see version 3 too. Real data could not use version 1 in any case, because version 1 requires the values to equal the dummy formula.
- **The scales are checked before they are fixed (the owner's direction, 2026-10-14).** The factors in the table are checked against the log of real samples that Siqiang pushes to the team repo (asked for by Fri 2026-10-16, a proposed date; hand-off document section 6.4) before they are fixed.
- **Values outside the `int16` range (to be agreed with Wen Ree; asked in the message).** The two options are: clamp the value to the `int16` limit, or drop that one sample. Either way Communications counts it and never drops a connection or a whole gesture. A clamped value cannot be told apart from a real value at the limit (3.2767 g can be either); if the model needs to know which samples were clamped, a per-sample flag is needed, which changes the packet and `on_sample` again. Neither option guarantees that a gesture is still recognised (hand-off document sections 8 step 1 and 13). The firmware has no such counter yet.
- **The model gets physical floats (the owner's direction, 2026-10-14; final when Wen Ree confirms).** The transport stays `int16`. On the Ultra96, Communications decodes each value and divides it by the same factor, so the model receives the 11 values in the agreed physical units; any normalisation is Wen Ree's (hand-off document section 7.2). The factors in this table and in the Ultra96 decoder must therefore stay identical. Restoring cannot recover precision lost when packing: acceleration and flex keep 4 decimal places, angular rate and angles 2.
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

**B. Power-up (`setup()`, `main.cpp:404-453`)**

1. Open serial at 115200. Set `boot_id = esp_random()` and write it into the source statistics too.
2. Create `ControlEngine(device ID, boot_id, SHA-256 function, initial rate)` with `new (std::nothrow)`, then create the state mutex `connectionStateMutex`.
3. Call `BLEDevice::init("LTC-COMMS")`. Set the security parameters (the diagnostic build only prints `ble_security=UNPROTECTED_DIAGNOSTIC not_protected_evidence`). Register the custom GAP and GATTS callbacks. Set the local MTU to `ESP_GATT_MAX_MTU_SIZE` and print `ble_local_mtu_configured`. A failure to set the MTU does not abort start-up; only the return code is printed.
4. Create the service and the 7 characteristics, start the service, advertise the service UUID with scan response on, set `bleReady`, and print `comms_ready …`.
5. Failure paths: if the `ControlEngine` allocation fails, the mutex cannot be created, or any security parameter fails, `setup()` returns directly. `bleReady` stays false, the main loop only idles, and the board does not advertise.

**C. Connection and authentication**

1. The laptop connects, and `onConnect` runs (`main.cpp:126-152`). If a connection already exists or a bond erase is in progress, the new connection is disconnected at once. Otherwise the firmware records the connection ID and the peer address, sets `authenticated` to false, clears the subscriptions, the control queue, the command cache, the file and any pending MTU probe, resets the MTU to 23, stops advertising and prints `ble_connected …`.
2. Protected build: the firmware itself calls `esp_ble_set_encryption(peer, ESP_BLE_SEC_ENCRYPT_MITM)`. On failure it prints `ble_security_request_failed` and disconnects.
3. A security request from the peer (`onSecurityRequest`) is accepted only when there is a current connection and no bond erase is in progress.
4. First pairing: the stack generates a 6-digit passkey, `onPassKeyNotify` prints it to serial, and the operator enters it on Windows with the input hidden. With an existing bond, the link is encrypted directly and no passkey appears.
5. `onAuthenticationComplete` (`main.cpp:196-209`) sets `authenticated` only when all four hold: the peer address equals the current connection's, the result is success, `auth_mode` contains the three bits of `0x0d`, and no bond erase is in progress. It then prints `ble_security_complete …`. The callback structure contains key material; the firmware does not print it.
6. After MTU negotiation, `onMtuChanged` updates `negotiatedMtu` only for the current connection ID and prints `ble_mtu_changed`.
7. The laptop subscribes by writing each CCCD. While connected, `CccdCallbacks` sets the four subscription flags to each CCCD's current value.
8. Failure paths: if the authentication result belongs to the current peer but does not meet the requirement, the firmware disconnects the peer. If the peer asks the firmware to enter a passkey (`onPassKeyRequest`), the firmware returns the invalid value `UINT32_MAX`, so that pairing fails. Numeric-comparison confirmation (`onConfirmPIN`) is always refused.

**D. Each main-loop pass (`loop()`, `main.cpp:455-561`)**

1. Record `nowMs = millis()`. If `bleReady` is false, only call `delay(1)` and return.
2. Read serial commands.
3. Check whether the bond erase has finished. Restart advertising if needed and print `ble_advertising_restarted`.
4. Take the mutex. It is held from here through step 10 (`main.cpp:483-549`). First discard an incomplete file that has been idle for more than 30 seconds.
5. Send tick check: continue only if `micros()` is at least `1000000 / rate` microseconds after the last send, and set "last send" to the current time (`main.cpp:486-488`).
6. Protected build, connected but not authenticated: increment `security_suppressed`. The notification gate is closed, and no data is sent.
7. 0002 subscribed and gate open: send the 4-byte counter. Only a successful submission increments the counter and prints `ble_notify_submitted`.
8. 0005 subscribed and gate open: if the MTU is below 35, increment `mtu_suppressed` and allocate no sequence number. Otherwise allocate `seq` first, then serialize, then submit, and finally increment `submitted` or `failures` according to the result. The sample is produced at `main.cpp:503-508`: `serializeFixturePacket(…, fixtureRandomWord())` takes 8 values from the dummy data table (with `COMMS_LEGACY_DUMMY=1`, the formula in `serializeDummyPacket` is used instead). The real sensor module's "read one sample" goes here. When 0005 is not subscribed or the gate is closed, no sequence number is allocated.
9. Control queue not empty, 0008 subscribed and gate open: take the frame at the head of the queue and pass it to `ControlEngine::process`; if there is a response, notify it. This step is not bound by the sensor send tick, but it handles at most one frame per pass. If the rate changed, reset "last send" to the current time and print `b07_rate_changed` (`main.cpp:517-529`).
10. A pending MTU probe: if 0004 is not subscribed or the gate is closed, print `reason=not_ready`. If the length exceeds MTU − 3 or `ESP_GATT_MAX_MTU_SIZE − 3`, print a rejection. Otherwise send the N-byte probe packet and, on success, print `mtu_probe_submitted`.
11. Release the mutex. If 1000 ms have passed since the last report, print `alive` and `comms_stats`. Finally call `delay(1)`.

**E. Reading source statistics (the laptop reads 0006)**

1. The callback copies `sensorStats` under the mutex, serializes it to 24 bytes and uses that as the read response (`main.cpp:223-235`). The read itself changes no counter.
2. The read permission is `READ_ENC_MITM`. The stack rejects unencrypted reads.
3. The laptop reads once before subscribing to 0005 and once after stopping notifications. It reconciles using `next_seq` and `boot_id` from the two reads ([detail chapter 3](03-laptop-relay-and-tools.md)).

**F. Control writes (the laptop writes 0007; handled in the GATTS callback on the Bluetooth task, `main.cpp:271-305`)**

1. Only real WRITE events on the 0007 handle are processed. If the length is outside 14 to 194, `offset` is non-zero, it is a prepared write, or the value is empty: print `b07_control_rejected reason=malformed bytes=…` and send no response.
2. Checks: no bond erase in progress; the write's connection ID equals the current connection; connected; 0008 subscribed; authenticated; MTU at least 64; frame length not above MTU − 3; queue not full. If all hold, the whole frame is copied into the queue.
3. Otherwise increment `control_queue_rejected`. If the write came from the current connection, which is authenticated and has subscribed to 0008, and the frame starts with `B7`, the firmware immediately replies with a 14-byte rejection: status 2 when frame length and MTU are both acceptable (that is, the queue is full), status 6 when they are not. The rejection frame keeps the request's `id` and `offset`. In all other cases (not authenticated, 0008 not subscribed, a write from another connection) there is no response.
4. The stack sends the ATT-level write response. It only says that the write arrived, not that the application accepted it. Application acceptance is shown only by the response on 0008 (comment at `main.cpp:292-293`).

**G. MTU probe writes (the laptop writes 0003, `main.cpp:306-325`)**

1. Only real WRITE events on the 0003 handle are processed. The write must be exactly 2 bytes, with `offset` 0, not a prepared write, and a non-empty value; otherwise print `mtu_probe_rejected reason=malformed request_bytes=…`.
2. If the write comes from the current connection, 0004 is subscribed, the gate is open and no probe is pending, record the requested length; the main loop sends the probe (see D, step 10). Otherwise print `mtu_probe_rejected reason=pending` or `reason=not_ready`.

**H. Disconnect and reconnect**

1. `onDisconnect` (only for the current connection ID, `main.cpp:154-168`) clears authentication, the subscriptions, the control queue, the command cache and the highest handled `id`, and the file. It resets the MTU to 23, marks advertising for restart when no bond erase is in progress, and prints `ble_disconnected`.
2. The next main-loop pass restarts advertising and prints `ble_advertising_restarted`.
3. No samples are produced while disconnected, `seq` does not advance, and there is no offline buffer. `boot_id` does not change; after reconnecting, sequence numbers continue from where they stopped. The rate keeps its pre-disconnect value until a restart or another rate change.
4. Seen downstream, a reconnect can still leave gaps in `seq`. On a BLE disconnect the laptop discards that glove's queued samples (`laptop/bridge.py:910`, `113-119`), and on a TLS reconnect samples already written but not acknowledged count as ambiguous drops and are not resent ([detail chapter 3](03-laptop-relay-and-tools.md)). The disconnected time itself shows only as a jump in `uptime_ms`, because the board makes no samples then (hand-off document section 7.2).

**I. Bond erase (type `erase-bonds` plus Enter on serial, `main.cpp:338-371`, `461-470`)**

1. Connected or already erasing: print `erase_bonds_rejected …` and do nothing.
2. Otherwise enter the erase state: set `authenticated` to false, stop restarting advertising, stop advertising, list the bonds, call `esp_ble_remove_bond_device` for each one, print `erase_bonds_requested count=N`, and wait for the stack's completion callbacks (`gapCallback`).
3. When all completion callbacks have arrived, no bonds remain and there were no failures: leave the erase state, resume advertising and print `erase_bonds_complete remaining=0 remove_Windows_bond_then_pair_again`. When the board has no bonds, this path is taken too.
4. Failure paths: if listing the bonds fails, print `erase_bonds_failed return_code=… restart_required=1`. If a removal fails or bonds remain, print `erase_bonds_failed remaining=… failures=… restart_required=1`. In both cases the erase state is not cleared, authentication and advertising stay off, and the board must be restarted.
5. Serial input is handled line by line: `\r` is ignored; an empty line gets no response; a line longer than 31 characters, or any line other than `erase-bonds`, prints `serial_command_unknown supported=erase-bonds`.

## Why it is designed this way

1. **A fixed 32 bytes, written byte by byte in little-endian order.** C++ and Python then get the same result from the same bytes, independent of struct alignment and host byte order. A fixed length plus a version number exposes a format mismatch; for the same reason the planned 38-byte packet is a new version, 3. Rejected: application-level fragmentation, CRC and compression, because BLE already provides link integrity. Source: `docs/archive/design/week7-selected-design-2026-09-06.md` item 3; `docs/archive/test-evidence/week7-packet-firmware-evidence.md`.
2. **If the MTU is too small, nothing is sent, and this is counted separately (`mtu_suppressed`).** The notification payload limit is MTU − 3, and a truncated packet is meaningless. Rejected: silent truncation, or fragmentation by the firmware itself. Source: selected design item 3.
3. **No offline backlog; no samples are generated while disconnected.** An old gesture sent late would be treated as a new live action. Rejected: buffering on the ESP and sending later. Source: selected design item 4; "Scope and acceptance" in `docs/archive/design/specs/2026-09-17-dual-esp-reception.md` ("No offline history or retransmission protocol").
4. **Allocate the sequence number first, then try to submit.** A sample whose submission fails still uses up a sequence number, so a loss cannot be hidden by reusing the number. Rejected: incrementing the sequence only after a successful submission. That was the old rule in selected design item 4, and the dual-board specification replaced it. Source: dual-board specification "Scope and acceptance".
5. **A separate 24-byte source statistics characteristic.** The laptop reads it once before subscribing and once after stopping, and reconciles over the range `[start.next_seq, end.next_seq)`, so the first and last samples can be checked too. A successful submission alone does not prove delivery. Source: dual-board specification "Scope and acceptance".
6. **SC, MITM and bonding; the passkey is shown only on the local serial port; the characteristics and CCCDs all require encryption with MITM; the application also gates on the authentication result.** These are two layers of protection. The attribute permissions block unencrypted access. The application gate blocks a "success" callback after a downgrade. Rejected: Just Works, automatic downgrade and automatic bond deletion. Source: selected design items 13 and 24.
7. **No `setStaticPIN()`.** This Arduino helper overwrites the authentication mode. The firmware calls `esp_ble_gap_set_security_param` for each parameter instead and checks every return value. Source: the comment at `main.cpp:249-250`; the firmware evidence document.
8. **No extra HMAC, HKDF or AES-GCM on top of BLE.** The authenticated BLE link plus the SSH and TLS legs after it already cover the whole path. Another key and nonce protocol that nobody has reviewed would only add burden. Rejected: the application-level encryption scheme in section 10.1 of the architecture draft. Source: selected design item 14; `docs/archive/design/architecture-and-interface-draft-v0.1.md` section 10.1.
9. **`esp_ble_gatts_send_indicate` sends to the current connection only.** `BLECharacteristic::notify()` broadcasts and returns no result, so it cannot support submission counts. `BLEServer::getGattsIf()` is private in Arduino 2.0.17, so the firmware takes the interface number from the `ESP_GATTS_REG_EVT` registration event. Source: the comments at `main.cpp:103-104` and `261-262`; the firmware evidence document.
10. **Write fields are read only for a real WRITE event with a matching handle.** The GATTS callback parameter is a union. The bytes of another event (for example EXEC_WRITE) must not be parsed as a write. The cost: prepared writes and execute writes are not supported. Source: selected design item 20.
11. **Policy logic lives in portable C++11 headers.** Serialization, security policy, event parsing and the control state machine can then be tested on the host without flashing a board. Source: dual-board specification "Interfaces and boundaries".
12. **Left and right identity is a compile-time constant, in two build environments.** The identity travels with the firmware and is not guessed at run time. Source: dual-board specification "Scope and acceptance".
13. **A board's physical identity is the Bluetooth address derived from the factory MAC, not the COM port number.** With one programming cable, two boards connected one after the other can get the same COM number. The firmware uses `static_assert(CONFIG_ESP32_UNIVERSAL_MAC_ADDRESSES == 4)` to guarantee that the "factory base plus 2" conversion holds. Source: the comments at `flash.py:69-71` and `103`; `main.cpp:563-565`.
14. **The control channel uses two separate protected characteristics and does not touch the sensor stream's sequence numbers.** Commands, rate changes and files are counted separately and do not affect throughput reconciliation. Files only go from the laptop into ESP memory; resuming after power loss is not supported. Source: "Contracts" in `docs/archive/design/plans/2026-09-28-co-features.md`; "Protected BLE controls" and "Files" in `docs/co-protocol-v2.md`.
15. **The callback only copies control frames into a 4-frame queue; the main loop handles one frame per pass.** The sensor send tick runs first, so bulk work cannot delay the timing. Source: the comment at `main.cpp:515-516`. The design records do not name a rejected alternative.
16. **The command cache holds 8 entries; `id` must increase within one connection; an old `id` pushed out of the cache is always rejected.** Resending the same command gets the same response, with no second transform. An old request cannot have a new effect. The firmware prevents repeats only within one connection; preventing repeated game effects across connections is the job of the command record on the Ultra96 (comment at `comms_control.h:47-48`). Source: "Contracts" in the CO features plan; `docs/co-protocol-v2.md`.
17. **The dummy data header is generated from editable JSON.** The laptop's simulated source and the firmware use the same data. Changing the data is a build step and does not change the wire format. Source: "Decisions" in the CO features plan.
18. **The unprotected build is a separate, explicitly named environment.** It is available when a comparison is needed, but the normal build is always protected. The diagnostic build states on serial that it cannot serve as protection evidence. Source: selected design item 13.
19. **`CORE_DEBUG_LEVEL=0`.** The Arduino BLE library prints the passkey at INFO level. With framework logs off, the only interactive output left is the firmware's own line. Source: `platformio.ini:9-11`; the firmware evidence document.

## Cautions and known limitations

- **What is sent today is not sensor data.** The 8 values come from `common/dummy_fixtures.json`. The row is chosen at random, and the same row may repeat.
- **Editing the JSON does not change a board that is already flashed.** Regenerate the header, build and flash. `flash.py` rewrites the Git-tracked `comms_fixtures.h` every time.
- **A successful submission is not delivery.** `submitted` only means the stack accepted the submission. It is evidence level 1.
- **The two failure counters count different things.** The serial `submission_errors` counts failed submissions on every characteristic (counter, sensor, probe, control response). The source statistics `failures` counts sensor packets only. Use the source statistics for reconciliation.
- **The rate is not reset on disconnect.** `ControlEngine::disconnect()` does not change `rateHz_`. Only a restart or another rate-change command changes it.
- **At high rates the actual packet rate is below the setting.** When the send tick check passes, "last send" is set to the current time, and each pass also has `delay(1)`, so the period is rounded up. A 70 Hz setting measured about 66 packets/s per board, which matches the code (this is an inference). A 50 Hz setting measured about 49.98 packets/s. The highest clean setting measured is 70 Hz (about 66 packets/s delivered), with the 32-byte dummy packet; real 38-byte data has not been measured. 75 Hz failed because the right board had 260 source submissions rejected by the stack, not because of downstream loss. 100 Hz also failed (`docs/archive/test-evidence/co-live-deployment-2026-09-28.md`).
- **The mutex is held over a wide range.** `connectionStateMutex` is held for all of `main.cpp:483-549`, and the BLE callbacks also need it. A slow operation added in this range in future (for example an I2C read) will block the callbacks.
- **A received file stays in memory** until the next file begin, an abort or a disconnect. The firmware does not use the file content; it only checks the digest. After a digest mismatch (status 4), the incomplete file still holds the slot. Abort it, wait 30 seconds or disconnect before starting another file.
- **A changed GATT table needs re-pairing.** After the control characteristics were added on 28 September, a targeted bond recovery was done on the Windows side (deployment record).
- **Bond recovery is a manual procedure.** The firmware never deletes bonds automatically and never lowers the protection level.
- **The 0002 counter stream prints one serial line per notification.** Subscribe to it only for diagnosis.
- **The single-board diagnostic tools cannot choose a board.** `laptop.ble_counter_receiver` and `laptop.mtu_probe` scan by service UUID and connect to whichever board they find first. Both boards advertise the same name, so power only one board when using these tools. They also do not set a rate; the board keeps its last rate.
- **The platform version is not pinned.** `platformio.ini` says `platform = espressif32`. The verified combination is Espressif32 7.1.0 with Arduino-ESP32 2.0.17 (package version `3.20017.241212`), and this is also what is installed on this machine. In the local SDK, `ESP_GATT_MAX_MTU_SIZE` is 517, `ESP_GATT_DEF_BLE_MTU_SIZE` is 23 and `CONFIG_ESP32_UNIVERSAL_MAC_ADDRESSES` is 4.
- **`flash.py` works only on Windows.** A port name must be `COM` plus digits, and the interpreter path for `esptool` is `.platformio\penv\Scripts\python.exe`.
- **Reading the MAC resets the board.** `esptool read_mac` goes through the ROM. It does not flash and does not read the application's serial output.
- **The board connected first becomes LEFT (ID 1).** If the order is swapped on a reflash, the left and right identities swap, and the mapping is written in the new order. Label the two boards LEFT and RIGHT after flashing.
- **Without a mapping file, the default addresses hard-coded in the code are used.** `DEFAULT_BOARDS` in `tools/demo_boards.py` holds the original operator's two boards. After changing boards, run `python flash.py` first.
- **The firmware does not report its own version or commit.** `comms_ready` carries only the device ID, packet length, packet version, rate, protection, control version and file limit. To tell whether a board runs the current firmware, check that the magic is `LCS1` when the laptop reads the source statistics. Old firmware makes the laptop report `invalid source statistics magic; flash this board with the current firmware` (`laptop/source_audit.py:51`). The capture report's `workspace_source_sha256` covers the firmware sources (`firmware/esp32/platformio.ini`, `include/` and `src/`), but it describes the laptop's working copy and does not prove which version is flashed on the board (`laptop/reporting.py:13-37`).
- **No Week 7 names remain in the firmware.** No TLS host name, no `Week7*` symbol and no dated folder appears in the firmware source. The control frame magic `B7` and the serial prefix `b07_` refer to the team number B07. The `'W','7'` in `host_control.cpp` is a negative test that must be rejected.

### Status of the two boards and the local files (2026-10-14)

| Item | Status |
|---|---|
| Left board | Flashed with the current firmware on 2026-10-14 and verified: local loopback 100/100 packets; another run of 349 packets with source statistics reconciliation passing, a rate change to 20 Hz confirmed, and all 3 commands round-tripped (hand-off document section 6.1). |
| Right board | Still runs the Week 7 firmware and sends `W7` packets and `W7S1` statistics. The current laptop program rejects it when it reads the source statistics, reporting `invalid source statistics magic; flash this board with the current firmware`. This board is not subscribed, and start-up times out after 30 seconds (hand-off document section 9.2). See "How to run and verify" for how to flash it. Flashing it is in the owner's plan for Thu 2026-10-15 (hand-off document section 6.4). |
| `.comms-local/boards.json` (ignored by Git) | Exists; written 2026-10-14 03:05; `version` is 1 and `status` is `ready`. The left and right addresses are the same as the built-in `DEFAULT_BOARDS` and the old `.week7-local/boards.json`. So there is no need to rerun `python flash.py` for the mapping. There is no capture folder under `.comms-local/` yet. This holds for the owner's two boards only. Siqiang's gloves are other boards (flashing them is proposed for Sat 10-17 or Sun 10-18, Mon 10-19 morning at the latest, until Siqiang confirms; hand-off document section 6.4): flash them with the full `python flash.py`, which records their addresses and replaces this mapping. The owner's boards can still be captured afterwards by giving both `--left-address` and `--right-address` to `demo.py run` or `live`. Once a glove runs the Communications firmware, Siqiang's own Bluetooth recording script can no longer connect to it (hand-off document section 7.1). |
| `.week7-local/boards.json` | Still present, but the code no longer reads it. |
| `.week7-local/flashed-firmware-2026-09-29/left/firmware.bin`, `right/firmware.bin` | Archive copies of the firmware flashed on 29 September. They have the same SHA-256 as the `firmware.bin` files under `firmware/esp32/.pio/build/firebeetle32-left/` and `firebeetle32-right/` in the main working copy (built 2026-09-29). Keep them; do not delete them (hand-off document section 9.1, item 6). |
| `firmware/esp32/.pio/` (main working copy, ignored by Git) | Old build products from 29 September; the symbols are still in the old `week7` namespace. Do not flash the `firmware.bin` here directly. `platformio run` and `python flash.py` rebuild from the current source. |
| `D:\LetThemCook-attic\2026-10-14\flashed-firmware-left-2026-10-14\` (copied from the build folder of the removed `comms-cleanup` worktree) | Built 2026-10-14 02:51. Judging by the time, this is the build used for this flash of the left board. The `firmware/` folder it was built from is the same as in local `main` and in the team main after PR #18; after `d2fff21` (now `28db0b3`), the only change under `firmware/` was to the test file `host_control.cpp`. |

### Extension point: connecting the real sensor module (planned, not built)

The division of work is the owner's proposal of 2026-10-14, final when Siqiang confirms it (hand-off document sections 3.1 and 7.1). Siqiang delivers a working sensor module (initialization, read one sample, a description of the data format). olsonwangyj, the Communications owner, calls it from the Communications firmware and is responsible for scaling to `int16`, packing, BLE sending and connection management. Capture algorithms, calibration and sensor problems belong to Siqiang.

The interface requirements (functions, shapes, and what the other side must state) are maintained only in hand-off document section 7.1: initialization `bool gloveBegin()`, an optional periodic update `void gloveUpdate()`, and read one sample `bool gloveRead(float out[11])`. These are suggested shapes; Siqiang chooses the names. None of these functions exists yet, and the firmware calls none of them. This section records only the technical constraints that come from the Communications firmware code itself, and their reasons.

1. **Initialization must return on failure.** Initialization is called in `setup()`. If any step in `setup()` does not return before `advertising->start()` and `bleReady = true` are reached, the board never advertises and the main loop only idles (`main.cpp:404-453`, `457`).
2. **Reading a sample must not block or call `delay()`.** The code that takes the sample today runs while `connectionStateMutex` is held (`main.cpp:483-549`). The BLE callbacks for connect, disconnect, MTU change, authentication complete, CCCD write, source statistics read, control write and MTU probe write all wait for this lock with `portMAX_DELAY`. A slow sample read stalls all of these callbacks.
3. **Time spent per loop pass lowers the actual rate.** The send tick is checked once per pass, the period counts from the start of the pass that sent (`main.cpp:485-488`), and each pass ends with `delay(1)`. So the period rounds up to whole passes: a longer pass (for example a `gloveUpdate()` on every pass) increases the rounding, and a read longer than the interval delays the next packet. Today a 70 Hz setting gives about 66 packets/s.
4. **How often the periodic update is called.** If `gloveUpdate()` is needed, the main loop calls it once per pass. A pass takes about 1 ms plus that pass's work. When `bleReady` is false, the main loop does nothing.
5. **The serial port belongs to the Communications firmware.** The firmware calls `Serial.begin(115200)` itself, the main loop reads serial input to find `erase-bonds`, and the passkey is printed only on serial. So the module must not call `Serial.begin` again, must not read serial input, and must not print per sample.
6. **The radio belongs to the Communications firmware.** The firmware uses `BLEDevice` (BLE). The reference sketch `hardware/gloves/29_sept/imu_v7.ino` sends CSV text over Bluetooth Classic `BluetoothSerial` and has its own `setup()` and `loop()`, so the two cannot be linked together as they are.
7. **Identity and time are filled in by the Communications firmware.** Left and right identity comes from `COMMS_DEVICE_ID`, `seq` from `allocateSampleSequence`, and `uptime_ms` is `millis()` at the start of the pass. The module does not provide these.
8. **Scaling is done in the Communications firmware.** The 11 floats are converted to `int16` with the factors in the 38-byte table above. How a value outside the `int16` range is handled (clamp to the limit or drop that one sample, counted either way) is still to be agreed with Wen Ree (see the 38-byte section). The planned module contract says `out[]` must not contain NaN (hand-off document section 7.1). On the Ultra96, Communications divides by the same factors to give the model physical floats (hand-off document section 7.2).

**Places the Communications firmware itself must change (when the 38-byte version-3 packet is implemented; planned):**

| Location | Today | Why it must change |
|---|---|---|
| `comms_packet.h:9`, `29`, `34-38`, `60` | `kPacketSize = 32`; the version byte is written as 1 (line 29) or 2 (line 60); a loop writes 8 channels | New length 38 (with the 11 values only), version 3, 11 channels. Versions 1 and 2 go: whatever dummy data is kept (today the `COMMS_LEGACY_DUMMY` formula and the table) is sent as version 3 with 11 values |
| `comms_security.h:19` | `sensorFitsMtu` checks for at least 35 | 38 bytes need at least 41 |
| `main.cpp:503-510` | Takes dummy data | Call the sensor module to read a sample, scale it (with the out-of-range rule once it is agreed with Wen Ree, and its counter), then pack it |
| `setup()` from `main.cpp:404` | No sensor initialization | Call the sensor module's initialization |
| `main.cpp:450-451` | `packet_bytes=32` is hard-coded; `packet_version` is printed as 1 or 2 | Print the real length and version 3 |
| `comms_control.h:62`, `102-103`, `123`, `126`, `140-149` | The command payload is handled as 32 bytes, version 2, 8 channels; the output buffer must be at least 50 | Whether a command still embeds a whole packet must be decided first; with an embedded 38-byte packet the response is 52 bytes |
| `common/dummy_fixtures.json`, `tools/generate_dummy_fixtures.py:11`, `comms_fixtures.h` | 8 values per row | The dummy test data moves to the version-3 11-value format: 11 values per row (only the newest version is supported) |
| `platformio.ini` | Default 10 Hz | For 50 Hz, use `-DCOMMS_INITIAL_RATE_HZ=50` or a rate-change command at run time |
| Host tests and `tests/fixtures/` | 32-byte version-1 vectors | Replace them with 38-byte version-3 golden vectors, written before the code (hand-off document section 8) |

The places in the laptop, Ultra96 and phone code that must change at the same time are in hand-off document section 8, step 1. The firmware does not depend directly on any interface of Wen Ree's or Jie Ling's. Its scale factors are shared with the planned Ultra96 decoder, which restores physical floats for the model (see the 38-byte section).

**Planned dates for the firmware part.** These come from hand-off document section 6.4. Teammate dates are the owner's proposals, as asked in the messages, until the teammates confirm them; the owner's own plan is proposed too. Teammates deliver code by pushing it to the team repo on GitHub, not over Telegram. The team meets in person on Tue 2026-10-20 to integrate.

| Date | Who | What |
|---|---|---|
| Thu 10-15 | Siqiang | Answers to the questions in the message (hand-off document section 7.1); with Wen Ree, whether the glove's IDLE/MOVING state travels in V1, which freezes the version-3 layout |
| Thu 10-15 | olsonwangyj | Flash the right board with the current firmware; start the version-3 38-byte packet in firmware, laptop and Ultra96, with golden vectors and tests |
| Fri 10-16 | Siqiang | The sensor module (`gloveBegin` / `gloveUpdate` / `gloveRead`, suggested names, in one `.h` and one `.cpp` file) and a CSV log of real samples from each glove, pushed to the team repo under `hardware/` |
| Fri 10-16 | olsonwangyj | Build the firmware with the module. The owner's boards have no IMU or flex sensors, so on them check only that it compiles, that `gloveBegin()` returns false without blocking, and that the board still advertises; check the scales against the sample log before fixing them. Real readings are first tested on the gloves (Sat 10-17 or Sun 10-18) |
| Sat 10-17 or Sun 10-18 (Mon 10-19 morning at the latest) | Siqiang | Both gloves, so the owner can flash and test them, and if possible left with the owner until Tuesday for the Monday dry run |
| Sun 10-18 | olsonwangyj | Flash both gloves (full `python flash.py`) and test with Siqiang |
| Mon 10-19 | olsonwangyj | Full dry run from the gloves to the game; keep the evidence and list the problems for Tuesday |
| Tue 10-20 | Siqiang | Both gloves, charged, with USB cables, for the in-person session |

If time runs short, the 38-byte packet and Siqiang's module come second, after renewing the certificate and redeploying the Ultra96 service (hand-off document section 6.4). If the module is late, the rest of the chain can still be tested with dummy data; because version 3 replaces versions 1 and 2, that dummy data is version 3 with 11 values per row (the `common/dummy_fixtures.json` row above).

### History and removed items

- From 2026-10-08 (commit `d227a84`), the firmware's magic values changed from `W7` and `W7S1` to `LC` and `LCS1`. At that time the command payload still accepted `W7`.
- On 2026-10-14, `d2fff21` (now `28db0b3` after the history rewrite in hand-off document section 6.2; same files) removed that compatibility and the fallback read of `.week7-local`. The same day at 03:14, `4c2b078` (now `5db56ad`) merged it into local `main`. The command payload now accepts only `LC` (`comms_control.h:124`), and `host_control.cpp:66-72` asserts that commands with magic `W7`, `WC` or `L7` all get status 1. The board mapping is read and written only at `.comms-local/boards.json` (`tools/demo_boards.py:9`, `21-24`, `55`). When this was removed, the right board had not yet been flashed with the current firmware; see the status table above.
- The 17 old captures recorded with the Week 7 firmware (in `.week7-local/`) contain `W7` packets, and the current `demo.py report` no longer passes them. To review the old evidence, use the team main commit `880abba`. It replaced `ec398b6` when the history was rewritten (hand-off document section 6.2) and has the same files.
- The "Firmware and pairing" section of `docs/week7-runbook.md` is still written the old way: it builds and uploads only the default environment `firebeetle32` (ID 1), hard-codes the original operator's PlatformIO path, and mentions `W7`. The current procedure is `flash.py`.

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
```

- Label the two boards LEFT and RIGHT after flashing. When you reflash later to change the dummy data, connect LEFT first and RIGHT second.
- Build without flashing: `platformio run -d firmware/esp32 -e firebeetle32-left` (use `-right` for the right board). If `platformio` is not on PATH, use `~\.platformio\penv\Scripts\platformio.exe`.
- Regenerate only the dummy data header: `python -m tools.generate_dummy_fixtures`.

**Reflash only the right board (hand-off document section 6.3, step 3)**

```powershell
platformio run -d firmware/esp32 -e firebeetle32-right -t upload --upload-port COMx
```

- This command does not read the MAC and does not change `.comms-local/boards.json`. The Bluetooth address comes from the factory MAC and does not change on a reflash, so the mapping stays valid as long as it is the same right board. A full `python flash.py` run also works: connect the left board first, then the right board.
- If Windows says the bond needs authentication after the flash, follow "Bond recovery" below, then run `python flash.py --pair right`.

**What serial should show**

1. Start-up: `comms_ready device_id=1 packet_bytes=32 packet_version=2 rate_hz=10 protected=1 control_version=1 file_max_bytes=65536` (`device_id=2` on the right board).
2. Every second: `alive …` and `comms_stats …`.
3. Successful pairing or reconnect: `ble_security_complete success=1 auth_mode=13 approved=1 current_peer=1 reason=0`.
4. After the laptop starts a capture: `authenticated=1` in `comms_stats`; `sensor_submitted` and `next_seq` grow each second by about the rate; `mtu_suppressed` and `submission_errors` do not grow. The MTU measured in past runs is `mtu=517`.

**Bond recovery**

1. Stop every laptop client for this board, and wait for `ble_disconnected` on serial.
2. Type `erase-bonds` plus Enter on serial, and wait for `erase_bonds_complete remaining=0 …`. Neither `erase_bonds_rejected` nor `erase_bonds_failed` counts as done; the latter requires a board restart.
3. In Windows Bluetooth settings, remove only this board.
4. Run `python flash.py --pair left` (or `right`) again in a new process. Pairing repeatedly in the same process after the bonds changed was measured to fail (selected design item 24).

**Host tests (no hardware needed; they need `g++` or `clang++` on PATH, otherwise the C++ tests are skipped)**

```powershell
python -m pytest tests/test_firmware_control.py tests/test_firmware_events.py tests/test_firmware_source_stats.py tests/test_flash.py tests/test_demo_boards.py tests/test_sensor.py tests/test_co_contracts.py -q -p no:cacheprovider
```

- All tests: `python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider`. Do not run `python -m pytest` without paths from the repository root (`AGENTS.md` rule 4).
- Compiler options: `-std=c++11 -Wall -Wextra -Werror -I firmware/esp32/include`.
- Each of the three firmware tests requires its program to print one line: `PASS B07 command, rate, bounded file and validation`, `PASS GATT event/union and malformed-write regression`, `PASS source statistics accounting, serialization, wrap, and validation`. `host_packet.cpp` prints no PASS line. It prints two hex lines instead, which `tests/test_sensor.py` compares line by line with the golden vectors.

**What the host-side tests cover**

| Test | Coverage |
|---|---|
| `host_packet.cpp` | Hex of the two golden packets; capacity 31, device 0 and 3, and null pointers all fail; formula dummy values at `seq` 0, 1999, 2000 and `0xffffffff`; `auth_mode` missing SC (`0x05`), missing MITM (`0x09`), missing bond (`0x0c`), and a failed result are each rejected; notification gate truth table; MTU 34 rejected, 35 and 517 accepted |
| `host_source_stats.cpp` | A failed sample takes sequence 0 and a successful sample takes sequence 1; byte-by-byte comparison of the 24 bytes; all three counters wrap from `UINT32_MAX` to 0; null pointer, capacity 23, and device 0 and 3 return false and leave the buffer unchanged |
| `host_events.cpp` | Non-WRITE events, null parameters and a wrong handle are ignored; an MTU probe write must be exactly 2 bytes (1 and 3 are rejected), and prepared, `offset` 1 and empty value are judged malformed; control writes of 13 and 195 bytes, `offset` 1, prepared and empty value are judged malformed |
| `host_control.cpp` | Control gate, 6 combinations; table dummy data version 2, different random numbers choose different rows, modulo wrap; commands with packet magic `W7`, `WC` or `L7` get status 1 (lines 66 to 72); a command's channel plus-1 wrap and `uptime` replacement; a resend gets the same response; same `id` with different content conflicts; wrong boot, wrong device, wrong sequence and wrong packet version in the payload all get status 1; after 10 new commands push it out of the cache, an old `id` conflicts; accepted again after a disconnect; rate change 200 accepted, 201, 0 and `offset` 1 rejected; file begin, concurrency, out of order, resend, conflict, early end, abort after a digest mismatch, repeated abort, oversize 65537, cleared on disconnect, 30-second timeout; null pointers, too-short input, too-small output buffer and a non-`B7` magic all return 0 with no response; a frame with control version 2 and a frame with opcode `0x7f` get status 6; `id` 0, wrong device, non-zero status and a 181-byte chunk get status 1; MTU 63 and 64, chunk capacity 47 and 180 |
| `tests/test_flash.py` | Both environments are built before the board prompt; two boards on the same COM port one after the other; with several ports the port must be chosen by hand; an invalid choice does not flash; cancel; bad port data; a failed subprocess returns its real exit code 7; `--ports`, `--pair`, `--monitor`, an invalid monitor port, mutually exclusive options, `--help` run from outside the repository |
| `tests/test_demo_boards.py` | The flash order is written as the mapping and drives `demo.py run` and `--pair`; the same board connected twice is rejected before the right flash, and the mapping stays `incomplete` and blocks capture; a failed left or right flash never publishes `ready`; built-in default addresses and configuration validation; a failed write keeps the old file; the factory MAC plus 2 conversion and invalid output; the exact `read_mac` command; `--boards` is read-only; a failed identity read does not flash and keeps the mapping; explicit address arguments to `demo.py` can still override the mapping |
| `tests/test_co_contracts.py:32` | `comms_fixtures.h` exactly equals the output of `render_header()` |

**Verifying the diagnostic characteristics with the laptop tools** (details in [detail chapter 3](03-laptop-relay-and-tools.md)): `python -m laptop.ble_counter_receiver` uses 0002; `python -m laptop.mtu_probe` uses 0003 and 0004. Power only one board when using them.
