# Let Them Cook (CG4002 B07): Communications and integration hand-off

**Readers:** olsonwangyj (called Yoz in the team), the Communications owner, and every agent that takes over this repository later.
**Purpose:** after reading it you know what the project is, how the Communications subsystem works, why it is designed this way, where it stands now, what must not be done, and what comes next.
**Last updated:** 2026-10-14 (change log in section 14).

---

## 0. How to use this document

1. Read sections 1 to 3 first (project, role, boundaries), then section 6 (current progress) and section 9 (things not to do). Read sections 4, 5 and 8 before changing Communications code. To find what a folder or file does, use the code map in section 12.
2. Which source wins: **code > this document > olsonwangyj's other documents > teammates' READMEs and documents**. Teammates' documents disagree with the code in places (see 4.9 and the detail chapters). When they conflict, trust the code and record the conflict in this document.
3. **Keeping the documents current is a rule. The owner set it on 2026-10-14 (`AGENTS.md` rules 7 and 8).** Every change to Communications code, and every change to what is deployed (boards, Ultra96 service, phone app, certificates), is not finished until the documents describe it, in the same piece of work. The documents are:
   - this hand-off document: always section 6 (progress) and section 14 (change log); section 12 (code map) when a file is added, moved, renamed or removed; section 7 when an interface changes; section 10 when the owner corrects an understanding;
   - the matching detail chapter in `docs/handoff-details/`;
   - `docs/co-protocol-v2.md` when a wire format, message, constant or limit changes.

   Sections 6 and 14 are also updated when an interface is agreed with a teammate or the owner corrects an understanding, even when no code changes. After a change, read the affected passages and correct every statement the change made untrue. Formal documents (this document, its detail chapters, specifications, quickstarts, runbooks) are written in English. Chat with the owner may be in Chinese.
4. Finer detail, down to each constant, each status string and the source of each design decision, is in the six chapters under `docs/handoff-details/` (index in 12.5). This document on its own contains every point needed to take over.
5. Historical material is in `docs/archive/`. Those files keep the names of their time (`week7`, `W7`) and are not updated. Use them only to find where a design decision came from.

---

## 1. One-minute overview

- **Project:** NUS CG4002 capstone, team B07, "Let Them Cook". A single-player AR cooking game, similar to Overcooked. The player wears two sensor gloves and makes gestures. A model on the Ultra96 FPGA board recognises the gestures. The results drive a Unity AR game on an iPhone.
- **olsonwangyj's two roles:** owner of the Communications subsystem (the main technical work), and since 2026-10-13 also integration lead. Integration V1 must run by **2026-10-20 (Tuesday)**. The final version is due around Week 13.
- **What Communications does:** it sends each module's data out and makes sure the next module receives it accurately. The chain glove → laptop → Ultra96 → iPhone has run end to end on real hardware with dummy data, and the evidence is kept.
- **Three interfaces not yet connected:** the real glove sensor module (Siqiang), the model's entry and exit on the board (Wen Ree), and the game script that calls the Communications bridge (Jie Ling).
- **The two most urgent things:** first, the server certificate deployed to the board in September expired on 2026-10-06 15:11:29 UTC. That date was read from the laptop's copy of the same certificate. Whether the board's certificate was replaced later has not been checked. Renew the certificate before redeploying (section 6.3). Second, the three teammates' interfaces must be settled soon (section 7).

---

## 2. What the project is

### 2.1 Target form

```text
Two gloves (each: one FireBeetle ESP32 + IMU + 2 flex sensors)
   │  each glove: about 50 samples per second, 11 values per sample
   ▼
Windows laptop (relay)
   │  SSH tunnel through the NUS jump host
   ▼
Ultra96 FPGA board: gesture model (11 values from each of the two gloves × 50 time steps = a 50×22 window → 6 gesture classes)
   │  recognition results
   ▼
Unity AR game on the iPhone (chop, wash, pick up, put down, throw, extinguish fire)
```

Communications owns every arrow in the diagram. What happens inside the box at each end of an arrow is decided by that box's owner.

### 2.2 Team and code ownership

| Person | GitHub | Owns | Repository paths |
|---|---|---|---|
| Yoz (the Communications owner) | `olsonwangyj` | Communications; integration lead | `firmware/` `common/` `laptop/` `ultra96/` `phone/` `ios-visualizer/` `tests/` `tools/` `demo.py` `flash.py` `requirements-dev.txt` `docs/` `AGENTS.md` `CLAUDE.md` |
| Siqiang | `siqiangz` | Glove hardware and sensors | `hardware/` |
| Wen Ree | `Wrooi` | AI model and FPGA | `src/` `models/` `data/` `reports/` `fpga/` `export_fpga_reference.py` `requirements.txt` |
| Jie Ling | `gohjieling834` | Unity AR game | `vis/` |

Teammates' paths are **read-only**. The full rules are in `AGENTS.md` at the repository root.

### 2.3 State of each subsystem (2026-10-14, per the code)

**Gloves (Siqiang, `hardware/`)**

- The reference firmware is `hardware/gloves/29_sept/imu_v7.ino`. It has its own `setup()`/`loop()` and calibrates the gyroscope at start-up.
- Each sample is 11 floats in the order `ax, ay, az, gx, gy, gz, yaw, pitch, roll, flex1, flex2`: acceleration (g, gravity removed, range ±2 g), angular rate (°/s, bias removed, range ±250 °/s), Euler angles (degrees), and two flex values (12-bit ADC divided by 4095, range 0.0 to 1.0).
- Hardware used: I2C SDA 21 / SCL 22 / 400 kHz; ADC pins 34 and 35.
- Output is CSV text over **Bluetooth Classic serial** (`BluetoothSerial`), at about 50 Hz. The repository has three sketch variants. They output 11, 12 and 13 fields.
- It **cannot be linked with the Communications firmware as it is**: both have their own `setup()`/`loop()`, and the Communications firmware uses BLE, not Bluetooth Classic.

**Model and FPGA (Wen Ree, `src/` `models/` `fpga/`)**

- The model is a CNN. Its input is a 50×22 window: 50 time steps, and each step is 11 left-glove values plus 11 right-glove values. Its output is 6 classes. The classes are in `models/class_names.json`: `PICKUPHOLD`, `PLACEDOWN`, `CHOP`, `WASH`, `THROW`, `FIREEXT`. Inputs are not normalised.
- `src/live_inference.py` currently reads data itself from two hard-coded Windows serial ports, `COM3` and `COM4`, at 115200 baud, exactly 11 values per line, and prints predictions on the laptop. The confidence threshold is 0.70. **It has no entry point that the board service can call.**
- The FPGA side (`fpga/`) is currently a test module plus the first convolution layer. `fpga/README_FPGA_PYNQ.md` says that loading the overlay needs `sudo` and a different interpreter.
- The owner once reproduced the forward pass with NumPy. All 30 golden outputs matched. Converting the 11 values to int16 with the scale factors in 4.2 and back did not change the predictions. This was only a Communications-side check that fixed-point transport does not affect the model. **How inference is implemented is Wen Ree's business.**

**Game (Jie Ling, `vis/`)**

- An iOS AR project in Unity 6000.5.10f1. The action entry points are `OnSelectPressed`, `OnGrabPressed`, `OnDropPressed`, `OnChopPressed` and `OnWashPressed`.
- `vis/Assets/Scripts/Network/TlsDataReceiver.cs` is a TLS server that listens on port 5005 on the phone and only displays the text it receives. `vis/README.md` describes it the same way. **This direction is the opposite of the NUS network model** (nothing can connect in to the phone). No Communications code connects to 5005.
- `vis/Assets/Scripts` has no code yet that calls the Communications bridge (`CommsStart` and the others). The game logic has no network input.

**Communications (the owner)**

- The whole chain runs on real hardware with dummy data: two ESP32 boards → laptop → Ultra96 → iPhone. Details are in section 4; measured data in 6.1.
- The firmware sends dummy data and does not read sensors. The board service does not call the model; it picks a random dummy label itself. The iPhone only displays results as text and triggers no game action. These three places are the three interfaces to connect with teammates.

### 2.4 Timeline

| Date | Event |
|---|---|
| From 2026-09-06 | Communications Week 7 design and implementation |
| 2026-09-19 to 09-28 | Two-board hardware tests, iPhone tests, v2 protocol and control features go live |
| 2026-10-01 | Last recorded full-chain capture on hardware |
| 2026-10-06 | The server certificate deployed to the board in September expires (date read from the laptop's copy; the board's copy has not been checked) |
| 2026-10-08 | Marker changed from `W7` to `LC` and session from `week7-demo` to `ltc-comms` (compatibility kept at the time) |
| 2026-10-13 | olsonwangyj becomes integration lead; PR #15 merged into the team main branch |
| 2026-10-14 | Week 7 compatibility code removed; documents reorganised; this hand-off document written |
| **2026-10-20** | **Integration V1 deadline** |
| Around Week 13 | Final version |

The team's expectations are on the "Integration formulation" page of the team Google document: <https://docs.google.com/document/d/1P3-7mIIms9bHz4wJCk0NqZe7pYlBCBmjCKYXMzWKqlc> (append `/mobilebasic` to the URL to read it without signing in).

---

## 3. The owner's role and boundaries

olsonwangyj's own words (2026-10-14):

> I'm responsible for leading the integration, while my main technical responsibility is the communications subsystem. Each teammate remains responsible for the quality and performance of their own component. My role is to ensure that the components communicate correctly and to coordinate the team's work toward a functioning integrated system.

Further clarification the same day: as Communications owner, the owner is responsible only for sending each module's data out and making sure the next module receives it accurately. Nothing else is the owner's. How teammates implement their own parts is not the owner's concern.

**Communications owns:**

- In the firmware: packing, BLE sending, pairing security and connection management. After the real sensor module is merged in, the owner still writes this firmware.
- On the laptop: BLE reception, queueing, conversion to network messages, delivery to the board through the SSH tunnel, and ACK checking.
- On the board: receiving samples, de-duplication, replying with ACKs, and pushing results to the subscribed phone.
- On the iPhone: the SSH/TLS client, result validation, and the three C functions that hand results to Unity.
- Identity, counters and evidence for every segment.

**Not Communications (do not list these as the owner's tasks, and do not ask about them on the owner's behalf):**

- Sensor capture algorithm, calibration, sensor faults → Siqiang.
- Pairing left and right glove samples, building 50×22 windows, deciding whether a gesture or idle happened, model accuracy and speed → Wen Ree.
- Mapping labels to game actions, cooldowns and repeats, any script in `vis/` → Jie Ling.

**What leading integration means:** defining the cross-module interfaces clearly (format, rate, labels, transport, timing, who connects to whom) and coordinating who delivers what on which day. It does not mean taking on the quality of teammates' components.

---

## 4. The Communications subsystem in detail

### 4.1 The full chain

```text
Left  FireBeetle ESP32 (device_id=1) ─┐ BLE GATT notifications, one 32-byte packet per sample
Right FireBeetle ESP32 (device_id=2) ─┴──────────► Windows laptop (BLE central)

Laptop ─TCP→ local 127.0.0.1:18889 ─SSH -L→ stujump:22 → Ultra96:22 → on-board 127.0.0.1:8888 (ingest service)
        inside TLS: SENSOR_BATCH →        ← INGEST_ACK

iPhone ─in-app SSH→ stujump:22 → Ultra96:22 → on-board 127.0.0.1:9999 (result gateway)
        inside TLS: SUBSCRIBE →   ← SUBSCRIBED   ← GESTURE_RESULT

Inside the iPhone: Swift client ─three C functions, polled every frame by the Unity main thread→ Unity
```

