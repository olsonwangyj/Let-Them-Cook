# Week 7 Communications Test-Gated Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Demonstrate a real DFR0478 ESP32 sending deterministic dummy data over BLE/GATT to the Laptop, the Laptop forwarding it over TLS/TCP through its own SSH local forward to Ultra96, and Ultra96 delivering a deterministic result to a real Phone running the teammate-provided minimal Visualizer.

**Architecture:** Two tracks establish the BLE and Ultra96 paths independently. The Laptop bridge joins them only after both paths pass their own tests. A desktop `PhoneSimulator` temporarily validates the Gateway path, but the final Week 7 demonstration requires a real Phone and a separate BLE security gate.

**Tech stack:** DFRobot DFR0478 FireBeetle ESP32, PlatformIO, proposed Arduino framework, BLE/GATT, Windows, Intel Wireless Bluetooth, Python/Bleak, TLS/TCP, OpenSSH `-L`, Ultra96, desktop `PhoneSimulator`, and later the teammate-provided Unity receiver.

**Spec:** `docs/architecture-and-interface-draft-v0.1.md`

## 1. Status and constraints

**Confirmed:**

- ESP32-to-Laptop uses BLE/GATT.
- ESP32 is the BLE Peripheral and GATT Server.
- Laptop is the BLE Central and GATT Client.
- ESP32 does not use Wi-Fi.
- Laptop is the TLS/TCP application client of the Ultra96 Ingestion Server.
- Laptop creates its own SSH local forward using uppercase `-L` through `stfjump.comp.nus.edu.sg`.
- Ultra96 application services bind only to `127.0.0.1`.
- Ultra96 sends `GESTURE_RESULT` directly over the eventual Phone connection; the Laptop is not the result relay.
- The real Phone must participate before the final Week 7 demonstration and must use its own independent SSH `-L`.
- There is no direct Phone-to-Laptop application connection and no SSH `-R`.

**Proposed test defaults:**

- Arduino framework and 115200-baud serial monitor for the first DFR0478 test.
- A small diagnostic BLE counter before any sensor packet.
- Bounded real-time queues that drop the oldest stale telemetry when full.
- Four-byte big-endian length followed by UTF-8 JSON for Laptop-to-Ultra96 test framing.

**Still unresolved:**

- Final BLE UUIDs and `SENSOR_BATCH` layout.
- Sensor fields, widths, units, scaling, batch size, and final sampling rate.
- Final BLE pairing mode and characteristic security permissions.
- HMAC/HKDF/AES-GCM application-layer protection.
- Exact ports, TLS certificates, SAN/SNI identity, trust anchors, and mTLS.
- Phone inner protocol, mobile SSH implementation, registration, association, and routing identifiers.

Test-only formats, acknowledgements, trace fields, and routing shortcuts must remain clearly labelled and must not silently become production contracts.

## 2. Known environment and dependencies

| Item | Current status |
|---|---|
| ESP board | DFRobot DFR0478 FireBeetle ESP32, ESP-WROOM-32 |
| PlatformIO board ID | `firebeetle32` |
| ESP USB serial | CH340; actual Windows COM port to be detected |
| Laptop | Windows |
| Bluetooth adapter | Intel Wi-Fi 6E AX211 / Intel Wireless Bluetooth |
| Bluetooth USB ID | VID `8087`, PID `0033` |
| Bluetooth driver | `24.40.10.3` |
| Jump host | `stfjump.comp.nus.edu.sg`; `stujump` is treated as a probable typo unless an authoritative working command proves otherwise |
| Temporary simulator | Runs initially on the same Laptop using a separate application connection and, where required, a separate SSH `-L` |
| Unity receiver | Not yet implemented by the Visualizer teammate |

The written Week 7 rubric, final encryption criteria, AI ingestion contract, Phone platform, TLS credential design, and Unity protocol are important but do not block the reversible serial, BLE-counter, Bleak, MTU, or independent SSH-forward experiments.

