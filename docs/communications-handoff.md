# Let Them Cook (CG4002 B07): Communications and integration hand-off

**Readers:** olsonwangyj (called Yoz in the team), the Communications owner, and every agent that takes over this repository later.
**Purpose:** after reading it you know what the project is, how the Communications subsystem works, why it is designed this way, where it stands now, what must not be done, and what comes next.
**Last updated:** 2026-10-16 (change log in section 14).

---

## 0. How to use this document

1. Read sections 1 to 3 first (project, role, boundaries), then section 6 (current progress) and section 9 (things not to do). Read sections 4, 5 and 8 before changing Communications code. To find what a folder or file does, use the code map in section 12.
2. Which source wins: **code > this document > olsonwangyj's other documents > teammates' READMEs and documents**. Teammates' documents disagree with the code in places (see 4.9 and the detail chapters). When they conflict, trust the code and record the conflict in this document.
3. **Keeping the documents current is a rule. The owner set it on 2026-10-14 (`AGENTS.md` rules 7 and 8).** Every change to Communications code, and every change to what is deployed (boards, Ultra96 service, phone app, certificates), is not finished until the documents describe it, in the same piece of work. The documents are:
   - this hand-off document: always section 6 (progress) and section 14 (change log); section 12 (code map) when a file is added, moved, renamed or removed; section 7 when an interface changes; section 10 when the owner corrects an understanding;
   - the matching detail chapter in `docs/handoff-details/`;
   - `docs/co-protocol-v3.md` (the protocol specification; it was `co-protocol-v2.md` until 2026-10-14) when a wire format, message, constant or limit changes.

   Sections 6 and 14 are also updated when an interface is agreed with a teammate or the owner corrects an understanding, even when no code changes. After a change, read the affected passages and correct every statement the change made untrue. Formal documents (this document, its detail chapters, specifications, quickstarts, runbooks) are written in English. Chat with the owner may be in Chinese.
4. Finer detail, down to each constant, each status string and the source of each design decision, is in the six chapters under `docs/handoff-details/` (index in 12.5). This document on its own contains every point needed to take over. Where a chapter disagrees with this document, this document governs, and the code governs both (point 2).
5. Historical material is in `docs/archive/`. Those files keep the names of their time (`week7`, `W7`) and are not updated. Use them only to find where a design decision came from.

---

## 1. One-minute overview

- **Project:** NUS CG4002 capstone, team B07, "Let Them Cook". A single-player AR cooking game, similar to Overcooked. The player wears two sensor gloves and makes gestures. A model on the Ultra96 FPGA board recognises the gestures. The results drive a Unity AR game on an iPhone.
- **olsonwangyj's two roles:** owner of the Communications subsystem (the main technical work), and since 2026-10-13 also integration lead. Integration V1 must run by **2026-10-20 (Tuesday)**, when the team meets in person to integrate it together (the schedule up to that day is in 6.4). The final version is due around Week 13.
- **What Communications does:** it sends each module's data out and makes sure the next module receives it accurately. The chain glove → laptop → Ultra96 → iPhone has run end to end on real hardware with dummy data, and the evidence is kept.
- **Three interfaces to connect:** the glove sensor module (Siqiang; delivered on 2026-10-15 and built into the `-glove` firmware, but not yet run on a glove), the model's entry and exit on the board (Wen Ree; nothing delivered yet), and the game script that calls the Communications bridge (Jie Ling; nothing delivered yet).
- **The Communications side of all three interfaces exists in code (branch `comms/protocol-v3`, merged into `main` and pushed to the fork on 2026-10-16; team pull request #19 open, <https://github.com/B07-CG4002/Let-Them-Cook/pull/19>).** Protocol version 3 replaced versions 1 and 2 everywhere (2026-10-14 evening): a 38-byte packet with 11 values, the model entry and exit on the board (`start(emit)`, `on_sample`, a thread-safe `emit`), model labels and real confidence on every receiver, and the per-result function `CommsNextResult` in the Swift client. On 2026-10-15 Siqiang pushed his sensor module (team commit `51593be`) and answered the questions; by his answer, **a glove sends samples only while his movement detector says MOVING**. So the IDLE/MOVING state does not travel in the packet, and the 11-value layout stays. Communications added this "gating": the firmware asks the glove module before each sample and skips IDLE ticks without using a sequence number; the source statistics grew to 36 bytes (marker still `LCS3`) with a "gated" flag and idle/unread/refused counters; the laptop judges a gated board's coverage by its ticks; the Ultra96 service lets a silent ingest connection wait 600 s instead of 5 s. New `-glove` firmware environments build Siqiang's unchanged module, and `python flash.py --glove` flashes it. Python, firmware and tool code is built and tested on the laptop (842 passed, 4 skipped at `4c6ab4c`). The Swift client is now compiled and tested on Linux in a Swift 6.1 container (72 tests); it is not yet built for iOS. The C# reference core `CommsPhoneCore.cs` now compiles (C# 7.0) and its self-test passed (113 checks, PowerShell 7); the Unity component `CommsPhoneReceiver.cs` was checked by reading only. **Gating is built but has not run on hardware:** the right board was unplugged before the gated build could be flashed. Version 3 has run on hardware only on the right board against a service on the laptop, with the 2026-10-14 build and its 24-byte statistics, which the current laptop refuses (section 6.1). Not done: any hardware run of the current firmware, the Ultra96 redeploy, the phone rebuild, and any run of both gloves, the Ultra96 and the phone together on version 3. Section 6.5 lists every decision with its status.
- **The two most urgent things:** first, the server certificate deployed to the board in September expired on 2026-10-06 15:11:29 UTC (read from the laptop's copy; the board's copy has not been checked). A renewed certificate from the same CA was made on 2026-10-14 and is valid until 2026-11-13 14:27:35 UTC, but it is **not on the board yet**: the owner deploys it together with the version-3 service with `python -m tools.deploy_service` (section 6.3). Second, both boards must be flashed with the current firmware and the gating checked on hardware, and the remaining teammate interfaces (Wen Ree's model module, Jie Ling's game script) must be settled soon (sections 6.3 and 7).

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

### 2.3 State of each subsystem (2026-10-15, per the code)

**Gloves (Siqiang, `hardware/`)**

- **The sensor module for the Communications firmware was delivered on 2026-10-15.** Siqiang pushed team commit `51593be` (11:11 +08:00): `hardware/gloves/integration_files/` with `glove_sensor.h`, `glove_sensor.cpp` and `movement_model_params.h` (the same weights as `model_threshold_variant_1`). It has no `setup()`/`loop()`, no serial output and no radio. Its functions: `gloveBegin()`, `gloveUpdate()`, `gloveRead(float out[11])`, `gloveIsMoving()` (classifier ready and MOVING) and `gloveMovementReady()`. It also runs his movement detector: a logistic regression over a 1 s window of 50 samples, evaluated every 200 ms; MOVING after 2 windows above the threshold, IDLE after 3 below. The Communications firmware builds an unchanged copy of it (4.3). Two issues found in it on 2026-10-15 are described in 7.1.
- **Siqiang's answers (relayed by the owner, 2026-10-15):** (A) the authoritative sketch is `hardware/gloves/model_threshold_variant_1/debug_esp32_ml_movement_detector_v1.ino` with `movement_model_params.h`; (B) I2C at 400 kHz, no other libraries, `begin` takes about 5.1 s; (C) a call takes at most about 10 to 20 ms, usually far less; (D) left and right use the same code; his 12th value `SENS_GL_LEFT`/`RIGHT` and the Bluetooth names `SENSOR_GLOVE_LEFT`/`RIGHT` were only for his PC, and Communications does not need them (`device_id` comes from the Communications build; the boards advertise `LTC-COMMS`); (E) the final version sends data only while his detector says MOVING, and nothing while IDLE; (F) he asked whether he can still record. Answer: his Bluetooth Classic script cannot connect to the BLE firmware; he can flash his own sketch, or record through the chain with `python demo.py run` and `python -m tools.export_capture`, with a build that sends IDLE samples too (`-DCOMMS_GLOVE_SEND_ALL=1`). He wraps the decision in a bool function, and the owner asked that the Communications firmware call it.
- His standalone sketches (`29_sept/imu_v7.ino`, the variant-1 debug sketch) have their own `setup()`/`loop()` and calibrate the gyroscope at start-up. They output CSV text over **Bluetooth Classic serial** (`BluetoothSerial`), at about 50 Hz; the repository's sketch variants output 11, 12 and 13 fields. They **cannot be linked with the Communications firmware**; the `integration_files` module can.
- Each sample is 11 floats in the order `ax, ay, az, gx, gy, gz, yaw, pitch, roll, flex1, flex2`: acceleration (g, gravity removed, range ±2 g), angular rate (°/s, bias removed, range ±250 °/s), Euler angles (degrees), and two flex values (12-bit ADC divided by 4095, range 0.0 to 1.0).
- Board: both gloves use DFRobot FireBeetle ESP32 boards (confirmed by the owner, 2026-10-14; not a question for Siqiang).
- Hardware used: I2C SDA 21 / SCL 22 / 400 kHz; ADC pins 34 and 35.

**Model and FPGA (Wen Ree, `src/` `models/` `fpga/`)**

- The model is a CNN. Its input is a 50×22 window: 50 time steps, and each step is 11 left-glove values plus 11 right-glove values. Its output is 6 classes. The classes are in `models/class_names.json`: `PICKUPHOLD`, `PLACEDOWN`, `CHOP`, `WASH`, `THROW`, `FIREEXT`. Inputs are not normalised.
- `src/live_inference.py` currently reads data itself from two hard-coded Windows serial ports, `COM3` and `COM4`, at 115200 baud, exactly 11 values per line, and prints predictions on the laptop. The confidence threshold is 0.70. **It has no entry point that the board service can call.**
- The FPGA side (`fpga/`) is currently a test module plus the first convolution layer. `fpga/README_FPGA_PYNQ.md` says that loading the overlay needs `sudo` and a different interpreter.
- The owner once reproduced the forward pass with NumPy. All 30 golden outputs matched. Converting the 11 values to int16 with the scale factors in 4.2 and back did not change the predictions. This was only a Communications-side check that fixed-point transport does not affect the model. **How inference is implemented is Wen Ree's business.**

**Game (Jie Ling, `vis/`)**

- An iOS AR project in Unity 6000.5.10f1. The action entry points are `OnSelectPressed`, `OnGrabPressed`, `OnDropPressed`, `OnChopPressed` and `OnWashPressed`.
- `vis/Assets/Scripts/Network/TlsDataReceiver.cs` is a TLS server that listens on port 5005 on the phone and only displays the text it receives. `vis/README.md` describes it the same way. **This direction is the opposite of the NUS network model** (nothing can connect in to the phone). No Communications code connects to 5005.
- `vis/Assets/Scripts` has no code yet that calls the Communications bridge (`CommsStart` and the others). The game logic has no network input.
- The camera hand tracking in the game (MediaPipe `HandLandmarker` in `HandTrackingManager.cs`), and the MediaPipe web hand-landmarker sample and the "Visualiser demo" screen recording that Wen Ree shared in the team chat on 2026-10-14, are Jie Ling's part (the owner's clarification, 2026-10-14). None of them crosses a Communications interface.

**Communications (the owner)**

- The whole chain has run on real hardware with dummy data: two ESP32 boards → laptop → Ultra96 → iPhone (version 2, 32-byte packets; last full run 2026-10-01). Details are in section 4; measured data in 6.1.
- Since 2026-10-14 the code is protocol version 3 (section 4.2). The firmware takes every sample from a glove module. The default builds use the built-in dummy module (11-value dummy rows, no sensors). The `-glove` builds (2026-10-15) use Siqiang's module and send only while it reports MOVING; they compile and link but have not run on a glove. The board service hands each sample to a model through the model interface; without `--model` it uses a built-in dummy model that answers every sample with a random `REST`/`FIST`/`OPEN`/`POINT` at confidence 1.0. The iPhone only displays results as text and triggers no game action; `CommsNextResult` exists in the Swift source and is compiled and tested on Linux, but it is not built for iOS or installed. These three places are the three interfaces to connect with teammates.

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
| 2026-10-14 (evening) | Right board flashed and checked; server certificate renewed locally; protocol version 3, the board model interface, model labels and `CommsNextResult` implemented on branch `comms/protocol-v3`; right board reflashed with version 3 and checked; deploy and board-check tools added (section 6.5) |
| 2026-10-15 | Siqiang answers the questions and pushes his sensor module (`51593be`); gating (send only while MOVING), 36-byte source statistics, the 600 s ingest idle limit, the `-glove` firmware environments, `flash.py --glove` and the capture exporter built on `comms/protocol-v3`; the Swift client compiled and tested on Linux; the C# reference core (`CommsPhoneCore.cs`) compiled and its self-test passed. None of it has run on hardware yet (section 6) |
| **2026-10-20** | **Integration V1 deadline: the team meets in person and integrates together** |
| Around Week 13 | Final version |

The team's expectations are on the "Integration formulation" page of the team Google document: <https://docs.google.com/document/d/1P3-7mIIms9bHz4wJCk0NqZe7pYlBCBmjCKYXMzWKqlc> (append `/mobilebasic` to the URL to read it without signing in).

---

## 3. The owner's role and boundaries

olsonwangyj's own words (2026-10-14):

> I'm responsible for leading the integration, while my main technical responsibility is the communications subsystem. Each teammate remains responsible for the quality and performance of their own component. My role is to ensure that the components communicate correctly and to coordinate the team's work toward a functioning integrated system.

Further clarification the same day: as Communications owner, the owner is responsible only for sending each module's data out and making sure the next module receives it accurately. Nothing else is the owner's. How teammates implement their own parts is not the owner's concern.

**Communications owns:**

- In the firmware: calling the glove module (including its send decision, once per sample), scaling, packing, BLE sending, pairing security and connection management. With Siqiang's module built in (2026-10-15), the owner still writes this firmware; the module itself stays Siqiang's, as an unchanged copy.
- On the laptop: BLE reception, queueing, conversion to network messages, delivery to the board through the SSH tunnel, and ACK checking.
- On the board: receiving samples, de-duplication, replying with ACKs, and pushing results to the subscribed phone.
- On the board, also: calling the model through the model interface (`start(emit)`, `on_sample`) and carrying what it emits to the phone. What the model does is Wen Ree's.
- On the iPhone: the SSH/TLS client, result validation, and the C functions that hand results to Unity: the three existing ones plus the per-result function `CommsNextResult` (written 2026-10-14; compiled and tested on Linux on 2026-10-15, not yet built for iOS; 7.3). Still to do: push `CommsNative` to the team repo with short steps for adding it to the Xcode project.
- Identity, counters and evidence for every segment.

**Not Communications (do not list these as the owner's tasks, and do not ask about them on the owner's behalf):**

- Sensor capture algorithm, calibration, sensor faults, and the movement detector that decides when a glove is MOVING → Siqiang.
- Pairing left and right glove samples, building 50×22 windows, deciding whether a gesture or idle happened, model accuracy and speed → Wen Ree.
- Mapping labels to game actions, cooldowns and repeats, any script in `vis/` → Jie Ling.

**What leading integration means:** defining the cross-module interfaces clearly (format, rate, labels, transport, timing, who connects to whom) and coordinating who delivers what on which day. It does not mean taking on the quality of teammates' components.

### 3.1 Division of work at each hand-over

The owner wants the division as simple and clear as possible: Communications moves data correctly and does nothing else. This table is the single statement of who does what. Section 7 gives the details of each row. It is the owner's proposal of 2026-10-14. Siqiang's row is what he delivered and answered on 2026-10-15; the other rows become final when those teammates confirm them in their replies.

| Hand-over | The teammate does | Communications (olsonwangyj) does |
|---|---|---|
| Glove sensors → glove firmware | **Siqiang:** the sensor module (delivered 2026-10-15, `hardware/gloves/integration_files/`). It returns one sample of 11 floats in the agreed order and units (`gloveBegin`, `gloveUpdate`, `gloveRead`) and decides when the glove is MOVING (`gloveIsMoving`). Calibration, accuracy, sensor faults and the movement detector | Builds an unchanged copy of the module into the `-glove` firmware, calls it, sends a sample only while the module reports MOVING, scales each value to int16, packs the 38-byte packet, sends it over BLE, manages the connection |
| Glove → laptop → Ultra96 | (nobody else) | All of it: BLE reception, the SSH and TLS route, ACKs, reconciliation |
| Ultra96 service → model | **Wen Ree:** `start(emit)` and `on_sample(...)`. Pairing the gloves, building windows, inference, deciding when to produce a result, the label set | Decodes each sample, restores physical floats, calls `on_sample` once per sample, provides `emit`, carries each result unchanged to the phone |
| Phone → game | **Jie Ling:** everything in Unity and the iOS build: the C# that calls the bridge (pushed to `vis/`), what the game does with each result, exporting the project, adding `CommsNative` to the Xcode project, building, and installing the app on their own iPhone with their own Mac | The `CommsNative` library and its functions, the per-result queue (`CommsNextResult`), pushed to the team repo (`ios-visualizer/CommsNative`), short steps for adding it to the Xcode project, and help if the build fails |
| Model ↔ game | **Wen Ree and Jie Ling agree between themselves:** the label names, how often a label is produced, and whether consecutive identical labels (for example several `CHOP`) mean one action or several | Passes every result through as it is. It does not merge, split, filter or reinterpret results |

---

## 4. The Communications subsystem in detail

### 4.1 The full chain

