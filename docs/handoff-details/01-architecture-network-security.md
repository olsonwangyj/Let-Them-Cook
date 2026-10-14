# Detail chapter 1: Architecture, network and security model

> This is a detail chapter of [`../communications-handoff.md`](../communications-handoff.md). It was checked line by line against local `main` on 2026-10-14 (then commit `25fe4e4`; after the history rewrite of the same day the identical content is `dc582c7`). Later on 2026-10-14 it was brought in line with the owner's direction, rules and schedule of that day (hand-off sections 3.1, 4.2, 6.2, 6.4, 7, 8 and 13). The interface shapes and the teammate dates are proposals until the teammates confirm them; the owner's only rules are that only the newest protocol version is supported and that teammates deliver code by pushing to the team repo on GitHub. No Communications code changed between `dc582c7` and these updates. The code is the source of truth: where this chapter and the code disagree, follow the code.

## Purpose and boundaries

The Communications subsystem does one thing: it sends each module's data out and makes sure the next module receives it accurately. Communications ends at the interface. It passes every result through unchanged: it never merges, splits, filters or reinterprets results. Who does what at each hand-over is the table in section 3.1 of the hand-off document.

Finished documents are not finished integration. Every measured result so far used the 32-byte dummy packet and dummy labels, and every teammate interface in section 7 of the hand-off document is planned, not built (see "Current state of the three external interfaces" below).

This chapter describes the state after the Week 7 compatibility code was removed on 2026-10-14. The sensor packet magic is only `LC`. The source statistics magic is only `LCS1`. The session ID defaults to `ltc-comms` everywhere. The local evidence and board-map folder is `.comms-local`. For what was removed and in which commit, see "History and removals" under "Caveats and known limitations".

**End-to-end topology (V1: one user, two gloves, one laptop, one Ultra96, one iPhone)**

```text
Left  FireBeetle ESP32 (device_id=1) ─┐ BLE GATT Notify, 32-byte packets
Right FireBeetle ESP32 (device_id=2) ─┴────────────► Windows laptop (BLE Central)

Laptop ─TCP→ local 127.0.0.1:18889 ─SSH -L→ stujump:22 → Ultra96:22 → on-board 127.0.0.1:8888
        inside TLS: SENSOR_BATCH →    ← INGEST_ACK

iPhone ─in-app SSH→ stujump:22 → Ultra96:22 → on-board 127.0.0.1:9999
        inside TLS: SUBSCRIBE →    ← SUBSCRIBED    ← GESTURE_RESULT

Inside the iPhone: Swift client ─C function polling→ Unity main thread
```

| Hop | Who initiates, who listens | Transport | Data direction | Protection |
|---|---|---|---|---|
| ESP32 and laptop | The laptop (Central / GATT client) connects to the ESP32 (Peripheral / GATT server). Each board accepts one connection at a time. The firmware disconnects a second connection at once (`main.cpp:126-131`). | BLE GATT. Samples use the Notify characteristic `6e1c0005-…`. | Samples: ESP32 to laptop. Control writes on `…0007`: laptop to ESP32; responses come back on `…0008`. Source statistics on `…0006`: read by the laptop. | LE Secure Connections + MITM + bond. The ESP32 can only display the passkey (`ESP_IO_CAP_OUT`, `main.cpp:251-252`). Every characteristic and CCCD requires encryption with authentication. The firmware sends no notification before authentication completes. |
| Laptop to the on-board ingest service | The laptop program connects to local `127.0.0.1:18889`. OpenSSH `-L` goes through `stujump:22` to `Ultra96:22` and lands on on-board `127.0.0.1:8888`. | TCP, SSH local forward, TLS, JSON with a 4-byte length prefix | `SENSOR_BATCH` upstream. `INGEST_ACK` comes back on the same connection. One independent TLS connection per glove. | Both SSH hops check host keys strictly. TLS 1.2 or later, with checks on the CA and on the host name `ultra96.week7.internal`. |
| iPhone to the on-board result gateway | In-app SwiftNIO SSH connects to `stujump:22`, opens `direct-tcpip` to `Ultra96:22`, then opens `direct-tcpip` to on-board `127.0.0.1:9999`. The phone listens on no port. | Nested SSH channels, TLS, the same framing | `SUBSCRIBE` upstream once. After that the phone only receives `SUBSCRIBED` and `GESTURE_RESULT`. | Two SSH host public keys are pinned in source. TLS trusts only the imported CA. The CA fingerprint is pinned in source. Host name and validity period are checked. |
| Swift client to Unity | The Unity main thread calls a C function every frame | In-process C ABI | Display text: Swift to Unity. Planned, not built: one structured result per call through `CommsNextResult` (section 7.3 of the hand-off document) | Does not cross the network |

The VPN only provides network reachability. The code contains no VPN logic. With the VPN on, traffic still goes through `stujump`. The SSH jump host is how the Ultra96 is reached. Ports 8888 and 9999 are reachable only through SSH channels.

The phone code has a `useJump` switch (`Configuration.swift:29`, `IntegrationController.swift:69-70`). When it is off, the app skips `stujump` and connects directly to `Ultra96:22`. This route was never verified on site. V1 does not use it, and it is not a fallback route. V1 uses only the jump host.

**Communications is responsible for**