Before Ultra96 testing, obtain the assigned Ultra96 hostname, relevant usernames, confirmation that normal SSH login works, and the applicable `stfjump` command. Never store passwords, private keys, VPN credentials, or unredacted secrets in the repository.

## 3. Dependency order

```text
Track 1 — real ESP and BLE
A. Board identification and serial smoke
→ B. ESP BLE advertisement and counter notification
→ C. Laptop Bleak scan/connect/subscribe/reconnect
→ D. Actual ATT MTU measurement
→ E. Dummy-packet proposal, approval, codec and live test

Track 2 — Ultra96 and result delivery with mock input
F. Ultra96 loopback echo/ingestion
→ G. Laptop SSH -L and TLS/TCP
→ I. Deterministic dummy result
→ J. Gateway and desktop PhoneSimulator

Join
E + G
→ H. Laptop BLE-to-Ultra96 bridge
H + I + J
→ K. Partial end-to-end rehearsal
→ L. BLE security and protected regression rehearsal
→ M. Real Phone/Unity and final Week 7 rehearsal
```

Track 1 and the mock-driven parts of Track 2 may proceed in parallel. Gate H is the join point; it depends on the approved real BLE packet path and working Ultra96 transport.

## 4. Gate summary

| Gate | Deliverable | Pass condition |
|---|---|---|
| **A** | DFR0478 serial smoke firmware | Correct COM port; build/upload succeed; five-minute stable output; reset and power cycle create a new boot ID and restart sequence/uptime |
| **B** | ESP advertises one test service and sends a small counter notification | Service and Notify characteristic are discoverable; submitted counter values are visible in ESP serial logs; connect/disconnect does not reboot the ESP unexpectedly |
| **C** | Windows/Bleak counter receiver | Scan→connect→discover→subscribe occurs in order; at least 1,000 counters received; gaps/duplicates reported; power-loss reconnect and ten-minute soak pass |
| **D** | Measured ATT MTU and notification boundary | Both endpoints' observations recorded; usable payload limit proven; an oversized value is rejected before sending and never silently truncated |
| **E** | Approved deterministic dummy packet and matching codecs | Format selected only after Gate D review; immutable `.bin`/`.json` vectors agree with ESP and Laptop; malformed and oversized packets rejected |
| **F** | Ultra96 loopback echo/ingestion server | Split/coalesced frames handled; malformed/oversized/partial frames rejected; service verified bound only to `127.0.0.1` |
| **G** | Laptop SSH `-L` plus TLS/TCP connectivity | 100 framed messages accepted and correlated in Ultra96 logs; tunnel failure/recovery works; invalid TLS identity fails without plaintext fallback |
| **H** | BLE-to-Ultra96 bridge | Bounded queue, visible stale/drop metrics, and one TCP writer; no unlimited growth or stale replay |
| **I** | Deterministic Ultra96 dummy result | Valid test input produces the expected unique result; invalid input produces none; test trace correlates input without defining Phone routing |
| **J** | Ultra96 Gateway and desktop simulator | At least 100 expected results received; malformed data and reconnect handled; second test connection does not become a Laptop result relay |
| **K** | Partial real-ESP end-to-end rehearsal | Ten-minute path works; ESP, SSH, ingestion, and simulator failures are tested separately; gaps and stale-data handling are visible |
| **L** | BLE pairing, bonding, link encryption, and protected regression | Approved protection state is verified; protected characteristic access and bonded reconnect pass; Gates C, E, and K pass again with security enabled |
| **M** | Real Phone and teammate Unity receiver | Phone uses its own SSH `-L` and displays/prints the result over the complete protected path; no topology violation is introduced |

## 5. Clarified BLE counter and Bleak sequence

### Gate A — Serial smoke

Only these files are authorized for the first implementation task:

- `firmware/esp32/platformio.ini`
- `firmware/esp32/src/main.cpp`