```text
Left  FireBeetle ESP32 (device_id=1) ─┐ BLE GATT notifications, one 38-byte packet per sample
Right FireBeetle ESP32 (device_id=2) ─┴──────────► Windows laptop (BLE central)

Laptop ─TCP→ local 127.0.0.1:18889 ─SSH -L→ stujump:22 → Ultra96:22 → on-board 127.0.0.1:8888 (ingest service)
        inside TLS: SENSOR_BATCH →        ← INGEST_ACK

iPhone ─in-app SSH→ stujump:22 → Ultra96:22 → on-board 127.0.0.1:9999 (result gateway)
        inside TLS: SUBSCRIBE →   ← SUBSCRIBED   ← GESTURE_RESULT

Inside the board service: each new sample → model (start/on_sample; emit hands results back)
Inside the iPhone: Swift client ─C functions, polled every frame by the Unity main thread→ Unity
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

**Protocol version 3 is the only version (since 2026-10-14, branch `comms/protocol-v3`).** It replaced versions 1 and 2 everywhere, by the owner's rule that only the newest version is supported (section 8, step 1). Nothing on the wire accepts version 1 or 2 any more; every component is upgraded together. The full specification is `docs/co-protocol-v3.md`. **The layout is provisional only for the scale check:** it is frozen after the scales are checked against Siqiang's real samples and Wen Ree agrees (section 13). The IDLE/MOVING question is settled: the state does not travel in the packet. By Siqiang's answer (2026-10-15) a glove sends samples only while his detector says MOVING, so every sample sent is a MOVING sample (4.3).

**BLE sensor packet: 38 bytes, little-endian, Python format `<2sBBIII11h`**

| Offset | Length | Field | Value |
|---|---|---|---|
| 0 | 2 | Marker | ASCII `LC` (`4C 43`), the only marker accepted |
| 2 | 1 | Version | 3, the only value accepted |
| 3 | 1 | `device_id` | 1 = left, 2 = right (compile-time constant) |
| 4 | 4 | `boot_id` | A random number drawn once per power-up |
| 8 | 4 | `seq` | Starts at 0 on each power-up and adds 1 per sample sent. A number is not reused after a failed submission. A send tick that sends nothing (the glove is IDLE, has no valid reading, or the sample is refused by scaling) takes no number, so it shows as a longer `uptime_ms` step, not as a `seq` gap |
| 12 | 4 | `uptime_ms` | This board's own `millis()`, read right after the glove module's reading. The two boards are not synchronised |
| 16 | 22 | 11 × int16 | `ax ay az gx gy gz yaw pitch roll flex1 flex2`, from the glove module: Siqiang's module in the `-glove` builds, otherwise the built-in dummy module (rows of `common/dummy_fixtures.json`) |

| Index | Field | Unit delivered by the sensor module | Scale (physical = int16 / scale) | int16 range |
|---|---|---|---|---|
| 0–2 | `ax` `ay` `az` | g, gravity removed | ×10000 | ±3.2767 g |
| 3–5 | `gx` `gy` `gz` | °/s, bias removed | ×100 | ±327.67 °/s |
| 6–8 | `yaw` `pitch` `roll` | degrees | ×100 | ±327.67° |
| 9–10 | `flex1` `flex2` | 0.0–1.0 | ×10000 | maximum 3.2767 |

A 38-byte notification needs ATT MTU ≥ 41 (firmware `sensorFitsMtu`, laptop `SENSOR_MTU_FLOOR`). The measured negotiated MTU is 517. The application-layer byte rate is 38 × 50 Hz × 2 boards = 30.4 kbps at most; a gated glove sends less, and nothing while the player is still. One board at 50 Hz with 38-byte packets was measured clean for 65 s on 2026-10-14 (6.1); two boards together with 38-byte packets have not been measured. The deterministic-formula dummy mode (old version 1, `COMMS_LEGACY_DUMMY`) no longer exists; `-DCOMMS_FIXTURE_SEED=<n>` still makes the fixture choice reproducible.

**Source statistics: 36 bytes, `<4sBB2xIIIIIII` (since 2026-10-15)**: marker `LCS3`, `device_id`, `flags` (bit 0 = gated: the board skips the send ticks its glove module calls IDLE; the other bits are 0), 2 reserved zero bytes, then seven uint32 totals since boot: `boot_id`, `next_seq`, `submitted` (successful submissions), `failures` (failed submissions), `idle` (ticks the glove module called IDLE), `unread` (ticks without a valid reading), `refused` (samples refused by scaling). `idle`, `unread` and `refused` count ticks that sent nothing and took no `seq`. The laptop accepts exactly 36 bytes, the marker `LCS3`, zero reserved bytes, and no flag other than bit 0. It reads them once before subscribing and twice at shutdown (after turning notifications off, and again to confirm nothing changed; 4.4). They are used for the reconciliation "generated on the board = received by the laptop = acknowledged by the Ultra96" and, for a gated board, for its coverage (4.4). The 24-byte `LCS3` format of 2026-10-14 ran only on the right board, so the marker was kept. Any 24-byte value (that format, or version 2's `LCS1`) is refused before subscribing with `source statistics must contain exactly 36 bytes; flash this board with the current firmware`; a 36-byte value with another marker gets `invalid source statistics magic; flash this board with the current firmware`.

**BLE control frame: 14-byte header, marker `B7`** (the team number B07, not Week 7): control version 1, opcode, `device_id`, status, `id`, `offset`, followed by at most 180 bytes of payload. Opcodes: command (1), rate (2, 1 to 200 Hz), file begin/chunk/end/abort (`0x10` to `0x13`, at most 65536 bytes, checked with SHA-256). The control channel needs MTU ≥ 64. A command carries one whole version-3 packet, so a command frame and its answer are 52 bytes; the board adds 1 to each of the 11 values (32767 wraps to -32768) and puts its own clock in `uptime_ms`. Commands do not go through the glove module, so a gated board answers them whether the glove is MOVING or IDLE.

**Network frame:** 4-byte big-endian length + a strict UTF-8 JSON object, with a body of 1 to 16384 bytes. The field set must match exactly. **There is no error message; on an error the connection is closed.**

| `type` | `v` | On-board port | Direction | Fields besides `v`, `type`, `session_id` |
|---|---|---|---|---|
| `SENSOR_BATCH` | 3 | 8888 | laptop → board | `device_id`, `boot_id`, `seq`, `uptime_ms`, `values` (11 int16), `request_id` |
| `INGEST_ACK` | 3 | 8888 | board → laptop | `device_id`, `boot_id`, `seq`, `status` (`accepted` or `duplicate`), `request_id` |
| `SUBSCRIBE` | 1 | 9999 | phone → board | None |
| `SUBSCRIBED` | 1 | 9999 | board → phone | None |
| `GESTURE_RESULT` | 3 | 9999 | board → phone | `device_id`, `boot_id`, `seq`, `request_id`, `result_id`, `gesture`, `confidence` (10 keys in all) |

- `session_id` defaults to `ltc-comms` everywhere. Laptop, board service and phone must agree. On a mismatch the board closes the connection. It is configuration, not a password.
- The subscription envelopes stay at `v` 1: they never carried the packet version and did not change.
- `request_id` is always present in the three version-3 messages. It is `null` for ordinary samples and for model results. For keyboard commands it is 1 to 4294967295 and equals `seq`.
- `result_id` is `device_id:boot_id:seq`. Results of commands get the prefix `cmd:`. The phone uses it to de-duplicate, so a model result must name one sample, and a second result for the same sample is refused on the board.
- `gesture`: any label of 1 to 32 characters from `A–Z a–z 0–9 _ -` (the six model classes `PICKUPHOLD`, `PLACEDOWN`, `CHOP`, `WASH`, `THROW`, `FIREEXT` fit). Communications does not know the label set; Wen Ree and Jie Ling agree it.
- `confidence`: a JSON number (not a boolean), finite, from 0 to 1; integers 0 and 1 are allowed.
- The same rules are checked by the board before sending and by every receiver (`ultra96/protocol.py`, `phone/receiver.py`, `phone/unity/CommsPhoneCore.cs`, `CommsCore/Protocol.swift`). A result the phone rejects ends the phone session, so the board refuses an invalid model result before it is sent.

### 4.3 Firmware (`firmware/esp32/`)

- PlatformIO + Arduino framework, board `firebeetle32`. `platformio.ini` has six build environments:
  - the default `firebeetle32` (`default_envs`; protected; ID 1, because `COMMS_DEVICE_ID` defaults to 1). `platformio run` without `-e` builds it, so flashing it onto the right board makes that board ID 1;
  - `firebeetle32-left` (ID 1);
  - `firebeetle32-right` (ID 2);
  - `firebeetle32-left-glove` (ID 1) and `firebeetle32-right-glove` (ID 2), added 2026-10-15 for the real gloves: they link Siqiang's module (`COMMS_GLOVE_MODULE=1`), send only while it reports MOVING, and start at 50 Hz (`COMMS_INITIAL_RATE_HZ=50`). `[env]` sets `lib_ignore = glove_sensor`, and only these two environments clear it;
  - the unprotected diagnostic environment `firebeetle32-unprotected-diagnostic`, which must be named explicitly.

  The first three and the diagnostic one use the built-in dummy module. The verified combination is Espressif32 7.1.0 + Arduino-ESP32 2.0.17. `platformio.ini` does not pin the versions. Build sizes on 2026-10-15: the dummy `firebeetle32-right` uses 7.5% of RAM (39964 bytes) and 85.6% of flash (1121625 bytes); the `-glove` builds use 7.9% of RAM (42196 bytes) and 87.6% of flash (1148437 bytes right, 1148433 left).
- Advertised name `LTC-COMMS`, the same on both boards. They are told apart by Bluetooth address and by the `device_id` in the packet. Service UUID `6e1c0001-7a45-4dc4-b678-3f2d5a9c1001`, with 7 characteristics.
- Security: LE Secure Connections + MITM + bond. The board can only display (DisplayOnly). The 6-digit passkey is printed only on the local serial port, and the operator types it on Windows. The application adds one more gate: notifications are sent only when all three authentication-mode bits (SC, MITM, bond) are set.
- **The glove module API (`include/comms_glove.h`, 2026-10-15).** The firmware takes samples only through four plain functions: `bool gloveBegin()` (once in `setup()`, before BLE starts; may block for calibration; `false` = no sensor, and the board still advertises), `void gloveUpdate()` (every main-loop pass, connected or not), `bool gloveRead(float out[11])` (at a send tick, only while the laptop is connected and subscribed) and `bool gloveShouldSend()` (right after a successful `gloveRead`: `true` = MOVING, send; `false` = IDLE, skip). Build switches:
  - `COMMS_GLOVE_MODULE`: 0 (default) links the built-in dummy module `src/dummy_glove.cpp`, which returns the fixture rows as physical floats (int16 / scale; scaling them back gives the same int16, so the dummy packets keep their bytes); 1 links an external module. In the `-glove` environments that is Siqiang's module, an unchanged copy in `lib/glove_sensor/` (with the weights header also in `firmware/esp32/movement_model_params.h`) made by `python -m tools.sync_glove_module`. His `gloveBegin`, `gloveUpdate` and `gloveRead` have exactly these signatures; `src/glove_module.cpp` maps `gloveShouldSend()` to his `gloveIsMoving()`, which is false until his classifier has filled its first 1 s window;
  - dummy module only: `COMMS_DUMMY_MOVING_MS` (default 3000) and `COMMS_DUMMY_IDLE_MS` (default 0 = never IDLE). With an idle time, the dummy repeats from boot: MOVING for the moving time, then IDLE for the idle time (`include/comms_dummy_gate.h`, `dummyMoving`). This is the gated test build for boards without sensors;
  - external module only: `COMMS_GLOVE_SEND_ALL=1` sends every sample, IDLE included (for recording sessions);
  - the source is "gated" (`kGloveGated`) for the external module without `SEND_ALL`, and for the dummy with an idle time above 0. The source statistics report it in their flags (4.2).
- Each pass of the main loop: read serial commands → `gloveUpdate()`, outside the connection-state mutex → under the mutex: check the send tick for the current rate; only when authenticated, subscribed and the MTU is large enough, mark a sample as due → release the mutex → `produceSample()` (`firmware/esp32/src/main.cpp:404-431`): fill the 11 values with NaN, `gloveRead`, `gloveShouldSend` (only after a successful read), take `uptime_ms`, then `prepareSample` decides the outcome, all **outside the mutex**. Then, under the mutex again: if the laptop is still ready, commit the tick's counters and, only for a sample to send, allocate `seq`, pack, submit the notification and record success or failure; if the link changed meanwhile, nothing is counted, no `seq` is taken, and `race_dropped` rises → handle at most one control request per pass → print `alive` and `comms_stats` once a second. So once the laptop has turned notifications off, the source statistics no longer change (the bridge checks that at shutdown, 4.4).
- **The sample policy (`include/comms_sample.h`):** `prepareSample` gives one of four outcomes per tick. No valid reading → `unread`; IDLE → `idle` (the values are not scaled); a sample `scaleSample` refuses → `refused`; otherwise send. Only a sample to send takes a `seq`, so the other three show only as a longer `uptime_ms` step. `scaleSample` scales 11 physical floats to int16 with the scales in 4.2, rounding half away from zero. NaN or infinity always refuses the sample (a channel the module leaves unwritten stays NaN). A value outside int16 is clamped and counted (`clamped`) by default; building with `-DCOMMS_OUT_OF_RANGE_DROP=1` refuses the whole sample instead. The policy is provisional until Wen Ree answers (section 13).
- **The send tick keeps its rate (`sendTickDue`, `include/comms_sample.h`).** The next deadline is one interval after the previous deadline, not after the pass that noticed it. A slow pass (a glove module call of a few milliseconds) delays one tick without lowering the rate, as long as one pass stays shorter than the interval (20 ms at 50 Hz). A tick more than one interval late restarts from now: ticks a long stall covered are dropped, never sent as a burst.
- On boot the board first prints `glove_begin ok=<0|1> module=<dummy|external> gated=<0|1>`, then, once BLE is up, `comms_ready device_id=<1|2> packet_bytes=38 packet_version=3 rate_hz=10 protected=1 control_version=1 file_max_bytes=65536 glove=<dummy|external> gated=<0|1>` (`rate_hz=50` in the `-glove` builds). The once-a-second `comms_stats` line also prints `unread`, `idle`, `refused`, `clamped` and `race_dropped`. `clamped` and `race_dropped` are only on the serial line, not in the source statistics.
- While disconnected, no samples are produced, `seq` does not advance, and there is no offline buffer; `gloveUpdate()` keeps running. The rate is kept across a disconnect; only a reboot restores the build's default (10 Hz; 50 Hz in the `-glove` builds).
- There is only one serial command: `erase-bonds` (clear bonds, used to recover pairing).
- The policy logic is all in portable C++11 headers (`include/comms_*.h`). They compile and run as host tests without flashing a board (six programs, `test/host_*.cpp`). pytest compiles them with `g++` or `clang++`, whichever is on PATH, and skips them when neither is found. `main.cpp` and the two module files compile only in the board build.

**`flash.py`:** it first generates the dummy-data header and builds the left and right firmware, then prompts you to plug in the boards. **The first board plugged in is flashed as LEFT (ID 1); the second as RIGHT (ID 2).** It reads the factory MAC, adds 2 to get the Bluetooth address, and writes that into `.comms-local/boards.json`. **`python flash.py --glove`** (2026-10-15) flashes the real gloves: like the plain run it first regenerates the dummy-data header, then runs `python -m tools.sync_glove_module --check` and stops if a copy of Siqiang's module is out of date, then builds and flashes `firebeetle32-left-glove` and `firebeetle32-right-glove` in the same order. Other uses: `--ports`, `--boards`, `--pair [left|right|both]`, `--monitor COMx`. It works only on Windows.

**One board only** (the laptop has one programming cable, so the COM number says nothing about which board is attached): read the factory MAC first (`esptool.py --chip esp32 --port COMx read_mac`; Bluetooth address = MAC + 2; left `38:18:2B:19:82:AE`, right `38:18:2B:18:9D:6A`), then `platformio run -d firmware/esp32 -e firebeetle32-right -t upload --upload-port COMx` (or `-left`, or a `-glove` environment). This leaves `.comms-local/boards.json` unchanged. Then check that board alone with **`python -m tools.check_board right`** (or `left`): real BLE, the laptop relay, a service started on the laptop with throwaway certificates and the dummy model, and a local subscriber. By default it runs 65 s at 50 Hz, sends 3 commands, stops the stream normally so the source statistics reconcile, and prints `CHECK PASSED` only when generated = received = acknowledged with no error, the rate and MTU are confirmed and every command and sample got its result. Its summary line also prints `gated`, `idle`, `unread` and `refused`; idle ticks do not fail the check. No SSH, Ultra96 or phone is involved. Reflashing the application does not erase the bonds: on 2026-10-14 Windows kept its authenticated bond with the right board through two reflashes, and no new pairing was needed.

### 4.4 Laptop (`laptop/`, `demo.py`, `tools/`)

- `laptop/bridge.py` is the full path for one glove. `laptop/dual_bridge.py` runs two uncoupled `Bridge` instances at the same time, and `demo.py` calls it. **Each board has its own BLE connection, queue and TLS connection.** One board stalling does not affect the other.
- Per board: scan (by service UUID and address, 8 s limit) → connect (without the cached GATT table, 20 s limit) → confirm MTU ≥ 41 → confirm that the Windows bond is "encrypted and authenticated" → read the starting source statistics → subscribe to notifications. Both boards must be ready within 30 s.
- The BLE callback records the arrival time and copies the bytes into the board's bounded queue (64 entries; when full, the oldest is dropped). It also decodes the packet once to count goodput, hands a `sensor` or `sensor_invalid` record to the evidence thread, and updates the callback and silence counters. It does no network operations.
- Writer task: decode → check `device_id`, sequence number and connection generation → **drop samples that waited on the laptop for more than 2 s** → write `SENSOR_BATCH` → check each `INGEST_ACK` in send order. At most 32 frames are in flight at once (ACK window).
- **No retransmission.** When TLS drops, a write times out, or an ACK times out or does not match, that TLS connection is discarded. Frames already attempted are counted as ambiguous (`ambiguous_dropped`) and are not resent. The bridge reconnects after back-off (from 0.5 s, doubling, up to 5 s).
- Tail handling at shutdown: turn notifications off on the remote side while keeping the local callback, read the source statistics once, wait for the last packets to arrive, then read again to confirm nothing changed. This way losses at the start and end are reconciled too.
- **Source statistics in the report (2026-10-15, `laptop/source_audit.py`):** per board, `gated` (from the last snapshot), `source_idle`, `source_unread` and `source_refused` (differences within one power-up, otherwise empty) and `source_ticks` = generated + idle + unread + refused. `clean` keeps its rules; idle ticks never affect it.
- **Coverage per board (`board_coverage` in `laptop/dual_bridge.py`).** An ungated board must deliver at least 90% of the expected samples in the common window, with no silence longer than the 2 s freshness limit (unchanged). A gated board passes coverage when generated + `source_idle` ≥ 0.9 × `source_ticking_seconds` × the expected rate. `source_ticking_seconds` runs from the bridge's first sensor subscription to the quiesce read at shutdown, the same interval the board's counters cover (`laptop/bridge.py`). Its silence is not judged once it has reported idle ticks, because a still player is silent. The report gives each board's `coverage_expected` and `coverage_ratio` (covered / expected), the progress line prints `gated=yes|no|unknown`, and the `demo.py report` table has `Gated` and `Idle` columns.
- At the end it writes `report.json` (a placeholder first, then an atomic replace) and `packets.jsonl`. It prints `CAPTURE PASSED` only when everything matches.
- Pairing uses a custom WinRT flow (`laptop/windows_pairing.py`), because Bleak's own `pair()` may lower the protection level. **The laptop side supports only Windows.**
- Control channel: keyboard `1`/`2` send commands, `--rate` sets the rate, `--file` transfers a file. Commands use a separate TLS connection and are not retried after a timeout.

The five `demo.py` subcommands:

| Command | What it does |
|---|---|
| `python demo.py tunnel` | Opens the two-hop SSH local forward: local `127.0.0.1:18889` → on-board `127.0.0.1:8888`. Keep this terminal open |
| `python demo.py run` | Captures both boards for 60 s (default 10 Hz; it sets both boards to that rate, so use `--rate 50` with the `-glove` builds) and writes the report and evidence to `.comms-local/`. Its `Phone expected increase` assumes one result per accepted input, which holds only for the built-in dummy model (the line printed under it says so) |
| `python demo.py live` | Like `run`, but captures for 120 s by default and enables keyboard commands. Needs an interactive terminal |
| `python demo.py report [path]` | Re-checks the latest capture or the one given |
| `python demo.py service [--start]` | Inspects the board service over SSH. `--start` starts it in the foreground when both ports are free, from the folder and with the `--model`/`--model-path` of the service the newest local deployment record left running (`.comms-local/deployments/`), otherwise from the 28 September folder with the dummy model |

Other operator tools added on 2026-10-14: `python -m tools.check_board left|right` (one board, see 4.3) and `python -m tools.deploy_service` (upload, certificate and swap on the Ultra96, see 4.5 and 6.3). Added on 2026-10-15:

- `python -m tools.export_capture [capture folder or packets.jsonl] [--out FILE] [--device 1|2]` writes a capture's samples as CSV, one row per sample: `device_id`, `glove`, `boot_id`, `seq`, `uptime_ms`, then the 11 values in physical units (int16 / scale, 4 decimals), de-duplicated, in arrival order. By default it reads the newest capture under `.comms-local/` and writes `samples.csv` beside it; it never overwrites a file, and it warns when the capture dropped evidence records. It lets Siqiang record through the chain (answer F, 2.3).
- `python -m tools.sync_glove_module [--check]` copies Siqiang's module into the firmware, or with `--check` only compares (exit 1 if a copy differs; line endings are ignored). See 4.3.
- `python flash.py --glove` (4.3).

### 4.5 Ultra96 service (`ultra96/`)

- A standard-library-only asyncio process: `/usr/bin/python3 -u -m ultra96.server --cert … --key … [--session-id ltc-comms] [--ingest-port 8888] [--gateway-port 9999] [--event-log-dir <new directory>] [--model MODULE] [--model-path DIR] [--ingest-idle-timeout SECONDS]`. It runs as an ordinary user. It is not a system service, has no automatic restart, and does not use sudo (the board is shared). On start it prints `{"event": "model_ready", "model": …, "seconds": …}` and then the `listening` line; a model that cannot be imported or whose `start(emit)` raises prints `{"event": "model_failed", …}` and the service exits without opening its ports.
- How it was started decides what keeps it alive:
  - Started with `demo.py service --start`, it is the foreground process of that SSH session (`ssh -tt`) and exits when that terminal goes away.
  - The process recorded on the board (2026-09-28) was not started that way. The untracked script `.week7-local/co_deploy.py` launched it in the background with `subprocess.Popen(..., start_new_session=True)`. Its output goes to `BOARD_ROOT/evidence/`, and its PID is in `BOARD_ROOT/evidence/server.pid`. It does not depend on any SSH session and may still be running. Look for it when redeploying (6.3, step 1).
  - `python -m tools.deploy_service` (added 2026-10-14, the tracked successor of `co_deploy.py`) starts the service the same way, in the background in its own session, and replaces a running one of this user only after checking it (6.3).
- Both TLS listeners bind only to `127.0.0.1`. The service never dials out. The two ports together accept at most 8 concurrent connections (`MAX_CLIENTS`). Since 2026-10-15, when all 8 are taken, the ingest connection that has waited longest for its next frame is closed to admit the new client, provided it has waited at least 5 s (`INGEST_EVICTABLE_AFTER`; metric `idle_evicted` and a warning log line). Connections in the middle of streaming are never displaced; if none may go, the new client is refused (`client_limit`), as before.
- **Ingest port 8888:** read the frame → check fields and session → de-duplicate → for a new stream sample, call the model's `on_sample` (see below); for a new command, answer with one `cmd:` echo result itself → reply `INGEST_ACK`. A duplicate gets only `duplicate` and reaches neither the model nor the phone. **Since 2026-10-15 an ingest connection may wait up to 600 s for its next frame to begin** (`--ingest-idle-timeout`, 5 to 86400 s; constructor argument `ingest_idle_timeout`; `INGEST_IDLE_TIMEOUT`); once the first header byte has arrived, the rest of the frame must arrive within 5 s (`common/wire.py` `read_frame(..., idle_timeout=...)`). A connection closed for idleness counts in `rejected`. The reason is gating: a gated glove is silent while the player is still (5). The gateway port is unchanged.
- **Gateway port 9999:** a valid `SUBSCRIBE` registers that connection as the current subscriber and gets `SUBSCRIBED` back. **There is one subscriber at a time; a newcomer replaces the existing one.** The result queue holds 32 entries; when full, the oldest is dropped. A result that has been in the queue for 2 s is dropped. With no subscriber, results are dropped at once and never sent later.
- **The model interface (`ultra96/model.py`, built 2026-10-14; the names are the proposal to Wen Ree, 7.2).** The service loads a model: `--model MODULE` imports a module (from `--model-path DIR` first, if given) that has plain functions `start(emit)` and `on_sample(device_id, boot_id, seq, uptime_ms, values)`; without `--model` it uses the built-in dummy model. `start(emit)` runs once before the ports open. `on_sample` runs on the event-loop thread for each new stream sample, before that sample's ACK is written, with `values` as 11 floats in physical units (int16 / scale). Its exceptions, including `SystemExit`, are counted (`model_errors`) and never close the connection; calls longer than 5 ms are counted (`model_slow_calls`). A `SystemExit` while importing the model or in `start(emit)` ends in `model_failed` and a nonzero exit. `emit(gesture, confidence, device_id, boot_id, seq)` may be called from any thread; it returns `True` when the arguments are valid and the service is running (numpy-style numbers are converted), `False` otherwise. On the event loop the service then refuses a result whose glove power-up `(device_id, boot_id)` it has not seen or whose `seq` is above the highest accepted `seq` of that power-up (`model_results_rejected`; `ultra96/server.py:352-357`), or a result for a sample that already had one (`model_results_duplicate`, last 4096 kept), and otherwise sends a `GESTURE_RESULT` with `request_id: null` like any other result. A `seq` inside a gap (a sample lost before the board, so never accepted) is not detected: a result naming it is sent with a `result_id` for a sample the board never saw. Commands never reach the model.
- **The built-in dummy model** answers every accepted sample with one random `REST`, `FIST`, `OPEN` or `POINT` at confidence 1.0, so one accepted input still gives one result and every existing acceptance check still holds.
- De-duplication and replay protection live only in memory. For each `(device_id, boot_id)` the service keeps a sequence high-water mark that only rises, plus the latest 4096 fingerprints; a sample at or below the mark that is not among them is refused and the connection closed. One process lifetime allows at most 128 `(device_id, boot_id)` pairs and 4096 commands. After that the service must be restarted.
- If the model left non-daemon threads running, the stopped service prints `{"event": "exit_with_model_threads", …}` and exits anyway, so it cannot linger without ports.
- The `stopped` line printed at shutdown includes the model counters: `model_samples`, `model_results`, `model_errors`, `model_slow_calls`, `model_max_call_ms`, `model_results_rejected`, `model_results_duplicate`, `model_results_late` (emitted after the service stopped).
- The optional event log (`--event-log-dir`) is written on a background thread, capped at 50 MiB. Its `result_write_complete` only says that the board wrote the result into the connection. **It does not say that the phone received it.** `result_accepted` means an input was accepted, not that a result exists; model results add `model_result` and `model_result_refused` (with `reason` `unknown_identity` or `duplicate`).
- Certificates are generated by `tools/generate_comms_pki.py`: a CA (365 days) and a server certificate (**30 days**; CN and SAN are both `ultra96.week7.internal`). The server loads only the server certificate and key. Clients hold only the CA certificate. The CA private key never leaves the machine that generated it. Only the server is authenticated; there are no client certificates (SSH handles access control).

### 4.6 Phone client and the Week 7 receiver (`ios-visualizer/`, `phone/`)

**The current phone client is the Swift package `ios-visualizer/CommsNative`.**

- The user taps `Communications Connect` and enters the board's and the jump host's user names and passwords in a form. The first time, the CA certificate must also be imported. The app then builds: TCP to `stujump:22` → SSH (compare against the pinned host public key; password authentication) → `direct-tcpip` to the board's port 22 → a second SSH layer → `direct-tcpip` to `127.0.0.1:9999` → TLS (check CA, host name, validity) → send `SUBSCRIBE` → receive `SUBSCRIBED`. The whole process is limited to 10 s.
- After that it only receives results: unframe, validate (version 3, the 10 keys, the label and confidence rules of 4.2), de-duplicate by `result_id` (latest 4096), add 1 to `Received`, keep the latest result for the display, and (since 2026-10-14; compiled and tested on Linux, not yet built for iOS) put the result in the per-result queue that `CommsNextResult` empties. After 2 s without a new result the displayed label is cleared; the count stays. After subscribing there is no idle limit. Only a frame that has started but not finished is given 5 s.
- Errors fall into two classes. Network errors (connection dropped, timeout) trigger automatic back-off, reconnect and resubscribe. Authentication, trust and protocol errors (wrong password, host key mismatch, expired certificate, a result that fails validation) **end the session at once: no retry, and the passwords are cleared**. The user must enter the passwords again to reconnect.
- Passwords are kept only in memory. **As soon as the app stops being active (screen lock, going to the background, pulling down Control Center or Notification Center, an incoming call), it disconnects at once and clears the passwords.** Back in the foreground the user must connect again by hand, and the count starts from 0.
- Host names, both SSH host public keys, the CA fingerprint and the session ID are compiled into the app. Changing the board, the CA or the session ID means changing the source, rebuilding and reinstalling.

**Build status of the Swift package (2026-10-15): compiled and tested on Linux in a Swift 6.1 container (72 tests); not yet built for iOS.** The changes of 2026-10-14 were written without a Swift toolchain. On 2026-10-15 `swift build --build-tests` and `swift test` ran on a copy of `ios-visualizer/CommsNative` in the Docker image `swift:6.1` (Swift 6.1.3): 72 tests, 0 failures, in 6 runs (ConfigurationTests 6, DisplayMailboxTests 4, DisplayStateTests 15, ProtocolTests 13, TransportTests 26, TrustTests 8). No Apple SDK is available here, so the code under `#if os(iOS)` and `PythonBoardTests` were neither compiled nor run, and nothing was built for iOS or macOS. One fix was needed for Linux (`6583f9d`): `Configuration.swift` imports CryptoKit and Security only where they exist (swift-crypto stands in on Linux; the Security certificate parse is skipped on Linux only, and the CA fingerprint check still admits only the enrolled CA), and `Package.swift` links swift-crypto's `Crypto` into `CommsBridge` on Linux only. iOS builds are unchanged by it. Swift 6.1 is the minimum toolchain, because the pinned dependencies need tools version 6.1; the Mac needs Xcode with Swift 6.1 or newer.

**The C functions for Unity (`Sources/CommsBridge/DisplayMailbox.swift`).** The installed Week 7 build (the same package under its earlier name `Week7Native`, built on 2026-09-28) has the first three only under their Week 7 names, `Week7Start`, `Week7CopyDisplay` and `Week7Stop`, which the patched export calls. The `Comms*` names (added 2026-10-08), `CommsNextResult` and the display-text and validation changes of 2026-10-14 are in the source only and have never been installed.