- In the firmware: packing, BLE sending, pairing security and connection management. After the real sensor module is merged in, olsonwangyj, the Communications owner, still writes this firmware.
- On the laptop: BLE reception, queuing, conversion to network messages, delivery to the board through the SSH channel, and ACK checking.
- On the board: receiving samples, deduplication, returning ACKs, and pushing results to the subscribed phone. Planned, not built: decoding each sample back to 11 physical floats, calling the model entry `on_sample` once per sample, and providing the thread-safe result exit `emit` (section 7.2 of the hand-off document).
- On the iPhone: the SSH/TLS client, result validation, and the three C functions that hand data to Unity. Planned, not built: the per-result function `CommsNextResult` with real confidence, pushed to the team repo with short steps for adding `CommsNative` to the Xcode project (section 7.3 of the hand-off document; the owner's proposal of 2026-10-14, final when Jie Ling confirms).
- Identity fields, counters and evidence for every segment.

**Communications is not responsible for**

- Sensor capture algorithms, calibration and sensor faults: Siqiang.
- Pairing left and right glove samples, building model windows, deciding gesture or idle, deciding when to produce a result, the label set, model accuracy and speed: Wen Ree.
- Mapping labels to game actions, cooldowns and repeat firing, the Unity C# that calls the Communications functions (pushed to the team repo), and any script in `vis/`: Jie Ling.
- The label names, how often a label is produced, and whether several identical labels in a row (for example several `CHOP`) mean one action or several: Wen Ree and Jie Ling agree between themselves. Communications hands every result over as it is.

**Current state of the three external interfaces**

| Interface | Counterpart | What it is now | Status |
|---|---|---|---|
| Upstream: glove sensor module | Siqiang, `hardware/` | The Communications firmware reads no sensor. It sends 8 int16 dummy values from `common/dummy_fixtures.json`. Siqiang's reference firmware `hardware/gloves/29_sept/imu_v7.ino` outputs an 11-float CSV over Bluetooth Classic serial at about 50 Hz. | Not connected. Proposed (the owner's direction of 2026-10-14, final when Siqiang confirms; sections 3.1 and 7.1 of the hand-off document): Siqiang delivers a working sensor module, pushed to the team repo (planned shape `gloveBegin`, optional `gloveUpdate`, `gloveRead`). The owner calls it from the Communications firmware and owns scaling, packing into the planned version-3 packet (38 bytes with the 11 values only; the layout is frozen after the IDLE/MOVING answer), BLE sending and connection management. Planned, not built: nothing calls a sensor module yet, and version 3 does not exist in code. |
| Middle: model side | Wen Ree, `src/` `models/` `fpga/` | The board's `ultra96/server.py` calls no model. For each new v2 input it picks a label at random from `REST`, `FIST`, `OPEN`, `POINT`, with confidence fixed at `1.0` (`ultra96/server.py:264-267`). The model side has 6 classes today. Its input is a 50×22 window. `src/live_inference.py` reads its own input from Windows COM ports (`COM3` and `COM4`). | Not connected. Planned, not built: `start(emit)` and `on_sample(...)` from Wen Ree, and the thread-safe `emit` from Communications. The owner's direction of 2026-10-14, final when Wen Ree confirms: the model gets the 11 values as physical floats. Four validators reject the model's 6 labels and any confidence other than 1.0. Opening up the labels is a Communications extension point (section 8, step 5 of the hand-off document). |
| Downstream: game | Jie Ling, `vis/` | The Week 7 receiver is the `CommsNative` Swift client on the iPhone, plus the bridge in the Unity export project that calls `Week7Start` / `Week7CopyDisplay` / `Week7Stop`. The bridge hands Unity only a 4-line display text. `vis/Assets/Scripts/Network/TlsDataReceiver.cs` is still the old approach that listens on port 5005 on the phone. Nothing in `vis/Assets/Scripts` calls the Communications bridge. | Proposed (the owner's direction of 2026-10-14, final when Jie Ling confirms; section 7.3 of the hand-off document): the game calls the Communications functions from C# in the Unity project. Jie Ling does everything in Unity and the iOS build on their own Mac and iPhone: the C# that calls the Communications functions (pushed to `vis/`), the game logic, exporting the project, adding `CommsNative` to the Xcode project, building, and installing the app, all before the integration session on Tue 10-20. olsonwangyj pushes `CommsNative` (with `CommsNextResult`) to the team repo (`ios-visualizer/CommsNative`), sends short steps for adding it to the Xcode project, and helps whenever something goes wrong. No export is pushed or passed around. Communications needs no API from the game. Only `CommsStart`, `CommsCopyDisplay` and `CommsStop` exist. Today the path reaches only "display text", which holds only the latest result: it is a status display, not a game input. Planned, not built: the per-result function `CommsNextResult`, through which results will reach the game logic. |

Every item marked planned in this table exists only on paper. Only `CommsStart`, `CommsCopyDisplay` and `CommsStop` can be called today; the firmware still sends dummy data, and the board still makes up dummy labels. The proposed delivery dates for each teammate (proposals until the teammates confirm; teammates deliver code by pushing it to the team repo on GitHub, not over Telegram), and the owner's own plan up to the in-person integration session on Tue 2026-10-20, are in section 6.4 of the hand-off document.

`phone/unity/CommsPhoneReceiver.cs` is the Android reference implementation. It needs the phone to run a separate SSH local forward. It is not the iPhone receiver actually deployed in Week 7.

### Technical constraints on the teammate interfaces

The interface requirements for the three teammates (functions, fields, suggested function shapes, questions they must answer) live only in section 7 of the hand-off document. This chapter does not repeat them. Below are only the technical constraints that the code covered by this chapter imposes and that each teammate needs to know.

**Sensor module (Siqiang).** Section 7.1 of the hand-off document gives the planned shape `bool gloveBegin()`, an optional `void gloveUpdate()`, and `bool gloveRead(float out[11])` (the names are Siqiang's to choose; nothing calls them yet). The constraints from networking and security are:

- The module must not open any Bluetooth or Wi-Fi itself. The reference firmware uses `BluetoothSerial` (Bluetooth Classic). The Communications firmware uses BLE, and it alone configures the whole BLE security policy (Secure Connections, MITM, bond, no notifications before authentication).
- The module must not read serial input, and must not print to serial for every sample. The Communications firmware accepts the `erase-bonds` command on the 115200 serial port (`main.cpp:382`), and the 6-digit passkey is printed only to this serial port (`main.cpp:184-187`).
- The Communications firmware sets left or right at compile time (`COMMS_DEVICE_ID`, 1 left, 2 right, `main.cpp:21-23,33-34`). The module does not need to supply a left/right identifier.
- The main loop holds the connection-state mutex from the send-tick check through control-request handling (`main.cpp:483-549`; the sending part is `:500-513`). The BLE callbacks also take this mutex. So "read one sample" must not block.

**Model entry and exit (Wen Ree).** Section 7.2 of the hand-off document gives the planned shape; none of it exists yet. `start(emit)` is called once at start-up. The entry `on_sample(device_id, boot_id, seq, uptime_ms, values)` takes each newly accepted sample once and returns at once. The exit `emit(gesture, confidence, device_id, boot_id, seq)` is provided by Communications; the model calls it once per result, from any thread, with the identity of one sample the result used (usually the newest). Each result must point to a different sample, because the phone deduplicates by `result_id`. The owner's direction of 2026-10-14, final when Wen Ree confirms: `values` are 11 physical floats. Transport stays int16; Communications decodes the values on the board and divides by the scale; any normalisation is Wen Ree's. The field name on the wire is `gesture`. The constraints from the code are:

- The board service is a single asyncio event loop. Today the dummy result is generated synchronously in the sample-receiving coroutine, and `INGEST_ACK` is written after it (`ultra96/server.py:264-275`). If the entry blocks here, the ACKs for both gloves and the results for the phone are all delayed. The laptop waits at most 5 s after sending for each ACK (`laptop/bridge.py:605-613`), and sample freshness is 2 s. At 50 Hz, the 32-frame ACK window covers only 0.64 s of samples (`laptop/dual_bridge.py:414`).
- The result queue is an `asyncio.Queue`, and subscriber state has no lock (`ultra96/server.py:35,56-63,268-272`). Only the service's event-loop thread may touch them. If the model produces results in another thread or process, it must hand them over through the event loop (for example `loop.call_soon_threadsafe`). It must not call the enqueue function directly. The planned `emit` is that hand-over: Communications will write it so that a call from any thread is moved onto the event loop. It does not exist yet.
- Only one task may write frames on a connection (the convention in `common/wire.py:76-79`). Only the existing sender task (`ultra96/server.py:366-387`) may write results to the phone.
- The field set of `GESTURE_RESULT` is matched exactly in four places: the board, the iPhone and the two reference receivers. All four also require `device_id` to be 1 or 2, and `result_id` to equal the result's own `device_id:boot_id:seq` (prefixed `cmd:` for commands). So the correlation data can only be the identity of one sample. It cannot be an array or a nested object.
- The two gloves' samples arrive on two independent connections, with no pairing and no alignment. Communications does not retransmit. Missing samples are not filled in; they show as gaps in `seq`. Reconnects can leave such gaps. On a BLE disconnect the laptop discards that glove's queued samples (`laptop/bridge.py:113-120,910`; counted in `callback_generation_dropped`). On a TLS reconnect, samples already written but not acknowledged count as `ambiguous_dropped` and are not resent (`laptop/bridge.py:464-469,498`). While a glove is disconnected it makes no samples and `seq` does not advance (`main.cpp:500-504`), so the disconnected time shows only as a jump in `uptime_ms`.
- The board does not resend results either. A result waits on the board for at most 2 s (queue plus write into the phone's connection). That limits waiting on the board only; it is not an end-to-end latency bound and not a promise that the phone receives the result (section 7.2 of the hand-off document).

**Game-side calls (Jie Ling).** The signatures, semantics and C# declarations of the three C functions are in sections 4.6 and 7.3 of the hand-off document. The constraints from the code are:

- The phone opens no listening port. Results come in only through the bridge functions: the three that exist today, and the planned `CommsNextResult`. Nothing may depend on port 5005 any more.
- The symbols come from the static library `CommsNative`, which must be linked into `UnityFramework`. Proposed (2026-10-14, final when Jie Ling confirms): Jie Ling makes that link on their own Mac, following the owner's short steps (add the local Swift package `ios-visualizer/CommsNative` and link it into `UnityFramework`), then builds and installs the app. Before the link, the Xcode build reports `Undefined symbol: _CommsStart` and similar; this is expected. Whether `configure_xcode.py` works on a new export is unverified (section 13 of the hand-off document). `CommsCopyDisplay` returns the UTF-8 byte count, excluding the terminating 0. The caller allocates the buffer; Week 7 uses 2048 bytes (`ios-visualizer/tools/patch_export.py:112-113`). The C# declarations in section 7.3 of the hand-off document are derived from the `@_cdecl` signatures and have not been compiled in Unity. The symbols exist only in the iOS build (`DllImport("__Internal")`). Calls in the Unity Editor or on other platforms throw, so calls go inside `#if UNITY_IOS && !UNITY_EDITOR`. Section 7.3 of the hand-off document settles this. It is not a question for Jie Ling.
- Call `CommsStop` only when the app no longer uses Communications. Do not call it on a scene change or when the app goes to the background. It sets the status to `Stopped` at once. Then it stops the client, clears the passwords, removes the foreground and background notification observers, closes the setup form and removes the button (`DisplayMailbox.swift:48-55`, `IntegrationController.swift:91-108`). After that, `CommsStart` must be called again, and the user must enter the passwords again. So the component that calls it must survive across scenes. The Week 7 export calls `Week7Stop` when its object is destroyed only because that object lives until the app ends.
- The app works only in the foreground. Locking the screen or switching to the background disconnects at once and clears the passwords (`IntegrationController.swift:27-29`).
- The top-right corner of the screen must stay free for the native `Communications Connect` button (`IntegrationController.swift:42-58`). It is the only way to connect.
- The current bridge keeps only the latest result. The `confidence 1.0` in the text is hard-coded (`DisplayMailbox.swift:15-18`), and the Swift `GestureResult` has no confidence field (`Protocol.swift:7-15`). If several results arrive between two polls, the game sees only the last one; `Received` still counts all of them. So the text is a status display, not a game input. Line 2 of the text is the status; `Subscribed` means only that the subscription handshake with the Ultra96 succeeded, and does not prove that results are flowing.
- Planned and not built (the owner's direction of 2026-10-14, final when Jie Ling confirms): a fourth function, `int32_t CommsNextResult(char* buffer, int32_t capacity)`, takes out the oldest waiting result as one compact JSON object with its real confidence. It returns the bytes written, 0 when nothing is waiting, or the negative of the bytes needed when the buffer is too small (then it writes nothing and keeps the result). The game calls it in a loop each frame while it returns a positive number, with a 512-byte buffer. What it promises: results wait in arrival order, deduplicated by `result_id`, and each result that is not dropped can be taken out at most once. It does not promise that every result is delivered: results lost before the phone never arrive, and the queue itself drops results and counts each drop, under provisional V1 limits that are revisited after Wen Ree's answer. The queue is emptied when the session stops (Disconnect, the app becoming inactive, `CommsStop`) and when a new Connect starts; an automatic reconnect keeps it. A `confidence` field is added to the Swift `GestureResult` in the same step (section 8, step 5 of the hand-off document). The example object, the provisional limits and the planned date (Sun 10-18) are in sections 6.4, 7.3 and 13 of the hand-off document. Until it exists, the game can show the text but cannot drive actions reliably from it.

## Components and files

| File | Responsibility |
|---|---|
| `common/wire.py` | Network framing: a 4-byte big-endian length plus a strict UTF-8 JSON object; limit 16384 bytes; one 5 s deadline each for read and write; `ProtocolError`. |
| `common/tls.py` | TLS client and server contexts; minimum TLS 1.2; host-name constant `TLS_SERVER_NAME`; no "skip verification" branch. |
| `common/sensor.py` | Encoding and decoding of the 32-byte sensor packet (`SensorPacket`, `encode_packet`, `decode_packet`, `PACKET_MAGIC = b"LC"`); conversion to `SENSOR_BATCH`; loading and selecting from the dummy-data table. |
| `common/control.py` | Encoding, decoding and validation of BLE control frames (14-byte `B7` header). Unrelated to the network JSON. |
| `common/dummy_fixtures.json` | Editable 8-channel dummy-data table, 4 rows today. |
| `common/__init__.py` | Package exports. |
| `firmware/esp32/platformio.ini` | Build environments, four in all: the default `firebeetle32` (`default_envs`, protected build, ID 1 because `COMMS_DEVICE_ID` defaults to 1; `platformio run` without `-e` builds it, so flashing it onto the right-hand board makes that board ID 1), `firebeetle32-left` (ID 1), `firebeetle32-right` (ID 2), and the explicitly named unprotected diagnostic build `firebeetle32-unprotected-diagnostic`. |
| `firmware/esp32/src/main.cpp` | All BLE peripheral logic: the GATT service and its 7 characteristics, pairing security, sending samples at the set rate, the control queue, source statistics, `erase-bonds`. |
| `firmware/esp32/include/comms_packet.h` | Byte-by-byte serialisation of the 32-byte packet. |
| `firmware/esp32/include/comms_fixtures.h` | Dummy-data table generated from the JSON (rewritten by every `flash.py` run). |
| `firmware/esp32/include/comms_security.h` | Pure functions for the authentication bits, the notification gate, the sensor MTU floor (`sensorFitsMtu`, ATT MTU at least 35) and the control-write gate (`canAcceptControl`). |
| `firmware/esp32/include/comms_source_stats.h` | Sequence allocation, submission counting, 24-byte source statistics serialisation. |
| `firmware/esp32/include/comms_control.h` | Control state machine `ControlEngine`: commands, rate changes, file transfer, response cache. It also holds the control MTU floor 64 (`controlFitsMtu`, with `controlChunkCapacity`). |
| `firmware/esp32/include/comms_gatts_control.h` | Parses a write only on a real WRITE event. |
| `firmware/esp32/test/host_*.cpp` | Four header-file host tests, compiled and run with `g++` or `clang++`, whichever is on `PATH`. The tests are skipped when neither is found. |
| `laptop/bridge.py` | The whole path for one glove: BLE connection, MTU and bond checks, bounded queue, TLS writes, ACK checking, metrics, and tail-packet handling at shutdown. |
| `laptop/dual_bridge.py` | Runs two independent `Bridge` instances at once; one shared observation window; writes the overall report. `demo.py` actually calls it. |
| `laptop/source_audit.py` | Parses source statistics (`SOURCE_STATS_MAGIC = b"LCS1"`); reconciliation of "generated = received = ACKed". |
| `laptop/controls.py` | BLE control channel: keyboard commands, rate changes, file transfer. |
| `laptop/windows_pairing.py` | Pairs on Windows with "enter passkey + encryption and authentication", and checks the bond level. |
| `laptop/ble_connection.py` | Turns off the Windows GATT cache when it creates the Bleak client. |
| `laptop/ble_parameters.py` | Above 10 Hz, asks Windows for throughput-optimised connection parameters and records the actual values. |
| `laptop/ble_shutdown.py` | When a capture stops, turns off notifications on the remote side first and keeps the local callback to collect the tail. |
| `laptop/evidence.py` | Bounded background writer for `packets.jsonl` and the `.log`. |
| `laptop/goodput.py` | Measures the rate of valid sensor bytes received by the laptop. |
| `laptop/reporting.py` | Exclusive placeholder and atomic write for report files; source fingerprint. |
| `laptop/phone_simulator.py` | Desktop result subscriber, for rehearsals only. Once connected, it replaces the phone. |
| `laptop/mtu_probe.py`, `laptop/ble_counter_receiver.py`, `laptop/bounded_telemetry_queue.py` | Early diagnostic tools, and a generic queue that the main path does not use. |
| `laptop/requirements.txt` | `bleak==3.0.1`. The version must stay pinned: the tail-packet protection at shutdown depends on Bleak's internal attributes. |
| `ultra96/protocol.py` | Exact fields, value ranges, `session_id` rules and `result_id` generation for the five message types; the label allowlist `GESTURES` and the "confidence must be 1.0" check. |
| `ultra96/server.py` | Board service `CommsServer`: two loopback TLS listeners, ingest deduplication and ACK, single-subscriber result queue, command-line entry point. |
| `ultra96/diagnostics.py` | Optional bounded event log (`--event-log-dir`). |
| `phone/receiver.py` | Standard-library Python receiver (Termux / iSH). Connects to the local forward port 19999. Reference implementation. |
| `phone/unity/CommsPhoneCore.cs` | Unity-independent C# protocol, TLS trust and receive loop. Reference implementation. |
| `phone/unity/CommsPhoneReceiver.cs` | Android reference Unity component. Needs the phone to run a separate SSH forward. |
| `phone/ish_control.py` | Temporary maintenance-channel script for the iSH route (that route is abandoned). Its own folder name is now `comms-control`. The SSH config file name and host alias keep their Week 7 names (see "Caveats and known limitations"). |
| `ios-visualizer/CommsNative/Package.swift` | Swift package definition. Dependencies are pinned to SwiftNIO 2.102.0, NIOSSH 0.15.0, NIOSSL 2.37.4, swift-crypto 4.5.2. |
| `…/Sources/CommsCore/Protocol.swift` | Subscribe-frame encoding, result validation (label allowlist and confidence check), stream framing. |
| `…/Sources/CommsCore/DisplayState.swift` | Latest result, counters, deduplication, 2 s expiry. |
| `…/Sources/CommsTransport/CommsClient.swift` | Setting up two SSH hops plus TLS, failure classification (terminal or retry), back-off reconnection. |
| `…/Sources/CommsTransport/SSHRoute.swift` | Route parameters, port and timeout constants, failure types and status text. |
| `…/Sources/CommsTransport/Trust.swift` | Exact host public key comparison, password authentication, SSH channel byte conversion. |
| `…/Sources/CommsTransport/Subscriber.swift` | Sends `SUBSCRIBE` after the TLS handshake, receives frames, frame deadline. |
| `…/Sources/CommsTransport/Credentials.swift` | Clearable in-memory password holder. |
| `…/Sources/CommsBridge/Configuration.swift` | Fixed host names, the two SSH host public keys, the CA fingerprint; CA import validation; saving the public configuration. |
| `…/Sources/CommsBridge/IntegrationController.swift` | Foreground session management; the connect button; disconnect on going to the background. The session ID `ltc-comms` that the client uses is written here (`IntegrationController.swift:74`). |
| `…/Sources/CommsBridge/SetupViewController.swift` | Setup form. Its form text also shows `DUMMY gestures · session ltc-comms` (`SetupViewController.swift:51`). Change it together with the session ID in `IntegrationController.swift:74`. |
| `…/Sources/CommsBridge/DisplayMailbox.swift` | The C functions exported to Unity, `CommsStart`, `CommsCopyDisplay` and `CommsStop`, plus the three `Week7*` wrappers. The four-line text is assembled here. |
| `ios-visualizer/tools/patch_export.py` | The Week 7 receiver: patches the generated code of one specific Unity export, wires in the three `Week7*` calls, and disables the old listening loop. |
| `ios-visualizer/tools/configure_xcode.py` | Links `CommsNative` into `UnityFramework`. Also sets the app display name to `Week 7 Visualizer`. |
| `ios-visualizer/verify-import.py`, `import-manifest.json` | Validates the originally imported Unity export files. Applies only to an unpatched project. Running it on the current `xcode-export/` reports `IMPORT_CHECK_FAILED`, which is expected. |
| `ios-visualizer/reference/TlsDataReceiver.cs` | Archived copy of Jie Ling's original receiver script. |
| `ios-visualizer/NativePreview/` | Preview app without Unity, and simulator tests. |
| `ios-visualizer/xcode-export/` | The Unity export project used in Week 7 (generated code, 3479 files). |
| `demo.py` | Operator entry point: `tunnel`, `run`, `live`, `report`, `service`. |
| `flash.py` | Builds both firmware images, flashes them in order, records the boards' Bluetooth addresses, pairs, serial monitor. |
| `tools/ssh_tunnel.py` | Generates the two-hop, loopback-only OpenSSH local-forward command (explicit `ProxyCommand`, strict host keys); optional supervised restart. |
| `tools/demo_service.py` | Inspects or starts the board service over SSH. The board deployment folder constants `BOARD_ROOT` and `BOARD_SOURCE` are here. The caller passes in the session ID for a start. |
| `tools/demo_boards.py` | Reads and writes the left/right board Bluetooth address map, only in `.comms-local/boards.json`. The built-in default addresses are here. |
| `tools/generate_comms_pki.py` | Generates a new CA and server certificate. `--renew-server-from <CA_DIR>` uses the existing CA to issue only a new server certificate. |
| `tools/generate_dummy_fixtures.py` | Generates the firmware header file from the JSON. |
| `tools/comms_demo.py` | Packet example, single-board send demo, offline log audit. |
| `tools/rehearse_comms.py` | Local loopback end-to-end rehearsal. |
| `tools/rehearse_remote_comms.py` | Remote rehearsal through existing tunnels, with ACK and result reconciliation. Replaces the phone's subscription. |
| `tools/video_evidence.py` | Pulls one sample-and-ACK pair per device from a capture as an example. |
| `requirements-dev.txt` | Dependencies for the tests and the certificate tool: `pytest`, `cryptography`. It also lists `pyserial`, which Communications code does not use. Only scripts under `hardware/gloves/` (the recording scripts and two debug scripts in `model_threshold_variant_1/`) and `src/live_inference.py` import `serial`. `flash.py` reads the MAC and flashes with PlatformIO's bundled tools. |
| `tests/`, `laptop/tests/`, `phone/tests/`, `ios-visualizer/CommsNative/Tests/` | Automated tests. Directly relevant to this chapter: `tests/test_transport.py` (TLS trust, framing, certificate tool), `tests/test_ssh_trust.py` (effective two-hop SSH configuration), `tests/test_server_observation.py` (where results go), `CommsTransportTests` (phone-side SSH/TLS). |

**Present only on the fork, not in the team repo.** The team repo `upstream/main` (`5a004c6` after PR #18; before that `880abba`, which was `ec398b6` before the history rewrite of 2026-10-14) has no `docs/` at all (that folder holds every design record this chapter cites). It also has no `AGENTS.md`, `CLAUDE.md` or `.gitattributes`. Within Communications, the tracked files that exist only on local `main` of the fork (`origin`) are: `ios-visualizer/tools/patch_export.py`, `ios-visualizer/tools/configure_xcode.py`, `ios-visualizer/verify-import.py`, `ios-visualizer/import-manifest.json`, `ios-visualizer/reference/TlsDataReceiver.cs`, `tests/test_ios_export_patch.py`, and every file in `ios-visualizer/xcode-export/`. In the team repo, `ios-visualizer/` holds only `CommsNative/`, `NativePreview/`, `README.md`, `NATIVE-INTEGRATION.md` and `reference/teammate-localhost-cert.pem`. Teammates working from the team repo cannot open the paths above. The 2026-10-14 compatibility removal and the certificate renewal option reached the team repo's `main` through PR #18 (merge commit `5a004c6`), and the team main is merged into local `main` (section 6.2 of the hand-off document).

## Data formats and constants

**Addresses and ports**

| Item | Value | Defined in |
|---|---|---|
| Jump host | `stujump.comp.nus.edu.sg`, TCP 22 | `tools/ssh_tunnel.py:85`, `Configuration.swift:9` |
| Ultra96 | `makerslab-fpga-35.ddns.comp.nus.edu.sg`, TCP 22 | `tools/ssh_tunnel.py:86`, `Configuration.swift:8` |
| On-board ingest service | `127.0.0.1:8888` | `ultra96/server.py:149,464` |
| On-board result gateway | `127.0.0.1:9999` | `ultra96/server.py:149,465` |
| Laptop local forward port | `127.0.0.1:18889` (both the `demo.py` tunnel and its capture use it); the lower-level modules default to `18888` | `demo.py:42,53,120`, `laptop/bridge.py:37`, `laptop/dual_bridge.py:410`, `tools/ssh_tunnel.py:87` |
| Reference client local port | `127.0.0.1:19999` (used by the Python, Android and desktop subscribers); the native iPhone app does not use it | `phone/receiver.py:198`, `laptop/phone_simulator.py:72`, `phone/unity/CommsPhoneCore.cs:366` |
| iPhone ports | SSH 22 (jump host) and 22 (Ultra96), service 9999, no local listener | `SSHRoute.swift:31-33` |
| BLE advertised name | `LTC-COMMS`, the same on both boards | `main.cpp:41` |
| BLE service UUID | `6e1c0001-7a45-4dc4-b678-3f2d5a9c1001` | `main.cpp:42` |
| Accounts, board Bluetooth addresses | Not copied into this chapter; see the code | `tools/ssh_tunnel.py:85-86`, `demo.py:40-41`, `tools/demo_service.py:17-18`, `tools/demo_boards.py:10` |

**Identities and identifiers**

| Identifier | Type and range | Who produces it | When it changes | Purpose |
|---|---|---|---|---|
| `device_id` | uint8, only 1 (left) or 2 (right) | Firmware compile time, `-DCOMMS_DEVICE_ID` (`main.cpp:21-23,33-34`) | Only on reflash | Tells the two gloves apart. After the laptop connects by address, it also checks the `device_id` inside each packet. |
| BLE address | 6 bytes | The ESP32 factory MAC plus 2, derived by `flash.py` (`flash.py:68-69`) | Only when the board is replaced | The laptop uses it to find the specific board. |
| `boot_id` | uint32 random number | `esp_random()` in the firmware's `setup()` (`main.cpp:406`) | Every power-up or reset | Separates `seq` values before and after a reboot. It is only a correlation identifier, not a security identity. |
| `seq` | uint32, starts at 0 on every boot | The firmware assigns it before submitting the notification (`main.cpp:504`); it is not reused when submission fails | +1 per sample | Per-sample tracking; detects gaps, duplicates and reordering. |
| `uptime_ms` | uint32, wraps | Firmware `millis()` | Every sample | On-board time. The two gloves are not synchronised, so it cannot be used to compute end-to-end latency. |
| `session_id` | String, 1 to 128 characters, no control characters below 32 and no surrogates (`ultra96/protocol.py:20-25`) | Configuration value; default `ltc-comms` | When someone changes the configuration by hand | Ties together the inputs, ACKs and results of one deployment. Laptop, board and phone must agree. It is not a password. |
| `request_id` | Only in v2. `null` for telemetry; for commands 1 to 4294967295 and equal to `seq` | The laptop (random start, then increments; `laptop/controls.py:40`) | Every keyboard command | Separates ordinary samples from commands. |
| `result_id` | String `device_id:boot_id:seq`; commands are prefixed `cmd:` | The board builds it from the input identity (`ultra96/protocol.py:94-96`) | Every result | Phone deduplication; maps a result back to its input. |
| `subscriber_id` | In-process increasing integer | The board adds 1 for each accepted subscription (`ultra96/server.py:311-313`) | Every subscription | Appears only in diagnostic logs. |
| Generation (generation / epoch) | In-process increasing integer | Laptop (BLE connection, TLS connection); phone (connection attempt, display session) | Every reconnection | Invalidates late callbacks from old connections. Never on the wire. |
| `run_id`, `event_seq` | uuid4 hex; increasing integer | Board diagnostic log (`ultra96/diagnostics.py:68,143-148`) | Each time logging is enabled | Identify one event log and the order of events inside it. |

**Versions**

| Where | Value | Meaning |
|---|---|---|
| BLE sensor packet, byte 2 | 1 | Deterministic dummy data. The 8 values must equal `seq % 2000 − 1000 + 10·i`. Checked by the laptop when it decodes (`laptop/bridge.py:408-409`) and by the board when it validates network v1 (`ultra96/protocol.py:70-72`). The firmware sends it only when built with `-DCOMMS_LEGACY_DUMMY=1`. |
| Same | 2 | Any valid int16 values. The firmware sends this by default, with values taken from the dummy-data table. |
| Same | 3 (planned, not implemented) | The owner's direction of 2026-10-14, final when the teammates confirm: a new format for real glove data, 38 bytes with the 11 int16 values only; the final layout is frozen only after the IDLE/MOVING answer. No receiver can read it with the 8-value layout, so the firmware, laptop and Ultra96 parsers and the version checks on the result path change together (section 8, step 1 of the hand-off document). |
| Network message `v` | 1 | No `request_id` key. `gesture` must equal `GESTURES[seq % 4]`. |
| Same | 2 | Must carry the `request_id` key. `gesture` is one of the four labels, chosen at random by the board. |
| `v` of `SUBSCRIBE`, `SUBSCRIBED` | Only 1 allowed | The subscription envelope does not change version. After subscribing, both v1 and v2 results are accepted. |
| BLE control frame, byte 2 | 1 | Version of the `B7` control protocol, unrelated to the two versions above. `B7` is the team number B07, not Week 7. |

Protocol v1 and `COMMS_LEGACY_DUMMY` are the deterministic dummy-data mode, not backward compatibility. The Week 7 compatibility removal kept them on purpose.

The version rows above describe the current code. The owner's rule (2026-10-14) is that only the newest version is supported: there is no interoperability between versions, and an upgrade means reflashing both boards, redeploying the Ultra96 service and reinstalling the phone app together. When version 3 is built, it replaces versions 1 and 2 everywhere, including the dummy test data, which moves to the 11-value format. There is no transition period, such as keeping results at `v: 2`; it would not help anyway, because an old phone build also rejects labels other than the four dummy ones, confidence other than 1.0, another session and another field set (section 8, step 1 of the hand-off document).

**Message overview** (frame: a 4-byte big-endian length plus a UTF-8 JSON object; body 1 to 16384 bytes; the field set must match exactly; there are no error messages; on any error the connection is closed)

| `type` | On-board port | Direction | Fields besides `v`, `type`, `session_id` |
|---|---|---|---|
| `SENSOR_BATCH` | 8888 | Laptop to board | `device_id`, `boot_id`, `seq`, `uptime_ms`, `values` (8 int16); v2 adds `request_id` |
| `INGEST_ACK` | 8888 | Board to laptop | `device_id`, `boot_id`, `seq`, `status` (`accepted` or `duplicate`); v2 adds `request_id` |
| `SUBSCRIBE` | 9999 | Phone to board | None |
| `SUBSCRIBED` | 9999 | Board to phone | None |
| `GESTURE_RESULT` | 9999 | Board to phone | `device_id`, `boot_id`, `seq`, `result_id`, `gesture`, `confidence`; v2 adds `request_id` |

**BLE sensor packet, current 32 bytes** (Python format `<2sBBIII8h`; needs an ATT MTU of at least 35)

| Offset | Length | Field | Type | Value |
|---|---|---|---|---|
| 0 | 2 | Magic | ASCII | `LC` (`4C 43`). Only this one is accepted |
| 2 | 1 | Version | uint8 | 1 or 2 |
| 3 | 1 | `device_id` | uint8 | 1 or 2 |
| 4 | 4 | `boot_id` | uint32 little-endian | 0 to 4294967295 |
| 8 | 4 | `seq` | uint32 little-endian | 0 to 4294967295 |
| 12 | 4 | `uptime_ms` | uint32 little-endian | 0 to 4294967295 |
| 16 | 16 | `values[0..7]` | 8 int16 little-endian | −32768 to 32767 |

**Real glove data packet, planned 38 bytes (not implemented; extension point)**

- The owner's direction of 2026-10-14, final when the teammates confirm: the 11 values travel as 11 int16 fixed-point values in a new format, protocol version 3, which replaces versions 1 and 2 everywhere (see "Versions" above). Real data cannot use version 1, which requires the values to equal the dummy-data formula.
- With the 11 values only, 38 = the existing 16-byte header + 11 × 2 bytes. The final layout is frozen only after Siqiang and Wen Ree answer whether the glove's IDLE/MOVING state travels: an extra field changes the length, the MTU floor and `on_sample`.
- A 38-byte notification needs an ATT MTU of at least 41. The current gate is 35.
- Not measured. The 50 Hz and 70 Hz results of 2026-09-28 used the 32-byte dummy packet. Two gloves at 50 Hz would carry 38 × 50 × 2 = 30.4 kbps at the application layer.
- The owner's direction of 2026-10-14, final when Wen Ree confirms: the model gets physical floats. On the Ultra96, Communications decodes the int16 values and divides each by its scale. Restoring cannot recover precision dropped when packing. Any normalisation is Wen Ree's.
- Places that must change together: `comms_packet.h` (8 channels, `kPacketSize = 32`), `comms_control.h` (the command payload embeds a whole packet), `common/sensor.py:11,36` (packet format and 8 values), `common/control.py`, `common/dummy_fixtures.json`, `ultra96/protocol.py:67` (8 values), `comms_security.h:19` (MTU 35), `laptop/bridge.py:719` (MTU 35), and `laptop/goodput.py`. `laptop/goodput.py` counts bytes with `PACKET_SIZE` from `common.sensor`, so its byte count follows the packet size automatically; only its version-1 formula check needs review. Because only the newest version is supported, the version checks change in the same step: `common/sensor.py:33,79-80` (packet versions 1 and 2; `:50` copies the packet version into `SENSOR_BATCH.v`), `ultra96/protocol.py:42` (network versions accepted) and the version branches for deduplication and `request_id` (`ultra96/server.py:250-259`, `ultra96/protocol.py:46,89-90`), and on the result path, where the board copies the sample's version into `GESTURE_RESULT.v` (`ultra96/server.py:264`): `Protocol.swift:40`, `phone/receiver.py:115`, `phone/unity/CommsPhoneCore.cs:70`. Section 8, step 1 of the hand-off document has the full list.
- Out-of-range values: to be agreed with Wen Ree (asked in the message; section 8, step 1 and section 13 of the hand-off document). The options are to clamp the value to the int16 limit or to drop that one sample. Either way Communications counts it, and it never drops a connection or a whole gesture. In normal use every value is expected to fit, but that is not guaranteed: the final value depends on the module's processing (for example the gyro calibration bias is subtracted), not only on the raw sensor range. A clamped value cannot be told apart from a real value at the limit (3.2767 g can be either); if the model needs to know which samples were clamped, a per-sample flag is needed, which changes the packet and `on_sample`. Neither option guarantees that a gesture is still recognised.

Sample fields (order and units come from `imu_v7.ino`; the scale factors were chosen on 2026-10-14 and are checked against Siqiang's real sample log before they are fixed; the representable ranges are int16 arithmetic):

| Index | Field | Unit from the sensor module | Transmission scale | int16 representable range | Resolution |
|---|---|---|---|---|---|
| 0–2 | `ax`, `ay`, `az` | g, gravity removed | ×10000 | ±3.2767 g | 0.0001 g |
| 3–5 | `gx`, `gy`, `gz` | °/s, bias removed | ×100 | ±327.67 °/s | 0.01 °/s |
| 6–8 | `yaw`, `pitch`, `roll` | ° | ×100 | ±327.67° | 0.01° |
| 9–10 | `flex1`, `flex2` | normalised 0.0–1.0 | ×10000 | up to 3.2767 | 0.0001 |

**Constants for the overall behaviour**

| Behaviour | Value | Defined in |
|---|---|---|
| Firmware send rate | Default 10 Hz; settable from 1 to 200 Hz | `main.cpp:24-26,39` |
| Laptop queue | 64 per device; drops the oldest when full | `laptop/bridge.py:39,132-134` |
| Laptop freshness | A sample must be written out within 2.0 s of reception, otherwise it is dropped | `laptop/bridge.py:40,424-426` |
| Laptop I/O timeout | 5.0 s (TLS handshake, frame write, ACK wait) | `laptop/bridge.py:41` |
| Laptop BLE scan and connect timeouts | 8.0 s and 20.0 s | `laptop/bridge.py:42-43` |
| ACK window | Library default 1; `dual_bridge` and `demo.py` use 32; range 1 to 64 | `laptop/bridge.py:48,60`, `laptop/dual_bridge.py:414`, `demo.py:81` |
| Reconnect back-off | Starts at 0.5 s, doubles, capped at 5.0 s (laptop BLE, laptop TLS, phone). Laptop TLS resets to 0.5 s after an ACK arrives; the phone resets after a result arrives | `laptop/bridge.py:473-482,660-670,684,948`, `SSHRoute.swift:36-37`, `CommsClient.swift:149,210-211` |
| Frame limit | 16384 bytes | `common/wire.py:7`, `Protocol.swift:18` |
| Frame read and write timeout | 5.0 s | `common/wire.py:49,76` |
| Board concurrent connections | At most 8, including unfinished handshakes | `ultra96/server.py:181` |
| Board TLS handshake timeout | 5.0 s | `ultra96/server.py:216` |
| Board ingest connection idle | Closed when no new frame arrives within 5.0 s | `ultra96/server.py:248`, `common/wire.py:49` |
| Board result queue | 32 for the current subscriber; drops the oldest when full | `ultra96/server.py:35,57-60` |
| Board result freshness | Dropped once it has been queued for 2.0 s; the write timeout equals the remaining freshness. This limits only how long a result waits on the board (queue plus write into the phone's connection). It is not an end-to-end bound and not a promise that the phone receives the result | `ultra96/server.py:69-77,366-378` (`get_timed`, `_send_results`) |
| Subscriber count | One at a time; a new subscription replaces the old one | `ultra96/server.py:315-330` |
| Board deduplication | v1: the last 4096 entries. v2: one high-water mark per `(device_id, boot_id)` that only moves up, plus fingerprints of the last 4096 entries. At most 128 boot namespaces and 4096 commands. | `ultra96/server.py:88,256-259,277-307` |
| Phone connection deadline | 10 s, from starting TCP to receiving `SUBSCRIBED` | `SSHRoute.swift:34`, `CommsClient.swift:96-98,145` |
| Phone frame deadline | `SUBSCRIBED` must arrive in full within 5 s after `SUBSCRIBE` is sent. After that, each frame must arrive in full within 5 s of its first byte. Once subscribed with no partial frame, idle time has no deadline. | `SSHRoute.swift:35`, `Subscriber.swift:32,41-43` |
| Phone deduplication | The last 4096 `result_id` values | `DisplayState.swift:65-76` |
| Phone display freshness | Clears the label 2 s after the phone received the latest result (the phone's own window, counted from receipt); counters are kept | `DisplayState.swift:79,109-112` |
| Unity polling buffer | 2048 bytes | `ios-visualizer/tools/patch_export.py:112` |

**Trust material: who holds it, who verifies whom**

| Material | Who holds it | Use | Value or location |
|---|---|---|---|
| CA private key `ca-key.pem` | Only the machine that issued it (olsonwangyj's laptop), outside Git | Signs server certificates. It never goes onto the board or into the phone. | The output folder must be outside any Git repository and empty (`tools/generate_comms_pki.py:27-35`). The private key is written with `O_EXCL` and permission 600 (`:59-65,125`). |
| CA certificate `ca-cert.pem` | The laptop (`--ca` argument; default path in `demo.py:49-50`); the iPhone (after import, stored as `Application Support/Comms/comms-ca.pem`, `IntegrationController.swift:17`, `Configuration.swift:67`) | Clients use it to verify the board's server certificate | RSA 2048; CN `B07 Communications Development CA`; valid for 365 days; `path_length=0` (`tools/generate_comms_pki.py:112-118`). The CA in use is valid until 2027-09-06. |
| Server certificate and private key | The `tls/` folder in the Ultra96 deployment folder | The board presents its identity to clients | RSA 2048; CN and SAN are both `ultra96.week7.internal`; valid for 30 days; usage `serverAuth` (`tools/generate_comms_pki.py:38-56,94,113`) |
| TLS host name | In the certificate, and in the client code | Clients check against this name even when they connect to `127.0.0.1` | `ultra96.week7.internal` (`common/tls.py:4`) |
| CA fingerprint | Compiled into the iPhone source | The app accepts only a CA whose DER SHA-256 equals this value | `4dfba4905c171e68c3623dbc952154149076ed89004b85d475e858cc550760ec` (`Configuration.swift:12`). The fingerprint of the CA in use matches it. |
| SSH host public keys of the jump host and the Ultra96 | Laptop: the local `known_hosts`, not in the repository. iPhone: compiled into the source. | Clients verify the two SSH servers | Two `ssh-ed25519` public keys, see `Configuration.swift:10-11` |
| SSH passwords | Only the operator | The two SSH servers verify the client | On the laptop, typed at the OpenSSH prompt. On the iPhone, kept only in memory and cleared when the app goes to the background. |
| BLE bond keys | One copy each on the ESP32 and on Windows | Mutual authentication of the BLE link | During pairing, the ESP32 serial port shows a 6-digit passkey, which is entered on Windows |

TLS authenticates only the server. The board does not verify client certificates. Anyone who can log in to the Ultra96 is inside the trust boundary. `session_id` is not an access credential.

**Evidence levels**

| Level | Evidence | Where to see it | What it proves | What it does not prove |
|---|---|---|---|---|
| 1 | Source statistics `submitted` | ESP32 characteristic `…0006`; `source_submitted` in the report | ESP-IDF accepted this notification submission | That the laptop received it |
| 2 | Laptop `received` | `received` in `report.json`. The BLE callback count is the separate field `callback_received`. The progress line's `received=` prints the callback count. | The laptop's writer task took the packet from the queue and processed it | That the board received it |
| 3 | `INGEST_ACK` (`accepted` or `duplicate`) | `acked` in `report.json`; `sensor_ack` in `packets.jsonl` | The board application validated and accepted this input | That the phone received it; that a model ran inference |
| 4 | Board event `result_write_complete` | Recorded only when the service starts with `--event-log-dir`; the field `phone_receipt_confirmed` is always `false` (`ultra96/server.py:386-387`) | The board handed this frame to TCP/TLS | That the phone validated or displayed it |
| 5 | Phone `Received: N` | The iPhone screen, read by a person | Within this Connect session, the phone validated and accepted N distinct results | Per-result IDs; that a game action fired |

The report's `received` and `callback_received` differ when the queue drops packets.

Level 4 events are written first to `events.partial.jsonl`. Only when the service shuts down cleanly is the file renamed to `events.jsonl`, and `status.json` written (`ultra96/diagnostics.py:62-65,324`). The event queue holds 2048 entries and the file limit is 50 MiB (`ultra96/diagnostics.py:56`). When the queue overflows or the file is full, events are only counted; forwarding is never blocked (`ultra96/diagnostics.py:154-159,205-212`). `--event-log-dir` must be a new folder that does not exist yet (`ultra96/diagnostics.py:62`).

The phone sends no application-level acknowledgement. The phone keeps no per-result ID ledger. The `CAPTURE PASSED` line printed by `demo.py` is level 3.

## Workflow

**Normal path**

Preconditions: the VPN is connected; the board service is already running; the board service, the firmware on both boards and the phone app are all built from the current source (for the current deployment state, see section 6.3 of the hand-off document).

1. The board starts the service: `/usr/bin/python3 -u -m ultra96.server --cert <tls>/server-cert.pem --key <tls>/server-key.pem --session-id ltc-comms --ingest-port 8888 --gateway-port 9999`. It opens two listeners on `127.0.0.1` and prints `{"event": "listening", "host": "127.0.0.1", "tls": true, "ingest_port": 8888, "gateway_port": 9999}`.
2. The phone subscribes. The user taps `Communications Connect`. The app connects to `stujump:22`, compares the host public key and logs in with a password. It opens `direct-tcpip` to `Ultra96:22`, compares that public key and logs in. It then opens `direct-tcpip` to `127.0.0.1:9999`. It runs the TLS handshake with server name `ultra96.week7.internal`. After the handshake it sends `SUBSCRIBE`. The whole process is limited to 10 s. After `SUBSCRIBE` is sent, the phone starts a separate 5 s timer for `SUBSCRIBED` (`Subscriber.swift:32,60-66`). If `SUBSCRIBED` has not arrived in full within 5 s, the phone records `frame deadline exceeded` and retries after back-off. This 5 s timer and the 10 s connection deadline run at the same time.
3. The board reads `SUBSCRIBE` within 5 s, checks `session_id`, adds 1 to the subscriber number, closes the old subscriber and replies `SUBSCRIBED`. The phone status becomes `Subscribed` (`CommsClient.swift:146`). This means only that the subscription handshake with the Ultra96 succeeded. It does not prove that results are flowing.
4. The laptop opens the tunnel: `python demo.py tunnel`. Local `127.0.0.1:18889` forwards to on-board `127.0.0.1:8888`.
5. The laptop starts the capture: `python demo.py run`. For each glove: scan (limit 8 s), connect (limit 20 s), confirm an MTU of at least 35, confirm the Windows bond is "encrypted and authenticated", read the starting source statistics, subscribe to sensor notifications. Both gloves must be ready within 30 s (`laptop/dual_bridge.py:418`).
6. Every `1000000 / rate_hz` microseconds the ESP32 checks (`main.cpp:486-487`): connected, subscribed, authenticated, MTU at least 35. If all pass, it assigns `seq`, packs 32 bytes, submits the notification and records `submitted` or `failures`. A notification needs no confirmation from the peer.
7. The laptop's BLE callback records the arrival time on the monotonic clock and copies the bytes into that device's bounded queue. It also decodes the packet once for the goodput statistics, hands a `sensor` or `sensor_invalid` record to the evidence thread, and updates the callback and silence counters. It does no network operations.
8. The writer task takes one packet: decodes it, checks `device_id`, checks for gaps, duplicates and reordering, checks the connection generation, checks freshness.
9. On the first send it opens a TLS connection to `127.0.0.1:18889`, with a 5 s handshake limit (`laptop/bridge.py:349-353`). It checks the generation and freshness once more. It writes `SENSOR_BATCH`; the write timeout is the smaller of 5 s and the remaining freshness.
10. The board reads the frame, validates the fields and `session_id`, and deduplicates. New input: it generates a `GESTURE_RESULT`, puts it in the subscriber's queue if there is a subscriber, then replies `INGEST_ACK` with `status` `accepted`. Duplicate input: it replies only `duplicate` and produces no result.
11. The laptop checks the ACKs in send order: `v`, `type`, `session_id`, `device_id`, `boot_id`, `seq` (v2 adds `request_id`). The ACK deadline for each frame is 5 s after it was sent. If the check passes, `acked` increases by 1.
12. The board sender task takes a result. Results that are already 2 s old are dropped. The rest are written to the subscriber within their remaining freshness. This 2 s limit covers only waiting on the board. Bytes already handed to TCP/TLS cannot be recalled, and the board does not learn whether the phone received them.
13. The phone assembles the bytes into complete frames and validates the fields, `session_id`, `result_id`, label and confidence. The display state then checks the session generation and deduplicates. If all pass, `Received` increases by 1 and the result is saved as the latest result. The phone's own 2 s display window starts when it receives the result.
14. The Unity main thread polls the display text every frame. In the Week 7 export the call is `Week7CopyDisplay(buffer, 2048)`; new game code calls `CommsCopyDisplay`; both are the same implementation. The text is copied only when it has changed. The Week 7 export writes it into the existing text label. The text holds only the latest result, so results that arrive between two polls can be overwritten. It is a status display, not a game input. The planned `CommsNextResult` will hand out results one at a time, each result that is not dropped at most once (section 7.3 of the hand-off document); it does not exist yet.
15. Normal end: the laptop stops notifications, reads the final source statistics, drains the queue and the outstanding ACKs, closes TLS, and writes `report.json`.

In step 10 the result is queued first and the ACK is sent after it. The two travel on different connections. Their arrival order is not guaranteed.

The text in step 14 has four lines (`DisplayMailbox.swift:15-18`):

```text
Communications • DUMMY inference
<status>
<gesture>  |  <result_id>  |  confidence 1.0      (reads No live result when there is no current result)
Received: <N>
```

**Failure paths**

| What happens | What the system does | What it leaves behind |
|---|---|---|
| BLE authentication has not completed | The firmware sends no notification. The laptop reports `authenticated Windows bond required; run laptop.windows_pairing first` (`laptop/windows_pairing.py:25`) and retries after back-off. | Firmware `security_suppressed`; laptop `ble_errors` |
| MTU below 35 | The firmware does not send. The laptop rejects the connection (`laptop/bridge.py:719-720`). | Firmware `mtu_suppressed`; laptop `ble_errors` |
| The board still runs Week 7 firmware (source statistics magic is not `LCS1`) | When the laptop reads source statistics it reports `invalid source statistics magic; flash this board with the current firmware` (`laptop/source_audit.py:50-51`). This board is not subscribed. The dual-board capture ends after 30 s with `startup:TimeoutError` (`laptop/dual_bridge.py:161-171`). | `source_stats_errors`; a startup failure in the report |
| Packet magic is not `LC` (only single-board tools that do not read source statistics get here) | Decoding fails with `invalid sensor packet magic; expected LC` (`common/sensor.py:77-78`) | `malformed` |
| Laptop queue full | Drops the oldest entry | `queue_dropped` |
| A sample stays on the laptop for more than 2 s | Dropped, not sent | `stale_dropped` |
| Tunnel drops, TLS error (including an expired certificate), ACK timeout, mismatched ACK | Close this TLS connection. Frames whose write was already attempted are counted as ambiguous drops and are not resent. Reconnect after back-off. | `transport_errors` for every one of these. An ACK timeout or a mismatched ACK increments both `ack_errors` and `transport_errors`. A TLS connect or handshake failure increments only `transport_errors`. Frames whose write was attempted count in `ambiguous_dropped`. |
| An ingest connection is idle for more than 5 s (for example, a glove drops out and reconnects) | The board closes the connection. The laptop's next frame fails on the old connection and is handled as in the row above. | Board `rejected`; laptop as in the row above |
| A glove's BLE link drops without a reboot | The laptop discards that glove's queued samples and reconnects after back-off (`laptop/bridge.py:113-120,910`). While disconnected the glove makes no samples and `seq` does not advance. Nothing is resent. | `disconnects`; `callback_generation_dropped` (and `generation_dropped` for a sample the writer had already taken). The discarded samples show as a `seq` gap; the disconnected time shows only as a jump in `uptime_ms`. |
| ESP32 reboots | `boot_id` changes and `seq` restarts at zero. The laptop scans, connects and subscribes again. | `new_boots`, `disconnects`; this capture does not count as clean |
| The board receives a bad frame, wrong fields or a wrong `session_id` | It closes the connection at once. It sends no error message and writes no log. | `rejected` (visible only in the metrics printed when the service stops) |
| v2: same identity with different content, `seq` not increasing, namespaces or commands exhausted | Same as above | `rejected` |
| No subscriber | The result is dropped. `INGEST_ACK` is still `accepted`. | `disconnected_results`; event `result_no_subscriber` |
| The subscriber reads slowly | When the queue is full, the oldest is dropped; results 2 s old are dropped. If a write does not finish in what is left of the 2 s, the board ends that subscription and abandons what is queued; the phone reconnects | `result_drops`, `result_stale`; events `result_send_failed`, `result_abandoned` |
| A second subscriber connects | The old subscriber is closed; unsent results in its queue are abandoned | `replaced`; events `subscriber_replaced`, `result_abandoned` |
| The phone finds a host public key mismatch, a rejected password, a CA/certificate/host name/validity check failure, or a protocol error | Terminal: no automatic retry; the passwords are cleared (`CommsClient.swift:186-206`) | Status `Disconnected: <reason>; correct setup and reconnect`. For TLS and protocol failures the reason text is `SSH, TLS or protocol verification failed` |
| The phone connection closes, the 10 s deadline passes, a partial frame, or `SUBSCRIBED` takes more than 5 s | Reconnects after back-off and subscribes again. Each reconnection logs in to both SSH hops with the passwords again, with no limit on the number of attempts. | Status `Disconnected: <reason>; retrying`, where the reason is `connection closed`, `connection deadline exceeded` or `frame deadline exceeded` |
| The phone locks or the app goes to the background | Disconnects at once and clears the passwords. After returning to the foreground, the user must tap Connect again. | Status `Paused — return and connect again` |
| A ninth connection reaches the board | Closed at once | `client_limit` |
| A board listener task dies | The process exits with a non-zero code | Log `listener task failed` |

## Why it is designed this way

The design records cited in this section are all under `docs/archive/`, which exists only on the fork. The text uses short names. "Selected design" is `docs/archive/design/week7-selected-design-2026-09-06.md` (cited by item number). "Architecture draft" is `docs/archive/design/architecture-and-interface-draft-v0.1.md` (cited by section number). "Dual-ESP spec" is `docs/archive/design/specs/2026-09-17-dual-esp-reception.md`. "iOS design spec" is `docs/archive/design/specs/2026-09-14-ios-visualizer-design.md`. Rejected approaches are listed only as history. They are not fallback options.

1. **Every client dials out; services bind only to loopback; access goes through SSH channels.** Reason: behind the NUS firewall, outsiders can reach the Ultra96 only through the VPN and `stujump`, by SSH on port 22. The laptop and the phone are not on the allowlist, so nobody can connect in to them. Rejected: the phone as a server waiting for connections (the teammate's original port 5005 approach); the laptop connecting directly to the phone; opening Ultra96 application ports to the outside; SSH reverse forwarding `-R`; the laptop relaying results. Records: Architecture draft sections 3 and 6; Selected design item 12.
2. **The phone connects to the board itself, not through the laptop.** Reason: the phone owns its whole route, so results do not depend on the laptop being online. The laptop is only the input relay. Records: Architecture draft sections 3 and 5; the Selected approach section of the iOS design spec.
3. **TLS inside SSH, with a fixed host name.** Reason: SSH makes the board reachable. TLS, with a dedicated CA and a fixed name, confirms that the client reached the right service, and the check is not relaxed even for `127.0.0.1`. Rejected: plaintext inside the tunnel; skipping the host-name check; mutual certificates (SSH already authenticates access). Records: Selected design item 11; Architecture draft sections 10.2 and 10.3.
4. **Input and results use two ports and two connections. ACKs go only to the laptop; results go only to the subscriber.** Reason: the phone fetches its own results; the laptop is not a result relay. Rejected: the laptop relaying `GESTURE_RESULT`. Records: Selected design items 7 and 9; Architecture draft section 3.
5. **No retransmission and no replay; bounded queues; 2 s freshness.** Reason: a stale gesture that is resent would be treated as a new game action. Bounded queues stop a disconnection from piling up data without limit. Rejected: offline buffering on the ESP32; automatic resend after a failure; replaying history to a late subscriber. Each 2 s limit bounds waiting in one segment only (the laptop queue, the board queue plus the write into the phone's connection, the phone's display window counted from receipt). None of them is an end-to-end latency bound, and the board's limit is not a promise that the phone receives a result. Records: Selected design items 4, 9 and 10; Architecture draft section 11; Dual-ESP spec.
6. **One independent channel per board.** Reason: if one board loses power or hangs, the other continues. In the power-loss test on 2026-09-28, while the right board was powered off and recovering, all 111 packets from the left board were ACKed. Records: Dual-ESP spec; the Physical power loss section of `docs/archive/test-evidence/co-live-deployment-2026-09-28.md`.
7. **One subscriber; a newcomer replaces the old one.** Reason: V1 has one phone, and the result stream always has exactly one owner. V1 does not support multiple phones or per-user routing; the Architecture draft lists that as a later extension goal. Records: Selected design item 9; Architecture draft section 13.
8. **4-byte big-endian length prefix plus strict JSON; close the connection on any error, with no resynchronisation.** Reason: TCP has no message boundaries. After a bad frame, the next frame cannot be found reliably. Rejected: newline delimiting; WS/WSS; guessing the alignment after an error. Records: Selected design items 5 and 15.
9. **BLE uses Secure Connections + passkey + bond, with no extra application-layer encryption.** Reason: an authenticated BLE link plus SSH/TLS already covers the whole path. Adding HMAC/HKDF/AES-GCM would bring in a key and nonce protocol that nobody has reviewed. Rejected: application-layer HMAC/AES-GCM; automatic downgrade. Records: Selected design items 13 and 14.
10. **BLE, not Bluetooth Classic.** Reason: this choice was made and tested long ago. Settings of 50 Hz and 70 Hz both ran clean in the 2026-09-28 tests, with the 32-byte dummy packet. "70 Hz passed" means the 70 Hz setting, which delivered about 66 packets/s per board. Real 38-byte data has not been measured. Records: `docs/archive/test-evidence/co-live-deployment-2026-09-28.md`; section 5, item 15 of the hand-off document.
11. **The laptop uses an explicit `ProxyCommand`, not `-J`.** Reason: strict host-key checking, timeouts and `BatchMode` can then apply to each hop separately. Rejected: `-J`. Records: Selected design item 18.
12. **The phone uses in-app SSH (`direct-tcpip`) and opens no port on the phone.** Reason: the phone owns its whole route and does not depend on the laptop. Rejected: a TLS server listening on port 5005 on the phone (it requires others to connect in to the phone); iSH/Termux foreground forwarding; changing only the standalone C# script (that cannot change the already-exported app). Records: the Selected approach section of the iOS design spec.
13. **Host public keys and the CA fingerprint are pinned in source; no trust on first use.** Reason: on the phone there is no step where a person checks `known_hosts`. Cost: replacing the board or the CA requires a source change and an app rebuild. Records: the Security and setup section of the iOS design spec.
14. **Passwords live only in memory; leaving the foreground disconnects.** Reason: the on-site route uses password authentication. Keeping passwords off disk means there is no credential file to manage. It also avoids depending on iOS background survival, which has not been verified. Records: the Security and setup and the Protocol and lifecycle sections of the iOS design spec.
15. **The `device_id` + `boot_id` + `seq` triple; `seq` is assigned before submission; separate read-only source statistics.** Reason: after a reboot the sequence restarts at zero without being confused with old data. A failed submission does not hide a gap. Losses at the start and end of a capture can also be reconciled. Records: Selected design item 4; Dual-ESP spec. Selected design item 4 said at the time "increment only on a successful submission". The current code assigns `seq` before submission. Follow the Dual-ESP spec and the code.
16. **ACK window 32.** Reason: on the remote route, a single ACK wait measured about 2.4 s. Waiting for each ACK in turn would push later samples past the 2 s freshness. Freshness itself is not relaxed. Stop-and-wait remains available as window 1. Records: the "Implementation notes — bounded ACK window, 2026-09-19" section of the Dual-ESP spec; the measured numbers are in section 5, item 6 of the hand-off document.
17. **`session_id` is configuration, not a secret.** Reason: SSH handles access control. Records: Selected design item 6.
18. **Evidence is graded, and the levels do not substitute for each other.** Reason: ACKs and phone results travel on two independent connections. In a 60 s run on 2026-09-21, all 1203 inputs were ACKed, but the phone received only 1094, which is 109 fewer. The cause is still unknown. Records: Selected design items 16 and 27; section 7 of `docs/archive/reports/week7-system-technical-report.md`; `docs/archive/test-evidence/dual-esp-iphone-test-2026-09-21.md`; `docs/archive/test-evidence/phone-recovery-test-2026-09-21.md`.
19. **The board runs one process, uses only the standard library, is deployed in the user's own folder, installs no system service and uses no sudo.** Reason: the board is shared, so nobody else's environment is touched. The start script starts the service only when both ports are free, and it never stops or kills an existing process (`tools/demo_service.py:35-49`). Records: Selected design items 7 and 26.

## Caveats and known limitations

**Week 7 names that stay unchanged**

| Name | Location | Why it stays |
|---|---|---|
| TLS host name `ultra96.week7.internal` | `common/tls.py:4`, `tools/generate_comms_pki.py:24`, `CommsClient.swift:142`, `phone/receiver.py:16`, `phone/unity/CommsPhoneCore.cs:357` | It is in the server certificate, and every client checks against it. Renaming it requires a new certificate and an app rebuild. |
| `Week7Start`, `Week7CopyDisplay`, `Week7Stop` | `DisplayMailbox.swift:57-67`, `ios-visualizer/tools/patch_export.py:25-28` | The exported Unity project links against these three names. Part of the Week 7 receiver. |
| iOS reads of the old folder: `Application Support/Week7`, `week7-ca.pem` | `IntegrationController.swift:18`, `Configuration.swift:61-72` | The old folder is read only when the new folder has no file. Saves write only to the new folder. Part of the Week 7 receiver. |
| App display name `Week 7 Visualizer` | `ios-visualizer/tools/configure_xcode.py:160` | Part of the Week 7 receiver. |
| Comments and the temporary-file prefix `.week7-receiver-` in the patch script | `ios-visualizer/tools/patch_export.py:25,31,190` | Part of the Week 7 receiver. |
| Board deployment folder `/var/tmp/cg4002-week7-…-20260907` | `tools/demo_service.py:11-12` | It is a real folder on the board, and the existing deployment lives there. |
| Laptop CA default path `~/.codex/private/cg4002-week7-20260906/ca-cert.pem` | `demo.py:49-50` | It is a real folder on the laptop. On other machines, pass `--ca`. |
| iSH SSH config file name `week7-ish-password.conf` and host alias `week7-ultra96` | `phone/ish_control.py:191-195` | A source comment states that the phone's iSH was set up with these two names, and nothing in the repository creates new names. In the same file, the script's own folder name is now `comms-control` (`phone/ish_control.py:235,302`). |

**Certificates**

- The server certificate is valid for only 30 days. Only the copy kept on the laptop was checked: it expired at `2026-10-06 15:11:29 UTC`. That copy is the certificate deployed to the board in September. The CA is valid until 2027-09-06, and its SHA-256 equals the fingerprint recorded in the phone source.
- The 2026-09-28 deployment reused the existing TLS files (`docs/archive/test-evidence/co-live-deployment-2026-09-28.md`). The repository has no record of a certificate change after that. Nobody has checked the board's actual state, so the board's certificate is not verified as expired.
- If the board still has this certificate: the service starts normally, but every laptop TLS handshake fails. Only `transport_errors` increases, and no ACK arrives. The iPhone shows `Disconnected: SSH, TLS or protocol verification failed; correct setup and reconnect` and does not retry automatically.
- How to check: with the tunnel open, run `openssl s_client -connect 127.0.0.1:18889 -servername ultra96.week7.internal` on the laptop; or run `openssl x509 -in <deployment folder>/tls/server-cert.pem -noout -dates` on the board.
- Renewal: `--renew-server-from <CA_DIR>` of `tools/generate_comms_pki.py` (function `renew_server_identity`, `tools/generate_comms_pki.py:75-100`; the command line is at `:135-143`). It reads `ca-cert.pem` and `ca-key.pem` from `CA_DIR` and confirms that the private key belongs to that CA certificate. It refuses when the CA has less than 30 days of validity left. In a new, empty folder (which must be outside any Git repository) it writes a new `server-key.pem`, a 30-day `server-cert.pem` and a copy of `ca-cert.pem`. The CA itself does not change, so neither the CA fingerprint in the phone source nor the laptop's `--ca` needs to change. The full steps are in section 6.3 of the hand-off document. Tests: `test_renewed_server_certificate_keeps_the_ca_and_is_trusted_by_existing_clients` and `test_renewal_refuses_a_mismatched_key_an_occupied_folder_and_git` in `tests/test_transport.py`.
- Running the certificate tool without `--renew-server-from` generates a new CA and a new server certificate together. Then the CA fingerprint in the iPhone source must change, the app must be rebuilt and reinstalled, and the laptop's `--ca` must change too.

**Laptop SSH prerequisites**

- Both hops use `StrictHostKeyChecking=yes` (`tools/ssh_tunnel.py:26-28`). No code in the repository writes `known_hosts`. On a different laptop, `demo.py tunnel` and `demo.py service` exit at once with a host-key verification failure until both hosts' public keys are in the local `known_hosts`. The two ed25519 public keys to check against are in the phone source, `Configuration.swift:10-11`.
- The tunnel command calls a program named `ssh` directly (`tools/ssh_tunnel.py:29,33`). The OpenSSH client must be on `PATH`.
- Each endpoint must match `user@host`. User names allow only letters, digits, underscore and dot; a user name with a hyphen is rejected. Host names allow hyphens (`tools/ssh_tunnel.py:20-22`).
- Timeouts for the interactive command: `ConnectTimeout=20` on the proxy hop and `ConnectTimeout=60` on the target hop, which leaves time to type the password. In supervised mode both hops use 10 (`tools/ssh_tunnel.py:30,35`). Both hops set `ServerAliveInterval=15` and `ServerAliveCountMax=3`.
- `demo.py tunnel` starts one ssh child process and does not restart it after it exits (`demo.py:119-130`). `python -m tools.ssh_tunnel --run` does restart it, with a back-off that doubles from 0.5 s to 5 s and never resets (`tools/ssh_tunnel.py:52-80`). It forces `BatchMode=yes`, so it works only with key or agent authentication; passwords cannot be typed.
- The `--jump` and `--target` defaults of `demo.py tunnel` are the original operator's accounts (`demo.py:40-41`). Anyone else must pass them explicitly. The account, host and board path for `demo.py service` are hard-coded in `tools/demo_service.py:11-12,17-18`, and its command line has only `--start` and `--session-id`. Anyone else must change the source to use it.

**Phone**

- The jump host, the board host name, the host public keys, the CA fingerprint and the session ID are all compiled into the app. The laptop's `--jump`, `--target`, `--ca` and `--session-id` do not affect the phone.
- The app must stay in the foreground. Locking the screen or switching to the background disconnects and clears the passwords.
- The phone has no SSH keep-alive or heartbeat. When the network fails silently, the phone notices only when the operating system reports an error.
- Automatic retry on the phone means logging in to the jump host and the board again with the passwords, after a delay that starts at 0.5 s and doubles up to 5 s (reset after a result arrives), with no limit on attempts. The phone treats a service that is not running, a session mismatch and being replaced by another subscriber all as a closed connection, and retries. When the service is not ready, tap Disconnect first.
- One Connect is one counting session. Tapping Connect again resets `Received` to zero.

**Board**

- There is only one subscriber at a time. Running `laptop/phone_simulator.py` or a remote rehearsal replaces the phone.
- Results produced while there is no subscriber are dropped and never resent later. So get the phone to `Subscribed` before starting a capture.
- Deduplication state is only in memory. After a service restart, old inputs may be accepted again.
- v2 records at most 128 `(device_id, boot_id)` pairs. Each glove reboot uses one. Once they are used up, new boots are rejected and the service must be restarted. The reason for the rejection is not logged. The operator sees only that a freshly powered glove never connects, while the laptop's `ack_errors` and `transport_errors` keep growing.
- The board closes an ingest connection after 5 s idle. The 2026-09-28 power-loss test recorded the consequence: the first sample after the affected glove reconnected got no ACK and was counted as one ambiguous drop.
- The service is not a system service and has no automatic restart. How it runs depends on how it was started. Started with `demo.py service --start`, it runs in the foreground of an SSH session (`ssh -tt`, `tools/demo_service.py:15-26,50`); closing that terminal, the laptop sleeping or the VPN dropping makes it exit. The process recorded on the board on 2026-09-28 was started differently. The untracked `.week7-local/co_deploy.py` launched it in the background with `subprocess.Popen(..., start_new_session=True)` (`.week7-local/co_deploy.py:85`), with `--session-id week7-demo` and an `--event-log-dir` under `BOARD_ROOT/evidence/`. Its output goes to a log file under `BOARD_ROOT/evidence/`, and its PID is in `BOARD_ROOT/evidence/server.pid` (`.week7-local/co_deploy.py:107,111`). That process does not depend on any SSH session and may still be running. During a redeploy, find the old process through that PID file and through the listeners on 8888 and 9999 (`python demo.py service` prints `ss -ltnp`). `demo.py service --start` refuses to start while either port is in use, and it never stops an existing process.
- The board service logs one INFO line for every accepted input (`ultra96/server.py:262-263`). With both gloves at 50 Hz, that is about 100 lines per second. On the `demo.py service --start` path they all go through the foreground SSH terminal. The process started by `co_deploy.py` writes them to its log file under `BOARD_ROOT/evidence/`.
- `demo.py service --start` always `cd`s to the board's 2026-09-28 source snapshot `source-co-v2-20260928T122047Z` before starting (`tools/demo_service.py:11-12,33,50`). No tracked file deploys the current source to the board. The `co_deploy.py` used for the September deployment exists only in the untracked local `.week7-local/` (section 12.4 of the hand-off document). Since the import (`caf330e`), the repository's `ultra96/` has changed only in `d227a84`, which changed two default session IDs. `common/wire.py` and `common/tls.py` have not changed since the import. The repository cannot confirm whether the board snapshot is byte-for-byte the same as the imported version. The approach in section 6.3 of the hand-off document is: upload a new snapshot of `common/` and `ultra96/`, then change `BOARD_SOURCE` to the new folder. Whenever `ultra96/` changes in future, deploy it by hand first, then change `BOARD_SOURCE`.
- The session ID for `demo.py service --start` comes from `--session-id`, then the environment variable `LTC_COMMS_SESSION`, and is `ltc-comms` when neither is set (`demo.py:70-71,292`; `tools/demo_service.py:29-30,50,54`). It is printed before the start (`tools/demo_service.py:59`).

**End to end**

- No timestamp runs through the whole path. The 2 s freshness is each segment's own holding time, not end-to-end latency. On the board it limits how long a result waits in the queue and in the write into the phone's connection (`get_timed`, `_send_results` in `ultra96/server.py`); it says nothing about whether or when the phone receives the result. The phone has its own 2 s display window, counted from when it received a result.
- There is no guarantee of absolutely zero loss. Conclusions can only be drawn from the reconciliation of a specific capture. Reconnects can leave `seq` gaps (see "Technical constraints on the teammate interfaces" above).
- The phone status `Subscribed` means only that the subscription handshake with the Ultra96 succeeded. It does not prove that results are flowing.
- Only the labels `REST`, `FIST`, `OPEN`, `POINT` pass, and the confidence must equal 1.0. Four places check this: `ultra96/protocol.py:4,78-83`, `Protocol.swift:54-62`, `phone/receiver.py:125-130`, `phone/unity/CommsPhoneCore.cs:48-63`. Unless they change, the model's first real label makes the phone disconnect terminally.
- Opening up the labels takes more than changing the four validators. All four also require `device_id` to be 1 or 2, and `result_id` to equal the result's own `device_id:boot_id:seq` (prefixed `cmd:` for commands). The board's results are currently generated by `ultra96/server.py:264-267` itself. The Swift `GestureResult` has no `confidence` field, and the display text hard-codes `confidence 1.0` and `DUMMY inference` (`DisplayMailbox.swift:16,18`). Section 7.2 of the hand-off document proposes (final when Wen Ree confirms) that the planned exit `emit` carries the identity of one sample the result used (usually the newest, a different sample for each result), and Communications builds `result_id` from it. These changes are the content of section 8, step 5 of the hand-off document, which also adds the planned `confidence` field to the Swift `GestureResult` and the planned per-result function `CommsNextResult`. None of it is built yet.
- A leftover `LTC_COMMS_SESSION` in the terminal affects `demo.py run`, `live` and `service --start` together, but not the phone. Documents from the transition period told operators to set `LTC_COMMS_SESSION=week7-demo`. If it is left over, the laptop and a newly started service both use `week7-demo`, and `CAPTURE PASSED` appears as usual, while the phone stays at `Disconnected: connection closed; retrying`.
- `demo.py` uses local port 18889. Running `laptop.dual_bridge` or `tools.ssh_tunnel` directly defaults to 18888. The tunnel and the capture must use the same port.
- Both boards advertise the same name. They are told apart by Bluetooth address and by the `device_id` in the packet.
- The laptop side supports only Windows (pairing uses WinRT; `flash.py` assumes `COMx` serial ports and PlatformIO's Windows paths).
- Do not run `python -m pytest` without paths from the repository root. It collects `fpga/hls/export_conv1d_test.py`, which rewrites a tracked file as soon as it is imported.

**Documents that disagree with the code (follow the code)**

- The Architecture draft says `stfjump`. The code and the site use `stujump`.
- The Architecture draft's example writes the local port as 8888. The code uses 18888 and 18889.
- The Architecture draft says "no SSH `-R`". `phone/ish_control.py:99` used `-R` for a temporary maintenance channel. It is a historical script and is not on the application path.
- The iOS design spec says "the first result waits 30 s". The current code sets no deadline for idle time after subscribing.
- The archived technical report (`docs/archive/reports/week7-system-technical-report.md`) describes 5 characteristics, `Week7*` module names and `seq % 4` labels. The current code has 7 characteristics, `Comms*` module names and random v2 labels.
- `tools.generate_week7_pki`, `tools.rehearse_week7` and `Week7Server` in `docs/week7-runbook.md` no longer exist. The current names are `tools.generate_comms_pki`, `tools.rehearse_comms` and `CommsServer`. That runbook was not changed in the 2026-10-14 documentation update and is still out of date.
- `vis/README.md` says "the phone runs a TLS server on port 5005". That is the opposite direction to the settled network model. No Communications code connects to 5005.

**History and removals**

- On 2026-10-14 the compatibility with the old Week 7 version was removed: commits `28db0b3` and `b414696`, merged into local `main` by `5db56ad`, with the documents brought in line by `798438d`. Before the history rewrite of 2026-10-14 these were `d2fff21`, `5f2c12a`, `4c2b078` and `7479e2e`, with the same file contents (section 6.2 of the hand-off document). What was removed: acceptance of the old packet magic `W7` and the old statistics magic `W7S1` by the laptop decoder, the source statistics parser and the firmware command validation; the session ID `week7-demo` hard-coded in the board service start script; and the fallback reads of the old local folder `.week7-local` (board map, finding the latest capture).
- Current behaviour: `common/sensor.py:13,77-78` accepts only `LC`; `laptop/source_audit.py:13,50-51` accepts only `LCS1`; the command payload in `firmware/esp32/include/comms_control.h:124` accepts only `LC`, and `firmware/esp32/test/host_control.cpp:66-72` asserts that `W7`, `WC` and `L7` all return status 1; `tools/demo_boards.py:9,21-24` reads only `.comms-local/boards.json`; `demo.py:269-275` looks for `B07-*` only under `--output-root`; when there is no map file, `flash.py --boards` prints `Using built-in defaults; flash.py records new upload order.` (`flash.py:151-154`).
- `README.md`, `ios-visualizer/README.md`, `ios-visualizer/NATIVE-INTEGRATION.md` (`28db0b3`, `b414696`) and `docs/communications-quickstart.md`, `docs/co-protocol-v2.md`, `docs/B07-CO-protocol-explained.zh-CN.md` and `docs/integration-handoff.md` (`798438d`; that file has since moved to `docs/archive/design/integration-handoff-2026-10-08.md`) were rewritten; they mention the old magic values only as "rejected". The only document still out of date is `docs/week7-runbook.md`.
- The local `.comms-local/boards.json` already exists, with the same addresses as the old map, so the board map works without reflashing. `.comms-local/` holds no capture folder yet.
- The 17 old captures under `.week7-local/` all hold `W7` packets. Report review decodes the `raw_hex` in `packets.jsonl`, and the decoder now accepts only `LC`. So even `demo.py report` with the full path gives `CAPTURE NOT PASSED: packet evidence could not be verified.` (`demo.py:205-208`). To review this old evidence, go back to commit `880abba` (the team `main`; it was `ec398b6` before the history rewrite of 2026-10-14, with the same files, and its decoder still accepts `W7`). The last local capture (2026-10-01) still has packet magic `W7`, which shows both boards still ran the old firmware at that time.
- The earlier phone routes (iSH plus the Python receiver; Android plus Termux plus C#) remain in `phone/` only as reference implementations.

When one redeploy round is not finished, the combinations behave as follows. The current deployment state: the left board was flashed with the current firmware and verified on 2026-10-14; the right board still has the Week 7 firmware; the board service should still be the 2026-09-28 snapshot with session `week7-demo` (the background process started by `co_deploy.py`, see "Board" above); the iPhone has the Week 7 build of the app (section 6.3 of the hand-off document).

| Which end was not updated | Symptom | Basis |
|---|---|---|
| The board still has Week 7 firmware | When the laptop reads source statistics it reports `invalid source statistics magic; flash this board with the current firmware`. That board never becomes active, and the capture ends with `startup:TimeoutError`. | `laptop/source_audit.py:50-51`, `laptop/bridge.py:737-752`, `laptop/dual_bridge.py:161-171` |
| The board service still uses `week7-demo` | `SENSOR_BATCH` and `SUBSCRIBE` are rejected for the session mismatch, and the connection is closed at once. The laptop records `ack_errors` and `transport_errors`; `received` keeps growing while `acked` stays at 0. A current-build phone keeps showing `Disconnected: connection closed; retrying`. | `ultra96/protocol.py:50-51`, `ultra96/server.py:226-227,248,310`, `laptop/bridge.py:617-621`, `CommsClient.swift:186-191,208` |
| The phone still has the app installed in Week 7 | Its session ID is compiled into the app (`week7-demo`). A service started with `ltc-comms` closes its subscription. The app must be rebuilt from the current source and reinstalled on a Mac. | `IntegrationController.swift:74` (the session ID in the current source) |

## How to run and verify

**1. Checks that need no hardware**

```powershell
python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider

python -m tools.generate_comms_pki --output-dir <empty folder outside any Git repository>
python -m tools.rehearse_comms --pki-dir <same folder> --duration 30 --target 100
python -m tools.comms_demo packet
```

- The second group of commands generates single-use local rehearsal certificates, then starts a local board service, a bridge and a subscriber. It prints one line of JSON. `passed` should be `true`. `topology` is `local TLS only; SSH, remote Ultra96 and real Phone not exercised`.
- Generating certificates needs `cryptography` from `requirements-dev.txt`.
- `python -m tools.comms_demo packet` only prints an example packet and its network frame. It does not use the network.

**2. Full path on real hardware**

First confirm that all three ends have been updated to the current source as described in section 6.3 of the hand-off document, and that the server certificate has not expired. Only olsonwangyj may log in to the jump host and the Ultra96, in their own terminal.

```powershell
python demo.py service
python demo.py tunnel --jump '<jump-host user>@stujump.comp.nus.edu.sg' --target '<board user>@makerslab-fpga-35.ddns.comp.nus.edu.sg'
# iPhone: tap Communications Connect, wait for Subscribed, note Received
python demo.py run --ca '<path to ca-cert.pem>'
python demo.py report
```

| What to verify | How to check it |
|---|---|
| The services bind only to loopback | `demo.py service` prints `ss -ltnp` from the board. The local address of 8888 and 9999 must be `127.0.0.1`. |
| The board received the input (level 3) | The output ends with `CAPTURE PASSED: physical ESP input through Ultra96 ingestion ACKs.` (`demo.py:210`). For each device, Generated = Received = ACKed, and MissingBLE and MissingACK are both 0. |
| The phone received the results (level 5) | The increase of `Received` on the iPhone equals `Phone expected increase` in the output (the sum of both boards' `generated` plus the completed commands, `demo.py:209-211`). This is compared by hand; the program does not check it. |
| Identities match | In this run's `packets.jsonl`, find the `sensor` and `sensor_ack` records with the same `device_id`, `boot_id` and `seq`. |

`demo.py service --start` works only for the original deployment: it uses a fixed account and a fixed source folder.

**3. Checks of the security model**

- TLS negative cases: `test_tls_rejects_wrong_hostname_wrong_ca_and_plaintext` in `tests/test_transport.py`.
- Certificate renewal: the two `renew` tests in `tests/test_transport.py` (see "Certificates" above).
- Effective two-hop SSH configuration: `tests/test_ssh_trust.py` (expands the configuration with `ssh -G`; no network).
- On the board, "write complete does not mean the phone received it": `tests/test_server_observation.py`.
- Phone-side host public keys, passwords, CA, host name and expired certificates: run `swift test --package-path ios-visualizer/CommsNative` on a Mac.
- Certificate validity and fingerprint: `openssl x509 -in <certificate> -noout -fingerprint -sha256 -dates`. The CA fingerprint should equal the value in `Configuration.swift:12`. The server certificate is `tls/server-cert.pem` in the board deployment folder.

**4. Remote rehearsal with the desktop subscriber (replaces the phone's subscription)**

```powershell
python -m tools.ssh_tunnel
python -m tools.ssh_tunnel --local-port 19999 --remote-port 9999
python -m tools.rehearse_remote_comms --ca <ca-cert.pem> --confirmed-remote-topology --target 100 --duration 45
```

- The first two commands only print tunnel commands. Run each printed command in its own terminal and keep it open.
- The third command first completes TLS and `SUBSCRIBED`, then starts sending data, and finally reconciles ACKs and results one by one.
- `--confirmed-remote-topology` only records the operator's statement. Without it, the report says `existing local forwards; remote provenance unverified`.
- Do not run it during a demo or while testing with the phone. It replaces the phone.