The firmware prints once per second:

```text
alive boot_id=<value> sequence=<value> uptime_ms=<value>
```

Proposed diagnostic semantics:

- `boot_id`: one 32-bit value generated at startup.
- `sequence`: starts at zero and increments once per status line.
- `uptime_ms`: monotonic milliseconds since the current boot.

Test steps:

- [ ] Detect whether PlatformIO and the CH340 driver are already available; if either is absent, stop and request installation approval.
- [ ] Detect the COM port by comparing Windows serial devices before and after connecting the DFR0478.
- [ ] Build and upload the serial-only firmware.
- [ ] Monitor continuously for five minutes.
- [ ] Test one reset-button restart.
- [ ] Test one complete USB power disconnect and reconnect.

Gate A deliberately excludes BLE, sensors, Wi-Fi, SSH, TLS, Ultra96, PhoneSimulator, and Unity.

### Gate B — ESP advertisement and diagnostic counter

Required order:

1. Add one project-specific test service.
2. Add one Notify characteristic containing only a diagnostic counter.
3. Start advertising the service.
4. Increment the counter when the ESP submits a notification.
5. Log submitted counter values over serial for later comparison.

Proposed diagnostic defaults are an unsigned 32-bit little-endian counter, starting at zero after boot, sent at 10 notifications per second. These apply only to the counter smoke test. The payload is not `SENSOR_BATCH` and does not define the production byte order, rate, or packet contract.

### Gate C — Laptop Bleak receiver

The Laptop must perform these operations in order:

1. Scan and obtain the intended BLE device from its advertisement.
2. Match the project test service instead of depending only on the display name.
3. Connect using the discovered device object.
4. Discover the expected service and Notify characteristic.
5. Subscribe and wait for notification setup to complete.
6. Keep the callback short: copy or enqueue bytes, then parse and log outside the callback.
7. Treat the first received counter as that connection's baseline.
8. Detect and log later gaps, duplicates, and out-of-order values.
9. Detect ESP power loss, then rescan, reconnect, rediscover, and resubscribe after restart.
10. Recognize the new ESP boot rather than treating the restarted counter as an in-session rollback.

The 1,000-counter test and ten-minute soak are separate observations. Record discovery, connection, disconnect-detection, and reconnection durations without treating the initial measurements as final performance requirements.

### Gate D — ATT MTU before packet design

- Record the negotiated MTU visible on both the ESP and Windows/Bleak sides.
- Prove the effective notification-value limit on the real connection.
- Test a safe value, the expected boundary, and one byte beyond the boundary.
- Reject oversize data before notification submission.
- Never depend on implicit fragmentation or accept a truncated value as valid.

Do not assume that `N=1`, eight `int16` values, or a complete header fits before this gate passes.

### Gate E — Approval before dummy-packet implementation

After Gate D, compare:

1. Keeping the provisional eight `int16` readings if the complete header fits safely.
2. A clearly labelled compact test frame with smaller test-sentinel fields.
3. Explicit application-layer fragmentation and reassembly only if necessary.

Obtain approval before implementing any option. The previously discussed 19-byte or `i8[8]` proposal is not selected. Golden vectors freeze only the approved Week 7 test format, not the final sensor contract.

## 6. Ultra96 and result-path rules

- Test the TCP framing parser locally before introducing SSH or TLS.
- Ultra96 ingestion and Gateway services bind only to loopback.
- Test the SSH `-L` path independently before joining it to BLE.
- Plaintext TCP is permitted only as an isolated development diagnostic; the deployed path remains TLS/TCP through SSH `-L`.
- The TLS client must validate the approved service identity even though its TCP endpoint is a Laptop loopback port.
- Replace generic request/response testing with 100 framed messages accepted and correlated in Ultra96 logs.
- A test-only ingestion ACK is allowed if clearly named and specified. It must not be called `GESTURE_RESULT`.
- `GESTURE_RESULT` flows from Ultra96 to the Gateway client, not back to the Laptop as a result relay.
- The desktop simulator initially runs on the same Laptop but uses a separate application connection and, for deployed-path testing, a separate SSH `-L`.
- The simulator validates only the temporary Gateway protocol; it does not validate mobile SSH, Unity, or real-Phone behavior.
- A source boot/sequence trace may be used for test correlation but must not become a Phone/user association or routing identifier.