| Function | Semantics |
|---|---|
| `void CommsStart(void)` | Installs the button and the foreground/background notifications. **Does not start a connection**; only the user tapping the button and entering passwords starts one. Call it once |
| `int32_t CommsCopyDisplay(char* buffer, int32_t capacity)` | Takes one snapshot and builds four lines of UTF-8 text. If the text differs from what was last delivered and fits, it writes the text into the buffer (with a terminating 0) and returns the byte count. Otherwise it returns 0 and writes nothing. It never returns a negative number |
| `void CommsStop(void)` | The status changes to `Stopped` at once; everything is removed and the passwords are cleared. Call it only when the app truly stops using Communications |
| `int32_t CommsNextResult(char* buffer, int32_t capacity)` | Takes out the oldest waiting result as one compact JSON object, `{"result_id":"…","gesture":"…","confidence":…,"device_id":…}`, with a terminating 0, and returns its byte count. Returns 0 when nothing waits. When the buffer is null or smaller than the bytes plus the 0, it writes nothing, keeps the result and returns minus (bytes + 1). Details in 7.3 |

The four lines of text (the source since 2026-10-14; the installed Week 7 build still shows `Week 7 • DUMMY inference` on line 1 and `confidence 1.0` on line 3):

```text
Communications
<status>
<gesture>  |  <result_id>  |  confidence <the received confidence>        (when there is no new result, this line is No live result)
Received: <N>
```

Rules for the caller: only one poller; poll on the main thread every frame; use a 2048-byte buffer; decode as UTF-8; **use `result_id` to decide whether a result is new, not the label text**; do not call `CommsStop` on a scene change or when going to the background.

What the text can and cannot tell the game:

- The status `Subscribed` means only that the subscription handshake with the Ultra96 succeeded. It does not prove that results are flowing.
- Line 3 holds only the latest result, and the next result overwrites it. Results that arrive between two polls can be lost: if `CHOP` and then `PLACEDOWN` arrive between two frames, the game sees only `PLACEDOWN`. Comparing `result_id` stops the game acting twice on one result, but it cannot recover an overwritten one. `Received` still counts every result.
- So the text is a status display, not a game input. The game's actions are one-shot events, so the game needs results one at a time, not a display that the next result overwrites. That is `CommsNextResult` (7.3): each result that reaches the phone and is not dropped can be taken out at most once; it does not promise that every result is delivered. It is compiled and tested on Linux, but not yet built for iOS or installed.

**What "Week 7 receiver" means exactly (confirmed by the owner):** the `CommsNative` Swift client on the iPhone (the copy installed on 2026-09-28 was built from this package under its earlier name, `Week7Native`), plus the bridge in the Unity export that calls `Week7Start` / `Week7CopyDisplay` / `Week7Stop`. It is the receiver made temporarily for the Week 7 demo:

- The Unity source project was not available at the time, so it patches the generated code of one specific Unity export (`ios-visualizer/xcode-export/`, fork only). `ios-visualizer/tools/patch_export.py` rewrites four methods of Jie Ling's `TlsDataReceiver`: `Start` calls `Week7Start()`; `ListenLoop` is emptied, so the 5005 listener no longer runs; `Update` calls `Week7CopyDisplay(buffer, 2048)` every frame and writes the text into the label; `OnDestroy` calls `Week7Stop()`. `configure_xcode.py` links `CommsNative` into `UnityFramework`.
- The patch is locked to file hashes and accepts only that one export. It refuses an export made again from `vis/`.
- **It only displays text and has never triggered a game action.**
- **The `week7` names inside it are not touched**: the three `Week7*` wrapper functions, the old iOS data directory `Application Support/Week7`, the app display name `Week 7 Visualizer`, and the comments and temporary-file prefixes in the patch scripts.

**What is under `phone/` is for reference and diagnostics. It is not the receiver deployed on the iPhone:** `phone/receiver.py` (Python, Termux/iSH), `phone/unity/CommsPhoneCore.cs` and `CommsPhoneReceiver.cs` (Android reference; the phone must open its own SSH local forward to `127.0.0.1:19999`), and `phone/ish_control.py` (temporary maintenance script for the iSH route).

**Build status of the C# reference (2026-10-15): the core `CommsPhoneCore.cs` compiles, and its self-test passed (113 checks, PowerShell 7); the Unity component was checked by reading only.** `phone/unity/CommsPhoneCore.cs` compiled on its own at C# 7.0 with 0 errors and 0 warnings, against the .NET 10 libraries (not .NET Standard 2.1, which Unity uses). `pwsh -NoProfile -File phone/tests/run_core_tests.ps1` (PowerShell 7.6.7) passed 113 checks in 4 runs. No C# change was needed. `CommsPhoneReceiver.cs` (the Unity component) was checked by reading only. One behaviour differs from the iOS client: the Android reference empties its result queue at every new connection, automatic reconnects included (`phone/unity/CommsPhoneCore.cs:387` and `:426`), while the iOS queue keeps results across an automatic reconnect (they still expire after 2 s).

### 4.7 Evidence levels (none replaces another)

| Level | Evidence | Proves | Does not prove |
|---|---|---|---|
| 1 | Source statistics on the board: `submitted` | The Bluetooth stack accepted the notification submission | That the laptop received it |
| 2 | Laptop counts. `callback_received` is the BLE callback count; the progress line prints it as `received=`. The report's per-board `received` counts packets the writer task dequeued and processed. The two differ when the queue drops packets | `callback_received`: the BLE callback got the bytes. `received`: the writer task took them from the queue | That the board received it |
| 3 | `INGEST_ACK` | The board service validated and accepted this input, and (for a stream sample) that the model's `on_sample` returned | That the phone received it; that the model produced a result |
| 3a | Board counters `model_samples` / `model_results` (the `stopped` line) and the events `model_result` / `model_result_refused` | How many samples went to the model and how many of its results the board accepted for sending | That a result reached the phone |
| 4 | Board event `result_write_complete` | The board wrote the result into the connection | That the phone validated or displayed it |
| 5 | `Received: N` on the phone screen (read by a person) | Within this connection the phone accepted N distinct results | Individual IDs; that a game action was triggered |

Since 2026-10-15 the level-1 source statistics also count the ticks that sent nothing (`idle`, `unread`, `refused`; 4.2). They show that the board kept ticking, not that anything was sent. The `CAPTURE PASSED` printed by `demo.py` is level 3. The phone sends no application-level acknowledgement and keeps no per-result record. For the phone level, a person compares the increase in `Received` with `Phone expected increase`; that comparison is valid only while the board runs the built-in dummy model (one result per accepted input). `tools.check_board` reaches level 3 plus the results on a local subscriber, all on the laptop.

### 4.8 Trust material

| Material | Who holds it | Notes |
|---|---|---|
| CA private key `ca-key.pem` | Only the owner's laptop (outside the repository) | Never on the board, never on the phone |
| CA certificate `ca-cert.pem` | Laptop (`--ca`); iPhone (imported) | The current CA's SHA-256 is `4dfba4905c171e68c3623dbc952154149076ed89004b85d475e858cc550760ec`, valid until 2027-09-06. This fingerprint is pinned in `Configuration.swift` |
| Server certificate and key | `tls/` in the Ultra96 deployment directory | **The certificate deployed in September expired on 2026-10-06.** The date was read from the laptop's copy; whether the board's certificate was replaced later has not been checked. **A renewed pair** (same CA, CN/SAN `ultra96.week7.internal`, valid 2026-10-14 14:22:35 to 2026-11-13 14:27:35 UTC) is in `~/.codex/private/cg4002-comms-server-20261014/` on the owner's laptop, outside the repository. It is not on the board yet: `tools.deploy_service --server-cert-dir` installs it (6.3) |
| Both SSH host public keys | The laptop's `known_hosts`; the iPhone source | No trust on first use |
| SSH passwords | Only the operator | The laptop enters them at the OpenSSH prompt. The phone keeps them only in memory |
| BLE bond keys | One copy each on the ESP32 and on Windows | The passkey is shown only on the board's serial port |

### 4.9 Where documents and code disagree (the code wins)