| Hop | Who initiates, who listens | Transport | Protection |
|---|---|---|---|
| ESP32 ↔ laptop | The laptop connects to the ESP32. Each board accepts one connection at a time | BLE GATT. Samples on the notify characteristic `6e1c0005`; control write `6e1c0007`, response `6e1c0008`; source statistics read `6e1c0006` | LE Secure Connections + MITM + bond. Characteristics and CCCDs all require encryption with authentication. The firmware sends no notification before authentication completes |
| Laptop → on-board 8888 | The laptop connects to its local forwarded port; OpenSSH makes two hops to the board's loopback | TCP → SSH local forward → TLS → 4-byte big-endian length + JSON | Both SSH hops check host keys strictly. TLS ≥ 1.2, verifying the CA and the host name `ultra96.week7.internal` |
| iPhone → on-board 9999 | SwiftNIO SSH inside the app connects to the jump host, opens `direct-tcpip` to the board's port 22, then `direct-tcpip` to the board's loopback. **The phone listens on no port** | Nested SSH channels → TLS → the same framing | Both SSH host public keys and the CA fingerprint are pinned in the app source. Host name and validity period are checked |
| Swift → Unity | The Unity main thread calls a C function every frame | In-process C ABI | Does not cross the network |

Key points:

- **Every connection dials out.** The two board services bind only to `127.0.0.1` and can be reached only through SSH tunnels. Neither the laptop nor the phone accepts incoming connections.
- **Input and results use two unrelated connections.** ACKs go back only to the laptop. Results are pushed only to the subscribed phone. The laptop does not forward results.
- The VPN only makes the network reachable; the code has no VPN logic. **With the VPN on, traffic still goes through `stujump`.** V1 keeps the jump-host route.

### 4.2 Data formats

**BLE sensor packet: 32 bytes, little-endian, Python format `<2sBBIII8h`**

| Offset | Length | Field | Value |
|---|---|---|---|
| 0 | 2 | Marker | ASCII `LC` (`4C 43`). Since 2026-10-14 this is the only marker accepted |
| 2 | 1 | Version | 2 = any valid int16 (default; values taken from the dummy-data table); 1 = deterministic formula dummy data (build switch `COMMS_LEGACY_DUMMY=1`) |
| 3 | 1 | `device_id` | 1 = left, 2 = right (compile-time constant) |
| 4 | 4 | `boot_id` | A random number drawn once per power-up |
| 8 | 4 | `seq` | Starts at 0 on each power-up and adds 1 per sample. A number is not reused after a failed submission |
| 12 | 4 | `uptime_ms` | This board's own `millis()`. The two boards are not synchronised |
| 16 | 16 | 8 × int16 | Currently dummy data |

A 32-byte notification needs ATT MTU ≥ 35. The measured negotiated MTU is 517.

**Source statistics: 24 bytes, `<4sB3xIIII`**: marker `LCS1`, `device_id`, `boot_id`, `next_seq`, `submitted` (successful submissions), `failures` (failed submissions). The laptop reads them once before subscribing and once after stopping. They are used for the reconciliation "generated on the board = received by the laptop = acknowledged by the Ultra96".

**BLE control frame: 14-byte header, marker `B7`** (the team number B07, not Week 7): version 1, opcode, `device_id`, status, `id`, `offset`, followed by at most 180 bytes of payload. Opcodes: command (1), rate (2, 1 to 200 Hz), file begin/chunk/end/abort (`0x10` to `0x13`, at most 65536 bytes, checked with SHA-256). The control channel needs MTU ≥ 64.

**Network frame:** 4-byte big-endian length + a strict UTF-8 JSON object, with a body of 1 to 16384 bytes. The field set must match exactly. **There is no error message; on an error the connection is closed.**

| `type` | On-board port | Direction | Fields besides `v`, `type`, `session_id` |
|---|---|---|---|
| `SENSOR_BATCH` | 8888 | laptop → board | `device_id`, `boot_id`, `seq`, `uptime_ms`, `values` (8 int16); v2 adds `request_id` |
| `INGEST_ACK` | 8888 | board → laptop | `device_id`, `boot_id`, `seq`, `status` (`accepted` or `duplicate`); v2 adds `request_id` |
| `SUBSCRIBE` | 9999 | phone → board | None (only `v=1` allowed) |
| `SUBSCRIBED` | 9999 | board → phone | None |
| `GESTURE_RESULT` | 9999 | board → phone | `device_id`, `boot_id`, `seq`, `result_id`, `gesture`, `confidence`; v2 adds `request_id` |

- `session_id` defaults to `ltc-comms` everywhere. Laptop, board service and phone must agree. On a mismatch the board closes the connection. It is configuration, not a password.
- `request_id`: in v2 the key must be present. It is `null` for ordinary samples. For keyboard commands it is 1 to 4294967295 and equals `seq`.
- `result_id` is `device_id:boot_id:seq`. Results of commands get the prefix `cmd:`. The phone uses it to de-duplicate.

**Real glove data packet (decided, not yet implemented): 38 bytes = the existing 16-byte header + 11 × int16**

| Index | Field | Unit delivered by the sensor module | Scale | int16 range |
|---|---|---|---|---|
| 0–2 | `ax` `ay` `az` | g | ×10000 | ±3.2767 g |
| 3–5 | `gx` `gy` `gz` | °/s | ×100 | ±327.67 °/s |
| 6–8 | `yaw` `pitch` `roll` | degrees | ×100 | ±327.67° |
| 9–10 | `flex1` `flex2` | 0.0–1.0 | ×10000 | maximum 3.2767 |

A 38-byte notification needs ATT MTU ≥ 41. The application-layer byte rate is 38 × 50 Hz × 2 boards = 30.4 kbps. 32-byte packets were measured clean at 33.8 kbps. 38-byte packets have not been measured at all.

### 4.3 Firmware (`firmware/esp32/`)

- PlatformIO + Arduino framework, board `firebeetle32`. `platformio.ini` has four build environments:
  - the default `firebeetle32` (`default_envs`; protected; ID 1, because `COMMS_DEVICE_ID` defaults to 1). `platformio run` without `-e` builds it, so flashing it onto the right board makes that board ID 1;
  - `firebeetle32-left` (ID 1);
  - `firebeetle32-right` (ID 2);
  - the unprotected diagnostic environment `firebeetle32-unprotected-diagnostic`, which must be named explicitly.

  The verified combination is Espressif32 7.1.0 + Arduino-ESP32 2.0.17. `platformio.ini` does not pin the versions.
- Advertised name `LTC-COMMS`, the same on both boards. They are told apart by Bluetooth address and by the `device_id` in the packet. Service UUID `6e1c0001-7a45-4dc4-b678-3f2d5a9c1001`, with 7 characteristics.
- Security: LE Secure Connections + MITM + bond. The board can only display (DisplayOnly). The 6-digit passkey is printed only on the local serial port, and the operator types it on Windows. The application adds one more gate: notifications are sent only when all three authentication-mode bits (SC, MITM, bond) are set.
- Each pass of the main loop: read serial commands → check the send tick for the current rate → only when authenticated, subscribed and the MTU is large enough: allocate `seq`, pack, submit the notification, record success or failure → handle at most one control request per pass → print `alive` and `comms_stats` once a second.
- **Samples are produced in the block of `firmware/esp32/src/main.cpp` that calls `serializeFixturePacket` (about lines 503 to 510).** The real sensor module's "read one sample" connects here.
- While disconnected, no samples are produced, `seq` does not advance, and there is no offline buffer. The rate is kept across a disconnect; only a reboot restores the default 10 Hz.
- There is only one serial command: `erase-bonds` (clear bonds, used to recover pairing).
- The policy logic is all in portable C++11 headers (`include/comms_*.h`). They compile and run as host tests without flashing a board (`test/host_*.cpp`). pytest compiles them with `g++` or `clang++`, whichever is on PATH, and skips them when neither is found.

**`flash.py`:** it first generates the dummy-data header and builds the left and right firmware, then prompts you to plug in the boards. **The first board plugged in is flashed as LEFT (ID 1); the second as RIGHT (ID 2).** It reads the factory MAC, adds 2 to get the Bluetooth address, and writes that into `.comms-local/boards.json`. Other uses: `--ports`, `--boards`, `--pair [left|right|both]`, `--monitor COMx`. It works only on Windows.

### 4.4 Laptop (`laptop/`, `demo.py`, `tools/`)

- `laptop/bridge.py` is the full path for one glove. `laptop/dual_bridge.py` runs two uncoupled `Bridge` instances at the same time, and `demo.py` calls it. **Each board has its own BLE connection, queue and TLS connection.** One board stalling does not affect the other.
- Per board: scan (by service UUID and address, 8 s limit) → connect (without the cached GATT table, 20 s limit) → confirm MTU ≥ 35 → confirm that the Windows bond is "encrypted and authenticated" → read the starting source statistics → subscribe to notifications. Both boards must be ready within 30 s.
- The BLE callback records the arrival time and copies the bytes into the board's bounded queue (64 entries; when full, the oldest is dropped). It also decodes the packet once to count goodput, hands a `sensor` or `sensor_invalid` record to the evidence thread, and updates the callback and silence counters. It does no network operations.
- Writer task: decode → check `device_id`, sequence number and connection generation → **drop samples that waited on the laptop for more than 2 s** → write `SENSOR_BATCH` → check each `INGEST_ACK` in send order. At most 32 frames are in flight at once (ACK window).
- **No retransmission.** When TLS drops, a write times out, or an ACK times out or does not match, that TLS connection is discarded. Frames already attempted are counted as ambiguous (`ambiguous_dropped`) and are not resent. The bridge reconnects after back-off (from 0.5 s, doubling, up to 5 s).
- Tail handling at shutdown: turn notifications off on the remote side while keeping the local callback, read the source statistics once, wait for the last packets to arrive, then read again to confirm nothing changed. This way losses at the start and end are reconciled too.
- At the end it writes `report.json` (a placeholder first, then an atomic replace) and `packets.jsonl`. It prints `CAPTURE PASSED` only when everything matches.
- Pairing uses a custom WinRT flow (`laptop/windows_pairing.py`), because Bleak's own `pair()` may lower the protection level. **The laptop side supports only Windows.**
- Control channel: keyboard `1`/`2` send commands, `--rate` sets the rate, `--file` transfers a file. Commands use a separate TLS connection and are not retried after a timeout.

The five `demo.py` subcommands:

| Command | What it does |
|---|---|
| `python demo.py tunnel` | Opens the two-hop SSH local forward: local `127.0.0.1:18889` → on-board `127.0.0.1:8888`. Keep this terminal open |
| `python demo.py run` | Captures both boards for 60 s (default 10 Hz) and writes the report and evidence to `.comms-local/` |
| `python demo.py live` | Like `run`, but captures for 120 s by default and enables keyboard commands. Needs an interactive terminal |
| `python demo.py report [path]` | Re-checks the latest capture or the one given |
| `python demo.py service [--start]` | Inspects the board service over SSH. `--start` starts it when both ports are free |

### 4.5 Ultra96 service (`ultra96/`)

- A standard-library-only asyncio process: `/usr/bin/python3 -u -m ultra96.server --cert … --key … [--session-id ltc-comms] [--ingest-port 8888] [--gateway-port 9999] [--event-log-dir <new directory>]`. It runs as an ordinary user. It is not a system service, has no automatic restart, and does not use sudo (the board is shared).
- How it was started decides what keeps it alive:
  - Started with `demo.py service --start`, it is the foreground process of that SSH session (`ssh -tt`) and exits when that terminal goes away.
  - The process recorded on the board (2026-09-28) was not started that way. The untracked script `.week7-local/co_deploy.py` launched it in the background with `subprocess.Popen(..., start_new_session=True)`. Its output goes to `BOARD_ROOT/evidence/`, and its PID is in `BOARD_ROOT/evidence/server.pid`. It does not depend on any SSH session and may still be running. Look for it when redeploying (6.3, step 2).