For Gate H, provisionally use a configurable bounded queue and drop the oldest stale telemetry when full. Only one task owns writes to the Ultra96 TCP stream. Exact capacity and freshness thresholds are selected from measurements later rather than made prerequisites for Gate A.

## 7. Separate BLE security gate

Functional BLE is established first. Gate L is a separate approval and regression gate before the final real-Phone demonstration.

Minimum review scope:

- Pairing mode.
- Bond creation and storage.
- Link encryption.
- Characteristic authentication/encryption permissions.
- Reconnection using stored bonding information.
- Recovery after either endpoint loses or rejects a bond.

After approval, Gate L must:

- [ ] Establish the approved pairing and store a bond.
- [ ] Verify the active link's required encrypted/authenticated state rather than infer it from successful connection.
- [ ] Verify protected characteristic access follows the approved policy.
- [ ] Power-cycle the ESP and reconnect using stored bonding information.
- [ ] Restart the Laptop client and reconnect using stored bonding information.
- [ ] Exercise the documented missing/invalid-bond recovery path.
- [ ] Re-run the counter test, dummy-packet test, and partial end-to-end rehearsal with protection enabled.

HMAC, HKDF, and AES-GCM remain separate proposed application-layer mechanisms. They enter the Week 7 critical path only if the written rubric or a separate approved security decision requires them.

Laptop-to-Ultra96 TLS/TCP remains selected. Certificates, SAN/SNI identity, trust anchors, and mTLS remain unresolved until their dedicated review.

## 8. Final real-Phone gate

Gate M begins after the Visualizer teammate supplies a runnable minimal receiver.

Communications responsibilities are limited to:

- Inspecting and running that receiver.
- Documenting its required schema and transport.
- Keeping host and local port configurable.
- Connecting it to the Phone's own localhost-forwarded endpoint.
- Adapting the Ultra96 Gateway to the agreed raw TCP, WS, or WSS protocol.
- Supplying test messages and verifying the complete protected path.

The final Week 7 rehearsal must use the real ESP, real Laptop, real Ultra96, and real Phone. Real sensors, complete AR animation, marker detection, MediaPipe, game logic, and Unity UI design remain outside the Communications task.

## 9. Explicitly deferred

- Real IMU and flex-sensor integration.
- Final sensor representation, units, scales, and sample rate.
- A second physical ESP unless the rubric explicitly requires it.
- Two-glove synchronization, `TIME_SYNC`, `READY`, `START_AT`, and drift correction unless the written Week 7 criteria require them.
- Final `50 × 16` windows and real AI/FPGA inference.
- Multi-user behavior, Phone registration, association, subscription, and routing identifiers.
- Four concurrent ESP connections.
- HMAC/HKDF/AES-GCM unless separately approved.
- mTLS and production certificate rotation.
- Full Unity UI and AR behavior.

## 10. Gate evidence rules

- Record gate name, date, hardware/software versions, configuration, duration, expected result, and actual result.
- Store no credentials or secrets in evidence.
- Preserve both successful and failed observations.
- Do not mark a gate complete without reproducible logs or a working demonstration.
- Do not compensate for an earlier failed gate inside a later integration gate.
- Do not cross an explicit approval checkpoint by silently selecting an unresolved format or protocol.

## 11. Immediate next action after approval

Execute Gate A only. Do not begin Gate B in the same change. If PlatformIO or the CH340 driver is unavailable, stop and request installation approval rather than expanding Gate A automatically.