- `vis/README.md` says "the phone runs a TLS server on port 5005". The direction is the opposite of the network model. In the Week 7 export this code has been emptied.
- The archived architecture draft says `stfjump`; the code and the site use `stujump`. Its example port is 8888; the code uses 18888 and 18889.
- In `docs/week7-runbook.md`, `tools.generate_week7_pki`, `tools.rehearse_week7` and `Week7Server` have since been renamed `tools.generate_comms_pki`, `tools.rehearse_comms` and `CommsServer`.
- The archived iOS design specification says "wait 30 s for the first result". The current code has no idle limit after subscribing.
- `docs/B07-CO-protocol-explained.zh-CN.md` explains protocol version 2 (32 bytes, 8 values, `LCS1`). The code is version 3; `docs/co-protocol-v3.md` governs.

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
15. **BLE rather than Bluetooth Classic.** This choice was made and tested long ago: the 50 Hz and 70 Hz settings were both measured clean on 2026-09-28, with the 32-byte dummy packet (the 70 Hz setting actually delivered about 66 packets/s). With 38-byte packets, one board at 50 Hz was measured clean on 2026-10-14; two boards together and real sensor data have not been measured.
16. **Only one protocol version at a time (the owner's rule, 2026-10-14).** Each component accepts only version 3, so there is no mixed state to reason about; an upgrade means reflashing both boards, redeploying the board service and reinstalling the phone app together. The source-statistics marker moved to `LCS3` so that a board with old firmware is refused at start-up with a clear message instead of failing packet by packet. The subscription envelopes stay at version 1 because they did not change.
17. **Communications checks the shape of a result, not its meaning.** Any label of 1 to 32 safe characters and any confidence from 0 to 1 passes; the label set is for Wen Ree and Jie Ling. The board refuses a result the phone would reject, because a rejected result ends the phone session and clears its passwords.
18. **The model runs behind a narrow, counted interface.** `on_sample` runs on the service's single event loop before the ACK, so it must return at once; slow calls and exceptions are counted rather than allowed to close connections. `emit` may be called from any thread and moves the result onto the event loop, because the result queue has no lock. Commands never reach the model: their values are transformed dummy rows and their sequence numbers come from the command space, so they would corrupt the model's windows. The built-in dummy model keeps one result per input, so every acceptance check stays valid until the real result rate is known.
19. **Deploying is one checked step with rollback.** The board is shared and has no service manager. `tools.deploy_service` checks the new code, the certificate and key, and the running process (this user's, under the deployment folder, owning exactly the two ports) before stopping anything, and restarts the previous code and certificate if the new service does not come up.
20. **The glove decides when to send; Communications calls the decision once per sample (2026-10-15).** Siqiang's answer is that a glove sends only while his detector says MOVING, and the owner asked that the Communications firmware call his function. Calling it right after each successful read keeps the state out of the packet: no new field, no change to the 38-byte layout, the MTU floor or `on_sample`. The cost is that samples before the MOVING decision are never sent: they cannot be sent later, because the link's ceiling (about 66 packets/s per board) leaves no room for a backlog. That is a property of the detector, for Wen Ree to judge (7.2).
21. **A tick that sends nothing takes no `seq`, but it is counted.** A `seq` gap keeps one meaning: a lost sample. A pause (IDLE, no valid reading, refused) shows only as an `uptime_ms` jump. The skipped ticks are counted in the source statistics (`idle`, `unread`, `refused`), so the laptop can still reconcile and can tell a still player from a stalled board. The statistics grew to 36 bytes but kept the marker `LCS3`: the 24-byte `LCS3` ran only on the right board, and the length change alone refuses older firmware with a message to reflash.
22. **A gated board is judged by its ticks.** Idle ticks count toward coverage, because the board kept ticking, and silence is not judged once idle ticks are reported. The expectation is taken over the time sensor notifications were on, the same interval the board's counters cover, so a board that subscribed before the other one is not judged over the wrong window.
23. **Ingest connections may stay silent for 600 s, and a full server evicts the longest-silent one.** With the old 5 s limit every pause longer than 5 s closed a gated glove's stream, and the first frames after the pause were lost as ambiguous during the TLS reconnect. Once a frame has begun, 5 s still bounds it. A longer limit lets a vanished laptop's connection hold one of the 8 slots for up to 600 s (sshd may keep its socket), so when the slots are full the connection that has waited longest (at least 5 s) is closed instead of refusing the new client.
24. **Glove module calls never run under the connection mutex.** A call may take 10 to 20 ms (Siqiang's answer C), and the BLE callbacks take the same mutex. The tick is re-checked under the mutex and committed only if the laptop is still ready, so the source statistics stay unchanged once notifications are off, which the shutdown check relies on. The send tick advances by whole intervals, so a slow call delays one tick without lowering the rate.
25. **Siqiang's module is built from unchanged copies.** His folder is read-only, and his include path resolves only in a PlatformIO library layout. A tool copies his files byte for byte; a test and `flash.py --glove` refuse a stale copy; the weights header is placed in both locations, so his current include and the corrected one both work. Only the `-glove` environments link the module, so the owner's boards without sensors keep testing the chain with the dummy module (gated or not).

The source of each decision (the entry numbers in the archived design record) is in the design-reason part of each chapter in `docs/handoff-details/`.

---

## 6. Where things stand (2026-10-15)

### 6.1 Done and verified on hardware (dummy data; 32-byte version 2 unless the row says version 3)

| Item | Result | Date |
|---|---|---|
| Two-board baseline at 10 Hz | Left 652 and right 653, all ACKed; ATT MTU 517 | 09-28 |
| Rate sweep (per board) | 10, 25, 50, 60, 65 and 70 Hz pass; 75 Hz and 100 Hz fail. At 50 Hz, measured about 49.98 packets/s; the 70 Hz setting measured about 66 packets/s, 33.8 kbps for both boards together | 09-28 |
| ACK window 32 | 600 s: 6005 / 6001, all acknowledged | 09-19 |
| Single-board power-loss recovery | Reconnected in 11 s; the other board was unaffected; the first packet after recovery got no ACK (1 ambiguous) | 09-28 |
| iPhone count | 1202 in 60 s, 12003 in 600 s, and others, all as expected | 09-21 |
| File transfer | 4096 bytes, once per board, digests match | 09-28 |
| Firmware after the compatibility removal | Left board flashed with the then-current version-2 firmware (superseded by version 3; 6.3); local loopback 100/100 packets; another run of 349 packets with source reconciliation passed, a rate change to 20 Hz confirmed, and all 3 commands round-tripped | 10-14 |
| Right board, same version-2 firmware | Identified by factory MAC `38:18:2b:18:9d:68` (Bluetooth `…:9D:6A` = RIGHT) on COM3, flashed with `firebeetle32-right`. Checked against a service on the laptop (no SSH, Ultra96 or phone): 20 Hz / 30 s: 495 generated = received = ACKed, 3/3 commands; 50 Hz / 65 s: 3019 = 3019 = 3019, ATT MTU 517, connection interval 15 ms, longest silence 63 ms, 3/3 commands. Windows kept its authenticated bond; no new pairing | 10-14 |
| **Right board, version 3** | Flashed once from branch `comms/protocol-v3` (the review fixes changed no firmware); boot line `comms_ready device_id=2 packet_bytes=38 packet_version=3`. `python -m tools.check_board right` (50 Hz, 65 s, against a service on the laptop with the dummy model): `LCS3` statistics clean, 2934 generated = 2934 received = 2934 ACKed (seq 0 to 2933), 3/3 commands (52-byte frames) with their `cmd:` results, 2934 samples to the model and 2934 results back, slowest model call 0.39 ms, no error of any kind. Evidence for this run: `.comms-local/checks/2026-10-14-right-board-v3/`. After the review fix to `check_board`, a 10 s run with 8 commands also passed (320 = 320 = 320, 8/8); its JSON report went only to the console, and its numbers are written in the README of the same folder. This build has the 24-byte statistics of 2026-10-14 and no gating; the current laptop refuses it (6.3) | 10-14 |

Verified on the laptop but not on hardware (2026-10-14): `tools/deploy_service.py`'s board-side program on Linux (WSL Ubuntu, Python 3.10, the same Python version as the Ultra96): 27 of 27 checks, covering a deploy over a running version-2 service (the code of `5a004c6`, the team main, whose service code equals `c42b386`), a version-3 end-to-end exchange with the deployed service, rollback with certificate restore, a mismatched key refused, busy ports refused, a first start, and an old service that closes its ports but does not exit (stopped with SIGKILL). Its SSH half needs the owner's login and has not run. The renewed server certificate passed a local TLS 1.3 handshake. The full test suite passed (6.2).

Verified on the laptop but not on hardware (2026-10-15):

- **Swift client:** compiled and tested on Linux in a Swift 6.1 container (Docker image `swift:6.1`, Swift 6.1.3): 72 tests, 0 failures, in 6 runs. Not yet built for iOS or macOS (4.6).
- **C# reference receiver:** `CommsPhoneCore.cs` compiled at C# 7.0 (0 errors, 0 warnings, against the .NET 10 libraries); its self-test passed 113 checks under PowerShell 7.6.7, in 4 runs (4.6).
- **Firmware builds (PlatformIO):** the dummy `firebeetle32-right`, and `firebeetle32-left-glove` and `firebeetle32-right-glove` with Siqiang's module, compile and link (sizes in 4.3). Siqiang's unmodified files also compiled with `-Wall -Wextra` and no warnings in a scratch project.
- **Tests:** 841 passed, 4 skipped at `d582ce6`; 842 passed, 4 skipped at `4c6ab4c` (2026-10-16), which adds one test (6.2).

**Not verified: the gating on hardware.** The right board was unplugged before the gated build could be flashed. It still holds the 2026-10-14 version-3 build with 24-byte statistics, unless the interrupted attempt left its flash half-written; either way it must be flashed again before use (6.3). Neither the gated dummy, nor a `-glove` build, nor Siqiang's module has run on a board.

Unexplained history: on 2026-09-21, in one 60 s run, the phone received only 1094/1203 results (109 missing). The cause is unknown. Range testing has never been done.

### 6.2 Code and branch state

- **The work of 2026-10-15 on `comms/protocol-v3` (after the document commit `8a4cbad`):** `6583f9d` (the Swift package compiles on Linux, 4.6), `5d2e52f` (gating, 36-byte source statistics, the coverage rule, the 600 s ingest idle limit with eviction, `tools/export_capture.py`), `17012b8` (merge of the team main at `51593be`, Siqiang's module), `e24f8ea` (the module built into the `-glove` environments: `tools/sync_glove_module.py`, the copies under `firmware/esp32/lib/glove_sensor/` and `firmware/esp32/movement_model_params.h`, `src/glove_module.cpp`), `d582ce6` (`flash.py --glove`) and, on 2026-10-16, `4c6ab4c` (capture reports fingerprint the copies of the glove module: `laptop/reporting.py` adds `firmware/esp32/lib` and `firmware/esp32/movement_model_params.h` to `workspace_source_sha256`; the copy README names both locations of the weights header; one new test in `tests/test_laptop_controls.py`), followed by the document commit. **Tests: `python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider` gave 841 passed, 4 skipped at `d582ce6`, and 842 passed, 4 skipped at `4c6ab4c`.** The totals with `B07_LINUX_DEPLOY_TEST=1` were last recorded at `15de82e` (below). `tests/test_server_diagnostics.py::test_close_deadline_includes_status_persistence` is timing-sensitive and failed once under load; it passed on the rerun (9.2).
- **The owner's approvals of 2026-10-15 (in chat):** push `comms/protocol-v3` to the fork, merge it into `main`, push the team branch and open the team pull request, download the Swift Docker image, and download the .NET SDK. The two downloads are done. **At the time of writing nothing is pushed or merged, and no team pull request is open.**
- **Toolchains installed on 2026-10-15 (per user, with the owner's approval):** the .NET SDK 10.0.402 in `%USERPROFILE%\.dotnet` (Microsoft's `dotnet-install.ps1`) and PowerShell 7.6.7 as a .NET global tool, `%USERPROFILE%\.dotnet\tools\pwsh.exe`; neither is on PATH. The Docker image `swift:6.1` (Swift 6.1.3).
- **Protocol version 3 (2026-10-14 evening): local branch `comms/protocol-v3`, made from local `main` at `c42b386`.** It holds the code commits `a34c467` (core), `57a3fbd` (all components, tools and tests), `a4b907b` (the review fixes) `3b94990` (the Linux deploy test now hands bash a copy of `tests/linux/deploy_remote_test.sh` with LF endings, so it also runs from a checkout with CRLF endings; the same commit renames the specification to `co-protocol-v3.md`) and `15de82e` (paramiko errors end in a `FAILED:` line; `paramiko>=2.8,<4` in `requirements-dev.txt`; the Linux deploy test takes its old service from `5a004c6`, so it also runs in a clone of the team repository), followed by the document commit. **Final totals at `15de82e`: 780 passed, 3 skipped with `B07_LINUX_DEPLOY_TEST=1`; 779 passed, 4 skipped without.** Tests at `3b94990`: `python -m pytest tests laptop/tests phone/tests`: 778 passed, 4 skipped; with `B07_LINUX_DEPLOY_TEST=1`, which adds the WSL deploy test, 779 passed, 3 skipped, with 27 of 27 deploy checks (as at `a4b907b`). An adversarial review (seven reviewers: cross-peer consistency, firmware, the model interface, Swift, C#, tools, tests; each finding verified independently) found no defect in the firmware, Swift, C# or cross-peer rules (11,421 result bodies validated identically by the board, the Python receiver and a compiled C# harness) and nine real defects in the tools, the model interface and the tests; all nine are fixed in `a4b907b`. **Pushed on 2026-10-16 with the owner's approval of 2026-10-15:** `comms/protocol-v3` and `main` (fast-forwarded to it) are on the fork at `4d97242`; the team branch `comms/protocol-v3-team` is on the fork at `44d0f71`, and the team pull request <https://github.com/B07-CG4002/Let-Them-Cook/pull/19> (#19, base `main` of the team repo, not merged; the team repo has no CI checks) was opened from it. The branch for the team pull request: `comms/protocol-v3-team`, made from `upstream/main` (`5a004c6`) in the worktree `D:\LetThemCook-worktrees\protocol-v3-team`. It holds three commits: `348fc10` (the code of `comms/protocol-v3` at `3b94990`), `ed2aa1f` (the code of `15de82e`, plus the Communications lines of the shared `README.md`) and `ab3c7f6` (`ios-visualizer/README.md` and `NATIVE-INTEGRATION.md`), with none of the fork-only files (`docs/` and the others in 12.4), as for PR #18. Tests there (run by the lead): 761 passed, 4 skipped at `ab3c7f6` (the fork-only tests are absent); the opt-in Linux deploy test also passed there, from a checkout whose script had CRLF endings. **On 2026-10-15 (12:49) the branch was rebased onto the new team main `51593be`:** `348fc10` became `abaff6f`, `ed2aa1f` became `d2aa85a` and `ab3c7f6` became `09dc603`. On 2026-10-15 (12:52) the code of 2026-10-15 (up to `d582ce6`) was committed there as `8dbcaf2`; its message records 823 passed, 4 skipped on that branch. `4c6ab4c` is not on it yet. The worktree is clean. It is not pushed and no pull request is open (the owner approved both on 2026-10-15, above). The IDLE/MOVING answer did not change the packet.
- Team repository `upstream` = <https://github.com/B07-CG4002/Let-Them-Cook>. Its main branch is at `51593be`: Siqiang's module, pushed on 2026-10-15 at 11:11 +08:00, on top of `5a004c6` (PR #18, the cleanup below, merged on 2026-10-14 on top of `880abba`, PR #15). `17012b8` merged it into `comms/protocol-v3`.
- **History rewritten on 2026-10-14, outside the agent sessions:** the PR #15 merge commit on the team main branch (`ec398b6` became `880abba`) and the fork's `main` (for example `780db40` became `971fc52`) were rewritten to remove the `Co-Authored-By` lines from the commit messages. The file contents are identical. Local `main` was aligned with the fork's `main`. From now on, commit messages and pull request descriptions carry no attribution lines.
- **Pushing needs the owner's go-ahead.** On the evening of 2026-10-14 the owner asked that GitHub not be touched; later that evening the owner gave the go-ahead to push to the fork, and then asked for the team pull request to be opened and merged if it had no problems. Ask before any further push, and never push or merge into the team repo unasked. `gh` is now installed and logged in as `olsonwangyj`. On 2026-10-15 the owner approved the pushes, the merge into `main` and the team pull request for this work (above).
- olsonwangyj's fork `origin` = <https://github.com/olsonwangyj/Let-Them-Cook>. Local `main` has content beyond the team main branch that exists only on the fork: `docs/`, `ios-visualizer/xcode-export/`, `AGENTS.md`, `CLAUDE.md`, and several tools.
- **The 2026-10-14 cleanup (merged into the team main by PR #18, and into local `main`):** it removed compatibility with the old Week 7 version. The cleanup left only `LC` packets and `LCS1` statistics; since version 3 (first bullet of this section) only version-3 `LC` packets and `LCS3` statistics are accepted. The `.week7-local` directory is no longer read. The session for `demo.py service --start` defaults to `ltc-comms`, like `run`/`live`, and `--session-id` was added.
  - The team-facing branch `comms/remove-week7-legacy` also carries the certificate-renewal commit. Its tests: 551 passed, 3 skipped. It was rebased onto the rewritten team main `880abba` and its messages cleaned (same file contents), then `0b9ed2e` updated the old-evidence commit in `README.md`. It was pushed to the fork with the owner's go-ahead on 2026-10-14 (`0b9ed2e`, a lease-protected force push replacing the old `30e85a6`, which was based on the replaced `ec398b6`). Its tests at `30e85a6`: 551 passed, 3 skipped; the rebase changed no code.
  - Local `main` (which also has the fork-only tests): 569 passed, 3 skipped.
  - Pull request: <https://github.com/B07-CG4002/Let-Them-Cook/pull/18>, opened and merged on 2026-10-14 at the owner's request (mergeable and clean; the team repo has no CI checks; local tests passed). Merge commit `5a004c6`. The branch was then deleted locally and on the fork, and the team main was merged into local `main` with no change to any file, so the fork's `main` contains the team main.
- **Certificate renewal option (branch `comms/renew-server-certificate`, merged into local `main` and included in `comms/remove-week7-legacy`):** `tools/generate_comms_pki.py` gains `--renew-server-from <original CA directory>`, which uses the existing CA to issue only a new server certificate.
- Week 7 names **deliberately kept** in the cleanup:

| Name kept | Where | Why it is not changed |
|---|---|---|
| TLS host name `ultra96.week7.internal` | `common/tls.py`, the certificate tool, every receiver | It is written into the server certificate and every client verifies it. Renaming it means a new certificate and reinstalling the app |
| `Week7Start/CopyDisplay/Stop`, reading the old iOS directory, the app display name, and similar | `ios-visualizer/` | Part of the Week 7 receiver; the owner said explicitly not to touch them |
| Board deployment directory `/var/tmp/cg4002-week7-…-20260907` | `tools/demo_service.py` | A directory that really exists on the board |
| Default CA path `~/.codex/private/cg4002-week7-20260906/ca-cert.pem` | `demo.py` | A directory that really exists on the laptop |
| iSH config file name `week7-ish-password.conf` and host alias `week7-ultra96` | `phone/ish_control.py` | A file and an alias that already exist in iSH on the phone. Nothing in the repository would create new names |
| ~~Protocol v1 and `COMMS_LEGACY_DUMMY`~~ | Removed with version 3 (2026-10-14 evening) | Kept by the cleanup as the deterministic dummy-data mode; version 3 replaces versions 1 and 2, so it went |

- Side effect of the cleanup: old captures recorded with Week 7 firmware (all in `.week7-local/`) contain `W7` packets, and the current `demo.py report` no longer passes them. To re-check old evidence, use commit `880abba` (the team main after the history rewrite; it was `ec398b6`, with the same files). Likewise, captures made with version-2 firmware are refused by the version-3 tools (`tools/video_evidence.py` says so by name); check them with `c42b386` or the team main `5a004c6`.

### 6.3 Actual deployment state, and one redeploy round

Version 3 is a new protocol, so all ends must move to it together (only the newest version is supported). **Any step below that logs in to the jump host or the Ultra96 can be done only by the owner, in their own terminal** (see section 9).

| Device | Current state (2026-10-15) | What to do | Who |
|---|---|---|---|
| Left board | Version-2 firmware (flashed 10-14, earlier in the day). The current laptop refuses it at start-up with `source statistics must contain exactly 36 bytes; flash this board with the current firmware` | Step 2: flash the current firmware (`-e firebeetle32-left`), then `python -m tools.check_board left` | The owner, or an agent once its USB is connected |
| Right board | The 2026-10-14 version-3 build with 24-byte statistics (checked then, 6.1), unless the interrupted attempt to flash the gated build left its flash half-written: the board was unplugged during that attempt. The current laptop refuses the 10-14 build with the same 36-byte message | Step 2: flash the current firmware (`-e firebeetle32-right`), `python -m tools.check_board right`, then the gated dummy check | The owner, or an agent once its USB is connected |
| Siqiang's two gloves | Not flashed by Communications; they run whatever Siqiang last flashed | Step 6, with Siqiang | The owner, with Siqiang |
| Server certificate | The September certificate expired on 2026-10-06 (laptop copy; the board's copy unchecked). **Renewed pair ready** in `~/.codex/private/cg4002-comms-server-20261014/` (valid to 2026-11-13 14:27:35 UTC); not on the board | Installed by step 1 | The owner |
| Ultra96 service | Should still be the 28 September code snapshot (version 2, session `week7-demo`), started in the background by `.week7-local/co_deploy.py` (PID in `BOARD_ROOT/evidence/server.pid`); may still be running | Step 1 | The owner |
| iPhone app | The Week 7 build (version 2 results, dummy labels only, session `week7-demo`); it cannot read version-3 results | Steps 3 and 4 | The owner (Mac) |

Steps:

1. **Board service and certificate in one step** (from the repository root on the laptop, VPN on, with `comms/protocol-v3` checked out; the tool needs `paramiko` for both SSH hops and the upload; `requirements-dev.txt` lists it (`paramiko>=2.8,<4`, added with the documents after `3b94990`), and on this laptop it comes with Anaconda, version 2.8.1):

   ```powershell
   python -m tools.deploy_service --dry-run
   python -m tools.deploy_service --server-cert-dir "$HOME\.codex\private\cg4002-comms-server-20261014"
   ```

   The first command only prints the plan. The second asks for the jump-host and board passwords (typed by the owner; nothing is stored), uploads `common/` and `ultra96/` into a new folder `BOARD_ROOT/source-co-v3-<UTC stamp>`, and then, on the board: compiles it; checks that the new certificate and key match and do not expire within an hour; checks that the running `ultra96.server` is this user's, under `BOARD_ROOT`, and owns exactly `127.0.0.1:8888` and `:9999` (or that both ports are free); copies its code aside; nothing has changed on the board up to here. It then stops the old process with SIGTERM and waits until it has exited (after 10 s, SIGKILL once it has checked the PID is still the same process); backs up the old certificate pair to `BOARD_ROOT/tls/backup-<stamp>/` and installs the new one (key mode 600); starts the new service in the background with `--session-id ltc-comms` and an event log; waits until it listens on both ports. Any failure from the stop onwards stops the new service, restores the old certificate pair and restarts the previous code from the rollback copy. From the last check of the running process just before the stop (`tools/deploy_service.py:244` onwards), the final record (`deployed`, `rolled_back`, `failed_old_still_running`, `failed_nothing_running` or `rollback_failed_nothing_running`) is always printed and saved on the board in `BOARD_ROOT/evidence/active-deployment.json`. A refusal in the checks before it (more than one service of this user, a service outside `BOARD_ROOT`, ports not owned exactly or busy, a compile failure, a certificate and key that do not match or expire within an hour) leaves the running service and the certificate untouched (only the uploaded folder stays), prints the error and exits nonzero, and leaves no record on the board or under `.comms-local/deployments/`. If the laptop hears nothing for 2 × start timeout + 120 s, it says so and asks you to read that file (`python demo.py service`) before trying again. The board's record is printed and saved under `.comms-local/deployments/`, which `demo.py service --start` then follows. Without `--server-cert-dir`, the certificate on the board is kept, and the run refuses to deploy if that certificate is expired. Later, `--model MODULE --model-path DIR` starts Wen Ree's model instead of the dummy one. Then `python demo.py service` shows the new process, its folder and the two loopback listeners. The board-side half was tested on Linux (6.1); this will be its first run against the real board.
2. **Board firmware (both of the owner's boards; none of this has been done yet).**
   - **Plain build.** Plug in one board alone and confirm its factory MAC (left `38:18:2b:19:82:ac`, Bluetooth `38:18:2B:19:82:AE`; right `38:18:2b:18:9d:68`, Bluetooth `38:18:2B:18:9D:6A`). Then `platformio run -d firmware/esp32 -e firebeetle32-right -t upload --upload-port COMx` (or `-left`) and `python -m tools.check_board right` (or `left`). Expected: the serial lines `glove_begin ok=1 module=dummy gated=0` and `comms_ready … glove=dummy gated=0`, and `CHECK PASSED … gated=no idle=0 unread=0 refused=0`. Or run the full `python flash.py` with both boards (left first). If Windows asks for an authenticated bond after the firmware change: type `erase-bonds` on the board's serial port, remove the board in Windows Bluetooth settings, then run `python flash.py --pair left` (or `right`).
   - **Gated dummy check (one board).** In PowerShell: `$env:PLATFORMIO_BUILD_FLAGS = "-DCOMMS_DUMMY_MOVING_MS=3000 -DCOMMS_DUMMY_IDLE_MS=7000"`, then the same upload command, then `python -m tools.check_board right`. Expected: `glove_begin ok=1 module=dummy gated=1`; samples for 3 s, then 7 s of silence, repeating; `CHECK PASSED` with `gated=yes` and `idle` above 0, generated = received = acknowledged, and every command answered. Afterwards `Remove-Item Env:PLATFORMIO_BUILD_FLAGS` and flash the plain build again. A two-board `python demo.py run` with gated boards should also pass by the gated coverage rule (4.4).
   - **A `-glove` build on a board without sensors (one board).** `python -m tools.sync_glove_module --check`, then `platformio run -d firmware/esp32 -e firebeetle32-right-glove -t upload --upload-port COMx`. Expected: `glove_begin ok=0 module=external gated=1` without the 5 s calibration wait, and the board still advertises and pairs. It sends no samples: every tick counts as `unread`, so `tools.check_board` fails with "nothing acknowledged". Then flash the plain build again.
3. **Swift package on a Mac.** `swift test --package-path ios-visualizer/CommsNative`, with Xcode's Swift 6.1 or newer. The package compiles and its 72 tests pass on Linux (4.6). On the Mac, `swift test` builds for macOS: it adds `PythonBoardTests` and the Apple (CryptoKit, Security) branches of `Configuration.swift`, but not the `#if os(iOS)` code (`IntegrationController.swift`, `SetupViewController.swift`, the iOS branches of `DisplayMailbox.swift` and `Configuration.swift`). That code compiles only in an iOS build: the preview app built for an iOS simulator (the `xcodebuild` commands in `ios-visualizer/NATIVE-INTEGRATION.md`), or the app build in step 4. Fix any build error there before anything is installed.
4. **Phone app.** Needs a Mac and Xcode: run `python ios-visualizer/tools/patch_export.py` and `python ios-visualizer/tools/configure_xcode.py` on the Unity export (both scripts are fork only and can be rerun; the existing `ios-visualizer/xcode-export/` is already patched), then build and install with Xcode. This is the owner's test app; Jie Ling's game build follows 7.3.
5. **Acceptance.** `python demo.py tunnel` (terminal A); on the phone, tap Connect and wait for `Subscribed`; `python demo.py run` (terminal B). The run must print `CAPTURE PASSED`, and the increase in the phone's `Received` must equal the `Phone expected increase` in the output (valid while the board runs the dummy model).
6. **Siqiang's gloves (with Siqiang).** `python flash.py --glove`: it checks the module copies, builds both `-glove` environments, and flashes the left glove first, then the right. It writes the gloves' Bluetooth addresses into `.comms-local/boards.json`, replacing those of the owner's boards (9.2). Pair with `python flash.py --pair`. Hold each glove still at power-up: it calibrates for about 5 s before it starts advertising. Then `python -m tools.check_board left` and `right` while moving the glove (an idle glove sends nothing), and a two-glove capture at 50 Hz: `python demo.py run --rate 50` (without `--rate`, `demo.py run` sets both gloves to its default 10 Hz). For a recording session that keeps IDLE samples too, set `$env:PLATFORMIO_BUILD_FLAGS = "-DCOMMS_GLOVE_SEND_ALL=1"` before `python flash.py --glove`, capture with `python demo.py run --rate 50`, export with `python -m tools.export_capture`, then remove the variable and flash the gated build again.

To check whether the board's certificate has expired (with the tunnel open):

```powershell
openssl s_client -connect 127.0.0.1:18889 -servername ultra96.week7.internal
```

### 6.4 Integration progress and schedule

The team meets in person on **Tue 2026-10-20** to integrate V1 together. The schedule below works back from that day. All teammate dates are the owner's proposals until the teammates confirm them in their replies. Teammates deliver code by pushing it to the team repo on GitHub, not over Telegram. It was set on Wed 2026-10-14 at about 19:00 (Singapore time), when the messages were finalised.

- The messages to the three teammates (English, with explicit functions, fields and dates) were drafted on 2026-10-14, reviewed for accuracy against the code, for the role boundary and for clarity, revised after the owner's review and decisions, and handed to the owner. Each message lists what is needed by which date first, then the interface details, then the questions. Their content matches section 7. **Whether the messages have been sent, and how teammates replied, is for the owner to record here.**

What each teammate is asked for (in the messages, once the owner sends them; record the sending in this section):

| Date | Siqiang | Wen Ree | Jie Ling |
|---|---|---|---|
| Thu 10-15 | Answers to the questions in the message; with Wen Ree, whether the glove's IDLE/MOVING state travels in V1 | Answers to the questions; with Siqiang, whether the IDLE/MOVING state is needed; how out-of-range values should be handled | Answer: whether the timing works |
| Fri 10-16 | Sensor module as `gloveBegin` / `gloveUpdate` / `gloveRead` in one `.h` and one `.cpp` file, plus a CSV log of real samples from each glove, pushed to the team repo (under `hardware/`) | A first version that can be connected, even one that always returns the same label, pushed to the team repo: for in-process, the module and function names; for a separate process, how to start it, its dependencies, and its input and output in the format the owner sends on Thu 10-15 | |
| Sat 10-17 | Both gloves so the owner can flash and test them (Sat or Sun; Mon morning at the latest), and if possible left with the owner until Tuesday for the Monday dry run | | The Unity project changes pushed to the team repo (`vis/`): the C# that calls the Communications functions, with the 5005 listener removed |
| Sun 10-18 | | The version with the real model | Sun or Mon: once the owner says `CommsNextResult` is pushed, export, add `CommsNative`, build and install the app on Jie Ling's iPhone; report any build problem before Tuesday |
| Tue 10-20 | Both gloves, charged, with USB cables | Model and files ready on the Ultra96 | Their iPhone with the app, and their laptop to rebuild if needed |

Siqiang's Thursday answers and his Friday module both arrived on Thu 10-15 (2.3, 7.1). The module came as five functions in one `.h` and one `.cpp` (plus the weights header) under `hardware/gloves/integration_files/`. The log of real samples has not arrived; it can now also be recorded through the chain (7.1).

The owner's own plan (proposed, Communications work only):

| Date | Communications work |
|---|---|
| Wed 10-14 | Send the three messages |
| Thu 10-15 | Renew the server certificate and redeploy the Ultra96 service from current source (6.3; the owner's login); flash the right board; start the version-3 38-byte packet in firmware, laptop and Ultra96 with golden vectors and tests; open the team pull request; if Wen Ree's code must run as its own process, send Wen Ree the format for passing the fields between the two processes the same day; pass the confirmed label strings on to Jie Ling |
| Fri 10-16 | Build the firmware with Siqiang's sensor module. The owner's boards have no IMU or flex sensors, so on them check only that it compiles, that `gloveBegin()` returns false without blocking, and that the board still advertises; check the int16 scales against the sample log (real readings are first tested on the gloves). Connect Wen Ree's first version on the Ultra96 (`start`, `on_sample`, the thread-safe `emit`). Accept model labels and real confidence in the three Python and C# checks (`ultra96/protocol.py`, `phone/receiver.py`, `phone/unity/CommsPhoneCore.cs`) |
| Sat 10-17 | On the Mac: change the fourth check (`Protocol.swift`) and add `CommsNextResult` and the `confidence` field to the Swift client; rebuild the existing Week 7 export from current source and install it, so the phone can subscribe to the redeployed `ltc-comms` service before the new game build exists (6.3, step 4); push `CommsNative` with `CommsNextResult` to the team repo with short steps for adding it to the Xcode project, and tell Jie Ling |
| Sun 10-18 | Flash both gloves and test with Siqiang; help Jie Ling if the iOS build fails; connect Wen Ree's real model; before the dry run, redefine `Phone expected increase` and the rehearsal checks for the model's result rate (8, step 6), or record that the phone count is not compared in the dry run |
| Mon 10-19 | Full dry run: gloves → laptop → Ultra96 → model → phone. The phone side uses the owner's test app (the rebuilt Week 7 export) unless Jie Ling's game build is already installed; the game itself is first tested together with Jie Ling (Monday if Jie Ling is available, otherwise Tuesday). Keep the evidence and list the problems for Tuesday |
| Tue 10-20 | In-person integration session |

**Progress against this plan (2026-10-15; work that needs no teammate reply was done ahead of time at the owner's request):**

- Thursday items done: right board flashed (twice: version 2, then version 3) and checked; server certificate renewed (locally; the upload is the owner's step 1 in 6.3, now one command); version-3 packet in firmware, laptop and Ultra96 with golden vectors and tests.
- Friday items done on the Communications side: the model interface in the board-service code (`ultra96/model.py`: `start`, `on_sample`, thread-safe `emit`, `--model`; built and tested on the laptop, not yet deployed to the Ultra96), model labels and real confidence in `ultra96/protocol.py`, `phone/receiver.py` and `phone/unity/CommsPhoneCore.cs` (`CommsPhoneCore.cs`: on 10-14 only the changed part compiled, at C# 5; on 10-15 the whole file at C# 7.0, with its self-test); the firmware scaling helper for Siqiang's module (`comms_sample.h`; called since 10-15, below).
- Saturday items written early: `Protocol.swift`, the `confidence` field and `CommsNextResult`. **Compiled and tested on Linux on Thu 10-15 (72 tests); the iOS build still needs the Mac** (the iOS builds in 6.3 steps 3 and 4).
- **Thu 10-15, after Siqiang's answers (built on the laptop; not yet run on hardware):** gating (a glove sends only while MOVING), 36-byte source statistics, the gated coverage rule, the 600 s ingest idle limit with eviction, the capture exporter; Siqiang's module merged from the team main and built into the `-glove` environments (the Friday "build the firmware with Siqiang's module" item: it compiles and links; the board checks are not done); `flash.py --glove`; the C# reference core `CommsPhoneCore.cs` compiled (C# 7.0) and its self-test passed (113 checks; `CommsPhoneReceiver.cs` checked by reading only). The hardware check of the gating could not be done: the right board was unplugged before the gated build could be flashed.
- Still the owner's, in order: send the teammate messages (if not yet sent); run `tools.deploy_service` (6.3 step 1); flash and check both boards, the gated dummy and a `-glove` build on a board without sensors (step 2); push `comms/protocol-v3` to the fork, merge it into `main`, push the team branch and open the team pull request (approved on 10-15, not yet done); `swift test` and the phone build on the Mac (steps 3 and 4); acceptance (step 5); the gloves with Siqiang (step 6).
- Waiting for teammates: the scale check against real samples, the out-of-range policy, Wen Ree's module and result rate, whether the MOVING onset lag suits the model (7.2), Jie Ling's timing. The IDLE/MOVING question is answered: the state does not travel, and the packet did not change.

Order of priority if time runs short: (1) certificate and redeploy, because nothing works without them; (2) the 38-byte packet and Siqiang's module (in code since 10-14 and 10-15; the hardware checks remain); (3) Wen Ree's interface; (4) `CommsNextResult` and the iOS link. A hop whose teammate part is late can still be tested with Communications' own dummy data (in the 11-value version-3 format, which has landed on `comms/protocol-v3`) and dummy labels, so the rest of the chain is ready on Tuesday. Between the Thursday redeploy and the Saturday phone build, the installed Week 7 app cannot subscribe (it uses session `week7-demo`).

- The team-facing explainer: <https://claude.ai/code/artifact/b77bebd7-09f4-4c3e-9466-d4e19318359c> ("B07 integration: what to ask, what to tell, and why").

### 6.5 Decisions taken on 2026-10-14 (evening) and 2026-10-15, with reasons and status

The owner asked for all work that does not depend on teammates' replies, with technical decisions made within Communications and integration, recorded with reasons. Status words: **verified** = run or measured; **built** = compiled and tested on the laptop, not on the Ultra96 or the phone; **written** = not compiled (no toolchain); **provisional** = waits for a teammate's answer. Since 2026-10-15 the Swift client is compiled and tested on Linux (Swift 6.1 container, 72 tests) but not built for iOS; the rows say so where it matters.

| # | Decision | Reason | Status |
|---|---|---|---|
| D1 | Flash the right board after confirming by factory MAC that COM3 holds it | One programming cable reuses COM3; identity comes from the MAC, never the COM number | Verified (6.1) |
| D2 | Renew the server certificate now from the existing CA | Priority 1; needs no login; keeping the CA keeps the phone's pinned fingerprint and the laptop's `--ca` | Verified locally; not uploaded |
| D3 | Implement protocol version 3 now: 38 bytes, 11 int16, scales ×10000 / ×100 / ×100 / ×10000 | The owner's plan for Thursday; the pending answers (IDLE/MOVING, scales, out-of-range) would be small follow-ups | Built; right board verified (10-14 build); IDLE/MOVING answered without a packet change (D20); layout provisional only for the scale check |
| D4 | Version 3 replaces versions 1 and 2 everywhere, including the formula dummy (`COMMS_LEGACY_DUMMY`, `dummy_values`) | The owner's rule: only the newest version; the formula mode was identified only by the version byte | Built |
| D5 | `SUBSCRIBE`/`SUBSCRIBED` stay at `v` 1 | They never carried the packet version and did not change | Built |
| D6 | `request_id` always present (null for samples and model results) | Keeps exact field sets; commands still need it | Built |
| D7 | Source-statistics marker `LCS1` → `LCS3` (format unchanged) | A board with old firmware is refused at start-up with a clear message, instead of failing packet by packet | Built; right board verified with the 24-byte format; the format became 36 bytes on 10-15 (D23) |
| D8 | Labels: 1–32 characters of `A–Z a–z 0–9 _ -`; confidence: finite number 0–1; the board checks before sending | Communications carries labels without knowing the set; one rule on every peer; a rejected result ends the phone session | Built (Python; C# compiled with its self-test, 10-15); Swift compiled and tested on Linux, not built for iOS |
| D9 | Board model interface on the Communications side (`ultra96/model.py`, `--model`, `--model-path`) as proposed in 7.2 | Wen Ree's first version can plug in with no further Communications change | Built; names provisional |
| D10 | `emit` converts numpy-style numbers; `async def` model functions are refused at load | Models commonly produce numpy floats; an async `on_sample` would silently never run | Built |
| D11 | Commands never reach the model; the service answers each with one `cmd:` echo | Command values are transformed dummy rows with sequence numbers from the command space | Built |
| D12 | Built-in dummy model: one random dummy label per accepted sample, confidence 1.0 | Keeps every one-input-one-result acceptance check valid until the real rate is known; dummy labels cannot be mistaken for game actions | Built; verified on the right board via `check_board` |
| D13 | Firmware scaling helper with clamp (default) or drop (`-DCOMMS_OUT_OF_RANGE_DROP=1`); NaN/infinity always refused; no `seq` for a refused sample | Either answer from Wen Ree becomes a build flag; no false gaps | Built (host tests, both policies); called through `prepareSample` since 10-15; policy provisional |
| D14 | `CommsNextResult` in the Swift package: 32 waiting, 2 s, oldest dropped and counted, emptied on Connect/Disconnect/inactive/`CommsStop`, kept on automatic reconnect, minus (bytes + 1) when the buffer is too small, counters reset on Connect | As proposed in 7.3 | Compiled and tested on Linux (10-15); not built for iOS; limits provisional |
| D15 | `tools/deploy_service.py`, the tracked successor of `co_deploy.py`, with certificate install, checks, SIGKILL escalation and rollback | The redeploy is priority 1 and must replace code and certificate in one careful step on a shared board | Board-side half verified on Linux (27/27); SSH half not run |
| D16 | `tools/check_board.py` for one board; `demo.py service --start` follows the newest deployment record | Checks each board after flashing without the Ultra96; removes the stale `BOARD_SOURCE` pitfall | `check_board` verified on the right board (6.1); the `--start` part built (unit tests only; no deployment record exists yet) |
| D17 | Pass confidence through unrounded (a numpy float32 0.93 arrives as 0.9300000071525574) | Communications forwards results as they are; rounding would be a change of the model's output | Built |
| D18 | A model's `SystemExit` is treated like any other model error; leftover non-daemon model threads cannot keep a stopped service alive (`exit_with_model_threads`) | Wen Ree's existing scripts report missing files with `raise SystemExit(...)`; one such call must not take both gloves and the phone down, and a stopped service must really stop | Built (review fix) |
| D19 | `demo.py service --start` restarts the deployed model too (`--model`/`--model-path` read from the running process recorded at deploy time, validated) | Otherwise a restart after a reboot would silently run the dummy model | Built (review fix) |
| D20 | Call the glove module's send decision once per sample: `gloveShouldSend()` right after a successful `gloveRead()`; send only while it says MOVING. For Siqiang's module it is his `gloveIsMoving()` (`src/glove_module.cpp`) | Siqiang's answer E (data only while MOVING, nothing while IDLE); the owner asked that the firmware call his function; the state then needs no field, so the 11-value layout stays | Built; not yet run on hardware |
| D21 | No `seq` for a tick that sends nothing (IDLE, no valid reading, refused); count those ticks as `idle`, `unread`, `refused` | A `seq` gap keeps meaning a lost sample; a pause shows as an `uptime_ms` jump; the counters let the laptop reconcile and judge coverage | Built (host tests) |
| D22 | `COMMS_GLOVE_SEND_ALL=1` sends every sample, IDLE included (external module only; the board then reports itself ungated) | Recording sessions need idle data too (Siqiang's question F) | Built into the module path; no test covers the `=1` variant |
| D23 | Source statistics grow to 36 bytes, `<4sBB2xIIIIIII`: flags bit 0 = gated, then `idle`, `unread`, `refused`; the marker stays `LCS3` | The laptop must know that a board is gated (silence expected) and count its skipped ticks; the 24-byte `LCS3` ran only on the right board, so the length change alone refuses older firmware with a reflash message | Built (host and laptop tests); not yet run on hardware |
| D24 | Coverage of a gated board: generated + idle ≥ 90% of the ticks expected while its sensor notifications were on; silence not judged once it reports idle ticks; ungated boards unchanged | A still player makes a healthy gated board silent; its counters cover the subscription-to-quiesce interval, so the expectation uses that interval | Built |
| D25 | Ingest idle limit 600 s (`--ingest-idle-timeout`, 5 to 86400 s); 5 s once a frame has begun; with all 8 slots full, the ingest connection that has waited longest (at least 5 s) is closed (`idle_evicted`) | The old 5 s limit closed a still glove's stream and lost the first frames after each pause as ambiguous; a vanished laptop's connection could otherwise hold a slot for 600 s | Built (tests); not deployed |
| D26 | Build Siqiang's module from byte-identical copies made by `tools/sync_glove_module.py`; `--check`, `tests/test_glove_module_sync.py` and `flash.py --glove` refuse stale copies; the weights header goes to both `firmware/esp32/` and `lib/glove_sensor/src/` | His folder is read-only and his include path resolves only in a PlatformIO library layout; the second location lets the corrected include work too | Built (the `-glove` builds compile and link) |
| D27 | `firebeetle32-left-glove` / `-right-glove`: the module, gated, 50 Hz from boot; the other environments keep the dummy module | The model expects 50 Hz; the owner's boards have no sensors and keep testing the chain with dummy data | Built; not run on a board |
| D28 | `flash.py --glove`: the copy check first, then build and flash both `-glove` environments | One command for the real gloves that cannot flash a stale module | Built (unit test); not run on hardware |
| D29 | `tools/export_capture.py`: a capture's samples as CSV in physical units | Siqiang's Bluetooth Classic script cannot connect to the BLE firmware (question F); recording through the chain gives the agreed units | Built (tests) |
| D30 | Glove module calls run outside the connection mutex; the tick is committed only if the laptop is still ready (`race_dropped` otherwise); the send tick advances by whole intervals (`sendTickDue`) | A call may take 10 to 20 ms (answer C) and the BLE callbacks take the same mutex; the statistics must not change after notifications are off; a slow call must not lower the rate | Built (host tests for `sendTickDue` and `prepareSample`); not run on hardware |
| D31 | Swift: import CryptoKit and Security only where they exist; link swift-crypto into `CommsBridge` on Linux only (`6583f9d`) | Lets the package compile and its tests run on Linux without a Mac; the iOS code paths are unchanged | Verified on Linux (72 tests); iOS build not done |

What these decisions do **not** settle (section 13): the scales, the out-of-range policy, the model's function names and in-process use, the label set and result rate, whether the MOVING onset lag suits the model, and the `CommsNextResult` limits. The IDLE/MOVING field is settled: it does not travel (D20).

---

## 7. The three interfaces to connect

Communications specifies only which functions and fields are needed at each hand-over point. Function names and internal implementation are the other side's decision. Who does what is summarised in the table in 3.1.

**What exists (2026-10-15, branch `comms/protocol-v3`, not yet deployed or pushed):** the Communications side of 7.1 and 7.2 is built on the laptop: the gating, the sample policy and the scaling are host-tested with the dummy module, and the `-glove` firmware with Siqiang's module compiles and links (its module path is untested and has not run on a glove); the model interface on the board (`start(emit)`, `on_sample`, the thread-safe `emit`, `--model`) is built and tested on the laptop. Every receiver accepts model labels and real confidence. The Communications side of 7.3, `CommsNextResult`, is compiled and tested on Linux but not built for iOS. **On the teammates' side, only Siqiang's sensor module exists** (team commit `51593be`); there is no model module and no game script calling the bridge. Until the owner deploys and installs (6.3), the Ultra96 and the phone still run the version-2 builds: there only the three C functions exist, under their Week 7 names (`Week7Start`, `Week7CopyDisplay`, `Week7Stop`), and only `REST`, `FIST`, `OPEN`, `POINT` with confidence 1.0 are accepted. The messages to the teammates were written before this work and describe these parts as planned; that is still safe, because none of them is deployed.

The interface shapes and dates below are the owner's proposals of 2026-10-14. They become commitments when the teammates confirm them in their replies; Siqiang's part (7.1) is delivered. Teammates deliver code by pushing it to the team repo on GitHub, not by sending files over Telegram.

### 7.1 From Siqiang: the glove sensor module (called by the Communications firmware)

**Delivered on 2026-10-15** (team commit `51593be`, `hardware/gloves/integration_files/`). It is built into the `-glove` firmware but has not yet run on a glove. Division of work (the owner's direction of 2026-10-14, matching what Siqiang delivered): Siqiang delivers the sensor module (initialisation, reading one sample, the movement decision). **olsonwangyj** calls it from the Communications firmware and is responsible for scaling to int16, packing, BLE sending and connection management. The capture algorithm, calibration, the movement detector and sensor problems stay with Siqiang.

| Function | Delivered (`glove_sensor.h`) | How Communications calls it | Contract (from his header and code) |
|---|---|---|---|
| Initialise | `bool gloveBegin()` | Once, first in `setup()`, before BLE starts | I2C (400 kHz) and ADC set-up, then gyro calibration: a 2 s settle and 1000 readings, about 5.1 s in all (answer B), during which the glove must be still. Returns `false` promptly when the IMU does not answer, so the board still advertises |
| Periodic update | `void gloveUpdate()` | Once per main-loop pass, roughly every 1 to 2 ms, connected or not, outside the connection mutex | Reads the IMU at most once per millisecond (2 ms I2C timeout) and updates the Mahony filter, the flex values (every 20 ms) and the movement classifier (one sample every 20 ms). No `delay()` |
| Read one sample | `bool gloveRead(float out[11])` | At each send tick, about every 20 ms at 50 Hz, **only while the laptop is connected and subscribed**, so there can be seconds between calls | `true`: `out[]` holds the latest valid sample. `false` (with `out[]` zeroed): no valid sample, or the latest is older than 100 ms |
| Movement decision | `bool gloveIsMoving()`; also `bool gloveMovementReady()` | As `gloveShouldSend()` (`firmware/esp32/src/glove_module.cpp`), right after a successful `gloveRead()`; `gloveMovementReady()` is not called | `true` = MOVING: the classifier is ready and its smoothed state is MOVING. False until the first 1 s window has filled |

Apart from the calibration in `gloveBegin()`, none of the functions waits; a call takes at most about 10 to 20 ms, usually far less (answer C).

Order and units of the 11 values: `ax, ay, az` (g, gravity removed), `gx, gy, gz` (°/s, bias removed), `yaw, pitch, roll` (degrees), `flex1, flex2` (0.0 to 1.0). With the scale factors in 4.2, each value must stay within: acceleration ±3.2767 g, angular rate ±327.67 °/s, angles ±327.67°, flex at most 3.2767. With the current settings in the module (the same as in `imu_v7.ino`: ±2 g, so about ±3 g after gravity removal, a margin of only about 0.28 g; ±250 °/s; yaw and roll ±180°, pitch ±90°; flex 0 to 1), normal values are expected to fit, but that is not guaranteed: the final value depends on the module's processing (for example the gyro bias subtraction). How an out-of-range value is handled is to be agreed with Wen Ree (8, step 1).

**How Communications calls it (built 2026-10-15; not yet run on a glove):** the `-glove` environments build an unchanged copy of the module (`firmware/esp32/lib/glove_sensor/`, made by `python -m tools.sync_glove_module`; 4.3). `setup()` calls `gloveBegin()` first; `loop()` calls `gloveUpdate()` every pass; at each send tick `produceSample()` calls `gloveRead()`, then `gloveShouldSend()` (his `gloveIsMoving()`), then `prepareSample` (which scales with `scaleSample`), then `serializePacket`. A `false` from `gloveRead`, an IDLE decision or a refused sample sends nothing and takes no `seq`. With `-DCOMMS_GLOVE_SEND_ALL=1` every valid sample is sent, IDLE included, for recording sessions. His three sample functions have exactly the signatures Communications proposed, so only the movement decision needed the one-line adapter.

Constraints the Communications firmware places on the module (from the existing code). The delivered module meets them:

- PlatformIO, Arduino framework, board `firebeetle32`, Arduino-ESP32 core 2.0.17 (PlatformIO espressif32 7.1.0).
- The module does not define `setup()`/`loop()`. It does not call `Serial.begin()` and does not read the serial port (the serial port is used for pairing). It does not use `BluetoothSerial`, BLE or Wi-Fi (the radio belongs to the Communications firmware). It does not print to serial for each sample.
- `seq`, `uptime_ms` and the left/right identity are filled in by the Communications firmware. The module does not deal with them (answer D: his 12th value and Bluetooth names were only for his PC).

**Issues found in the module (2026-10-15; reported to the owner; Siqiang's files are untouched).** None blocks the Communications build. Whether and how to raise them with Siqiang is the owner's decision (messages to teammates stay on interfaces and dates, section 10).

1. **The include path does not resolve where the file lives.** `hardware/gloves/integration_files/glove_sensor.cpp:4` is `#include "../../../movement_model_params.h"`. From `hardware/gloves/integration_files/` that path points at the repository root, where no such file exists, so the file does not compile in its own folder. The header is in the same folder, so `#include "movement_model_params.h"` would fix it. Communications builds copies in the layout the current path expects (the header at `firmware/esp32/movement_model_params.h`), and the sync tool also puts the header beside the copied `.cpp`, so the corrected include works too.
2. **Any failed reading restarts the movement classifier.** In `gloveUpdate()`, more than 100 ms between calls (`glove_sensor.cpp:487-489`), a failed IMU read (`:494-496`) or a non-finite sample (`:533-535`) calls `resetMovementClassifier()` (`:301-311`). That empties the 1 s window and sets the state to not ready and not MOVING. `gloveIsMoving()` then stays false until a new window has filled and two evaluations agree, at least about 1.2 s (a 1 s window, then a second evaluation 200 ms later). For that long the glove sends nothing, even in the middle of a gesture. In the Communications firmware `gloveUpdate()` runs every 1 to 2 ms, so only two things trigger it: the first call after boot (BLE set-up runs between `gloveBegin()` and the first `gloveUpdate()`; harmless, as the window is still empty) and transient I2C failures (2 ms I2C timeout). A possible change, for Siqiang to decide: skip a single failed or non-finite sample instead of resetting, and reset only after a longer outage.
3. **One failed read during calibration makes `gloveBegin()` fail.** `calibrateGyroscope()` returns false as soon as any one of its 1000 IMU reads fails (`glove_sensor.cpp:171`), and `gloveBegin()` then returns false (`:464`). The Communications firmware calls `gloveBegin()` once at boot, so after such a glitch the glove counts every tick as unread and sends nothing until it is power-cycled. Possible fixes: skip a failed calibration read (his side), or retry `gloveBegin()` a few times in `setup()` (a small Communications change, not made yet; a missing IMU still fails within milliseconds, a glitch costs about 4 s per retry).
4. **A design property, for Wen Ree (7.2):** MOVING needs two consecutive above-threshold evaluations 200 ms apart, so it comes at best about 0.2 to 0.4 s after motion starts, later for gentle motion; IDLE needs three consecutive below-threshold evaluations, so a still tail of at least about 0.4 s, possibly 1 s or more, is sent after each movement (`glove_sensor.cpp:381-389`, `:412-416`). The exact lags need real data. Samples before the MOVING decision are never sent. The two gloves gate independently.

**Still asked of Siqiang:** real samples for the scale check (a log from his own sketch, or a recording through the chain: a build with `-DCOMMS_GLOVE_SEND_ALL=1`, `python demo.py run --rate 50`, then `python -m tools.export_capture`); both gloves for flashing with `python flash.py --glove` and a joint test (Sat 10-17 or Sun 10-18, Mon morning at the latest), left with the owner until Tuesday if possible (6.3 step 6); and, if the owner raises them, whether he changes points 1 and 2. Once the Communications firmware is on a glove, his Bluetooth Classic recording script can no longer connect to it. His answers to the earlier questions (authoritative sketch, timing, call times, left/right, IDLE/MOVING, recording) are in 2.3.

### 7.2 From Wen Ree: the model's entry and exit on the board (called by the Communications service on the board)

The connection point is `ultra96/model.py` and the call in `ultra96/server.py` (line 329). **The Communications side is built (2026-10-14); Wen Ree's module does not exist yet.** The service loads it with `--model MODULE` (and `--model-path DIR` for where it lives on the board), checks that `start` and `on_sample` are plain callables (not `async def`), and without `--model` uses its built-in dummy model. Suggested shape (names are theirs to choose; if Wen Ree picks other names, only `ultra96/model.py` changes):

| Function | Provided by | Called by whom, when | Contract |
|---|---|---|---|
| `start(emit)` | Wen Ree | Called once by the Communications service at start-up, before the first sample | Load the model here, and tell Communications how long that takes. `emit` is the result exit that Communications hands to the model |
| `on_sample(device_id, boot_id, seq, uptime_ms, values)` | Wen Ree | Called by Communications once for each newly accepted sample, on the service's single thread. The return value is unused | **Must return immediately.** The service is a single asyncio event loop, and the ACK is written only after this returns. If it is slow, the ACKs of both gloves are held up (the laptop waits at most 5 s for an ACK; sample freshness is 2 s). Inference must run on another thread or in another process |
| `emit(gesture, confidence, device_id, boot_id, seq)` | **Communications** (built) | Called by the model once per result. It may be called from any thread | Communications moves the call safely back onto the event loop (the result queue has no lock). Returns `True` when the arguments are valid and the service is running, `False` otherwise; numpy-style numbers are accepted. Refused results are counted on the board (`model_results_rejected`, `model_results_duplicate`, `model_results_late`). Invalid, unknown-identity and duplicate results also log a warning, at most one per kind per second; results emitted after the service stopped are only counted |

`on_sample` fields:

| Field | Type | Meaning |
|---|---|---|
| `device_id` | 1 or 2 | 1 = left, 2 = right |
| `boot_id` | uint32 | A random number for this power-up of this glove. It changes when the glove restarts |
| `seq` | uint32 | Sample sequence number within this power-up |
| `uptime_ms` | uint32 | This glove's own millisecond clock. The two gloves are not synchronised |
| `values` | 11 floats | Order and units as in 7.1. The owner's direction (2026-10-14), to be confirmed by Wen Ree: physical floats. The values travel as int16; Communications decodes them and divides by the scale, so the model gets the agreed physical units. Restoring cannot recover precision dropped when packing: acceleration and flex keep 4 decimal places, angular rate and angles 2. Any normalisation the model needs is Wen Ree's |

What Communications guarantees: within one power-up (same `device_id` + `boot_id`), `seq` only increases and never repeats. After a glove restart, `boot_id` changes and `seq` starts again from 0, so track by `(device_id, boot_id)`. Samples can be missing, and the missing ones show as gaps in `seq`: lost over the radio; evicted when the laptop's 64-place queue for that glove is full; dropped after waiting more than 2 s on the laptop (not resent); or lost when a link drops (on a BLE disconnect the laptop discards that glove's queued samples, and on a TLS reconnect the samples already written but not acknowledged count as ambiguous drops and are not resent; that includes the first frame sent after the board closed a silent ingest connection, after 600 s or earlier when it needs the slot, 4.5 and 9.2). While a glove is disconnected it produces no samples and `seq` does not advance, so the disconnected time itself shows only as a jump in `uptime_ms`. The two gloves arrive over two independent connections, **with no pairing and no alignment**. Pairing, building windows and deciding gesture or idle all happen after the entry point, on the model side.

**What reaches the model since gating (2026-10-15; built, not yet run on hardware):**

- **Only samples the glove's detector calls MOVING.** While a hand is still, its glove sends nothing, so `on_sample` gets nothing from it. A pause shows as a jump in `uptime_ms`; `seq` has no gap there, because a skipped tick takes no number. A `seq` gap still means a lost sample.
- **The two gloves decide independently.** One glove can send while the other is silent, so a 50-step window may hold samples from one hand only.
- **The start of a movement is not sent.** From Siqiang's code (`glove_sensor.cpp:381-389`, `:412-416`), MOVING needs two consecutive above-threshold evaluations 200 ms apart, so at best it comes about 0.2 to 0.4 s after a movement starts, and later for a gentle movement. IDLE needs three consecutive below-threshold evaluations, so it comes at least about 0.4 to 0.6 s after the 1 s window stops scoring as motion, and that window still holds the movement for up to 1 s after it stops. So a still tail of at least about 0.4 s, possibly 1 s or more, is sent after each movement. The exact lags need real data. Samples before the MOVING decision are never sent, and the link cannot send them later (about 66 samples/s per glove is the measured ceiling, so there is no room for a backlog). After a failed sensor reading, a glove may send nothing for about 1.2 s or more (7.1, point 2).
- In the `-glove` builds each glove starts at 50 Hz. `python demo.py run` without `--rate` sets both to 10 Hz (9.2).

Questions for Wen Ree about this (drafted for the owner on 2026-10-15; whether they were sent is for the owner to record in 6.4): whether the onset lag is acceptable for the model's windows, or whether the model needs the start of each movement (then it is a change on the detector side, to agree with Siqiang); and how the model treats a window in which one glove is silent.

`emit` fields:

| Field | Type | Meaning |
|---|---|---|
| `gesture` | string | The label text as it is (the field name on the wire is `gesture`): 1 to 32 characters from `A–Z a–z 0–9 _ -` |
| `confidence` | number from 0 to 1 | Confidence, passed on unrounded |
| `device_id`, `boot_id`, `seq` | as above | The identity of **one** sample this result used (usually the newest one in the window; either glove is fine). Communications uses it to build `result_id` (`device_id:boot_id:seq`). **Each result must point to a different sample**: the phone de-duplicates by `result_id`, and a second result with the same identity is dropped |

The result message cannot gain fields freely. The field set of `GESTURE_RESULT` is matched exactly in four places (the board, the iPhone and the two reference receivers), so the only correlation information is one sample's identity. Communications forwards the label and the confidence as they are, without filtering or renaming. Results, like samples, are not resent. The board drops a result when no phone is subscribed at the moment it is produced. When 32 results are already waiting, the oldest is dropped (`ResultQueue.put`). It also drops a queued result that has waited 2 s or more on the board (`get_timed`). The write to the phone's connection gets only what is left of those 2 s (`_send_results`). If the write does not finish in what is left of those 2 s, the board does more than drop that result: it ends that phone's subscription (`result_send_failed`, `reason=error`), abandons what is still queued, and the phone reconnects and subscribes again. This limits waiting on the board only. It is **not** a promise about when, or whether, the phone receives the result: bytes already handed to TCP/TLS cannot be recalled, and the phone keeps its own 2 s display window counted from when it received the result. There is no end-to-end latency bound (9.2).

Whether the model can run directly inside the Communications service process: the service runs as the ordinary user `xilinx` (no sudo) with `/usr/bin/python3` (3.10), and uses only the standard library itself. If the model code runs in this process, everything it imports (numpy, pynq and so on) must load under this interpreter and this user. `fpga/README_FPGA_PYNQ.md` says the overlay is loaded with sudo and the pynq-venv Python. If the model can only run that way, it is a separate process, and Communications defines a format for passing the same fields between the two processes on the board. That is the owner's work, not a new network route.

Asked of Wen Ree in the message (once the owner sends it): whether it can run inside the Communications process (module and function names) or must be a separate process, and which packages it depends on; the full label set (by default the six in `models/class_names.json`); how often a result is produced (`src/live_inference.py` currently, once 50 samples have accumulated, produces one result for every new sample, including those with confidence below 0.70, and has no "idle" label; is the board version the same?); a first version that can be connected by Fri 10-16 (even one that always returns the same label), pushed to the team repo: for the in-process option, the module and function names; for the separate-process option, how to start it, its dependencies, and its input and output in the format the owner sends on Thu 10-15; and how out-of-range values should be handled (8, step 1).

### 7.3 For Jie Ling: the interface Communications provides (called by the game)

Proposed (the owner's direction, 2026-10-14; final when Jie Ling confirms): **Jie Ling does everything in Unity and the iOS build, on their own Mac and iPhone: the C# that calls the Communications functions, the game logic, exporting the project, adding `CommsNative` to the Xcode project, building, and installing the app. olsonwangyj provides `CommsNative` in the team repo (`ios-visualizer/CommsNative`), pushes the new parts there, and sends short steps for adding it to the Xcode project.** Patching an export is no longer used, and no export is passed between people. Communications **needs no API from the game**. The game calls the three existing Communications C functions (section 4.6), plus the fourth one, `CommsNextResult` (in the source since 2026-10-14; compiled and tested on Linux since 2026-10-15; not yet built for iOS or installed), and can use the Week 7 receiver as an example. On the phone, Jie Ling uses the NUS VPN, logs in in the app with their own jump-host and board accounts, and imports the CA file the owner shares (9.2). The message asks Jie Ling to have it installed before the integration session on Tue 10-20 and to tell the owner about any problem at any time; the only question in it is whether the timing works.

C# declarations of the three functions (derived from the C signatures; not yet compiled in Unity). These symbols exist only in the iOS build. Calling them in the Unity Editor or on other platforms throws an exception, so calls go inside `#if UNITY_IOS && !UNITY_EDITOR`:

```csharp
[DllImport("__Internal")] static extern void CommsStart();
[DllImport("__Internal")] static extern int  CommsCopyDisplay(byte[] buffer, int capacity);
[DllImport("__Internal")] static extern void CommsStop();
```

- `CommsStart`: call once at start-up. It places the `Communications Connect` button in the top-right corner of the screen and does not connect by itself. A person taps the button, enters the jump-host and board login details, and imports the CA. Keep that corner clear.
- `CommsCopyDisplay`: call once per frame on the main thread with a 2048-byte buffer. It returns the number of UTF-8 bytes written (not counting the terminating 0). When nothing changed, or the buffer is null or too small, it returns 0 and writes nothing, and the game should keep the text it already has.
- `CommsStop`: call only when the app closes. It ends the session, clears the passwords and removes the button. Do not call it on a scene change or when going to the background.
- Line 2 of the text is the status. `Subscribed` means only that the subscription handshake with the Ultra96 succeeded; it does not prove that results are flowing.
- Line 3 holds only the latest result and is overwritten by the next one, so results that arrive between two polls can be lost (4.6). Use it to watch results while testing, not as game input. Line 1 is `Communications` in the current source (the installed Week 7 build still shows `Week 7 • DUMMY inference` and `confidence 1.0`); line 3 shows the received confidence (`DisplayMailbox.swift:16-18`). Do not parse the display text. Ids starting with `cmd:` come only from the owner's command tests on the laptop.
- **Per-result delivery is Communications' job; `CommsNextResult` is in the source (2026-10-14), compiled and tested on Linux (2026-10-15), but not yet built for iOS or installed.** The game's action entry points are one-shot: in `vis/Assets/Scripts/Core/GestureButtonController.cs` the `On...Pressed` methods are wired to the on-screen buttons' `OnClick()`, and its comment says Ultra96 gestures will call them later. So the game needs results one at a time, not a display that the next result overwrites. The owner's direction (2026-10-14): add a fourth bridge function that hands out structured results one at a time. Proposed shape:

  ```c
  int32_t CommsNextResult(char* buffer, int32_t capacity);
  ```

  It removes the oldest result still waiting and writes it as one compact UTF-8 JSON object with a terminating 0, for example `{"result_id":"1:305419896:42","gesture":"CHOP","confidence":0.93,"device_id":1}`, and returns the number of bytes written (not counting the 0). It returns 0 when no result is waiting. If the buffer is null or too small for the next result (it needs the bytes plus the terminating 0), it writes nothing, leaves the result in the queue and returns minus (bytes + 1), the capacity needed; with a 512-byte buffer this does not happen with the expected labels. The game calls it in a loop each frame while it returns a positive number. In C#: `[DllImport("__Internal")] static extern int CommsNextResult(byte[] buffer, int capacity);`. It exists in `DisplayMailbox.swift` since 2026-10-14 and was compiled and tested on Linux on 2026-10-15 (4.6); the owner tests it on the Mac and builds it for iOS (6.3 steps 3 and 4) and pushes `CommsNative` to the team repo by Sun 10-18 (6.4). Jie Ling can write the C# against the declaration now.

  What it promises, and what it does not: results wait in a queue in arrival order, de-duplicated by `result_id`, and each result that is not dropped can be taken out at most once. It does not promise that every result is delivered: results lost before the phone (board drops, reconnects, no subscriber) never arrive, and the queue itself drops results, counting each drop. Provisional V1 limits, the same rules the board uses: at most 32 results wait; when full, the oldest is dropped; a result still waiting 2 s after it reached the phone is dropped. At 50 results a second, 32 places last only about 0.64 s if the game stops reading, so the limits are revisited once Wen Ree says how often results come. The queue is emptied when the session stops (Disconnect, the app becoming inactive, `CommsStop`) and when a new Connect starts; an automatic reconnect keeps it, and its entries still expire after 2 s (also after a terminal error, which goes through the same path as a reconnect status). A null buffer counts as too small. Expired and dropped results are counted (`pendingExpired`, `pendingDropped` in the display snapshot; both reset on a new Connect, like `Received`). Expiry also happens while only `CommsCopyDisplay` is polled, so results that nobody takes out are dropped after 2 s rather than kept. Whether several identical labels in a row mean one action or several is for Wen Ree and Jie Ling to agree; Communications hands out every result as it is.
- Only one object may call `CommsCopyDisplay` (each call reports only the change since the previous call), and that object must survive scene changes. The same object would call `CommsNextResult`.
- What to do with a result (which action it maps to, cooldowns, repeats) is the game's business.
- The phone can no longer rely on the 5005 listener. Results come in only through the Communications bridge functions: the three that exist today and, once built for iOS and installed, `CommsNextResult`, which is the game input.
- Passwords are not saved. As soon as the app stops being active (going to the background, screen lock, pulling down Control Center or Notification Center, an incoming call), it disconnects and clears the passwords, and they must be entered again.
- Reference: in Week 7 the owner had no Unity project and patched the generated C++ (`TlsDataReceiver`) of one Xcode export. Jie Ling's own C# was never changed. The patched export is only on the fork. The patch script <https://github.com/olsonwangyj/Let-Them-Cook/blob/main/ios-visualizer/tools/patch_export.py> is for reference only and cannot be run against a new project.

Until `CommsNextResult` is built for iOS and installed, the game can show the text and test the connection, but it cannot drive actions reliably from it.

---

## 8. Communications' own extension points (the owner's work)

These are olsonwangyj's tasks, in order. Status on 2026-10-15 (branch `comms/protocol-v3`; details in 6.5):

1. **Real data packet, version 3. Done in code (built; the right board verified with the 2026-10-14 build).** 38 bytes (16-byte header plus 11 × int16), the scales in 4.2, version 3 only everywhere, the formula dummy removed, `LCS3` statistics (36 bytes since 2026-10-15), MTU floor 41, 52-byte command frames; golden vectors `tests/fixtures/comms-golden.json`, `comms-dummy.bin`, `comms-boundaries.bin` (hand-specified, printed identically by `firmware/esp32/test/host_packet.cpp`). The IDLE/MOVING question is answered without a packet change: a glove sends only while MOVING, and the state does not travel (D20). **Still open:** the scales are checked against Siqiang's real samples before the layout is frozen. In normal use every value is expected to fit, but that is not guaranteed: the final value depends on the module's processing (for example the gyro calibration bias is subtracted), not only on the raw sensor range. **Out-of-range values are to be agreed with Wen Ree**: the firmware supports both answers (clamp, the default, or drop with `-DCOMMS_OUT_OF_RANGE_DROP=1`), counts what it clamps or refuses, and never drops a connection or a whole gesture. A clamped value cannot be told apart from a real value at the limit (for example 3.2767 g can be either); if the model needs to know which samples were clamped, a per-sample flag is needed, which again changes the packet and `on_sample`. Neither option guarantees that a gesture is still recognised. **Only the newest version is supported (the owner's rule, 2026-10-14):** an upgrade means reflashing both boards, redeploying the Ultra96 service and reinstalling the phone app together; an old phone build rejects version-3 results.
2. **Connect the sensor module in the firmware. Done in code (built 2026-10-15); not yet run on a board.** The glove module API (`comms_glove.h`), gating, the sample policy (`prepareSample`) and `produceSample()` outside the connection mutex are in `main.cpp` (4.3). Siqiang's module is connected in the `firebeetle32-left-glove` and `-right-glove` builds (50 Hz from boot), which compile and link. **Still to do (6.3 step 2):** on the owner's boards (no IMU), check that a `-glove` build prints `glove_begin ok=0` without blocking and that the board still advertises; flash the gated dummy and check that it passes.
3. **Measure. One board done (2026-10-14 build); the gated firmware and two gloves not.** One board, 38 bytes, 50 Hz, 65 s, clean (6.1). Still needed: the gated dummy on one board; then two real gloves together, 50 Hz, at least 65 s, with clean source reconciliation and the gated coverage rule passing on both boards.
4. **Connect the model interface on the board. Done on the Communications side (built).** `ultra96/model.py` and `--model`; waits for Wen Ree's module (7.2).
5. **Accept model labels and real confidence. Done:** `ultra96/protocol.py` and `phone/receiver.py` (built and tested), `phone/unity/CommsPhoneCore.cs` (compiled at C# 7.0 on 2026-10-15, and its self-test passed 113 checks under PowerShell 7), `CommsCore/Protocol.swift`, the `confidence` field, `CommsNextResult` and the display texts (compiled and tested on Linux on 2026-10-15; not yet built for iOS). **Until the phone app is rebuilt, it cannot use the version-3 service:** it cannot subscribe (it uses session `week7-demo`), and any version-3 result, dummy or real, would end its session with a terminal error, because its result check does not accept version 3 (6.3 steps 3 and 4).
6. **The "one input, one result" criterion.** Once the model produces results per window, the reconciliation rules behind `Phone expected increase` in `demo.py` and in the two rehearsal tools (`tools/rehearse_comms.py`, `tools/rehearse_remote_comms.py`) must be redefined. **Not done:** it waits for Wen Ree's answer on the result rate. The built-in dummy model keeps one result per input, so these criteria stay valid while it is used (`demo.py run` prints a line saying so).
7. **Steps for adding `CommsNative` to the Xcode project.** Push `CommsNative` with `CommsNextResult` to the team repo and write short steps for Jie Ling: add the local Swift package `ios-visualizer/CommsNative` to the exported Xcode project and link it into `UnityFramework`. Jie Ling builds and installs; the owner helps if the build fails. `patch_export.py` is no longer needed. `configure_xcode.py` depends on fixed Xcode object IDs; whether it works on a new export is unverified. **Not done:** `CommsNative` (with `CommsNextResult`) is on the local branch only. It compiles and its tests pass on Linux; the owner approved pushing the team branch on 2026-10-15, but it is not pushed yet, and the steps wait for the iOS build on the Mac (6.3 steps 3 and 4).
8. **Do one redeploy round as in section 6.3 and run the acceptance check. Not done (the owner's login).** It is now one command for the board side (`tools/deploy_service.py`).

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

- **The certificate lasts only 30 days.** The renewed one expires on **2026-11-13 14:27:35 UTC**, before the final demo around Week 13, so renew again in early November (`--renew-server-from`, then `tools.deploy_service --server-cert-dir`). After it expires the service still starts, but the laptop gets no ACK at all and the phone stops at `SSH, TLS or protocol verification failed`. `tools.deploy_service` refuses to deploy with a certificate that expires within an hour. Running the certificate tool without `--renew-server-from` replaces the CA too, and then the fingerprint in the phone source and the laptop's `--ca` must both change.
- **The session ID must match on all three ends.** On a mismatch the board closes the connection. The symptom is `received` rising while `acked` stays at 0, or the phone bouncing between `Connecting` and `Disconnected`.
- **Port defaults differ.** `demo.py` uses 18889. Running modules such as `laptop.dual_bridge` or `tools.ssh_tunnel` directly defaults to 18888. The tunnel and the capture must use the same port.
- **Personal defaults are written in the code.** The default account in `demo.py tunnel`, the default path of `demo.py --ca`, the account and board paths in `tools/demo_service.py` (these cannot be changed with arguments), the jump-host account `yanjie` and `BOARD_ROOT` used by `tools/deploy_service.py` (`--jump-user`, `--board-user` change the accounts), and the two boards' Bluetooth addresses in `tools/demo_boards.py`. Watch these when the person, the machine or the boards change.
- **`demo.py service --start` follows the newest local deployment record** (`.comms-local/deployments/`, written by `tools.deploy_service`) and falls back to `BOARD_SOURCE`, the 28 September snapshot. A deployment made by hand, or from another laptop, leaves no record here, so `--start` would then start the old code.
- **The service process does not reclaim identity capacity.** Each glove power-up takes one `(device_id, boot_id)`. A process allows at most 128; when they run out, the service must be restarted. A restart clears the de-duplication state.
- **With no subscriber, results are dropped at once.** So get the phone to `Subscribed` first, then start the capture.
- **Silent ingest connections stay open for up to 600 s (since 2026-10-15).** A laptop that vanished (sleep, a VPN drop) can leave its connection open on the board for up to 600 s, because sshd may keep the socket; such half-open connections take some of the 8 client slots. When all 8 are taken, the board closes the ingest connection that has waited longest (at least 5 s) for a new client (`idle_evicted`, with a warning log line). A live glove that is only still and is closed this way (or after 600 s) reconnects when it next sends. The laptop reads ACKs only while frames are pending (`laptop/bridge.py:599-624`), so it notices the close only then: the first frame written after the close (usually only that one) counts as an ambiguous drop. The samples that arrive during the back-off of 0.5 s or more (`:668-673`) and the TLS reconnect wait in the 64-place queue (the oldest is dropped when it is full) and are dropped if older than 2 s. The event also raises `transport_errors` and `ambiguous_dropped` (and `ack_errors` when the ACK read fails), so that capture is not clean.
- **After the GATT table changes or the firmware is reflashed, Windows may need to pair again.** Recovery is manual: `erase-bonds` on the board's serial port → remove the board in Windows → pair again.
- **At high rates the actual packet rate is below the setting** (the 70 Hz setting gives about 66 packets/s). From 75 Hz up, packets are lost.
- **Whoever holds the phone logs in with their own account.** Any teammate can log the phone in with their own NUS VPN, jump-host and board accounts; it does not have to be olsonwangyj's phone or account (the owner's correction, 2026-10-14). Each person types only their own passwords; nobody shares a password. Because the passwords are not saved, the person holding the phone must be able to log in again whenever the app stops being active. Whoever builds the app installs it from their own Mac with their own Apple ID; with a free Apple ID the installed app expires after 7 days and is installed again.
- **The phone works only in the foreground.** Locking the screen or switching away disconnects it and clears the passwords.
- **There is no end-to-end timestamp.** The 2 s freshness is each segment's own waiting time, not end-to-end latency.
- **The model's `on_sample` runs on the service's only event loop, before the ACK.** A model that does its inference inside `on_sample` holds up the ACKs of both gloves (the laptop waits at most 5 s; sample freshness is 2 s). The counters `model_slow_calls` and `model_max_call_ms` in the `stopped` line show it; inference belongs on another thread or in another process. An `async def on_sample` is refused when the model loads. A model whose threads are not daemon threads no longer keeps a stopped service alive (`exit_with_model_threads`), but its threads end abruptly then.
- **The board service writes one INFO log line for each accepted input.** With both gloves at 50 Hz that is about 100 lines per second. They go to the service's output: the foreground SSH terminal when it was started with `demo.py service --start`, or the log file under `BOARD_ROOT/evidence/` when it was started in the background by `co_deploy.py` or `tools.deploy_service` (`server-co-<stamp>.log`, or `rollback-server-<stamp>.log` after a rollback). A service started by `tools.deploy_service` also writes an event log (`observer-co-live-<stamp>`) unless `--no-event-log` is given.
- **`flash.py` rewrites the Git-tracked `comms_fixtures.h` every time.** After changing `common/dummy_fixtures.json` you must reflash before the data on the board changes.
- **A leftover `LTC_COMMS_SESSION` in the terminal.** Documents from the transition period taught setting `LTC_COMMS_SESSION=week7-demo`. This variable affects `demo.py run`, `live` and `service --start` together, but not the phone. If it is still set, the laptop and a newly started service both use `week7-demo`. `CAPTURE PASSED` still appears, but the phone stays at `Disconnected: connection closed; retrying`. When troubleshooting, first make sure this variable is not set.
- **Neither end records why something was rejected.** For a bad frame, a session mismatch, an identity conflict or exhausted capacity, the board only closes the connection and adds 1 to `rejected`; it writes no log entry, and it prints its metrics only once, when the service stops. On the laptop, an ACK timeout or a mismatched ACK increments both `ack_errors` and `transport_errors`; a TLS connect or handshake failure increments only `transport_errors`. Neither counter records a reason. So an expired certificate and an unreachable port look the same (only `transport_errors`), and a session mismatch and a protocol version mismatch between the two ends look the same (the board closes the connection after the frame, which counts as both). For the 38-byte migration, both ends must be upgraded together.
- **The phone's "automatic retry" logs in to both SSH hops again and again.** When the board service is not running, the session does not match, or another subscriber has pushed the phone off, the phone treats it as a closed connection. It then logs in to the jump host and the board again with the passwords, after a delay that starts at 0.5 s and doubles up to 5 s (reset after a result arrives), with no limit on attempts. When the service is not ready, tap Disconnect first; do not leave the app on retrying.
- **A service started with `demo.py service --start` is the foreground process of that SSH session.** Closing that terminal, the laptop going to sleep or the VPN dropping all make the service exit. Keep the terminal that started the service open, like the tunnel terminal. This applies only to the `--start` path. The process recorded on the board on 2026-09-28 was started in the background by `.week7-local/co_deploy.py`, does not depend on any SSH session, and may still be running (4.5).
- **A different laptop needs `known_hosts` first.** Both SSH hops use strict host-key checking, and nothing in the repository writes `known_hosts`. The two public keys in the phone source `Configuration.swift` can be used to check them.
- **The single-board diagnostic tools cannot choose a board.** `laptop.ble_counter_receiver`, `laptop.mtu_probe` and `tools.rehearse_comms --ble` scan by service UUID and connect to whichever board they find first. The two boards advertise the same name, so power only one board when using these tools. They also do not set the rate, so the board keeps its last rate. `tools.check_board left|right` (2026-10-14) connects by the board's address and sets the rate, so the other board may stay powered.
- **Symptoms when a board still has old firmware.** The two-board capture reads the source statistics first. A value that is not 36 bytes long (version-2 firmware's `LCS1`, and the 24-byte `LCS3` of the 2026-10-14 build) is reported as `source statistics must contain exactly 36 bytes; flash this board with the current firmware`; a 36-byte value with another marker as `invalid source statistics magic; flash this board with the current firmware`. Week 7 firmware (`W7S1`) is refused too. That board is not subscribed, and start-up times out after 30 s. On 2026-10-15 both of the owner's boards are in this state (6.3).
- **Glove builds use 87.6% of the flash** (1148437 bytes; the dummy build 85.6%). About 160 KB are left for the module and the firmware to grow; watch the PlatformIO size line after any change.
- **A `-glove` build on a board without sensors sends nothing.** `gloveBegin()` reports no IMU (`glove_begin ok=0`), every send tick counts as `unread`, and `tools.check_board` fails with "nothing acknowledged". Use the plain environments on the owner's boards, and the `-glove` ones only on Siqiang's gloves.
- **A gated glove is silent while the player is still, and the first part of each movement is not sent** (7.2). A board in calibration does not advertise yet: hold the glove still for about 5 s after power-up. After a failed sensor reading the glove may send nothing for about 1.2 s or more (7.1, point 2).
- **`python demo.py run` sets both boards to 10 Hz unless `--rate` is given.** The `-glove` builds start at 50 Hz, the model's rate; run `python demo.py run --rate 50` with the gloves. The rate a capture sets stays until the board reboots.
- **`python flash.py --glove` rewrites `.comms-local/boards.json` with the gloves' addresses**, like any full `flash.py` run. Captures and `tools.check_board` then address the gloves, not the owner's boards; run `python flash.py` again with the owner's boards to switch back.
- **Stale copies of Siqiang's module.** The firmware builds copies, never the files in `hardware/`. After Siqiang changes his module in the team repo, merge the team main and run `python -m tools.sync_glove_module`. Until then `tests/test_glove_module_sync.py` fails and `flash.py --glove` refuses to build. Never edit the copies.
- **A timing-sensitive test.** `tests/test_server_diagnostics.py::test_close_deadline_includes_status_persistence` (a 0.01 s close, a 0.2 s wait) failed once under load on 2026-10-15 and passed on the rerun. Rerun it alone before treating it as a regression.
- **Captures made before version 3 cannot be re-checked with the current code** (`demo.py report`, `tools/video_evidence.py`); use `c42b386` or the team main `5a004c6` for them.
- **The opt-in Linux deploy test (`B07_LINUX_DEPLOY_TEST=1`) starts and stops `ultra96.server` processes inside the local WSL Ubuntu.** Never run `tests/linux/deploy_remote_test.sh` on the Ultra96 itself.
- **For agents: escapes can be rewritten on the way into a file.** On 2026-10-14 the tool layer turned `\u` escapes and `\n` inside strings passed through shell here-documents into literal characters in three cases. After writing test vectors or strings with backslash escapes, compare the file's bytes with what was meant (`git diff`, `py_compile`).
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
| Saying the link was tested only at 10 Hz, or that the Bluetooth approach is not decided | The 50 Hz and 70 Hz settings were measured clean on 2026-09-28 with the 32-byte dummy packet (70 Hz setting: about 66 packets/s). BLE was chosen long ago |
| Slipping opinions on the quality of teammates' components into messages (model accuracy, gyro range, a path bug, and so on) | Talk only about interfaces and delivery dates |
| Asking teammates questions the code already answers | Read the code first. Ask only what the code cannot answer (physical state, intent, plans) |
| Using a password the owner pasted | Never use, store or repeat it. The owner does the logins |
| Thinking Siqiang writes the firmware after the merge | Siqiang provides the sensor module. The owner writes the merged firmware |
| Wanting to rename the TLS host name, the `Week7*` functions and the like | These are either written into the certificate or part of the Week 7 receiver. Leave them |
| Assuming only the owner can log the phone in, because the jump-host account is personal | Any teammate can log in with their own NUS VPN, jump-host and board accounts; the phone need not be the owner's (2026-10-14) |
| Using gendered pronouns for teammates | Use names or "they" |

---

## 11. Running and verifying

**No hardware needed:**

```powershell
python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider
python -m tools.generate_comms_pki --output-dir <an empty directory outside the repository>      # one-off certificates, for local rehearsal only
python -m tools.rehearse_comms --pki-dir <the same directory> --duration 30 --target 100
python -m tools.sync_glove_module --check                    # the firmware's copies of Siqiang's module are current (exit 0)
python -m tools.export_capture [<capture folder>] [--out <file.csv>] [--device 1|2]   # a capture's samples as CSV
& "$env:USERPROFILE\.dotnet\tools\pwsh.exe" -NoProfile -File phone/tests/run_core_tests.ps1   # C# self-test (PowerShell 7)
```

The rehearsal starts a board service, a bridge and a subscriber on the local machine and prints one JSON line. `passed` should be `true`. With `B07_LINUX_DEPLOY_TEST=1` set, the pytest run also exercises the deploy tool's board-side program in WSL Ubuntu (it starts and stops `ultra96.server` processes there). On 2026-10-15, at `d582ce6`, the suite gave 841 passed, 4 skipped, and on 2026-10-16, at `4c6ab4c`, 842 passed, 4 skipped (without the opt-in Linux test; with it, the last recorded totals are those of `15de82e`, 780 passed, 3 skipped). The C# self-test prints `PASS 113 C# contract/frame/freshness checks`.

The Swift tests: on a Mac, `swift test --package-path ios-visualizer/CommsNative` (Xcode with Swift 6.1 or newer). On this laptop, in the Docker image `swift:6.1`, with the package and `ios-visualizer/reference` (two `ConfigurationTests` read a certificate there) mounted read-only and built in a copy inside the container, from the repository root: `docker run --rm -v "${PWD}/ios-visualizer/CommsNative:/src/CommsNative:ro" -v "${PWD}/ios-visualizer/reference:/src/reference:ro" swift:6.1 bash -c "cp -r /src /work && cd /work/CommsNative && swift build --build-tests && swift test"`. That gave 72 tests, 0 failures, on 2026-10-15; it does not cover the iOS-only code (4.6).

**One board, no Ultra96 (after flashing):**

```powershell
python -m tools.check_board right          # or left; 65 s at 50 Hz, 3 commands; prints CHECK PASSED and gated/idle/unread/refused
```

The gated dummy build and the `-glove` checks are in 6.3 step 2; the real gloves in 6.3 step 6 (`python flash.py --glove`).

**Deploying the board service (the owner's login):** `python -m tools.deploy_service --dry-run`, then `python -m tools.deploy_service [--server-cert-dir <folder>] [--model MODULE --model-path DIR]` (6.3 step 1). It needs `paramiko` (in `requirements-dev.txt`; on this laptop it comes with Anaconda, version 2.8.1); the dry run does not import it.

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

**Flashing and pairing:** `python flash.py` (left first, then right), `python flash.py --glove` (Siqiang's gloves with his module; left first), `python flash.py --pair left`, `python flash.py --monitor COMx`, `python flash.py --boards`. With the gloves, capture at their rate: `python demo.py run --rate 50`.

Symptoms, causes and recovery for common faults are in `docs/handoff-details/06-tests-operations-extension.md`.

---

## 12. Code map: what each folder and file does

This section lets a new agent know where things are without re-reading the code. Before changing a file, still read the file itself.

### 12.1 Top level

| Path | Owner | What it is |
|---|---|---|
| `firmware/esp32/` | Communications | BLE peripheral firmware for the two FireBeetle ESP32 boards (PlatformIO project), with the built-in dummy glove module and, in `lib/glove_sensor/`, an unchanged copy of Siqiang's module |
| `common/` | Communications | Python modules shared by the laptop and the Ultra96: packet format, control frames, network frames, TLS |
| `laptop/` | Communications | BLE reception and forwarding (relay) program on the Windows laptop |
| `ultra96/` | Communications | The service on the Ultra96: receives samples, replies with ACKs, pushes results to the phone |
| `phone/` | Communications | Reference and diagnostic receivers (Python, Android C#, iSH scripts). **Not** the one deployed on the iPhone |
| `ios-visualizer/` | Communications | The native iPhone client `CommsNative` (Swift), the patch tools of the Week 7 receiver, a preview app |
| `tools/` | Communications | Operations and rehearsal tools: tunnel, board service, certificates, dummy data, rehearsal, evidence |
| `tests/` | Communications | Communications Python tests (they also compile and run the firmware host tests) |
| `demo.py` | Communications | Day-to-day entry point: `tunnel`, `run`, `live`, `report`, `service` |
| `flash.py` | Communications | Builds and flashes the two boards (`--glove`: Siqiang's gloves with his module), records Bluetooth addresses, pairs, serial monitor |
| `requirements-dev.txt` | Communications | Dependencies for the tests, the certificate tool and the deploy tool (pytest, cryptography, `paramiko>=2.8,<4` for `tools/deploy_service.py`, added with the documents after `3b94990`; the pyserial listed there is not used by Communications code). On this laptop paramiko 2.8.1 comes with Anaconda |
| `docs/` | Communications | olsonwangyj's documents (fork only) |
| `AGENTS.md`, `CLAUDE.md` | Communications | Rules for agents: ownership table, role boundaries, test command, document rules (fork only) |
| `hardware/` | Siqiang | Glove firmware sketches, recording scripts, schematic, and the sensor module for the Communications firmware (`gloves/integration_files/`). **Read-only** |
| `src/`, `models/`, `data/`, `reports/`, `fpga/`, `export_fpga_reference.py`, `requirements.txt` | Wen Ree | Model training and inference, weights, data, FPGA project. **Read-only** |
| `vis/` | Jie Ling | Unity AR game project. **Read-only** |
| `README.md`, `.gitignore` | Shared | Only Communications lines may be added or changed |

### 12.2 Communications code, file by file

**`common/` (shared by both ends; changing it changes the laptop and the board service at once)**

| File | What it does |
|---|---|
| `sensor.py` | Encoding and decoding of the 38-byte version-3 sensor packet (`SensorPacket`, `encode_packet`, `decode_packet`, `PACKET_MAGIC = b"LC"`, `VERSION = 3`, `CHANNELS`, `SCALES`, `PACKET_SIZE`, `SENSOR_MTU_FLOOR`); `physical_values` (int16 / scale); converting a packet into a `SENSOR_BATCH` message; loading and choosing dummy data |
| `control.py` | Encoding, decoding and validation of BLE control frames (14-byte `B7` header); the rule for how commands transform the 11 values. Unrelated to network JSON |
| `wire.py` | Network frames: 4-byte big-endian length + strict UTF-8 JSON; limit 16384 bytes; a 5 s deadline for each read and write; `read_frame(..., idle_timeout=...)` (2026-10-15) waits that long for the first header byte, then 5 s for the rest of the frame; `ProtocolError` |
| `tls.py` | TLS client and server contexts; TLS 1.2 minimum; the host-name constant `TLS_SERVER_NAME`; no "do not verify" branch |
| `dummy_fixtures.json` | The editable 11-channel dummy-data table (4 rows: at rest, a chop-like row, a fast-rotation row and an int16-boundary row). The firmware header is generated from it |

**`firmware/esp32/`**

| File | What it does |
|---|---|
| `platformio.ini` | Six build environments: the default `firebeetle32` (protected, ID 1), `firebeetle32-left` (ID 1), `firebeetle32-right` (ID 2), `firebeetle32-left-glove` (ID 1) and `firebeetle32-right-glove` (ID 2) with Siqiang's module at 50 Hz, and the unprotected diagnostic `firebeetle32-unprotected-diagnostic`. `[env]` has `lib_ignore = glove_sensor`; only the `-glove` environments clear it |
| `src/main.cpp` | All the BLE peripheral run-time logic: the GATT service and its 7 characteristics, pairing security, the calls into the glove module (`gloveBegin` in `setup()`, `gloveUpdate` every pass, `produceSample()` at each send tick, lines 404-431), sending samples at the set rate, the control queue, source statistics, the `glove_begin`/`comms_ready`/`comms_stats` serial lines, the `erase-bonds` serial command |
| `src/dummy_glove.cpp` | The built-in dummy glove module (2026-10-15; linked when `COMMS_GLOVE_MODULE` is 0): fixture rows as physical floats, and the optional IDLE/MOVING cycle |
| `src/glove_module.cpp` | For Siqiang's module (linked when `COMMS_GLOVE_MODULE` is 1): `gloveShouldSend()` = his `gloveIsMoving()`, or always true with `COMMS_GLOVE_SEND_ALL=1` (2026-10-15) |
| `include/comms_glove.h` | The glove module API (`gloveBegin`, `gloveUpdate`, `gloveRead`, `gloveShouldSend`) and its build switches: `COMMS_GLOVE_MODULE`, `COMMS_DUMMY_MOVING_MS`, `COMMS_DUMMY_IDLE_MS`, `COMMS_GLOVE_SEND_ALL`; `kGloveGated` (2026-10-15) |
| `include/comms_dummy_gate.h` | The portable parts of the dummy module, host-tested: the IDLE/MOVING cycle `dummyMoving` and `dummyFixtureSample` (2026-10-15) |
| `lib/glove_sensor/` | Unchanged copies of Siqiang's `glove_sensor.cpp`, `glove_sensor.h` and `movement_model_params.h` (in `src/`), and a README that says not to edit them. Made by `tools/sync_glove_module.py` (2026-10-15) |
| `movement_model_params.h` | A second copy of Siqiang's weights header, where his `#include "../../../movement_model_params.h"` finds it from `lib/glove_sensor/src/` (2026-10-15) |
| `include/comms_packet.h` | Version-3 constants (`kPacketVersion`, `kChannelCount`, `kPacketSize` = 38) and byte-by-byte serialisation of the packet; `serializePacket` takes exactly 11 values (a shorter array does not compile); `serializeFixturePacket` builds a packet from a dummy-table row, now only as the reference for the host tests (the board's dummy module gives the same bytes through the sensor path) |
| `include/comms_sample.h` | `scaleSample`: 11 physical floats to 11 int16 (rounding half away from zero; NaN/infinity refused; clamp by default or drop with `-DCOMMS_OUT_OF_RANGE_DROP=1`). Since 2026-10-15 also `prepareSample` (the outcome of one tick: send, unread, idle or refused), `SampleCounters`, and `sendTickDue` (the send tick that keeps its rate) |
| `include/comms_fixtures.h` | The dummy-data table generated from `common/dummy_fixtures.json` (`flash.py` rewrites it every time) |
| `include/comms_security.h` | Pure functions: authentication-bit checks, the notification gate, the sensor MTU floor of 41 (`sensorFitsMtu`, packet size + 3) and the control-write gate (`canAcceptControl`) |
| `include/comms_source_stats.h` | Sequence allocation, submission counters, serialisation of the 36-byte source statistics (marker `LCS3`, the gated flag, `idle`, `unread`, `refused`) |
| `include/comms_control.h` | The control state machine `ControlEngine`: commands (one version-3 packet in, 52-byte answer out), rate, file transfer, response cache. Also the control MTU floor of 64 (`controlFitsMtu`), `controlChunkCapacity` and the output floor `kControlMinOutput` = 52 |
| `include/comms_gatts_control.h` | Parses writes only on real WRITE events |
| `test/host_*.cpp` | Six host tests (packet, events, source statistics, control, sample scaling, and since 2026-10-15 the glove module switches and dummy module in `host_glove.cpp`; the scaling test is built once per out-of-range policy, the glove test once per set of switches), compiled and run with `g++` or `clang++`, whichever is on PATH; skipped when neither is found |

**`laptop/`**

| File | What it does |
|---|---|
| `bridge.py` | The full path for one glove: scan, connect, MTU and bond checks, bounded queue, TLS writes, ACK checks, metrics, tail handling at shutdown; `source_ticking_seconds` (first sensor subscription to the quiesce read) for the gated coverage rule |
| `dual_bridge.py` | Runs two uncoupled `Bridge` instances at once, with one shared observation window, and produces the combined report. This is what `demo.py` calls. `board_coverage` holds the coverage rules for gated and ungated boards; the progress line prints `gated=` |
| `source_audit.py` | Parses the 36-byte source statistics (`SOURCE_STATS_MAGIC = b"LCS3"`, `SOURCE_STATS_SIZE`, `SOURCE_FLAG_GATED`); reconciles "generated = received = ACKed"; reports `gated`, `source_idle`, `source_unread`, `source_refused`, `source_ticks` |
| `controls.py` | The BLE control channel: keyboard commands, rate, file transfer |
| `windows_pairing.py` | Pairs on Windows with "passkey entry + encrypted and authenticated", and checks the bond level |
| `ble_connection.py` | Turns off the Windows GATT cache when creating the Bleak client |
| `ble_parameters.py` | Above 10 Hz, asks Windows for throughput-optimised connection parameters and records the actual values |
| `ble_shutdown.py` | When a capture stops, first turns notifications off on the remote side while keeping the local callback, to collect the tail packets |
| `evidence.py` | Writes `packets.jsonl` and the logs in the background, bounded |
| `goodput.py` | Measures the rate of valid sensor bytes received |
| `reporting.py` | Exclusive placeholder and atomic write of report files; source fingerprints (`workspace_source_sha256`; since `4c6ab4c`, 2026-10-16, it also covers `firmware/esp32/lib` and `firmware/esp32/movement_model_params.h`, so a changed copy of Siqiang's module shows in the report) |
| `phone_simulator.py` | A desktop result subscriber, for rehearsal only. **It pushes the phone off when it connects** |
| `mtu_probe.py`, `ble_counter_receiver.py`, `bounded_telemetry_queue.py` | Early diagnostic tools, and a general-purpose queue the main path does not use |
| `requirements.txt` | `bleak==3.0.1` (the version must stay pinned: the shutdown tail protection depends on Bleak internals) |
| `tests/` | Tests for the three diagnostic tools above |

**`ultra96/`**

| File | What it does |
|---|---|
| `server.py` | The board service `CommsServer`: two loopback TLS listeners, the client limit and the eviction of the longest-silent ingest connection (`MAX_CLIENTS`, `INGEST_EVICTABLE_AFTER`, `idle_evicted`), the ingest idle limit (`INGEST_IDLE_TIMEOUT`, `--ingest-idle-timeout`), ingest de-duplication and ACK, the call into the model (`on_sample`, line 329) and the command echo, `_model_result` (identity and duplicate checks for model results), the single-subscriber result queue, the command-line entry (`--model`, `--model-path`, the `model_ready`/`model_failed` lines) |
| `model.py` | The model interface: `DummyModel`, `load_model`, `ModelPort` (calls `start`/`on_sample`, counts errors and slow calls, the thread-safe `emit`), `normalize_result` |
| `protocol.py` | Exact fields and value ranges of the five messages (version 3; subscription envelopes version 1), `session_id` rules, `result_id` generation, the label rule (`GESTURE_PATTERN`, `valid_gesture`) and the confidence rule (`valid_confidence`); `DUMMY_GESTURES` for the dummy model and command echoes |
| `diagnostics.py` | Optional bounded event log (`--event-log-dir`); accepts the events `model_result` and `model_result_refused` too |

**`ios-visualizer/`**

| File | What it does |
|---|---|
| `CommsNative/Package.swift` | Swift package definition; dependencies pinned to exact versions of SwiftNIO, NIOSSH, NIOSSL and swift-crypto (they need Swift tools 6.1 or newer); since 2026-10-15 it links swift-crypto's `Crypto` into `CommsBridge` on Linux only |
| `CommsNative/Sources/CommsCore/Protocol.swift` | Subscribe frame encoding, result validation (version 3, 10 keys, the label and confidence rules), `GestureResult.confidence` and `nextResultJSON`, stream framing (compiled and tested on Linux; not built for iOS) |
| `CommsNative/Sources/CommsCore/DisplayState.swift` | Latest result, count, de-duplication (4096), 2 s expiry, and the per-result queue behind `CommsNextResult` (32 waiting, 2 s, `takeNext`; compiled and tested on Linux) |
| `CommsNative/Sources/CommsTransport/CommsClient.swift` | Building the two-hop SSH + TLS route, error classification (terminal or retry), back-off and reconnect |
| `CommsNative/Sources/CommsTransport/SSHRoute.swift` | Route parameters, port and timeout constants, failure types |
| `CommsNative/Sources/CommsTransport/Trust.swift` | Exact host-key comparison, password authentication, SSH channel byte conversion |
| `CommsNative/Sources/CommsTransport/Subscriber.swift` | Sends `SUBSCRIBE` after the TLS handshake, receives frames, frame deadline |
| `CommsNative/Sources/CommsTransport/Credentials.swift` | In-memory password holder that can be cleared |
| `CommsNative/Sources/CommsBridge/Configuration.swift` | Pinned host names, both SSH host public keys, CA fingerprint; CA import check; saving the public settings. Imports CryptoKit and Security only where they exist (swift-crypto on Linux, where the Security certificate parse is skipped; 2026-10-15) |
| `CommsNative/Sources/CommsBridge/IntegrationController.swift` | Foreground session management, the connect button, disconnect on leaving the foreground. The session ID `ltc-comms` the client uses is set here (line 74) |
| `CommsNative/Sources/CommsBridge/SetupViewController.swift` | The setup form. Its text `session ltc-comms` (line 51) also names the session |
| `CommsNative/Sources/CommsBridge/DisplayMailbox.swift` | The C functions exported to Unity, `CommsStart`, `CommsCopyDisplay`, `CommsStop`, `CommsNextResult` (compiled and tested on Linux; not built for iOS), and the `Week7*` wrappers. The four lines of text are built here |
| `CommsNative/Tests/` | Swift tests: 72 ran on Linux in a Swift 6.1 container on 2026-10-15 (`PythonBoardTests` did not run there); a Mac runs all of them |
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
| `unity/CommsPhoneCore.cs` | C# protocol, TLS trust and receive loop, with no Unity dependency (compiled at C# 7.0 on 2026-10-15). Its result queue is emptied at every new connection (4.6) |
| `unity/CommsPhoneReceiver.cs` | Android reference Unity component; the phone must open its own SSH local forward |
| `ish_control.py` | Temporary maintenance-channel script for the iSH route (that route is abandoned) |
| `tests/` | Tests for the Python above, and a C# self-test (`CoreSelfTest.cs`, run by `run_core_tests.ps1`; needs PowerShell 7; passed 113 checks under PowerShell 7.6.7 on 2026-10-15) |

**`tools/`**

| File | What it does |
|---|---|
| `ssh_tunnel.py` | Builds the two-hop, loopback-only OpenSSH local-forward command (explicit `ProxyCommand`, strict host keys) |
| `demo_service.py` | Inspects or starts the board service over SSH. `BOARD_ROOT`, the fallback `BOARD_SOURCE` and `board_source()` (the folder the newest local deployment record names) are here |
| `deploy_service.py` | Deploys the board service (2026-10-14): uploads `common/` and `ultra96/` into a new folder, optionally installs a renewed certificate, swaps the running service with checks, SIGKILL escalation and rollback; password prompts, strict `known_hosts`; the board's record in `BOARD_ROOT/evidence/active-deployment.json` and a local copy in `.comms-local/deployments/` |
| `check_board.py` | Checks one flashed board over real BLE against a service on the laptop (2026-10-14): source reconciliation, rate, commands, dummy-model results; the summary line also prints `gated`, `idle`, `unread`, `refused` (2026-10-15) |
| `export_capture.py` | Writes a capture's samples (`packets.jsonl`) as CSV in physical units, one row per sample (2026-10-15) |
| `sync_glove_module.py` | Copies Siqiang's module from `hardware/gloves/integration_files/` into `firmware/esp32/lib/glove_sensor/src/` and `firmware/esp32/movement_model_params.h`; `--check` only compares (2026-10-15) |
| `demo_boards.py` | Reads and writes the left/right Bluetooth address map (`.comms-local/boards.json`). The built-in default addresses are here |
| `generate_comms_pki.py` | Generates the CA and the server certificate. `--renew-server-from` renews only the server certificate with the existing CA |
| `generate_dummy_fixtures.py` | Generates the firmware header `comms_fixtures.h` from the JSON |
| `comms_demo.py` | Packet examples, a single-board send demo, offline log audit |
| `rehearse_comms.py` | Full rehearsal over local loopback (no SSH, no hardware) |
| `rehearse_remote_comms.py` | Remote rehearsal through an existing tunnel (its synthetic source sends dummy-table rows). **It pushes the phone's subscription off** |
| `video_evidence.py` | Extracts, from one capture, one example sample and its ACK per board; reads only version-3 captures |

**`tests/`**: 50 test files, 3 files under `fixtures/` that hold 2 golden vectors (`comms-golden.json` has two packet vectors; `comms-dummy.bin` and `comms-boundaries.bin` are their raw 38 bytes), and `linux/deploy_remote_test.sh` (the deploy tool's board-side checks, run in Linux or WSL only through `test_deploy_service.py` with `B07_LINUX_DEPLOY_TEST=1`). New on 2026-10-14: `test_model_interface.py` (the model interface and its server integration), `test_protocol_rules.py` (label and confidence rules, `physical_values`), `test_v3_events.py` (it replaced `test_v2_events.py`), `test_firmware_sample.py` (the scaling host test, both policies), `test_deploy_service.py`, `test_check_board.py`. New on 2026-10-15: `test_firmware_glove.py` (builds `host_glove.cpp` with several sets of glove switches, and checks that invalid switches do not compile), `test_export_capture.py`, `test_glove_module_sync.py` (the copies equal Siqiang's files; only the `-glove` environments link the module); `test_flash.py` gained the `--glove` case, `test_dual_bridge.py` the gated coverage cases, and `test_transport.py` the idle limit and eviction cases. On 2026-10-16 (`4c6ab4c`) `test_laptop_controls.py` gained a case that the report fingerprint covers the copies of the glove module. Files are named after what they test: `test_sensor.py` (packet format), `test_source_audit.py`, `test_laptop_controls.py`, `test_bridge_*.py`, `test_dual_*.py`, `test_transport*.py` (TLS, framing, certificate tool), `test_server_*.py`, `test_ssh_trust.py`, `test_demo_*.py`, `test_firmware_*.py` (compile and run the firmware host tests), `test_rehearsal.py`, and others.

### 12.3 Teammates' code (read-only; know it only well enough to connect to it)

**`hardware/gloves/` (Siqiang)**

| Path | What it is |
|---|---|
| `README.md` | Description of the two gloves: each has one ESP32, one MPU-6500 and two flex sensors; 11 values per sample |
| `integration_files/` | The sensor module for the Communications firmware (2026-10-15, `51593be`): `glove_sensor.h`, `glove_sensor.cpp`, `movement_model_params.h`. Copied unchanged into `firmware/esp32/` by `tools/sync_glove_module.py` (7.1) |
| `29_sept/imu_v7.ino` | An earlier reference sketch (CSV output over Bluetooth Classic serial) |
| `29_sept/imu_recording_terminal_v14.py`, `how_to_use.txt` | PC-side recording script and how to use it |
| `imu_v3.ino`, `imu_recording_terminal_v10.py`, `_v11.py` | Earlier versions |
| `model_threshold_variant_1/` | The IDLE/MOVING detector on the ESP32 (training script, parameter header, recording and test scripts). Its `debug_esp32_ml_movement_detector_v1.ino` with `movement_model_params.h` is the authoritative sketch (Siqiang's answer A, 2026-10-15) |
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
| `D:\LetThemCook` | Working copy. Local branches: `main` (tracks the fork), `comms/protocol-v3` (the version-3 work of 2026-10-14 evening to 2026-10-16, at `4d97242`, the same as `main`; both pushed to the fork on 2026-10-16; checked out) and `comms/protocol-v3-team` (the code-only team pull request branch; rebased on 2026-10-15 onto `upstream/main` `51593be`, commits `abaff6f`, `d2aa85a`, `09dc603`, `8dbcaf2` (the code of 2026-10-15 up to `d582ce6`) and `44d0f71` (the code of `4c6ab4c` and the iOS notes of `4d97242`); pushed to the fork on 2026-10-16; pull request #19; checked out in the worktree below, 6.2) |
| `upstream` | Team repository <https://github.com/B07-CG4002/Let-Them-Cook>, public, main branch unprotected, currently at `51593be` (Siqiang's module, 2026-10-15, on top of `5a004c6`: PR #18 merged on 2026-10-14 on top of `880abba`, which was `ec398b6` before the history rewrite; same files). PR #15 was merged without `gh`, with `git commit-tree` and a push |
| `origin` | olsonwangyj's fork <https://github.com/olsonwangyj/Let-Them-Cook>, public |
| Only on the fork, not in the team repository | All of `docs/`, `AGENTS.md`, `CLAUDE.md`, `.gitattributes`; the iOS build-artifact lines at the end of `.gitignore`; under `ios-visualizer/`: `tools/`, `verify-import.py`, `import-manifest.json`, `reference/TlsDataReceiver.cs` and `xcode-export/` (`reference/teammate-localhost-cert.pem` is also in the team repository); and `tests/test_ios_export_patch.py`. So teammates who clone the team repository cannot see the design records. Since `57a3fbd`, the fork's `.gitattributes` also has `tests/linux/*.sh text eol=lf`; a team checkout lacks that rule and can have the script with CRLF endings, which is why `3b94990` makes the deploy test hand bash an LF copy (6.2) |
| `.comms-local/` | Git-ignored. The local board map `boards.json` (left `38:18:2B:19:82:AE`, right `38:18:2B:18:9D:6A`); `checks/` with the evidence of 2026-10-14 (`2026-10-14-right-board-v2/`, `2026-10-14-right-board-v3/`, `2026-10-14-deploy-wsl/`, each with a README); `deployments/` will hold the records `tools.deploy_service` writes. There is no capture directory yet |
| `.week7-local/` | 17 historical capture directories (all `W7` packets), the September measurement results, an archive of the firmware flashed on 29 September, and the local scripts used in September: `co_deploy.py` (board deployment script with strict SSH trust and rollback; the 28 September deployment used it, and it started that service in the background with `start_new_session=True`, PID in `BOARD_ROOT/evidence/server.pid`), `co_acceptance.py`, `co_faults.py`, `co_final_check.py`, `co_iphone_capture.py` and others. Git-ignored and not versioned. **Keep it; do not delete it** |
| `release-tools/`, `output/` | The frozen packaging tools and 4 ZIP files used for the 30 September submission (listed in `.git/info/exclude`; local only) |
| `D:\LetThemCook-attic\2026-10-13\` | 2.3 GB of files moved out while tidying the workspace (not deleted; contains a README.txt) |
| `D:\LetThemCook-worktrees\` | One active worktree, `protocol-v3-team`, with the branch `comms/protocol-v3-team` (at `44d0f71`; clean; pushed to the fork, pull request #19). The `comms-cleanup` worktree was removed after PR #18 was merged; the folder `local-main-merge-backup-20261008T025556Z` is an old backup left from 2026-10-08 and is not a Git worktree |
| `~/.codex/private/cg4002-week7-20260906/` | The current CA (with its private key) and the September server certificate (expired). Not in Git |
| `~/.codex/private/cg4002-comms-server-20261014/` | The renewed server certificate and key (valid to 2026-11-13 14:27:35 UTC) and a copy of the CA certificate, made on 2026-10-14 with `--renew-server-from`; to be installed on the board by `tools.deploy_service --server-cert-dir`. Not in Git |
| `%USERPROFILE%\.dotnet\` | The .NET SDK 10.0.402 (installed per user with Microsoft's `dotnet-install.ps1`) and, in `tools\`, PowerShell 7.6.7 as a .NET global tool (`pwsh.exe`), both installed on 2026-10-15 with the owner's approval. Neither is on PATH |
| Docker image `swift:6.1` | Swift 6.1.3 for Linux, pulled on 2026-10-15 with the owner's approval; used to compile and test `CommsNative` (4.6, 11) |

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
| `co-protocol-v3.md` | olsonwangyj's current protocol specification (version 3: packet, messages, model results, control, files). It replaced `co-protocol-v2.md` on 2026-10-14 |
| `B07-CO-protocol-explained.zh-CN.md` | Chinese study companion, written for protocol version 2, explaining it byte by byte. Not a formal document; its banner lists the version-3 differences, and `co-protocol-v3.md` governs |
| `communications-quickstart.md` | Quick start |
| `week7-runbook.md` | The Week 7 operations manual (some command names are out of date; see 4.9) |
| `archive/` | History: assessment material, reports, measured evidence, design records, old manuals |
| `archive/design/integration-handoff-2026-10-08.md` | The English integration notes for teammates (PR #15), formerly `docs/integration-handoff.md`. Moved to the archive on 2026-10-14. Section 7 of this document holds the current interface requests |

### 12.6 What to change, and in which file

| What to change | File |
|---|---|
| How many values a packet holds, packet length | `firmware/esp32/include/comms_packet.h` (`kChannelCount`), `common/sensor.py` (`CHANNELS`, `SCALES`); `firmware/esp32/include/comms_sample.h` (`kChannelScale`, one scale per channel; a channel without an entry would get scale 0) and `firmware/esp32/test/host_sample.cpp` (asserts 11 channels); the `values` contract of `on_sample` (11 floats; `ultra96/model.py`, 7.2); the MTU floors, the command frame size and the golden vectors follow, and their tests must be updated; `comms_source_stats.h` and `laptop/source_audit.py` for the statistics marker; `tools/generate_dummy_fixtures.py` and `common/dummy_fixtures.json` |
| Scales or the out-of-range policy | `firmware/esp32/include/comms_sample.h` and `common/sensor.py` `SCALES` (both together); the policy is the build flag `COMMS_OUT_OF_RANGE_DROP` |
| Where the firmware gets samples | The glove module behind `firmware/esp32/include/comms_glove.h`: `src/dummy_glove.cpp` (the built-in dummy) or Siqiang's module (`-glove` environments); the tick itself is `produceSample()` in `src/main.cpp` |
| When a glove sends (gating) | Siqiang's detector decides (his module). On the Communications side: `src/glove_module.cpp` (`gloveShouldSend`), the switches in `comms_glove.h` (`COMMS_GLOVE_SEND_ALL`; for the dummy, `COMMS_DUMMY_MOVING_MS` and `COMMS_DUMMY_IDLE_MS`) |
| Siqiang's module changed in the team repo | Merge the team main, then `python -m tools.sync_glove_module`; never edit the copies in `firmware/esp32/lib/glove_sensor/` or `firmware/esp32/movement_model_params.h` |
| Source statistics fields | `firmware/esp32/include/comms_source_stats.h` and `laptop/source_audit.py` together (the length is also the firmware check, 4.2); the fake peripherals in the tests serve the same 36 bytes |
| Coverage rule of a gated board | `board_coverage` in `laptop/dual_bridge.py` |
| Ingest idle limit, client slots | `ultra96/server.py` (`INGEST_IDLE_TIMEOUT`, `INGEST_EVICTABLE_AFTER`, `MAX_CLIENTS`), or at start-up `--ingest-idle-timeout` |
| Default send rate | `platformio.ini` (`-DCOMMS_INITIAL_RATE_HZ`; 50 in the `-glove` environments) or, at run time, `demo.py run --rate` |
| How the board produces results | The model: `--model MODULE` on the service; the interface in `ultra96/model.py`; the dummy model is `DummyModel` there |
| Which labels and confidence values are allowed | `ultra96/protocol.py` (also used by `ultra96/model.py`), `CommsCore/Protocol.swift`, `phone/receiver.py`, `phone/unity/CommsPhoneCore.cs` (all four change together, then the phone app is rebuilt) |
| `CommsNextResult` limits (32 waiting, 2 s) | `DisplayState.swift` (`pendingCapacity`, `pendingLifetime`) |
| Text or functions for Unity | `ios-visualizer/CommsNative/Sources/CommsBridge/DisplayMailbox.swift` |
| Session ID | Laptop: `--session-id` or `LTC_COMMS_SESSION`. Board: the service's `--session-id`. Phone: two places that change together, `IntegrationController.swift:74` (the value used) and the form text in `SetupViewController.swift:51`; then rebuild |
| Jump-host and board host names, SSH host public keys, CA fingerprint | Laptop: `tools/ssh_tunnel.py` and the `demo.py` arguments. Phone: `Configuration.swift` (rebuild) |
| Board deployment directory | `BOARD_ROOT` and the fallback `BOARD_SOURCE` in `tools/demo_service.py` (also used by `tools/deploy_service.py`); after a deploy, `.comms-local/deployments/` |
| Bluetooth addresses of the two boards | Run `python flash.py`; the result is in `.comms-local/boards.json` |
| Queue length, freshness, timeouts, ACK window | Laptop: `BridgeConfig` in `laptop/bridge.py`, and `demo.py`. Board: `ultra96/server.py`. Phone: `SSHRoute.swift`, `DisplayState.swift` |
| Certificates | `tools/generate_comms_pki.py` |

---

## 13. Not yet confirmed

- The actual state of the server certificate, the service process and the code snapshot on the board (olsonwangyj must log in and check; `tools.deploy_service --dry-run` then the real run show and replace them).
- Whether the left board needs pairing again after its version-3 reflash. (The right board did not, through two reflashes on 2026-10-14.)
- Whether the right board's flash was left half-written when it was unplugged on 2026-10-15 (it is reflashed either way, 6.3).
- Whether the gating works on hardware: the gated dummy (6.3 step 2) has not run on a board.
- Whether a `-glove` build on a board without sensors prints `glove_begin ok=0` without blocking and still advertises; and whether Siqiang's module works in the Communications firmware on his gloves (calibration, the MOVING timing, 50 Hz with BLE running).
- Whether 38 bytes × 50 Hz × 2 boards is clean on hardware (one board is, with the 2026-10-14 build), and whether two gated gloves pass the gated coverage rule.
- Whether `tools/deploy_service.py` works over the real SSH route (its board-side half passed on Linux; its paramiko half has never connected).
- Whether the Swift package builds for iOS and passes there (it compiles and its 72 tests pass on Linux; the `#if os(iOS)` code and `PythonBoardTests` were not compiled), and whether `CommsPhoneReceiver.cs` compiles in Unity (checked by reading only; `CommsPhoneCore.cs` compiles at C# 7.0 and its self-test passes).
- Whether `demo.py`'s `Phone expected increase` and the rehearsal criteria still apply: only while the dummy model runs.
- Whether `configure_xcode.py` works on a new Unity export.
- Direct mode (the phone not going through the jump host) was never verified on site. V1 does not use it.
- Why the phone missed 109 results on 2026-09-21.
- Wen Ree's and Jie Ling's replies about the interfaces in section 7 (Siqiang answered and delivered on 2026-10-15).

The owner's rules (2026-10-14):

- Only the newest version is supported. No interoperability between versions; upgrading means reflashing, redeploying and reinstalling everything together (8, step 1).
- Teammates deliver code by pushing it to the team repo on GitHub, not over Telegram.

The owner's direction (2026-10-14), proposed to the teammates and final when they confirm (3.1, 7, 8):

- The model gets the 11 values as physical floats. Transport stays int16.
- The game gets results one at a time through a structured per-result function, `CommsNextResult` (one compact JSON object per call; bytes written, 0, or the negative of the bytes needed including the terminating 0; 512-byte buffer; called in a loop each frame). Written on 2026-10-14; compiled and tested on Linux on 2026-10-15, not yet built for iOS.
- Jie Ling does everything in Unity and the iOS build (the C# calls, the game logic, the export, adding `CommsNative`, building and installing on their own iPhone with their own Mac); olsonwangyj pushes `CommsNative` to the team repo and writes the steps for adding it.
- The real-data packet is protocol version 3; 38 bytes with the 11 values only; the scales are checked against Siqiang's real output before they are fixed. Implemented on 2026-10-14 with this layout.
- The model interface on the board as in 7.2 (`start(emit)`, `on_sample`, thread-safe `emit`), loaded with `--model`. Implemented on 2026-10-14; the names change if Wen Ree picks others, and a separate-process model would need a bridge between the two processes on the board.

Settled with Siqiang on 2026-10-15 (his answers and his delivered module, 2.3, 7.1): a glove sends samples only while his detector says MOVING, and the Communications firmware calls his decision for each sample (the owner's request). So the IDLE/MOVING state does not travel in the packet, and the 11-value layout stays.

Decided by the agent within Communications on 2026-10-14 (6.5), open to the owner's review: the subscription envelopes stay at version 1; `request_id` stays; the statistics marker becomes `LCS3`; the label rule (1 to 32 of `A–Z a–z 0–9 _ -`) and the confidence rule (finite, 0 to 1); commands bypass the model; the dummy model gives one result per sample; confidence is passed on unrounded; the `CommsNextResult` counters reset on a new Connect.

Decided by the agent within Communications on 2026-10-15 (6.5, D20 to D31), open to the owner's review: the gate is called once per sample; a tick that sends nothing takes no `seq`; idle, unread and refused ticks are counted in the source statistics, which grow to 36 bytes under the same marker `LCS3`, while `clamped` and `race_dropped` stay on the serial line only; the send-all switch for recording; the gated coverage rule; the 600 s ingest idle limit with eviction; Siqiang's module built from checked copies, with the weights header in both locations; the `-glove` environments at 50 Hz; `flash.py --glove`; the capture exporter; the Swift Linux build fix.

Still open:

- Out-of-range values: clamp or drop that one sample, to be agreed with Wen Ree (the firmware does clamp by default and can be built to drop); and whether the model needs a per-sample flag (8, step 1).
- The scales: checked against Siqiang's real samples before the layout is frozen (7.1).
- Whether the MOVING onset lag (at best about 0.2 to 0.4 s, longer for gentle movements; the exact lags need real data), the still tail after each movement and one-glove windows suit the model (Wen Ree; any change is on the detector side, with Siqiang; 7.2).
- Whether Siqiang changes the two points found in his module: the include path and the classifier reset after a failed reading (7.1). The owner decides whether to raise them.
- The label set and the result rate (Wen Ree and Jie Ling), and with them the new acceptance criteria (8, step 6).
- The `CommsNextResult` queue limits: provisional 32 waiting and 2 s after reaching the phone, revisited once Wen Ree says how often results come.

---

## 14. Change log

| Date | What changed |
|---|---|
| 2026-10-14 | First version. It covered: the project and the state of each subsystem; role and boundaries; the full Communications chain, the formats, how each segment works and the design reasons; the state after the Week 7 compatibility removal; the left board flashed with the current firmware; the finding that the September server certificate expired on 10-06 (read from the laptop's copy), and the new renewal option; the API needs of the three interfaces; the owner's corrections |
| 2026-10-14 | The six detail chapters were finalised against the current code after two fact-checks and a completeness review |
| 2026-10-14 | The teammate messages were rewritten with explicit functions and fields, reviewed for accuracy, role boundary and clarity, and handed to the owner. Section 7 was updated to match |
| 2026-10-14 | The owner set two rules: the documents are updated with every code or deployment change, and formal documents are written in English (`AGENTS.md` rules 7 and 8; section 0, point 3). The hand-off document and the detail chapters were rewritten in English, and the Chinese versions were removed from the repository (an unmaintained snapshot is in `D:\LetThemCook-attic\2026-10-14\handoff-zh-CN\`). `docs/integration-handoff.md` (8 October) moved to `docs/archive/design/integration-handoff-2026-10-08.md`, because section 7 supersedes it |
| 2026-10-14 | After a review forwarded by the owner: the 2 s rule is described as a limit on waiting on the board, not an end-to-end guarantee (7.2); `Subscribed` means only that the subscription handshake succeeded; reconnects can leave `seq` gaps; the 70 Hz result is a setting (about 66 packets/s) measured with the 32-byte dummy packet; every interface in section 7 is marked as planned, not built; section 1 separates finished documents from unfinished integration; the latest-only display text is described as unable to carry every result |
| 2026-10-14 | The owner's direction (later reworded from "decided" to "proposed", see the next row): physical floats to the model; a structured per-result function `CommsNextResult` for the game; Jie Ling writes the Unity calls while olsonwangyj links `CommsNative` into the Xcode export; the 38-byte packet is version 3 with scales checked against real data. Added the division-of-work table (3.1). Out-of-range handling and the queue limits were left open (superseded by a later row: to be agreed with Wen Ree; provisional limits). The teammate messages were revised to match |
| 2026-10-14 | The question to Siqiang about whether the gloves use FireBeetle boards was dropped: they do, and the owner knows it (2.3) |
| 2026-10-14 | The owner's direction: Jie Ling builds and installs the iOS app on their own Mac and iPhone, after adding `CommsNative` from the team repo with the owner's short steps; no export is pushed or passed around. The message to Jie Ling now asks only whether the timing works (3, 3.1, 6.4, 7.3, 8, 9.2, 13) |
| 2026-10-14 | Corrected by the owner: any teammate can log the phone in with their own NUS VPN, jump-host and board accounts, so the phone need not be the owner's. The question to Jie Ling is now which iPhone is used on Tuesday (6.4, 9.2, 10). An earlier change that same evening had wrongly said only the owner could log the phone in |
| 2026-10-14 | At the owner's request, PR #18 was opened on the team repo and merged (`5a004c6`); the merged branch and its worktree were removed (the left-board firmware build in it was copied to `D:\LetThemCook-attic\2026-10-14\flashed-firmware-left-2026-10-14\`), and the team main was merged into local `main` (6.2, 12.4) |
| 2026-10-14 | With the owner's go-ahead, the pull request branch was pushed to the fork (`0b9ed2e`, replacing `30e85a6`) and local `main` was pushed (6.2) |
| 2026-10-14 | The owner chose that Jie Ling does the Unity iOS export (Jie Ling knows the Unity version and settings, and the owner needs no Unity install): Jie Ling pushes the Unity changes to `vis/` and the export to a separate branch with Git LFS; olsonwangyj links `CommsNative` into the export and installs (3, 3.1, 6.4, 7.3, 8, 13). Local branches tidied: the merged `codex/integration-handoff` branch and four old worktrees whose commits are all in `main` were removed; an untracked `docs/` copy found in one of them was moved to `D:\LetThemCook-attic\2026-10-14\integration-handoff-worktree-docs\`. Only `main` and the team pull request branch `comms/remove-week7-legacy` remain |
| 2026-10-14 | Round-3 check applied: no remaining "decided" or "exactly once" wording; the laptop's full queue and the board's 32-place queue named as loss causes (7.2); range fit stated as expected, not guaranteed (7.1); the teammate table and the owner's Thursday row match the iOS split (Unity check on the Mac); the old-evidence commit is now `880abba`; the messages were made more polite and say "asked" only once sent |
| 2026-10-14 | Git state (6.2): the team main and the fork's `main` were rewritten outside the agent sessions to drop attribution lines; local `main` aligned; the pull request branch rebased locally onto `880abba` and not pushed, because the owner asked that GitHub not be touched for now |
| 2026-10-14 | After a second review forwarded by the owner, and two new rules from the owner: only the newest version is supported (no interoperability; upgrade everything together; version 3 replaces versions 1 and 2, including the dummy data); teammates push code to GitHub instead of sending it over Telegram. The owner's direction and the dates are now marked as proposals until the teammates confirm. `CommsNextResult` promises only that each result not dropped is taken out at most once, and states its buffer-too-small and queue-clearing rules; its limits are provisional. Out-of-range handling is to be agreed with Wen Ree, with the reasons for caution. The 38-byte layout is frozen only after the IDLE/MOVING answer. Wen Ree's Friday deliverable covers both the in-process and the separate-process option. The owner builds the iOS export from Jie Ling's pushed Unity project |
| 2026-10-14 | A check of the documents and the messages together: the schedule now secures the gloves for the Monday dry run, splits the label checks (three on Friday, the Swift one on Saturday), adds a Saturday rebuild of the Week 7 export so the phone can subscribe after the redeploy, and redefines `Phone expected increase` before the dry run; the delivery form of each teammate deliverable is stated; a failed result write ends the phone subscription (7.2); version 3 must be handled on the result path (8); the IDLE/MOVING question goes to both Siqiang and Wen Ree; phone retry timing corrected (9.2); `CommsNextResult` returns one JSON object per call (the owner's direction, final when Jie Ling confirms) with provisional queue limits (13) |
| 2026-10-14 | Schedule set up to the in-person integration session on Tue 10-20 (6.4): teammate deliverables by date, and the owner's own plan with priorities. The messages were reordered to list what is needed by which date first |
| 2026-10-14 | Cross-check corrections applied: how the board service was started and what keeps it alive (4.5, 6.3, 9.2, 12.4); the path of the iOS patch scripts (6.3 step 4); the server certificate expiry checked only on the laptop's copy (1, 2.4, 4.8, 6.3); only `ios-visualizer/reference/TlsDataReceiver.cs` is fork-only (12.4); where the sensor and control MTU floors live (12.2); four PlatformIO environments, including the default `firebeetle32` with ID 1 (4.3, 6.3, 12.2); host tests use `g++` or `clang++` and are skipped without either (4.3, 12.2); `demo.py live` runs 120 s and needs an interactive terminal (4.4); what the BLE callback does (4.4); `received` versus `callback_received` (4.7); which failures increment `ack_errors` and `transport_errors` (9.2); the locations of the `DUMMY` texts and the `Protocol.swift` line range (8 step 5); `laptop/goodput.py` follows `PACKET_SIZE` (8 step 1); the phone holds the session in two places (12.2, 12.6); 3 fixture files but 2 golden vectors (12.2); `src/live_inference.py` hard-codes `COM3`/`COM4` at 115200 baud, with no evidence they are Bluetooth ports (2.3) |
| 2026-10-14 (evening) | Protocol version 3 on the local branch `comms/protocol-v3` (code commits `a34c467`, `57a3fbd`, `a4b907b`, `3b94990`): a 38-byte packet with 11 values, `LCS3` statistics, versions 1 and 2 and the formula dummy removed; the board model interface (`ultra96/model.py`, `--model`, `--model-path`) with a built-in dummy model; model labels and real confidence on every receiver; `CommsNextResult` in the Swift package (written, not compiled); `tools/deploy_service.py` and `tools/check_board.py`; `demo.py service --start` follows the newest deployment record. The right board was flashed with version 2 and then version 3 and checked against a service on the laptop; the server certificate was renewed locally (not on the board). An adversarial review found nine defects, fixed in `a4b907b`. The specification became `co-protocol-v3.md`. Decisions D1 to D19 with their status (6.5). The owner's clarification: the MediaPipe hand tracking and the visualiser demo Wen Ree shared are Jie Ling's part (2.3). Sections changed: 0, 1, 2.3, 2.4, 3, 3.1, 4.1 to 4.9, 5, 6.1 to 6.5, 7, 8, 9.2, 11, 12.1, 12.2, 12.4, 12.5, 12.6, 13 |
| 2026-10-14 (evening) | Fact-check corrections: a model result is refused for an unknown power-up or a `seq` above the highest accepted one, and a `seq` inside a gap is not detected (4.5); a deploy refused in its checks before the stop leaves no record (6.3 step 1); `tools.deploy_service` needs `paramiko`, which no requirements file lists (6.3, 11, 12.1; superseded by the next row: `requirements-dev.txt` now lists it); the installed Week 7 app can neither subscribe to the version-3 service nor accept any version-3 result (8 step 5); display lines 1 and 3 in the current source (7.3); test totals at `3b94990` with and without `B07_LINUX_DEPLOY_TEST=1` (1, 6.2, 11); the code-only branch `comms/protocol-v3-team` and its worktree (6.2, 12.4); the right board was flashed once with version 3, and the 10 s re-run has no saved evidence (6.1); D16's status split (6.5); the `CommsPhoneCore.cs` caveat in the progress list (6.4); the log files of a service started by `tools.deploy_service` (9.2); the cleanup's `LCS1` sentence written as history (6.2); what Wen Ree shared, without the guess that it runs on the phone (2.3); the `on_sample` call is at `ultra96/server.py:277` (7.2, 12.2); where a detail chapter disagrees with this document, this document governs (0) |
| 2026-10-15 | Second fact-check corrections: the installed Week 7 build is the package under its earlier name `Week7Native`, built on 2026-09-28; it exports the three functions only as `Week7Start`/`Week7CopyDisplay`/`Week7Stop` and shows `Week 7 • DUMMY inference` (4.6, 7, 7.3); `CommsNextResult` is in the source, not planned (7.3); `paramiko>=2.8,<4` was added to `requirements-dev.txt` with the documents, after `3b94990`, and still has to be added to the team branch `348fc10` (6.2, 6.3, 12.1); the left board's firmware of 10-14 was version 2 (6.1); what was compiled of the C# reference, and the C# self-test that was not compiled (1, 12.2, 13); the model interface is in the board-service code, not on the Ultra96 (6.4); which refused results log a warning, at most one per kind per second (7.2); the laptop reads the source statistics twice at shutdown (4.2); `comms_sample.h`, `host_sample.cpp` and the `on_sample` contract follow the channel count (12.6); the fork-only `.gitignore` lines and the `.gitattributes` rule for `tests/linux/*.sh` (12.4) |
| 2026-10-15 | Final clean-up after the documentation pass: `tools/deploy_service.py` reports paramiko errors with a `FAILED:` line and `requirements-dev.txt` lists `paramiko>=2.8,<4` (`15de82e`); the opt-in Linux deploy test uses `5a004c6` as its old service; the team branch `comms/protocol-v3-team` gained `ed2aa1f` (the same code fixes and the shared `README.md` Communications lines) and `ab3c7f6` (the iOS notes), and is clean at `ab3c7f6`, not pushed (6.2, 12.4); `CommsNextResult` returns minus (bytes + 1) when the buffer is null or too small (7.3); `NATIVE-INTEGRATION.md` no longer tells new integrations to keep patched bridge calls. Totals: 780 passed, 3 skipped with the Linux test; 779 passed, 4 skipped without |
| 2026-10-15 | Siqiang's answers (A to F) and his sensor module (team commit `51593be`, `hardware/gloves/integration_files/`); by his answer a glove sends only while his detector says MOVING, so the IDLE/MOVING state does not travel and the packet is unchanged. Built on `comms/protocol-v3` (`6583f9d`, `5d2e52f`, merge `17012b8`, `e24f8ea`, `d582ce6`): the glove module API with the built-in dummy and the dummy gate; gating (the decision called once per sample, no `seq` for a skipped tick, glove calls outside the connection mutex, a send tick that keeps its rate, new serial fields); 36-byte `LCS3` source statistics with the gated flag and idle/unread/refused counters; the laptop's report columns and the gated coverage rule; the 600 s ingest idle limit (`--ingest-idle-timeout`) and the eviction of the longest-silent ingest connection; `tools/export_capture.py`; Siqiang's module built from checked copies (`tools/sync_glove_module.py`) in the new `-glove` environments at 50 Hz; `flash.py --glove`; the Swift package compiles on Linux. Verified on the laptop: Swift compiled and tested on Linux in a Swift 6.1 container (72 tests), not built for iOS; the C# reference core `CommsPhoneCore.cs` compiled (C# 7.0) and its self-test passed (113 checks, PowerShell 7; `CommsPhoneReceiver.cs` checked by reading only); the firmware builds; 841 passed, 4 skipped. Not run on hardware: the right board was unplugged before the gated build could be flashed. Two issues found in Siqiang's module, reported to the owner (7.1). The owner approved the pushes, the merge, the team pull request and the two toolchain downloads; the .NET SDK, PowerShell 7 and the Swift image are installed; nothing is pushed yet; the team branch was rebased onto `51593be` and gained `8dbcaf2` (the code of 2026-10-15 up to `d582ce6`, 823 passed, 4 skipped there). Decisions D20 to D31 (6.5). Citations moved: the `on_sample` call is now at `ultra96/server.py:329` and the model-result refusal at `:352-357`; the step for the old board process is 6.3 step 1. Sections changed: 1, 2.3, 2.4, 3, 3.1, 4.2 to 4.7, 4.9, 5, 6.1 to 6.5, 7, 7.1, 7.2, 7.3, 8, 9.2, 11, 12.1 to 12.4, 12.6, 13 |
| 2026-10-16 | `4c6ab4c` on `comms/protocol-v3`: capture reports fingerprint the copies of Siqiang's module (`laptop/reporting.py`: `workspace_source_sha256` also covers `firmware/esp32/lib` and `firmware/esp32/movement_model_params.h`); the copy README names both locations of the weights header, so the 4.9 entry about it is removed; one new test. Tests at `4c6ab4c`: 842 passed, 4 skipped. Fact-check corrections: the team branch holds `8dbcaf2` (the code of 2026-10-15 up to `d582ce6`; 823 passed, 4 skipped there), clean and not pushed, and not yet `4c6ab4c` (6.2, 12.4, 14); only the C# core `CommsPhoneCore.cs` was compiled, and `CommsPhoneReceiver.cs` was checked by reading only (1, 2.4, 4.6, 6.4, 14); `swift test` on a Mac builds for macOS, so the `#if os(iOS)` code compiles only in an iOS build (6.3 step 3, 6.4, 7.3, 8 step 7); the `-glove` firmware with Siqiang's module only compiles and links, while the gating, the sample policy and the scaling are host-tested with the dummy module (7); the MOVING and IDLE lags follow from his code only as bounds (at best about 0.2 to 0.4 s to MOVING; a still tail of at least about 0.4 s, possibly 1 s or more), and the exact lags need real data (7.1, 7.2, 13); after the board closes a silent ingest connection, usually only the first frame sent counts as ambiguous, the queued samples wait through the back-off, and that capture is not clean (7.2, 9.2); `flash.py --glove` regenerates the dummy-data header before the copy check (4.3). Sections changed: 1, 2.4, 4.3, 4.6, 4.9, 6.1 to 6.4, 7, 7.1, 7.2, 7.3, 8, 9.2, 11, 12.2, 12.4, 13, 14 |
| 2026-10-16 | With the owner's approval of 2026-10-15: the team branch gained `44d0f71` (the code of `4c6ab4c` and the final iOS notes; 824 passed, 4 skipped there); `comms/protocol-v3` and `main` (fast-forwarded) were pushed to the fork at `4d97242`, `comms/protocol-v3-team` at `44d0f71`, and the team pull request #19 was opened (not merged). A fourth issue in Siqiang's module was recorded in 7.1 (a failed read during calibration makes `gloveBegin()` fail); the Swift container command was corrected to mount `ios-visualizer/reference` too (11; `NATIVE-INTEGRATION.md`) |