- Both TLS listeners bind only to `127.0.0.1`. The service never dials out. The two ports together accept at most 8 concurrent connections.
- **Ingest port 8888:** read the frame → check fields and session → de-duplicate → for a new sample, generate one result and, if there is a subscriber, put it in the result queue → reply `INGEST_ACK`. A duplicate sample gets only `duplicate` and produces no result. An idle ingest connection is closed after 5 s.
- **Gateway port 9999:** a valid `SUBSCRIBE` registers that connection as the current subscriber and gets `SUBSCRIBED` back. **There is one subscriber at a time; a newcomer replaces the existing one.** The result queue holds 32 entries; when full, the oldest is dropped. A result that has been in the queue for 2 s is dropped. With no subscriber, results are dropped at once and never sent later.
- **Results are currently fake.** They are generated at `ultra96/server.py:264-267`: v2 picks one of `REST`, `FIST`, `OPEN`, `POINT` at random, with confidence fixed at 1.0. **This is where the model interface will connect.**
- De-duplication and replay protection live only in memory. For each `(device_id, boot_id)`, v2 keeps a sequence high-water mark that only rises, plus the latest 4096 fingerprints. One process lifetime allows at most 128 `(device_id, boot_id)` pairs and 4096 commands. After that the service must be restarted.
- The optional event log (`--event-log-dir`) is written on a background thread, capped at 50 MiB. Its `result_write_complete` only says that the board wrote the result into the connection. **It does not say that the phone received it.**
- Certificates are generated by `tools/generate_comms_pki.py`: a CA (365 days) and a server certificate (**30 days**; CN and SAN are both `ultra96.week7.internal`). The server loads only the server certificate and key. Clients hold only the CA certificate. The CA private key never leaves the machine that generated it. Only the server is authenticated; there are no client certificates (SSH handles access control).

### 4.6 Phone client and the Week 7 receiver (`ios-visualizer/`, `phone/`)

**The current phone client is the Swift package `ios-visualizer/CommsNative`.**

- The user taps `Communications Connect` and enters the board's and the jump host's user names and passwords in a form. The first time, the CA certificate must also be imported. The app then builds: TCP to `stujump:22` → SSH (compare against the pinned host public key; password authentication) → `direct-tcpip` to the board's port 22 → a second SSH layer → `direct-tcpip` to `127.0.0.1:9999` → TLS (check CA, host name, validity) → send `SUBSCRIBE` → receive `SUBSCRIBED`. The whole process is limited to 10 s.
- After that it only receives results: unframe, validate, de-duplicate by `result_id` (latest 4096), add 1 to `Received`, and **keep only the latest result**. After 2 s without a new result the displayed label is cleared; the count stays. After subscribing there is no idle limit. Only a frame that has started but not finished is given 5 s.
- Errors fall into two classes. Network errors (connection dropped, timeout) trigger automatic back-off, reconnect and resubscribe. Authentication, trust and protocol errors (wrong password, host key mismatch, expired certificate, a result that fails validation) **end the session at once: no retry, and the passwords are cleared**. The user must enter the passwords again to reconnect.
- Passwords are kept only in memory. **As soon as the app stops being active (screen lock, going to the background, pulling down Control Center or Notification Center, an incoming call), it disconnects at once and clears the passwords.** Back in the foreground the user must connect again by hand, and the count starts from 0.
- Host names, both SSH host public keys, the CA fingerprint and the session ID are compiled into the app. Changing the board, the CA or the session ID means changing the source, rebuilding and reinstalling.

**The three C functions for Unity (`Sources/CommsBridge/DisplayMailbox.swift`):**

| Function | Semantics |
|---|---|
| `void CommsStart(void)` | Installs the button and the foreground/background notifications. **Does not start a connection**; only the user tapping the button and entering passwords starts one. Call it once |
| `int32_t CommsCopyDisplay(char* buffer, int32_t capacity)` | Takes one snapshot and builds four lines of UTF-8 text. If the text differs from what was last delivered and fits, it writes the text into the buffer (with a terminating 0) and returns the byte count. Otherwise it returns 0 and writes nothing. It never returns a negative number |
| `void CommsStop(void)` | The status changes to `Stopped` at once; everything is removed and the passwords are cleared. Call it only when the app truly stops using Communications |

The four lines of text:

```text
Communications • DUMMY inference
<status>
<gesture>  |  <result_id>  |  confidence 1.0        (when there is no new result, this line is No live result)
Received: <N>
```

Rules for the caller: only one poller; poll on the main thread every frame; use a 2048-byte buffer; decode as UTF-8; **use `result_id` to decide whether a result is new, not the label text**; the bridge gives only the latest result, so do not assume that every result is seen; do not call `CommsStop` on a scene change or when going to the background.

**What "Week 7 receiver" means exactly (confirmed by the owner):** the `CommsNative` Swift client on the iPhone, plus the bridge in the Unity export that calls `Week7Start` / `Week7CopyDisplay` / `Week7Stop`. It is the receiver made temporarily for the Week 7 demo:

- The Unity source project was not available at the time, so it patches the generated code of one specific Unity export (`ios-visualizer/xcode-export/`, fork only). `ios-visualizer/tools/patch_export.py` rewrites four methods of Jie Ling's `TlsDataReceiver`: `Start` calls `Week7Start()`; `ListenLoop` is emptied, so the 5005 listener no longer runs; `Update` calls `Week7CopyDisplay(buffer, 2048)` every frame and writes the text into the label; `OnDestroy` calls `Week7Stop()`. `configure_xcode.py` links `CommsNative` into `UnityFramework`.
- The patch is locked to file hashes and accepts only that one export. It refuses an export made again from `vis/`.
- **It only displays text and has never triggered a game action.**
- **The `week7` names inside it are not touched**: the three `Week7*` wrapper functions, the old iOS data directory `Application Support/Week7`, the app display name `Week 7 Visualizer`, and the comments and temporary-file prefixes in the patch scripts.

**What is under `phone/` is for reference and diagnostics. It is not the receiver deployed on the iPhone:** `phone/receiver.py` (Python, Termux/iSH), `phone/unity/CommsPhoneCore.cs` and `CommsPhoneReceiver.cs` (Android reference; the phone must open its own SSH local forward to `127.0.0.1:19999`), and `phone/ish_control.py` (temporary maintenance script for the iSH route).

### 4.7 Evidence levels (none replaces another)

| Level | Evidence | Proves | Does not prove |
|---|---|---|---|
| 1 | Source statistics on the board: `submitted` | The Bluetooth stack accepted the notification submission | That the laptop received it |
| 2 | Laptop counts. `callback_received` is the BLE callback count; the progress line prints it as `received=`. The report's per-board `received` counts packets the writer task dequeued and processed. The two differ when the queue drops packets | `callback_received`: the BLE callback got the bytes. `received`: the writer task took them from the queue | That the board received it |
| 3 | `INGEST_ACK` | The board service validated and accepted this input | That the phone received it; that the model ran inference |
| 4 | Board event `result_write_complete` | The board wrote the result into the connection | That the phone validated or displayed it |
| 5 | `Received: N` on the phone screen (read by a person) | Within this connection the phone accepted N distinct results | Individual IDs; that a game action was triggered |

The `CAPTURE PASSED` printed by `demo.py` is level 3. The phone sends no application-level acknowledgement and keeps no per-result record. For the phone level, a person compares the increase in `Received` with `Phone expected increase`.

### 4.8 Trust material

| Material | Who holds it | Notes |
|---|---|---|
| CA private key `ca-key.pem` | Only the owner's laptop (outside the repository) | Never on the board, never on the phone |
| CA certificate `ca-cert.pem` | Laptop (`--ca`); iPhone (imported) | The current CA's SHA-256 is `4dfba4905c171e68c3623dbc952154149076ed89004b85d475e858cc550760ec`, valid until 2027-09-06. This fingerprint is pinned in `Configuration.swift` |
| Server certificate and key | `tls/` in the Ultra96 deployment directory | **The certificate deployed in September expired on 2026-10-06.** The date was read from the laptop's copy; whether the board's certificate was replaced later has not been checked. See 6.3 |
| Both SSH host public keys | The laptop's `known_hosts`; the iPhone source | No trust on first use |
| SSH passwords | Only the operator | The laptop enters them at the OpenSSH prompt. The phone keeps them only in memory |
| BLE bond keys | One copy each on the ESP32 and on Windows | The passkey is shown only on the board's serial port |

### 4.9 Where documents and code disagree (the code wins)

- `vis/README.md` says "the phone runs a TLS server on port 5005". The direction is the opposite of the network model. In the Week 7 export this code has been emptied.
- The archived architecture draft says `stfjump`; the code and the site use `stujump`. Its example port is 8888; the code uses 18888 and 18889.
- In `docs/week7-runbook.md`, `tools.generate_week7_pki`, `tools.rehearse_week7` and `Week7Server` have since been renamed `tools.generate_comms_pki`, `tools.rehearse_comms` and `CommsServer`.
- The archived iOS design specification says "wait 30 s for the first result". The current code has no idle limit after subscribing.

---

## 5. Why it is designed this way

