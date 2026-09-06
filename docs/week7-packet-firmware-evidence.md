# Week 7 packet and firmware evidence — 2026-09-06

This task implements Task 1 of the selected Week 7 design. It establishes codec,
portable firmware policy and build evidence. Physical BLE results belong in the
continuation report; this task did not access a BLE device or serial port.

## Packet interface and independent vectors

`common.sensor` exports `SensorPacket(device_id, boot_id, seq, uptime_ms, values)`,
`encode_packet`, `decode_packet`, and `dummy_values`; `packet.to_message(session_id)`
returns the exact `SENSOR_BATCH` dictionary. The packet is frozen and copies input
values into a tuple. Booleans, floats, out-of-range integers, invalid lengths,
invalid device IDs, unsupported versions and wrong magic are rejected with
`ValueError`. Channels can contain any eight int16 values: deterministic dummy
value validation belongs to the dummy-inference consumer, not the binary codec.

Wire format is `<2sBBIII8h`, exactly 32 bytes. All multibyte fields are little
endian. No native C/C++ structure layout, padding or host endianness is used.

| Offset | Length | Field |
| --- | --- | --- |
| 0 | 2 | ASCII `W7` |
| 2 | 1 | Version 1 |
| 3 | 1 | Device 1 or 2 |
| 4 | 4 | Random boot correlation ID |
| 8 | 4 | Submission sequence |
| 12 | 4 | Device uptime in milliseconds |
| 16 | 16 | Eight signed int16 values |

The committed `tests/fixtures/week7-golden.json` and two `.bin` files were
hand-specified before either implementation. Tests read the committed bytes;
there is no regeneration step using either codec. The normal vector uses device
2, boot `0x78563412`, sequence 42, uptime `0x01020304`, and channels
`[-958, -948, -938, -928, -918, -908, -898, -888]`. The boundary vector includes
uint32 maximum, int16 minimum/maximum, signed minus one, zero and byte boundaries.

SHA-256 digests of the binary fixtures:

- `week7-dummy.bin`: `ed2837186599f774e179012298cc487e2de4b0a3f60680e8a5b7323c9bb4c2ec`
- `week7-boundaries.bin`: `81efbf71bbb54d9fe17d436cfe7eeed3be38f54bdf36e02cc268b3323d72eae5`

## Verification performed

Commands ran from `D:\LetThemCook-worktrees\week7-stage-d-onward`.

1. RED: `D:\Anaconda\python.exe -m pytest tests/test_sensor.py -q --maxfail=2`.
   Both independent vector tests failed with `ModuleNotFoundError: No module
   named 'common'`, before production codec creation.
2. RED: the native firmware test failed to compile because `week7_packet.h` did
   not exist, before portable serializer/security-policy creation.
3. GREEN: `D:\Anaconda\python.exe -m pytest tests/test_sensor.py -q` produced
   **52 passed**, including native C++ compilation and execution using
   `D:\Perl\c\bin\g++.exe` with C++11, `-Wall -Wextra -Werror`.
   The native program emits both packets and Python compares each with the
   independent literal hex; C++ assertions additionally cover invalid output
   capacity/device/null inputs, dummy wrap boundaries, authentication downgrade
   rejection, subscription/connection gating, diagnostic opt-in, and MTU 34/35.
4. Build invocation:

   ```powershell
   $env:PLATFORMIO_BUILD_DIR = 'D:\LetThemCook-builds\packet-firmware-week7'
   & 'C:\Users\Yanjie Wang\.platformio\penv\Scripts\platformio.exe' run `
     --project-dir firmware/esp32 `
     -e firebeetle32 -e firebeetle32-unprotected-diagnostic
   ```

   The first compile identified that `BLEServer::getGattsIf()` is private in the
   installed Arduino API. Inspection confirmed that public custom GATTS callbacks
   receive the same interface ID. Firmware now captures successful registration
   and uses that ID in targeted notification submissions.

   The corrected build finished with **2 succeeded** in 30.225 seconds. Protected:
   RAM 39,116 bytes; flash 1,116,689 bytes (85.2%). Explicit diagnostic: RAM 39,108
   bytes; flash 1,115,757 bytes (85.1%). No firmware binary or build directory is
   written into the repository. The packet tests were rerun afterward and again
   reported **52 passed**. Scoped `git diff --check` succeeded; Git only printed
   its configured LF-to-CRLF conversion notices.

Installed build stack: PlatformIO Core 6.1.19; Espressif32 platform 7.1.0;
Arduino-ESP32 package `3.20017.241212+sha.dcc1105b` (Arduino 2.0.17); Xtensa GCC
8.4.0+2021r2-patch5. Library API behavior was checked against these installed
headers and source files, not assumed from a different release.

## Firmware behavior and security boundaries

Default environment `firebeetle32` is protected. The separate environment
`firebeetle32-unprotected-diagnostic` explicitly defines
`WEEK7_UNPROTECTED_DIAGNOSTIC=1` and reports that fact over serial. It is not valid
protected-link acceptance evidence. Both profiles retain the original counter
and MTU-probe UUIDs; sensor Notify UUID is
`6e1c0005-7a45-4dc4-b678-3f2d5a9c1001`. Device ID defaults to 1 and can be set to 2
with `WEEK7_DEVICE_ID=2`. A compile-time assertion rejects any other device ID.
The GATT service explicitly reserves 24 handles for four characteristics and
three CCCDs, avoiding the library's implicit default capacity.

Dummy generation is 10 Hz, `value[i] = (seq % 2000) - 1000 + 10*i`. Values have no
physical units or calibration. Samples are submitted only when authenticated,
subscribed and negotiated ATT MTU is at least 35. `sensorSequence` advances only
when `esp_ble_gatts_send_indicate(..., need_confirm=false)` returns `ESP_OK`.
This means accepted submission to the local Bluetooth stack, not proof of
delivery. No offline backlog is retained. Uptime captures the outage even if
sequence remains unchanged. Serial counters distinguish submissions, insufficient
MTU suppression, waiting-for-security suppression and submission errors.

The protected configuration uses checked calls for SC+MITM+bonding,
`ESP_IO_CAP_OUT`, 16-byte maximum key size, encryption/identity key distribution,
and `ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH`. Configuration errors stop setup
before advertising. IDF's header explicitly says SC-only acceptance requires
that final setting as well as the SC authentication bit. The Arduino
`setStaticPIN()` helper is not used because its implementation overwrites the
authentication mode with `SC_ONLY`.

The stack generates a fresh passkey for each pairing and invokes the display
callback. Its only application output is an interactive local serial line with
the prefix `PAIR LOCALLY: enter ` and six digits. **Do not capture raw pairing
serial output into files or evidence.** Arduino `CORE_DEBUG_LEVEL=0` also suppresses
the library's own INFO passkey logging. An unexpected remote keypad request
returns an invalid passkey; numeric-comparison confirmation is rejected because
this device has no confirmation input. There is no automatic downgrade.

Every Notify characteristic and CCCD requires encrypted MITM access; the MTU
control characteristic requires encrypted MITM writes. The application gate
requires a successful authentication callback for the current peer whose
`auth_mode` contains SC, MITM and bonding bits. It resets on connect/disconnect,
rejects downgrade/failure, and targets the single accepted connection instead of
broadcasting. Diagnostic-only mode is the sole explicit gate bypass. Safe serial
evidence includes `ble_security_complete success=1 auth_mode=13 approved=1
current_peer=1 reason=0`; no callback key material is logged.

For deliberate bond recovery, first disconnect the Windows client. Send
`erase-bonds` followed by newline over local serial. Firmware stops advertising,
rejects active-link erasure, enumerates/removes bond records, waits for IDF removal
completion callbacks and confirms `erase_bonds_complete remaining=0` before
advertising again. Remove the stale Windows bond and pair again. If a removal
fails, authentication and advertising stay closed with `restart_required=1`;
restart and deliberately retry. No bond is silently erased after a connection
failure.

Build/native-test success does not establish actual radio encryption, Windows
pairing support, bonded reconnect behavior, CCCD rejection on an unprotected
link, sensor delivery, bond erasure on NVS, or full protected E2E. Those require
the physical tests in the runbook and continuation report. BLE bonding is not an
application user authorization system, and this demo policy does not claim final
course-rubric security certification.