1. **Every connection dials out; board services bind only to loopback and are reached only through SSH.** Under the NUS firewall rules, the Ultra96 can be reached from outside only through the VPN and the jump host `stujump`, using SSH (port 22). The laptop and the phone are on no allow-list, so nobody can connect in to them. These approaches were therefore rejected: the phone as a server waiting for incoming connections (the teammate's original 5005 approach); the laptop connecting directly to the phone; opening the board's 8888/9999 to the outside; SSH reverse forwarding; the laptop forwarding results.
2. **The phone connects to the board itself, not through the laptop.** The phone owns its whole route, so results do not depend on the laptop being online. The laptop is only an input relay.
3. **TLS inside SSH, with a fixed host name.** SSH gets the connection there. TLS, with a dedicated CA and a fixed name, confirms that the connection reaches the right service, even though TCP connects to `127.0.0.1`. There are no mutual certificates, because SSH has already authenticated the client.
4. **No retransmission, no replay, bounded queues, 2 s freshness.** A stale gesture delivered late would be taken as a new game action. So every segment drops data rather than send old data. Queues are bounded, so memory cannot grow without limit during a fault.
5. **The `device_id` + `boot_id` + `seq` triple; the sequence number is assigned before submission; separate read-only source statistics.** After a board reboot the sequence restarts at zero without being confused with old data. A sample whose submission failed still uses a sequence number, so a loss is not hidden. Losses at the start and end can be reconciled.
6. **ACK window 32.** On the remote route a single ACK took up to 2.375 s. With stop-and-wait per frame, later samples exceeded the 2 s freshness and were dropped (two 600 s tests dropped 1 and 33). With window 32, a 600 s test had every sample acknowledged. The freshness limit itself was not relaxed.
7. **One independent channel per board.** When one board loses power or stalls, the other continues. Measured during a power-loss recovery: the healthy board had 111 packets and 111 ACKs.
8. **BLE uses Secure Connections + passkey + bond, with no extra application-layer encryption.** The authenticated BLE link plus the SSH/TLS after it covers the whole path. A home-made key protocol on top would only add something unreviewed.
9. **One subscriber; a newcomer replaces the old one.** V1 has only one phone, and the result stream always has exactly one owner.
10. **Length prefix + strict JSON; close the connection on error.** TCP has no message boundaries. After a bad frame there is no reliable way to resynchronise.
11. **Host public keys and the CA fingerprint are pinned in the phone source.** The phone has no step where a person checks `known_hosts`, so there is no trust on first use. The cost: changing the board or the CA means rebuilding the app.
12. **Passwords only in memory; leaving the foreground disconnects.** The route on site uses password authentication. Nothing is written to disk, so there is no credential file to manage. It also does not rely on unverified iOS background survival.
13. **One process on the board, standard library only, no sudo, no system service.** The board is shared; do not disturb other people's environment. The start script starts the service only when the ports are free and never stops or kills an existing process.
14. **Graded evidence.** ACKs and phone results use two independent connections, and there has been a case where all ACKs arrived while the phone received fewer results. So each evidence level speaks only for its own segment.
15. **BLE rather than Bluetooth Classic.** This choice was made and tested long ago: the 50 Hz and 70 Hz settings were both measured clean on 2026-09-28.

The source of each decision (the entry numbers in the archived design record) is in the design-reason part of each chapter in `docs/handoff-details/`.

---

## 6. Where things stand (2026-10-14)

### 6.1 Done and verified on hardware (all with 32-byte dummy data)

| Item | Result | Date |
|---|---|---|
| Two-board baseline at 10 Hz | Left 652 and right 653, all ACKed; ATT MTU 517 | 09-28 |
| Rate sweep (per board) | 10, 25, 50, 60, 65 and 70 Hz pass; 75 Hz and 100 Hz fail. At 50 Hz, measured about 49.98 packets/s; the 70 Hz setting measured about 66 packets/s, 33.8 kbps for both boards together | 09-28 |
| ACK window 32 | 600 s: 6005 / 6001, all acknowledged | 09-19 |
| Single-board power-loss recovery | Reconnected in 11 s; the other board was unaffected; the first packet after recovery got no ACK (1 ambiguous) | 09-28 |
| iPhone count | 1202 in 60 s, 12003 in 600 s, and others, all as expected | 09-21 |
| File transfer | 4096 bytes, once per board, digests match | 09-28 |
| Firmware after the compatibility removal | Left board flashed with the current firmware; local loopback 100/100 packets; another run of 349 packets with source reconciliation passed, a rate change to 20 Hz confirmed, and all 3 commands round-tripped | 10-14 |

Unexplained history: on 2026-09-21, in one 60 s run, the phone received only 1094/1203 results (109 missing). The cause is unknown. Range testing has never been done.

### 6.2 Code and branch state

- Team repository `upstream` = <https://github.com/B07-CG4002/Let-Them-Cook>. Its main branch is at `ec398b6` (PR #15 merged).
- olsonwangyj's fork `origin` = <https://github.com/olsonwangyj/Let-Them-Cook>. Local `main` has content beyond the team main branch that exists only on the fork: `docs/`, `ios-visualizer/xcode-export/`, `AGENTS.md`, `CLAUDE.md`, and several tools.
- **The 2026-10-14 cleanup (merged into local `main`):** it removed compatibility with the old Week 7 version. Now only `LC` packets and `LCS1` statistics are accepted. The `.week7-local` directory is no longer read. The session for `demo.py service --start` defaults to `ltc-comms`, like `run`/`live`, and `--session-id` was added.
  - The team-facing branch `comms/remove-week7-legacy` is on the fork at `30e85a6` and also carries the certificate-renewal commit. Its tests: 551 passed, 3 skipped.
  - Local `main` (which also has the fork-only tests): 569 passed, 3 skipped.
  - Pull request link: <https://github.com/B07-CG4002/Let-Them-Cook/compare/main...olsonwangyj:Let-Them-Cook:comms/remove-week7-legacy>. The pull request is waiting for the owner to open it. Agents do not push to `upstream`.
- **Certificate renewal option (branch `comms/renew-server-certificate`, merged into local `main` and included in `comms/remove-week7-legacy`):** `tools/generate_comms_pki.py` gains `--renew-server-from <original CA directory>`, which uses the existing CA to issue only a new server certificate.
- Week 7 names **deliberately kept** in the cleanup:

| Name kept | Where | Why it is not changed |
|---|---|---|
| TLS host name `ultra96.week7.internal` | `common/tls.py`, the certificate tool, every receiver | It is written into the server certificate and every client verifies it. Renaming it means a new certificate and reinstalling the app |
| `Week7Start/CopyDisplay/Stop`, reading the old iOS directory, the app display name, and similar | `ios-visualizer/` | Part of the Week 7 receiver; the owner said explicitly not to touch them |
| Board deployment directory `/var/tmp/cg4002-week7-…-20260907` | `tools/demo_service.py` | A directory that really exists on the board |
| Default CA path `~/.codex/private/cg4002-week7-20260906/ca-cert.pem` | `demo.py` | A directory that really exists on the laptop |
| iSH config file name `week7-ish-password.conf` and host alias `week7-ultra96` | `phone/ish_control.py` | A file and an alias that already exist in iSH on the phone. Nothing in the repository would create new names |
| Protocol v1 and `COMMS_LEGACY_DUMMY` | Several places | The deterministic dummy-data mode, not compatibility with an old version |

- Side effect of the cleanup: old captures recorded with Week 7 firmware (all in `.week7-local/`) contain `W7` packets, and the current `demo.py report` no longer passes them. To re-check old evidence, use commit `ec398b6`.

### 6.3 Actual deployment state, and one redeploy round

After the compatibility removal, all three ends must move to builds of the current source. **Any step below that logs in to the jump host or the Ultra96 can be done only by the owner, in their own terminal** (see section 9).

| Device | Current state | What to do | Who |
|---|---|---|---|
| Left board | **Flashed with the current firmware** (10-14, COM3) | Nothing | — |
| Right board | Still Week 7 firmware (sends `W7`). The current laptop program rejects it with `invalid source statistics magic; flash this board with the current firmware` | Flash the right board | The owner, or an agent once USB is connected |
| Server certificate | **The laptop's copy, which is the same certificate deployed to the board in September, expired on 2026-10-06 15:11:29 UTC.** The repository has no record of a later replacement. The board's actual state has not been checked | Renew with the original CA and upload to the board | The owner |
| Ultra96 service | Should still be the 28 September code snapshot with session `week7-demo`. It was started in the background by `.week7-local/co_deploy.py` (PID in `BOARD_ROOT/evidence/server.pid`) and may still be running | Upload a new snapshot of `common/` and `ultra96/`; verify, then stop the old process; start the new one; change `BOARD_SOURCE` in `tools/demo_service.py` to the new directory | The owner |
| iPhone app | The Week 7 build, session `week7-demo` | Rebuild from the current source on a Mac and install | The owner |

Steps:

1. **Renew the server certificate.** The CA stays the same, so neither the CA fingerprint in the phone source nor the laptop's `--ca` changes.

   ```powershell
   python -m tools.generate_comms_pki --renew-server-from "$HOME\.codex\private\cg4002-week7-20260906" --output-dir <a new empty directory outside the repository>
   ```

   Put `server-cert.pem` and `server-key.pem` from the new directory into the board's TLS directory (key permissions 600). The new certificate is again valid for only 30 days.
2. **Board service.** Only the `common/` and `ultra96/` directories are needed. Put them in a new directory; do not overwrite the directory the running service uses. The old process was started in the background and does not depend on an SSH session, so expect it to be running: its PID is in `BOARD_ROOT/evidence/server.pid`, and `python demo.py service` lists the `ultra96.server` processes with their working directories. Before stopping it, check with `ps -p <PID> -o pid=,uid=,args=` and `readlink -f /proc/<PID>/cwd` that it is your own `ultra96.server`, then run `kill -TERM <PID>`. Do not use `pkill` and do not kill by port. After starting the new service you should see `{"event": "listening", "host": "127.0.0.1", "tls": true, "ingest_port": 8888, "gateway_port": 9999}`.
3. **Right board firmware.** Flash only the right board: `platformio run -d firmware/esp32 -e firebeetle32-right -t upload --upload-port COMx`. Without `-e`, PlatformIO builds the default `firebeetle32` environment, which is ID 1. Or run the full `python flash.py` (plug in the left board first, then the right). If Windows asks for an authenticated bond after the firmware change: type `erase-bonds` on the board's serial port, remove the board in Windows Bluetooth settings, then run `python flash.py --pair right`.
4. **Phone app.** Needs a Mac and Xcode: `swift test --package-path ios-visualizer/CommsNative`, then run `python ios-visualizer/tools/patch_export.py` and `python ios-visualizer/tools/configure_xcode.py` on the Unity export (both scripts are fork only and can be rerun; the existing `ios-visualizer/xcode-export/` is already patched), then build and install with Xcode.
5. **Acceptance.** `python demo.py tunnel` (terminal A); on the phone, tap Connect and wait for `Subscribed`; `python demo.py run` (terminal B). The run must print `CAPTURE PASSED`, and the increase in the phone's `Received` must equal the `Phone expected increase` in the output.

To check whether the board's certificate has expired (with the tunnel open):

```powershell
openssl s_client -connect 127.0.0.1:18889 -servername ultra96.week7.internal
```

### 6.4 Integration progress

- The messages to the three teammates (in English, with explicit functions and fields) were drafted on 2026-10-14. They were reviewed for accuracy against the code, for the role boundary, and for whether the reader can understand them, and then handed to the owner. Their content matches section 7. They ask for replies by Thursday (10-15). Siqiang and Wen Ree deliver their interfaces by Friday (10-16). Jie Ling delivers the export by Sunday (10-18). **Whether the messages have been sent, and how teammates replied, is for the owner to record here.**
- The team-facing explainer: <https://claude.ai/code/artifact/b77bebd7-09f4-4c3e-9466-d4e19318359c> ("B07 integration: what to ask, what to tell, and why").

---

## 7. The three interfaces to connect

Communications specifies only which functions and fields are needed at each hand-over point. Function names and internal implementation are the other side's decision.

### 7.1 From Siqiang: the glove sensor module (called by the Communications firmware)

Agreed division of work: Siqiang delivers a working sensor module (initialisation, reading one sample, a description of the data format). **olsonwangyj** calls it from the Communications firmware and is responsible for scaling to int16, packing, BLE sending and connection management. The capture algorithm, calibration and sensor problems stay with Siqiang.

| Function | Suggested shape (names are theirs to choose) | How Communications calls it | Contract |
|---|---|---|---|
| Initialise | `bool gloveBegin()` | Once in `setup()` | I2C/ADC initialisation and gyro calibration. If no IMU is found it must return `false`, not wait forever (otherwise the board never advertises). `imu_v7.ino` currently blocks for about 5 s (1 s start-up, then gyro calibration, during which the glove must be completely still) |
| Periodic update (optional) | `void gloveUpdate()` | Once per main-loop pass, roughly every 1 to 2 ms, whether or not the laptop is connected | For filters that need updates more often than packets are sent. The Mahony filter in `imu_v7.ino` already updates once per pass with the actual dt |
| Read one sample | `bool gloveRead(float out[11])` | At each packet send, about every 20 ms (50 Hz), **only while the laptop is connected and subscribed**, so there can be seconds between calls | `true` means `out[]` holds a valid current sample. `false` means there is no valid sample now. `out[]` must not contain NaN |

Apart from the calibration phase of `gloveBegin()`, none of the three functions may call `delay()` or wait.

Order and units of the 11 values: `ax, ay, az` (g, gravity removed), `gx, gy, gz` (°/s, bias removed), `yaw, pitch, roll` (degrees), `flex1, flex2` (0.0 to 1.0). With the scale factors in 4.2, each value must stay within: acceleration ±3.2767 g, angular rate ±327.67 °/s, angles ±327.67°, flex at most 3.2767. The current settings in `imu_v7.ino` are all within range: the ±2 g range with gravity removed gives about ±3 g (a margin of only about 0.28 g); ±250 °/s; yaw and roll ±180°, pitch ±90°; flex 0 to 1.

Constraints the Communications firmware places on the module (from the existing code):

- PlatformIO, Arduino framework, board `firebeetle32`, Arduino-ESP32 core 2.0.17 (PlatformIO espressif32 7.1.0).
- The module does not define `setup()`/`loop()`. It does not call `Serial.begin()` and does not read the serial port (the serial port is used for pairing). It does not use `BluetoothSerial`, BLE or Wi-Fi (the radio belongs to the Communications firmware). It does not print to serial for each sample.
- `seq`, `uptime_ms` and the left/right identity are filled in by the Communications firmware. The module does not deal with them.

Already asked of Siqiang in the message (the code cannot answer these): which sketch is authoritative; whether the behaviours above will stay; the longest single-call time of `gloveUpdate()`/`gloveRead()`; a log of real samples (only the 11 output values); whether the left and right glove code differ; whether the extra IDLE/MOVING state in `model_threshold_variant_1` (12 October) must travel with the samples in V1; whether both gloves are FireBeetles and when they can be flashed (once the Communications firmware is flashed, Siqiang's Bluetooth recording script can no longer connect to that glove).

### 7.2 From Wen Ree: the model's entry and exit on the board (called by the Communications service on the board)

The connection point is `ultra96/server.py:264-267`. Suggested shape (names are theirs to choose):

| Function | Provided by | Called by whom, when | Contract |
|---|---|---|---|
| `start(emit)` | Wen Ree | Called once by the Communications service at start-up, before the first sample | Load the model here, and tell Communications how long that takes. `emit` is the result exit that Communications hands to the model |
| `on_sample(device_id, boot_id, seq, uptime_ms, values)` | Wen Ree | Called by Communications once for each newly accepted sample, on the service's single thread. The return value is unused | **Must return immediately.** The service is a single asyncio event loop, and the ACK is written only after this returns. If it is slow, the ACKs of both gloves are held up (the laptop waits at most 5 s for an ACK; sample freshness is 2 s). Inference must run on another thread or in another process |
| `emit(gesture, confidence, device_id, boot_id, seq)` | **Communications** | Called by the model once per result. It may be called from any thread | Communications moves the call safely back onto the event loop (the result queue has no lock). This is code the owner will write |

`on_sample` fields:

| Field | Type | Meaning |
|---|---|---|
| `device_id` | 1 or 2 | 1 = left, 2 = right |
| `boot_id` | uint32 | A random number for this power-up of this glove. It changes when the glove restarts |
| `seq` | uint32 | Sample sequence number within this power-up |
| `uptime_ms` | uint32 | This glove's own millisecond clock. The two gloves are not synchronised |
| `values` | 11 numbers | Order and units as in 7.1. By default, physical floats restored from int16 (acceleration and flex to 4 decimal places, angular rate and angles to 2). Wen Ree can ask for the raw int16 instead |

What Communications guarantees: within one power-up (same `device_id` + `boot_id`), `seq` only increases and never repeats. After a glove restart, `boot_id` changes and `seq` starts again from 0, so track by `(device_id, boot_id)`. Samples can be missing: lost over the radio, or dropped after waiting more than 2 s (not resent). These show as gaps in `seq`. While a glove is disconnected, no samples are produced and `seq` does not advance; a reconnect shows only as a jump in `uptime_ms`. The two gloves arrive over two independent connections, **with no pairing and no alignment**. Pairing, building windows and deciding gesture or idle all happen after the entry point, on the model side.

`emit` fields:

| Field | Type | Meaning |
|---|---|---|
| `gesture` | string | The label text as it is (the field name on the wire is `gesture`) |
| `confidence` | number from 0 to 1 | Confidence |
| `device_id`, `boot_id`, `seq` | as above | The identity of **one** sample this result used (usually the newest one in the window; either glove is fine). Communications uses it to build `result_id` (`device_id:boot_id:seq`). **Each result must point to a different sample**: the phone de-duplicates by `result_id`, and a second result with the same identity is dropped |

The result message cannot gain fields freely. The field set of `GESTURE_RESULT` is matched exactly in four places (the board, the iPhone and the two reference receivers), so the only correlation information is one sample's identity. Communications forwards the label and the confidence as they are, without filtering or renaming. But results, like samples, are not resent: if a result cannot reach the phone within 2 s (for example, when the phone is not connected), it is dropped. The game also reads only the latest result each frame.

Whether the model can run directly inside the Communications service process: the service runs as the ordinary user `xilinx` (no sudo) with `/usr/bin/python3` (3.10), and uses only the standard library itself. If the model code runs in this process, everything it imports (numpy, pynq and so on) must load under this interpreter and this user. `fpga/README_FPGA_PYNQ.md` says the overlay is loaded with sudo and the pynq-venv Python. If the model can only run that way, it is a separate process, and Communications defines a format for passing the same fields between the two processes on the board. That is the owner's work, not a new network route.

Already asked of Wen Ree in the message: whether it can run inside the Communications process (module and function names) or must be a separate process, and which packages it depends on; the full label set (by default the six in `models/class_names.json`); how often a result is produced (`src/live_inference.py` currently, once 50 samples have accumulated, produces one result for every new sample, including those with confidence below 0.70, and has no "idle" label; is the board version the same?); when a first version that can be connected will be ready (even one that always returns the same label).

### 7.3 For Jie Ling: the interface Communications provides (called by the game)

Agreed: **Jie Ling adds the phone client into the game in the Unity project**. Patching the export is no longer used. Communications **needs no API from the game**. The game calls the three Communications C functions (section 4.6) and can use the Week 7 receiver as an example. olsonwangyj links `CommsNative` into the newly exported `UnityFramework` (section 8, item 7). Jie Ling delivers an Xcode project exported from the current `vis/` that already calls the three functions. Before the link, the Xcode build reports `Undefined symbol: _CommsStart` and similar; this is expected.

C# declarations of the three functions (derived from the C signatures; not yet compiled in Unity). These symbols exist only in the iOS build. Calling them in the Unity Editor or on other platforms throws an exception, so calls go inside `#if UNITY_IOS && !UNITY_EDITOR`:

```csharp
[DllImport("__Internal")] static extern void CommsStart();
[DllImport("__Internal")] static extern int  CommsCopyDisplay(byte[] buffer, int capacity);
[DllImport("__Internal")] static extern void CommsStop();
```

- `CommsStart`: call once at start-up. It places the `Communications Connect` button in the top-right corner of the screen and does not connect by itself. A person taps the button, enters the jump-host and board login details, and imports the CA. Keep that corner clear.
- `CommsCopyDisplay`: call once per frame on the main thread with a 2048-byte buffer. It returns the number of UTF-8 bytes written (not counting the terminating 0). When nothing changed, or the buffer is null or too small, it returns 0 and writes nothing, and the game should keep the text it already has.
- `CommsStop`: call only when the app closes. It ends the session, clears the passwords and removes the button. Do not call it on a scene change or when going to the background.
- Line 3 holds only the latest result. Split it on `"  |  "` (two spaces, a vertical bar, two spaces): the first part is the gesture, the second the result id (for example `1:305419896:42`). The same gesture repeated still gets different ids, so compare ids, not gesture text, to decide whether a result is new. After 2 s without a new result, line 3 becomes `No live result`, which only means nothing new arrived. Do not rely on line 1 (`DUMMY inference` will change) or on `confidence 1.0` (currently a placeholder). Ids starting with `cmd:` come only from command tests the owner runs on the laptop.
- Only one object may call `CommsCopyDisplay` (each call reports only the change since the previous call), and that object must survive scene changes.
- What to do with a result (which action it maps to, cooldowns, repeats) is the game's business.
- The phone can no longer rely on the 5005 listener. Results come in only through these three functions.
- Passwords are not saved. As soon as the app stops being active (going to the background, screen lock, pulling down Control Center or Notification Center, an incoming call), it disconnects and clears the passwords, and they must be entered again.
- Reference: in Week 7 the owner had no Unity project and patched the generated C++ (`TlsDataReceiver`) of one Xcode export. Jie Ling's own C# was never changed. The patched export is only on the fork. The patch script <https://github.com/olsonwangyj/Let-Them-Cook/blob/main/ios-visualizer/tools/patch_export.py> is for reference only and cannot be run against a new project.

**One bridge limitation the owner must decide on (see section 13):** the current bridge keeps only the latest result, and `confidence 1.0` in the text is hard-coded. If several results arrive between two polls, the game sees only the last one (`Received` still counts them all). The message to Jie Ling is written for "V1 parses the four lines of text". If the owner wants per-result delivery, the message must change before it is sent.

---

## 8. Communications' own extension points (the owner's work; none done yet)

These are olsonwangyj's tasks. Do them in order. For each step, write the tests and golden vectors first.

1. **38-byte real data packet.** Settle the version number and the saturation rule for out-of-range values, then change these together: `firmware/esp32/include/comms_packet.h` (8 channels → 11), `comms_security.h:19` (MTU 35 → 41), `comms_control.h` (the command payload embeds a whole packet), `common/sensor.py`, `common/control.py`, `common/dummy_fixtures.json`, `laptop/bridge.py` (MTU check), `ultra96/protocol.py:67` (8 values). `laptop/goodput.py` counts bytes with `PACKET_SIZE` from `common.sensor`, so it follows the packet size automatically; only its version-1 formula check needs review. Real data cannot use version 1 (version 1 requires the values to equal the dummy-data formula).
2. **Connect the sensor module in the firmware.** In `main.cpp`: call the initialisation in `setup()`, and replace the block that calls `serializeFixturePacket` with "read sample → scale → pack". This block runs while holding the connection-state mutex, which the BLE callbacks also take, so nothing slow may happen here. For 50 Hz use `-DCOMMS_INITIAL_RATE_HZ=50` or `--rate 50`.
3. **Measure.** Two real gloves, 38 bytes, 50 Hz, at least 65 s, with clean source reconciliation on both boards.
4. **Connect the model interface on the board.** Replace `ultra96/server.py:264-267`.
5. **Accept model labels and real confidence.** Four checks currently accept only `REST`/`FIST`/`OPEN`/`POINT`, with confidence exactly 1.0: `ultra96/protocol.py:4,78-83`, `ios-visualizer/CommsNative/Sources/CommsCore/Protocol.swift:54-62`, `phone/receiver.py`, `phone/unity/CommsPhoneCore.cs`. **Without this change, the model's first real label makes the phone disconnect with a terminal error.** This step also covers the display text `DUMMY inference` and the hard-coded `confidence 1.0` (`DisplayMailbox.swift`, lines 16 and 18), and the setup-form text `DUMMY gestures · session ltc-comms` (`SetupViewController.swift:51`). The owner has said explicitly that Communications must support this itself and that the owner will make the change.
6. **The "one input, one result" criterion.** Once the model produces results per window, the reconciliation rules behind `Phone expected increase` in `demo.py` and in the two rehearsal tools (`tools/rehearse_comms.py`, `tools/rehearse_remote_comms.py`) must be redefined.
7. **Linking a new Unity export.** `patch_export.py` is no longer needed. `configure_xcode.py` depends on fixed Xcode object IDs; whether it works on a new export is unverified.
8. Do one redeploy round as in section 6.3 and run the acceptance check.

---

## 9. Prohibitions and cautions

### 9.1 Things not to do

1. **Do not change teammates' code.** `hardware/`, `src/`, `models/`, `data/`, `reports/`, `fpga/`, `vis/`, `export_fpga_reference.py` and `requirements.txt` are read-only. That includes changes that look harmless: line endings, formatting, dependency versions, regenerated files. When integration really needs a teammate to change code, write down exactly what to change and why, and give it to olsonwangyj to raise with them.
2. **Do not change how Communications connects, and do not propose alternatives or fallback routes.** BLE to the laptop, the laptop and the phone each connecting to the Ultra96 over SSH, the phone client handing results to the game through three C functions: these are settled, and they are designed for the NUS firewall rules. In particular, do not propose "the laptop connects to the phone's port 5005", "a phone hotspot", "a direct connection on a shared LAN" or the like. Other modules adapt to Communications.
3. **Do not overstep.** Do not do or supply any part of a teammate's implementation in the owner's name (for example, writing inference code for the model owner or C# scripts for the game owner). Do not list pairing, windowing, gesture decisions or label mapping as the owner's tasks. Do not judge the quality of teammates' components on the owner's behalf.
4. **Do not touch passwords.** Do not enter, store (not in files, memory or commit messages) or repeat the jump-host or Ultra96 passwords, even if the owner pastes them into the conversation and says they may be used. For any step that logs in, give the command and let the owner run it in their own terminal.
5. **Do not push to the team repository (`upstream`)** unless the owner asks for it explicitly. Pushing to the fork (`origin`) is fine.
6. **Do not delete files the owner has not put under version control.** To clean up, move them to `D:\LetThemCook-attic\`. `.week7-local/` holds historical evidence and copies of the firmware flashed in September; keep it.
7. **Do not run `pytest` without paths from the repository root.** It collects `fpga/hls/export_conv1d_test.py`, which rewrites a tracked file as soon as it is imported. Use `python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider`.
8. **Do not touch the `week7` names in the Week 7 receiver** (see 4.6 and the table in 6.2).
9. **Do not run a second subscriber during a demo or a joint test** (`laptop/phone_simulator.py`, `tools/rehearse_remote_comms.py`). The board has only one subscriber slot, and they would push the phone off.
10. **Refer to teammates by name or "they". Do not guess anyone's gender from their name.**

### 9.2 Pitfalls

- **The certificate lasts only 30 days.** After it expires the service still starts, but the laptop gets no ACK at all and the phone stops at `SSH, TLS or protocol verification failed`. Running the certificate tool without `--renew-server-from` replaces the CA too, and then the fingerprint in the phone source and the laptop's `--ca` must both change.
- **The session ID must match on all three ends.** On a mismatch the board closes the connection. The symptom is `received` rising while `acked` stays at 0, or the phone bouncing between `Connecting` and `Disconnected`.
- **Port defaults differ.** `demo.py` uses 18889. Running modules such as `laptop.dual_bridge` or `tools.ssh_tunnel` directly defaults to 18888. The tunnel and the capture must use the same port.
- **Personal defaults are written in the code.** The default account in `demo.py tunnel`, the default path of `demo.py --ca`, the account and board paths in `tools/demo_service.py` (these cannot be changed with arguments), and the two boards' Bluetooth addresses in `tools/demo_boards.py`. Watch these when the person, the machine or the boards change.
- **`BOARD_SOURCE` in `tools/demo_service.py` points to the 28 September snapshot.** If it is not changed after redeploying, `demo.py service --start` still starts the old code.
- **The service process does not reclaim identity capacity.** Each glove power-up takes one `(device_id, boot_id)`. A process allows at most 128; when they run out, the service must be restarted. A restart clears the de-duplication state.
- **With no subscriber, results are dropped at once.** So get the phone to `Subscribed` first, then start the capture.
- **The board closes an ingest connection after 5 s idle.** The first sample after a glove drops and reconnects may get no ACK, and is counted as one ambiguous drop.
- **After the GATT table changes or the firmware is reflashed, Windows may need to pair again.** Recovery is manual: `erase-bonds` on the board's serial port → remove the board in Windows → pair again.
- **At high rates the actual packet rate is below the setting** (the 70 Hz setting gives about 66 packets/s). From 75 Hz up, packets are lost.
- **The phone works only in the foreground.** Locking the screen or switching away disconnects it and clears the passwords.
- **There is no end-to-end timestamp.** The 2 s freshness is each segment's own waiting time, not end-to-end latency.
- **The board service writes one INFO log line for each accepted input.** With both gloves at 50 Hz that is about 100 lines per second. They go to the service's output: the foreground SSH terminal when it was started with `demo.py service --start`, or the log file under `BOARD_ROOT/evidence/` when it was started by `co_deploy.py`.
- **`flash.py` rewrites the Git-tracked `comms_fixtures.h` every time.** After changing `common/dummy_fixtures.json` you must reflash before the data on the board changes.
- **A leftover `LTC_COMMS_SESSION` in the terminal.** Documents from the transition period taught setting `LTC_COMMS_SESSION=week7-demo`. This variable affects `demo.py run`, `live` and `service --start` together, but not the phone. If it is still set, the laptop and a newly started service both use `week7-demo`. `CAPTURE PASSED` still appears, but the phone stays at `Disconnected: connection closed; retrying`. When troubleshooting, first make sure this variable is not set.
- **Neither end records why something was rejected.** For a bad frame, a session mismatch, an identity conflict or exhausted capacity, the board only closes the connection and adds 1 to `rejected`; it writes no log entry, and it prints its metrics only once, when the service stops. On the laptop, an ACK timeout or a mismatched ACK increments both `ack_errors` and `transport_errors`; a TLS connect or handshake failure increments only `transport_errors`. Neither counter records a reason. So an expired certificate and an unreachable port look the same (only `transport_errors`), and a session mismatch and a protocol version mismatch between the two ends look the same (the board closes the connection after the frame, which counts as both). For the 38-byte migration, both ends must be upgraded together.
- **The phone's "automatic retry" logs in to both SSH hops again and again.** When the board service is not running, the session does not match, or another subscriber has pushed the phone off, the phone treats it as a closed connection. It then logs in to the jump host and the board again with the password, at most every 5 s, with no limit on attempts. When the service is not ready, tap Disconnect first; do not leave the app on retrying.
- **A service started with `demo.py service --start` is the foreground process of that SSH session.** Closing that terminal, the laptop going to sleep or the VPN dropping all make the service exit. Keep the terminal that started the service open, like the tunnel terminal. This applies only to the `--start` path. The process recorded on the board on 2026-09-28 was started in the background by `.week7-local/co_deploy.py`, does not depend on any SSH session, and may still be running (4.5).
- **A different laptop needs `known_hosts` first.** Both SSH hops use strict host-key checking, and nothing in the repository writes `known_hosts`. The two public keys in the phone source `Configuration.swift` can be used to check them.
- **The single-board diagnostic tools cannot choose a board.** `laptop.ble_counter_receiver`, `laptop.mtu_probe` and `tools.rehearse_comms --ble` scan by service UUID and connect to whichever board they find first. The two boards advertise the same name, so power only one board when using these tools. They also do not set the rate, so the board keeps its last rate.
- **Symptoms when a board still has old firmware.** The two-board capture reads the source statistics first. If the marker is not `LCS1`, it reports `invalid source statistics magic; flash this board with the current firmware`, that board is not subscribed, and start-up times out after 30 s.
- **`verify-import.py` only works on a freshly imported, unpatched Unity export.** Running it on the already-patched `xcode-export/` reports `IMPORT_CHECK_FAILED`; this is expected.

---

## 10. Misunderstandings the owner has corrected (do not repeat them)

olsonwangyj corrected each of these.

| Wrong | Right |
|---|---|
| Proposing "the laptop connects to the phone's port 5005 over a shared network or a hotspot" | It breaks the NUS firewall rules. The phone connects by itself, through `stujump` over SSH, to the Ultra96 result gateway |
| Proposing alternatives or fallback routes for the connection, or promising to change how the phone client connects | The Communications connection design is the right approach. It does not change and has no fallback |
| Thinking that with the VPN on, the board can be reached directly | With the VPN on, traffic still goes through `stujump`. V1 keeps the jump-host route |
| Treating `phone/unity/CommsPhoneReceiver.cs` as the receiver deployed on the iPhone | It is the Android reference implementation. "Week 7 receiver" means `CommsNative` on the iPhone plus the `Week7*` bridge in the export |
| Proposing to give the NumPy inference code to Wen Ree, or to write C# scripts for Jie Ling | Overstepping. The owner only calls their interfaces; how they implement them is not the owner's concern |
| Writing pairing, windowing, one label per gesture, or label mapping as the owner's work | These are the teammates' work. Communications ends at the interface |
| Saying the link was tested only at 10 Hz, or that the Bluetooth approach is not decided | 50 Hz and 70 Hz were measured clean on 2026-09-28. BLE was chosen long ago |
| Slipping opinions on the quality of teammates' components into messages (model accuracy, gyro range, a path bug, and so on) | Talk only about interfaces and delivery dates |
| Asking teammates questions the code already answers | Read the code first. Ask only what the code cannot answer (physical state, intent, plans) |
| Using a password the owner pasted | Never use, store or repeat it. The owner does the logins |
| Thinking Siqiang writes the firmware after the merge | Siqiang provides the sensor module. The owner writes the merged firmware |
| Wanting to rename the TLS host name, the `Week7*` functions and the like | These are either written into the certificate or part of the Week 7 receiver. Leave them |
| Using gendered pronouns for teammates | Use names or "they" |

---

## 11. Running and verifying

**No hardware needed:**

```powershell
python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider
python -m tools.generate_comms_pki --output-dir <an empty directory outside the repository>      # one-off certificates, for local rehearsal only
python -m tools.rehearse_comms --pki-dir <the same directory> --duration 30 --target 100
```

The rehearsal starts a board service, a bridge and a subscriber on the local machine and prints one JSON line. `passed` should be `true`. The Swift tests run on a Mac: `swift test --package-path ios-visualizer/CommsNative`.

**Full chain on hardware (connect the VPN first; olsonwangyj does the logins):**

```powershell
python demo.py service          # inspect the board's ports and processes
python demo.py tunnel           # terminal A, keep it open
# iPhone: tap Communications Connect, wait for Subscribed, note Received
python demo.py run              # terminal B
python demo.py report
```

| What to verify | How to check |
|---|---|
| The board received the input (level 3) | `CAPTURE PASSED`; for each board, Generated = Received = ACKed |
| The phone received the results (level 5) | The increase in `Received` on the iPhone equals `Phone expected increase` in the output (compared by a person) |
| The services bind only to loopback | In the `ss -ltnp` output printed by `demo.py service`, the local address of 8888 and 9999 is `127.0.0.1` |

**Flashing and pairing:** `python flash.py` (left first, then right), `python flash.py --pair left`, `python flash.py --monitor COMx`, `python flash.py --boards`.

Symptoms, causes and recovery for common faults are in `docs/handoff-details/06-tests-operations-extension.md`.

---

## 12. Code map: what each folder and file does

This section lets a new agent know where things are without re-reading the code. Before changing a file, still read the file itself.

### 12.1 Top level

| Path | Owner | What it is |
|---|---|---|
| `firmware/esp32/` | Communications | BLE peripheral firmware for the two FireBeetle ESP32 boards (PlatformIO project) |
| `common/` | Communications | Python modules shared by the laptop and the Ultra96: packet format, control frames, network frames, TLS |
| `laptop/` | Communications | BLE reception and forwarding (relay) program on the Windows laptop |
| `ultra96/` | Communications | The service on the Ultra96: receives samples, replies with ACKs, pushes results to the phone |
| `phone/` | Communications | Reference and diagnostic receivers (Python, Android C#, iSH scripts). **Not** the one deployed on the iPhone |
| `ios-visualizer/` | Communications | The native iPhone client `CommsNative` (Swift), the patch tools of the Week 7 receiver, a preview app |
| `tools/` | Communications | Operations and rehearsal tools: tunnel, board service, certificates, dummy data, rehearsal, evidence |
| `tests/` | Communications | Communications Python tests (they also compile and run the firmware host tests) |
| `demo.py` | Communications | Day-to-day entry point: `tunnel`, `run`, `live`, `report`, `service` |
| `flash.py` | Communications | Builds and flashes the two boards, records Bluetooth addresses, pairs, serial monitor |
| `requirements-dev.txt` | Communications | Dependencies for the tests and the certificate tool (pytest, cryptography; the pyserial listed there is not used by Communications code) |
| `docs/` | Communications | olsonwangyj's documents (fork only) |
| `AGENTS.md`, `CLAUDE.md` | Communications | Rules for agents: ownership table, role boundaries, test command, document rules (fork only) |
| `hardware/` | Siqiang | Glove firmware sketches, recording scripts, schematic. **Read-only** |
| `src/`, `models/`, `data/`, `reports/`, `fpga/`, `export_fpga_reference.py`, `requirements.txt` | Wen Ree | Model training and inference, weights, data, FPGA project. **Read-only** |
| `vis/` | Jie Ling | Unity AR game project. **Read-only** |
| `README.md`, `.gitignore` | Shared | Only Communications lines may be added or changed |

### 12.2 Communications code, file by file

**`common/` (shared by both ends; changing it changes the laptop and the board service at once)**

| File | What it does |
|---|---|
| `sensor.py` | Encoding and decoding of the 32-byte sensor packet (`SensorPacket`, `encode_packet`, `decode_packet`, `PACKET_MAGIC = b"LC"`); converting a packet into a `SENSOR_BATCH` message; loading and choosing dummy data |
| `control.py` | Encoding, decoding and validation of BLE control frames (14-byte `B7` header); the rules for how commands transform the 8 values. Unrelated to network JSON |
| `wire.py` | Network frames: 4-byte big-endian length + strict UTF-8 JSON; limit 16384 bytes; a 5 s deadline for each read and write; `ProtocolError` |
| `tls.py` | TLS client and server contexts; TLS 1.2 minimum; the host-name constant `TLS_SERVER_NAME`; no "do not verify" branch |
| `dummy_fixtures.json` | The editable 8-channel dummy-data table (4 rows now). The firmware header is generated from it |

**`firmware/esp32/`**

| File | What it does |
|---|---|
| `platformio.ini` | Four build environments: the default `firebeetle32` (protected, ID 1), `firebeetle32-left` (ID 1), `firebeetle32-right` (ID 2), and the unprotected diagnostic `firebeetle32-unprotected-diagnostic` |
| `src/main.cpp` | All the BLE peripheral run-time logic: the GATT service and its 7 characteristics, pairing security, sending samples at the set rate, the control queue, source statistics, the `erase-bonds` serial command |
| `include/comms_packet.h` | Byte-by-byte serialisation of the 32-byte packet; values taken from the dummy-data table |
| `include/comms_fixtures.h` | The dummy-data table generated from `common/dummy_fixtures.json` (`flash.py` rewrites it every time) |
| `include/comms_security.h` | Pure functions: authentication-bit checks, the notification gate, the sensor MTU floor of 35 (`sensorFitsMtu`) and the control-write gate (`canAcceptControl`) |
| `include/comms_source_stats.h` | Sequence allocation, submission counters, serialisation of the 24-byte source statistics |
| `include/comms_control.h` | The control state machine `ControlEngine`: commands, rate, file transfer, response cache. Also the control MTU floor of 64 (`controlFitsMtu`) and `controlChunkCapacity` |
| `include/comms_gatts_control.h` | Parses writes only on real WRITE events |
| `test/host_*.cpp` | Four host tests (packet, events, source statistics, control), compiled and run with `g++` or `clang++`, whichever is on PATH; skipped when neither is found |

**`laptop/`**

| File | What it does |
|---|---|
| `bridge.py` | The full path for one glove: scan, connect, MTU and bond checks, bounded queue, TLS writes, ACK checks, metrics, tail handling at shutdown |
| `dual_bridge.py` | Runs two uncoupled `Bridge` instances at once, with one shared observation window, and produces the combined report. This is what `demo.py` calls |
| `source_audit.py` | Parses source statistics (`SOURCE_STATS_MAGIC = b"LCS1"`); reconciles "generated = received = ACKed" |
| `controls.py` | The BLE control channel: keyboard commands, rate, file transfer |
| `windows_pairing.py` | Pairs on Windows with "passkey entry + encrypted and authenticated", and checks the bond level |
| `ble_connection.py` | Turns off the Windows GATT cache when creating the Bleak client |
| `ble_parameters.py` | Above 10 Hz, asks Windows for throughput-optimised connection parameters and records the actual values |
| `ble_shutdown.py` | When a capture stops, first turns notifications off on the remote side while keeping the local callback, to collect the tail packets |
| `evidence.py` | Writes `packets.jsonl` and the logs in the background, bounded |
| `goodput.py` | Measures the rate of valid sensor bytes received |
| `reporting.py` | Exclusive placeholder and atomic write of report files; source fingerprints |
| `phone_simulator.py` | A desktop result subscriber, for rehearsal only. **It pushes the phone off when it connects** |
| `mtu_probe.py`, `ble_counter_receiver.py`, `bounded_telemetry_queue.py` | Early diagnostic tools, and a general-purpose queue the main path does not use |
| `requirements.txt` | `bleak==3.0.1` (the version must stay pinned: the shutdown tail protection depends on Bleak internals) |
| `tests/` | Tests for the three diagnostic tools above |

**`ultra96/`**

| File | What it does |
|---|---|
| `server.py` | The board service `CommsServer`: two loopback TLS listeners, ingest de-duplication and ACK, the single-subscriber result queue, the command-line entry. **Fake results are generated at lines 264 to 267; the model interface connects here** |
| `protocol.py` | Exact fields and value ranges of the five messages, `session_id` rules, `result_id` generation. **The label allow-list `GESTURES` and the "confidence must be 1.0" check are here** |
| `diagnostics.py` | Optional bounded event log (`--event-log-dir`) |

**`ios-visualizer/`**

| File | What it does |
|---|---|
| `CommsNative/Package.swift` | Swift package definition; dependencies pinned to exact versions of SwiftNIO, NIOSSH, NIOSSL and swift-crypto |
| `CommsNative/Sources/CommsCore/Protocol.swift` | Subscribe frame encoding, result validation (**label allow-list and confidence check**), stream framing |
| `CommsNative/Sources/CommsCore/DisplayState.swift` | Latest result, count, de-duplication (4096), 2 s expiry |
| `CommsNative/Sources/CommsTransport/CommsClient.swift` | Building the two-hop SSH + TLS route, error classification (terminal or retry), back-off and reconnect |
| `CommsNative/Sources/CommsTransport/SSHRoute.swift` | Route parameters, port and timeout constants, failure types |
| `CommsNative/Sources/CommsTransport/Trust.swift` | Exact host-key comparison, password authentication, SSH channel byte conversion |
| `CommsNative/Sources/CommsTransport/Subscriber.swift` | Sends `SUBSCRIBE` after the TLS handshake, receives frames, frame deadline |
| `CommsNative/Sources/CommsTransport/Credentials.swift` | In-memory password holder that can be cleared |
| `CommsNative/Sources/CommsBridge/Configuration.swift` | Pinned host names, both SSH host public keys, CA fingerprint; CA import check; saving the public settings |
| `CommsNative/Sources/CommsBridge/IntegrationController.swift` | Foreground session management, the connect button, disconnect on leaving the foreground. The session ID `ltc-comms` the client uses is set here (line 74) |
| `CommsNative/Sources/CommsBridge/SetupViewController.swift` | The setup form. Its text `DUMMY gestures · session ltc-comms` (line 51) also names the session |
| `CommsNative/Sources/CommsBridge/DisplayMailbox.swift` | The C functions exported to Unity, `CommsStart`, `CommsCopyDisplay`, `CommsStop`, and the `Week7*` wrappers. The four lines of text are built here |
| `CommsNative/Tests/` | Swift tests (run on a Mac) |
| `NativePreview/` | A preview app without Unity, and its UI tests |
| `tools/patch_export.py` | Week 7 receiver: patches the generated code of that one Unity export (fork only) |
| `tools/configure_xcode.py` | Links `CommsNative` into `UnityFramework` (fork only) |
| `verify-import.py`, `import-manifest.json` | Check the Unity export as first imported; only for a project not yet patched (fork only) |
| `reference/TlsDataReceiver.cs` | Archived copy of Jie Ling's original receiver script (fork only) |
| `xcode-export/` | The Unity export used in Week 7, 3479 files, large files in LFS (fork only) |
| `README.md`, `NATIVE-INTEGRATION.md` | Notes on the source and on the integration boundary |

**`phone/` (reference and diagnostics)**

| File | What it does |
|---|---|
| `receiver.py` | Standard-library Python receiver (Termux/iSH); connects to the local forwarded port 19999 |
| `unity/CommsPhoneCore.cs` | C# protocol, TLS trust and receive loop, with no Unity dependency |
| `unity/CommsPhoneReceiver.cs` | Android reference Unity component; the phone must open its own SSH local forward |
| `ish_control.py` | Temporary maintenance-channel script for the iSH route (that route is abandoned) |
| `tests/` | Tests for the Python above, and a C# self-test script (needs PowerShell 7) |

**`tools/`**

| File | What it does |
|---|---|
| `ssh_tunnel.py` | Builds the two-hop, loopback-only OpenSSH local-forward command (explicit `ProxyCommand`, strict host keys) |
| `demo_service.py` | Inspects or starts the board service over SSH. The board deployment directory constants `BOARD_ROOT` and `BOARD_SOURCE` are here |
| `demo_boards.py` | Reads and writes the left/right Bluetooth address map (`.comms-local/boards.json`). The built-in default addresses are here |
| `generate_comms_pki.py` | Generates the CA and the server certificate. `--renew-server-from` renews only the server certificate with the existing CA |
| `generate_dummy_fixtures.py` | Generates the firmware header `comms_fixtures.h` from the JSON |
| `comms_demo.py` | Packet examples, a single-board send demo, offline log audit |
| `rehearse_comms.py` | Full rehearsal over local loopback (no SSH, no hardware) |
| `rehearse_remote_comms.py` | Remote rehearsal through an existing tunnel. **It pushes the phone's subscription off** |
| `video_evidence.py` | Extracts, from one capture, one example sample and its ACK per board |

**`tests/`**: 45 files: 42 test files, and 3 files under `fixtures/` that hold 2 golden vectors (`comms-golden.json` has two packet vectors; `comms-dummy.bin` and `comms-boundaries.bin` are their raw 32 bytes). Files are named after what they test: `test_sensor.py` (packet format), `test_source_audit.py`, `test_laptop_controls.py`, `test_bridge_*.py`, `test_dual_*.py`, `test_transport*.py` (TLS, framing, certificate tool), `test_server_*.py`, `test_ssh_trust.py`, `test_demo_*.py`, `test_firmware_*.py` (compile and run the firmware host tests), `test_rehearsal.py`, and others.

### 12.3 Teammates' code (read-only; know it only well enough to connect to it)

**`hardware/gloves/` (Siqiang)**

| Path | What it is |
|---|---|
| `README.md` | Description of the two gloves: each has one ESP32, one MPU-6500 and two flex sensors; 11 values per sample |
| `29_sept/imu_v7.ino` | The current reference firmware sketch (CSV output over Bluetooth Classic serial) |
| `29_sept/imu_recording_terminal_v14.py`, `how_to_use.txt` | PC-side recording script and how to use it |
| `imu_v3.ino`, `imu_recording_terminal_v10.py`, `_v11.py` | Earlier versions |
| `model_threshold_variant_1/` | An experiment that detects "is there motion" on the ESP32 (training script, parameter header, debug sketch) |
| `glove_schematic_week7.png` | Schematic |

**`src/`, `models/`, `data/`, `reports/`, `fpga/` (Wen Ree)**

| Path | What it is |
|---|---|
| `src/model.py` | The CNN definition |
| `src/train_model.py`, `cross_validate_model.py`, `evaluate_model.py`, `check_model.py` | Training, cross-validation, evaluation |
| `src/create_dataset.py`, `preprocess_sensor_data.py` | Dataset building and preprocessing |
| `src/inference.py`, `src/live_inference.py` | Offline inference; real-time inference reading glove data from two COM ports (prints results on the laptop) |
| `models/class_names.json`, `gesture_cnn*.pth` | The 6 class names; weights |
| `data/simulated/` | Simulated data |
| `reports/` | Evaluation results |
| `fpga/hls/` | HLS source: a multiply-accumulate test module, and a fixed-point first convolution layer with its testbench. **`export_conv1d_test.py` rewrites a tracked file as soon as it is imported, so do not run bare pytest from the root** |
| `fpga/pynq/`, `fpga/vivado/`, `fpga/validation/` | Bitstream of the multiply-accumulate module, Vivado project, validation data |
| `fpga/README_FPGA_PYNQ.md` | How to load the overlay on PYNQ (needs sudo) |
| `export_fpga_reference.py` | Exports reference data for checking the FPGA |

**`vis/` (Jie Ling)**

| Path | What it is |
|---|---|
| `Assets/Scripts/Core/` | Hand tracking and interaction: `HandTrackingManager.cs` (hand landmarks from the camera with MediaPipe), `GestureButtonController.cs` (action entry points `OnSelectPressed`, `OnGrabPressed`, `OnDropPressed`, `OnChopPressed`, `OnWashPressed`; wash is still empty), `Grabbable.cs`, and others |
| `Assets/Scripts/Kitchen/` | Kitchen logic: chopping board, chopping progress, ingredient state, ingredient bins, pot |
| `Assets/Scripts/AR/` | AR: spawning items from QR codes, headset two-eye layout, distortion |
| `Assets/Scripts/UI/` | Menus, hover feedback, scene loading |
| `Assets/Scripts/Network/TlsDataReceiver.cs` | A TLS server listening on 5005 on the phone that only displays the text it receives (direction opposite to the network model) |
| `Packages/com.github.homuler.mediapipe/` | MediaPipe Unity plug-in |
| The rest of `Assets/`, `ProjectSettings/` | Scenes, prefabs, assets, project settings |

### 12.4 Git and local-only directories

| Location | Contents |
|---|---|
| `D:\LetThemCook` | Working copy, local `main` |
| `upstream` | Team repository <https://github.com/B07-CG4002/Let-Them-Cook>, public, main branch unprotected, currently at `ec398b6`. PR #15 was merged without `gh`, with `git commit-tree` and a push |
| `origin` | olsonwangyj's fork <https://github.com/olsonwangyj/Let-Them-Cook>, public |
| Only on the fork, not in the team repository | All of `docs/`, `AGENTS.md`, `CLAUDE.md`, `.gitattributes`; under `ios-visualizer/`: `tools/`, `verify-import.py`, `import-manifest.json`, `reference/TlsDataReceiver.cs` and `xcode-export/` (`reference/teammate-localhost-cert.pem` is also in the team repository); and `tests/test_ios_export_patch.py`. So teammates who clone the team repository cannot see the design records |
| `.comms-local/` | The local board map `boards.json` (left `38:18:2B:19:82:AE`, right `38:18:2B:18:9D:6A`) and future captures (Git-ignored). There is no capture directory yet |
| `.week7-local/` | 17 historical capture directories (all `W7` packets), the September measurement results, an archive of the firmware flashed on 29 September, and the local scripts used in September: `co_deploy.py` (board deployment script with strict SSH trust and rollback; the 28 September deployment used it, and it started that service in the background with `start_new_session=True`, PID in `BOARD_ROOT/evidence/server.pid`), `co_acceptance.py`, `co_faults.py`, `co_final_check.py`, `co_iphone_capture.py` and others. Git-ignored and not versioned. **Keep it; do not delete it** |
| `release-tools/`, `output/` | The frozen packaging tools and 4 ZIP files used for the 30 September submission (listed in `.git/info/exclude`; local only) |
| `D:\LetThemCook-attic\2026-10-13\` | 2.3 GB of files moved out while tidying the workspace (not deleted; contains a README.txt) |
| `D:\LetThemCook-worktrees\comms-cleanup` | Worktree of branch `comms/remove-week7-legacy` (based on the team main branch; used to open the PR to the team repository) |
| `~/.codex/private/cg4002-week7-20260906/` | The current CA (with its private key) and the September server certificate. Not in Git |

### 12.5 `docs/` index

| File | Contents |
|---|---|
| `README.md` | The docs index |
| `communications-handoff.md` | This document |
| `handoff-details/01-architecture-network-security.md` | Detail chapter 1: architecture, network and security |
| `handoff-details/02-firmware.md` | Detail chapter 2: firmware |
| `handoff-details/03-laptop-relay-and-tools.md` | Detail chapter 3: laptop relay and tools |
| `handoff-details/04-ultra96-service-and-certificates.md` | Detail chapter 4: Ultra96 service and certificates |
| `handoff-details/05-phone-and-week7-receiver.md` | Detail chapter 5: phone client and the Week 7 receiver |
| `handoff-details/06-tests-operations-extension.md` | Detail chapter 6: tests, operations and extension points |
| `co-protocol-v2.md` | olsonwangyj's current protocol specification (v2, control, files) |
| `B07-CO-protocol-explained.zh-CN.md` | Chinese study companion to `co-protocol-v2.md`, explaining the protocol byte by byte. Not a formal document; the English specification governs |
| `communications-quickstart.md` | Quick start |
| `week7-runbook.md` | The Week 7 operations manual (some command names are out of date; see 4.9) |
| `archive/` | History: assessment material, reports, measured evidence, design records, old manuals |
| `archive/design/integration-handoff-2026-10-08.md` | The English integration notes for teammates (PR #15), formerly `docs/integration-handoff.md`. Moved to the archive on 2026-10-14. Section 7 of this document holds the current interface requests |

### 12.6 What to change, and in which file

| What to change | File |
|---|---|
| How many values a packet holds, packet length | `firmware/esp32/include/comms_packet.h`, `common/sensor.py`, `ultra96/protocol.py`, plus the MTU gates in `comms_security.h` and `laptop/bridge.py` |
| Where the firmware gets samples | `firmware/esp32/src/main.cpp` (the block that calls `serializeFixturePacket`) |
| Default send rate | `platformio.ini` (`-DCOMMS_INITIAL_RATE_HZ`) or, at run time, `demo.py run --rate` |
| How the board produces results | `ultra96/server.py:264-267` |
| Which labels and confidence values are allowed | `ultra96/protocol.py`, `CommsCore/Protocol.swift`, `phone/receiver.py`, `phone/unity/CommsPhoneCore.cs` (all four change together) |
| Text or functions for Unity | `ios-visualizer/CommsNative/Sources/CommsBridge/DisplayMailbox.swift` |
| Session ID | Laptop: `--session-id` or `LTC_COMMS_SESSION`. Board: the service's `--session-id`. Phone: two places that change together, `IntegrationController.swift:74` (the value used) and the form text in `SetupViewController.swift:51`; then rebuild |
| Jump-host and board host names, SSH host public keys, CA fingerprint | Laptop: `tools/ssh_tunnel.py` and the `demo.py` arguments. Phone: `Configuration.swift` (rebuild) |
| Board deployment directory | `BOARD_ROOT` and `BOARD_SOURCE` in `tools/demo_service.py` |
| Bluetooth addresses of the two boards | Run `python flash.py`; the result is in `.comms-local/boards.json` |
| Queue length, freshness, timeouts, ACK window | Laptop: `BridgeConfig` in `laptop/bridge.py`, and `demo.py`. Board: `ultra96/server.py`. Phone: `SSHRoute.swift`, `DisplayState.swift` |
| Certificates | `tools/generate_comms_pki.py` |

---

## 13. Not yet confirmed

- The actual state of the server certificate, the service process and the code snapshot on the board (olsonwangyj must log in and check).
- Whether the right and left boards need pairing again after reflashing.
- Whether 38 bytes × 50 Hz × 2 boards is clean on hardware.
- Whether `configure_xcode.py` works on a new Unity export.
- Direct mode (the phone not going through the jump host) was never verified on site. V1 does not use it.
- Why the phone missed 109 results on 2026-09-21.
- The three teammates' replies about the interfaces in section 7.

Needs the owner's decision:

- When the game gets results through the three C functions, is it enough for V1 to get only the latest result and the four lines of text (the message to Jie Ling is written this way), or must Communications add per-result delivery and real confidence to the bridge (end of 7.3)?
- Are the `values` handed to the model physical floats (the current default, written as "my plan" in the message) or raw int16?
- The message says the owner links `CommsNative` into Jie Ling's newly exported Xcode project. Does that fit the decision that Jie Ling adds the client into the game in the Unity project?
- The version number of the 38-byte packet, and what happens when a value exceeds the int16 range (saturate or drop).

---

## 14. Change log

| Date | What changed |
|---|---|
| 2026-10-14 | First version. It covered: the project and the state of each subsystem; role and boundaries; the full Communications chain, the formats, how each segment works and the design reasons; the state after the Week 7 compatibility removal; the left board flashed with the current firmware; the finding that the September server certificate expired on 10-06 (read from the laptop's copy), and the new renewal option; the API needs of the three interfaces; the owner's corrections |
| 2026-10-14 | The six detail chapters were finalised against the current code after two fact-checks and a completeness review |
| 2026-10-14 | The teammate messages were rewritten with explicit functions and fields, reviewed for accuracy, role boundary and clarity, and handed to the owner. Section 7 was updated to match |
| 2026-10-14 | The owner set two rules: the documents are updated with every code or deployment change, and formal documents are written in English (`AGENTS.md` rules 7 and 8; section 0, point 3). The hand-off document and the detail chapters were rewritten in English, and the Chinese versions were removed from the repository (an unmaintained snapshot is in `D:\LetThemCook-attic\2026-10-14\handoff-zh-CN\`). `docs/integration-handoff.md` (8 October) moved to `docs/archive/design/integration-handoff-2026-10-08.md`, because section 7 supersedes it |
| 2026-10-14 | Cross-check corrections applied: how the board service was started and what keeps it alive (4.5, 6.3, 9.2, 12.4); the path of the iOS patch scripts (6.3 step 4); the server certificate expiry checked only on the laptop's copy (1, 2.4, 4.8, 6.3); only `ios-visualizer/reference/TlsDataReceiver.cs` is fork-only (12.4); where the sensor and control MTU floors live (12.2); four PlatformIO environments, including the default `firebeetle32` with ID 1 (4.3, 6.3, 12.2); host tests use `g++` or `clang++` and are skipped without either (4.3, 12.2); `demo.py live` runs 120 s and needs an interactive terminal (4.4); what the BLE callback does (4.4); `received` versus `callback_received` (4.7); which failures increment `ack_errors` and `transport_errors` (9.2); the locations of the `DUMMY` texts and the `Protocol.swift` line range (8 step 5); `laptop/goodput.py` follows `PACKET_SIZE` (8 step 1); the phone holds the session in two places (12.2, 12.6); 3 fixture files but 2 golden vectors (12.2); `src/live_inference.py` hard-codes `COM3`/`COM4` at 115200 baud, with no evidence they are Bluetooth ports (2.3) |
