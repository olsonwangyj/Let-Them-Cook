# Architecture and Interface Draft V0.1

## 1. Purpose and authority

This document is the current Communications architecture baseline for the Let Them Cook CG4002 project. It records the approved topology while separating confirmed decisions from proposed implementation mechanisms and unresolved choices.

This document is not a fully professor-confirmed implementation specification. Its interpretation priority is:

1. Latest professor-confirmed network constraints and subsequent team corrections.
2. Official CG4002 SoC firewall material.
3. The Initial Design Report as a provisional design baseline.
4. Recommendations explicitly labelled as recommendations.

The document does not authorize implementation of any item labelled Proposed or TBD without further review.

## 2. Status definitions

- **Confirmed:** A selected project topology, scope boundary, role, or professor-confirmed deployment constraint that may be used as the current baseline.
- **Proposed:** An intended implementation mechanism that remains subject to interface review, prototyping, or testing.
- **TBD:** A choice that has not been selected or validated.

## 3. Current topology

```text
Left ESP32 glove  ── BLE/GATT ──┐
                                ├── Laptop Coordinator
Right ESP32 glove ── BLE/GATT ──┘
                                      │
                                      │ Laptop initiates TLS/TCP
                                      │ through its own SSH -L
                                      ▼
                           Ultra96 Ingestion Server
                               (loopback service)
                                      │
                                      ▼
                         Ultra96 Inference Pipeline
                    (proposed alignment and 50 × 16 window)
                                      │
                                      ▼
                           Ultra96 Result Router
                                      │
                                      ▼
                         Ultra96 Visualizer Gateway
                               (loopback service)
                                      ⇅
                         Full-duplex application connection
                                      ⇅
                    Phone's own SSH -L through stfjump
                                      ⇅
                               Phone / Unity
```

The Phone initiates its application connection to the Ultra96 Visualizer Gateway through its own SSH local forward. After the application connection is established, it is full-duplex, and Ultra96 sends `GESTURE_RESULT` back to the Phone over that connection.

Compact topology:

```text
ESP32 gloves
→ BLE/GATT
→ Laptop Coordinator

Laptop Coordinator
→ TLS/TCP through Laptop SSH -L
→ stfjump
→ Ultra96 Ingestion Server on loopback

Ultra96 Inference Pipeline
→ Ultra96 Result Router
→ Ultra96 Visualizer Gateway on loopback

Phone/Unity
→ Phone SSH -L through stfjump
→ Ultra96 Visualizer Gateway

Ultra96 Visualizer Gateway
→ GESTURE_RESULT over the established connection
→ Phone/Unity
```

The primary architecture contains:

- No ESP32 Wi-Fi.
- No direct Phone-to-Laptop application connection.
- No externally exposed Ultra96 application port.
- No SSH remote/reverse forwarding (`-R`).
- No requirement for the Laptop to relay `GESTURE_RESULT`.

## 4. Component responsibilities

### 4.1 ESP32 gloves

#### Confirmed topology

There are two glove streams. Each glove uses one FireBeetle ESP32 and communicates with the Laptop through BLE/GATT.

The ESP32 is:

- A BLE Peripheral.
- A GATT Server.
- The producer of one glove sensor stream.

#### Proposed implementation

Each glove is currently expected to use one MPU-6050 and two flex sensors. The proposed sample representation is:

```text
ax, ay, az, gx, gy, gz, flex1, flex2
```

The following remain proposed until the Sensor and AI ICs freeze the interface:

- The exact eight-channel representation.
- Field widths and signedness, including possible 16-bit encoding.
- Units, ranges, scale factors, and byte order.
- Approximately 50 Hz sampling.
- Binary `SENSOR_BATCH` encoding.
- Bounded sampling ring buffers.
- Batch formation and overflow policy.
- Sequence tracking and gap reporting.
- BLE application-layer protection.

Sensor wiring, electrical design, calibration, filtering, and feature selection are outside the Communications subsystem.

### 4.2 Laptop Coordinator

#### Confirmed topology

The Laptop is:

- BLE Central and GATT Client for both gloves.
- TLS/TCP client of the Ultra96 Ingestion Server.
- The SSH client that establishes its own local-forwarding tunnel through `stfjump`.
- Responsible for transporting glove data to Ultra96.

The Laptop is not the primary result relay to the Phone.

#### Proposed implementation

The Laptop is expected to manage:

- BLE scanning, connection, and reconnection.
- GATT service and characteristic discovery.
- Notification subscription.
- ATT MTU negotiation.
- Binary packet framing and parsing.
- Device, boot, and transport-connection state.
- Sequence checking and gap detection.
- Bounded queues and stale-data handling.
- Clock offset and drift estimation.
- `TIME_SYNC`, corrected timestamps, and `START_AT`.
- Authentication, replay rejection, and decryption if application-layer protection is adopted.
- SSH and TLS connection supervision.

These mechanisms remain proposed rather than professor-confirmed runtime requirements.

### 4.3 Ultra96

#### Confirmed topology

Ultra96:

- Hosts an ingestion application service on loopback.
- Hosts the inference functionality.
- Hosts a logical Visualizer Gateway on loopback.
- Delivers each inference result directly to the intended Phone connection without requiring the Laptop to relay it.

The Phone association, registration, authentication, subscription, ownership, and routing mechanism remains TBD.

#### Proposed implementation

Ultra96 may contain the following logical modules:

```text
Ingestion Server
Inference Pipeline
Result Router
Visualizer Gateway
```

They may be separate processes or modules within one process. The following remain proposed:

- Timestamp-based alignment of the two glove streams.
- A `50 × 16` inference window.
- Window stride and overlap.
- Gap tolerance.
- Normalization.

### 4.4 Phone/Unity

#### Confirmed topology

The Phone:

- Initiates its own SSH `-L` connection through `stfjump`.
- Initiates an application connection to the Ultra96 Visualizer Gateway.
- Receives inference results directly from Ultra96 over the established full-duplex application connection.
- Does not require a direct application connection to the Laptop.
- Performs marker detection, MediaPipe processing, AR interpretation, and game-context decisions locally.

#### TBD

- Mobile SSH application or library.
- Unity's relationship with the SSH process.
- WSS, WS, or length-prefixed TCP/JSON inside the tunnel.
- Whether application TLS is required inside the SSH tunnel.
- Phone registration, authentication, subscription, and connection ownership.
- The result-association and routing identifier, including whether a field is named `user_session_id`.
- VPN requirements.
- SSH key storage and Ultra96 host-key verification.
- iOS or Android background behavior.

## 5. Client/server roles

| Link | Client/Initiator | Server/Listener | Status |
|---|---|---|---|
| BLE connection | Laptop BLE Central | ESP32 BLE Peripheral | Confirmed |
| GATT interface | Laptop GATT Client | ESP32 GATT Server | Confirmed |
| Laptop SSH connection | Laptop SSH Client | Ultra96 `sshd`, reached through `stfjump` | Confirmed |
| Sensor application connection | Laptop TLS/TCP Client | Ultra96 Ingestion Server | Confirmed |
| Phone SSH connection | Phone SSH Client | Ultra96 `sshd`, reached through `stfjump` | Confirmed topology; implementation TBD |
| Visualizer application connection | Phone/Unity Client | Ultra96 Visualizer Gateway | Confirmed roles; inner protocol TBD |
| Result delivery | Ultra96 sends over the established full-duplex connection | Phone receives | Confirmed delivery direction; association mechanism TBD |

Client/server describes connection initiation and listening. It does not restrict later application-data direction.

## 6. NUS/SoC firewall model

In the stated NUS/SoC deployment environment, Ultra96's permitted inbound service is SSH on TCP port 22 through the authorized `stfjump` path. Application services such as ingestion and visualization remain bound to Ultra96 loopback and are accessed through SSH local forwarding.

Confirmed deployment constraints:

- Laptop and Phone are non-whitelisted devices.
- The design must not depend on another device opening a direct inbound TCP connection to the Laptop.
- Other Ultra96 application ports are not directly exposed through the NUS firewall.
- Ultra96 may run application servers internally on loopback.
- Those loopback services are reached through SSH local forwarding.

Example deployment:

```text
Permitted through the authorized network path:
Ultra96 sshd                 TCP 22

Ultra96 loopback only:
Ultra96 Ingestion Server     127.0.0.1:8888
Ultra96 Visualizer Gateway   127.0.0.1:9999
```

Ports `8888` and `9999` are examples, not frozen assignments.

Direct Phone-to-Laptop WSS is not a viable baseline under the stated NUS network constraints because it requires an inbound TCP path to the non-whitelisted Laptop. WSS itself is not specifically blocked and may still be used between Phone and Ultra96 inside the Phone's SSH tunnel.

## 7. Role of stfjump

`stfjump.comp.nus.edu.sg` is an SSH bastion or ProxyJump host. Conceptually, each tunnel has two network legs:

```text
Client → stfjump:22
stfjump → Ultra96:22
```

The final SSH endpoint is Ultra96.

`stfjump` does not:

- Run the inference service.
- Run the Visualizer Gateway.
- Decode or transform packets.
- Parse, store, or route `SENSOR_BATCH`.
- Parse, store, or route `GESTURE_RESULT`.
- Act as the project's data broker.

## 8. SSH local forwarding

Example Laptop command:

```bash
ssh -J <soc-user>@stfjump.comp.nus.edu.sg \
  -N \
  -L 127.0.0.1:8888:127.0.0.1:8888 \
  xilinx@<ultra96-host>
```

Application path:

```text
Laptop application
→ Laptop 127.0.0.1:8888
→ Laptop SSH client
→ authorized SSH connection on TCP 22
→ stfjump
→ Ultra96 sshd
→ Ultra96 127.0.0.1:8888
→ Ultra96 Ingestion Server
```

Interpretation:

- The application connects to `127.0.0.1:8888` on the Laptop.
- The left `127.0.0.1:8888` belongs to the SSH-client device, which is the Laptop in this example.
- The right `127.0.0.1:8888` is interpreted from the final SSH endpoint, Ultra96.
- No Windows inbound firewall rule is needed for this Laptop connection.
- Ultra96 port `8888` does not need to be externally opened.
- The SSH session must remain active while the application uses the forwarding channel.
- The forwarded TCP connection is full-duplex.
- Uppercase `-L` means local port forwarding.
- Lowercase `-l` specifies an SSH login username and does not create a tunnel.
- SSH `-R` is only an explanatory alternative and is not part of the selected architecture.
- This uses an authorized SSH facility; it does not disable the NUS firewall.

The Phone uses the equivalent topology from its own device. On the Phone, the left-hand loopback address belongs to the Phone, while the right-hand address belongs to Ultra96.

Phone SSH support, VPN requirements, key storage, host-key verification, and mobile background behavior require real-device testing.

## 9. Runtime data flow

1. Each ESP obtains or generates glove sensor records.
2. Under the proposed design, records enter a bounded ESP ring buffer.
3. A proposed PacketBuilder creates a BLE-compatible binary `SENSOR_BATCH`.
4. The ESP sends the batch using a GATT notification.
5. The Laptop first receives the notification bytes and parses only the outer framing or header required to identify and process the packet.
6. If the proposed application-layer protection is enabled, the Laptop then authenticates and decrypts the protected payload before parsing the plaintext sensor fields.
7. Under the proposed reliability design, the Laptop checks device and connection state, sequences, timestamps, gaps, and status.
8. Under the proposed synchronization design, the Laptop estimates clock offset and drift and creates corrected timestamps.
9. The Laptop sends validated timestamped batches over TLS/TCP through its SSH `-L`.
10. Ultra96 receives the batches while retaining glove-stream separation.
11. Ultra96 performs the proposed alignment, window formation, normalization, and inference.
12. Ultra96 produces `GESTURE_RESULT`.
13. Ultra96 sends the result to the intended Phone connection. Phone association, registration, authentication, subscription, ownership, and routing identifiers remain TBD.
14. The result crosses the established full-duplex application connection through the Phone's SSH tunnel.
15. Phone/Unity receives the result and applies its own AR and game-context logic.

## 10. Security boundary

### 10.1 Proposed ESP-Laptop protection

The current proposal is:

```text
BLE Secure Connections
+ pairing and bonding
+ provisioned device secret
+ HMAC challenge-response
+ HKDF session-key derivation
+ AES-GCM packet protection
```

BLE pairing, bonding, and the exact application-layer cryptographic transcript are not frozen. The following remain unresolved:

- Pairing association mode.
- Provisioning method.
- Key ownership and rotation.
- Nonce construction and reboot safety.
- Replay window.
- Authenticated header fields.
- Failure and re-pairing behavior.

### 10.2 Laptop-Ultra96

TLS/TCP inside SSH `-L` is the current topology. Certificate identity, hostname validation, client authentication, and credential provisioning remain to be specified.

### 10.3 Phone-Ultra96

Possible inner protocols are:

```text
WSS through SSH -L
WS through SSH -L
length-prefixed TCP/JSON through SSH -L
```

If WSS is selected, certificate trust and hostname validation through a localhost forwarding endpoint must be solved.

If WS or raw TCP is selected, SSH encrypts the network path, but the team must confirm whether SSH-level protection alone satisfies the course security requirement.

## 11. Proposed reliability and recovery behavior

The following behavior is planned but not frozen:

### ESP BLE disconnection

1. Keep the sampling buffer bounded.
2. Discard telemetry that is too old to be useful.
3. Resume advertising or reconnect according to the selected BLE strategy.
4. Re-establish pairing or bonding state as required.
5. Establish a new application-security context if the selected security design requires it.
6. Repeat the proposed time synchronization.
7. Report the lost interval through a proposed gap mechanism.
8. Prevent pre-reboot and post-reboot samples from being combined silently.

### Laptop SSH or TLS failure

1. Keep downstream queues bounded.
2. Drop stale sensor records rather than replaying old gestures.
3. Rebuild the Laptop SSH `-L` tunnel.
4. Re-establish TLS/TCP.
5. Start a fresh transport-connection context.
6. Notify Ultra96 of the discontinuity so incomplete windows can be discarded.

### Phone SSH or application failure

1. Rebuild the Phone SSH `-L` tunnel.
2. Reconnect to the Ultra96 Visualizer Gateway.
3. Perform the eventual registration, authentication, and subscription procedure.
4. Avoid replaying stale gesture results as new game actions.

## 12. Decision table

| Status | Items |
|---|---|
| **Confirmed** | Two glove streams; ESP32-Laptop BLE/GATT; Laptop BLE Central/GATT Client; ESP32 BLE Peripheral/GATT Server; Laptop TLS/TCP client; Ultra96 ingestion server; Laptop SSH `-L` through `stfjump`; Phone's independent SSH `-L` through `stfjump`; Ultra96 delivers results directly to the intended Phone connection; no Laptop result relay; no ESP Wi-Fi; no SSH `-R`; V1 uses one user, two gloves, one Laptop, one Ultra96, and one Phone |
| **Proposed** | MPU-6050 plus two flex readings per glove; eight-channel representation; 16-bit fields; units and scales; approximately 50 Hz; binary `SENSOR_BATCH`; GATT characteristic layout; ATT MTU and batch size; bounded buffers; sequences and gap reporting; clock correction, `TIME_SYNC`, and `START_AT`; HMAC/HKDF/AES-GCM; four-byte length-prefixed JSON for Laptop-Ultra96; `50 × 16` window |
| **TBD** | Exact sensor contract; final BLE UUIDs and packet layout; final cryptographic transcript; exact internal ports; Phone WSS/WS/TCP choice; application TLS requirement; Phone tunnel implementation; VPN requirement; mobile SSH lifecycle; Phone registration, authentication, subscription, association, and connection ownership; routing identifier name and authority, including whether `user_session_id` is used; association between Laptop glove assignments and the intended Phone; Ultra96 process decomposition |

## 13. V1 scope and future extensibility

Confirmed V1 scope:

```text
one user
two gloves
one Laptop
one Ultra96
one Phone
```

A future architecture may target:

```text
two users
four BLE glove connections
one multiplexed Laptop-Ultra96 connection
one independent SSH tunnel per Phone
```

This is an extensibility objective, not a validated capacity or a V1 requirement. Four simultaneous streaming ESP32 connections must be tested with the real Laptop Bluetooth adapter before being claimed.

Future support for per-user or per-session routing is an extensibility objective. No concrete identifier, registration, authentication, subscription, or association mechanism is currently proposed or confirmed.

An eventual implementation should avoid unnecessary hard-coded global variables tied to exactly one left and one right glove. The form of any registry or session abstraction remains a future design decision.

## 14. Week 7 communications path

```text
real ESP32 generating dummy sensor packets
→ BLE/GATT
→ real Laptop
→ Laptop SSH -L
→ real Ultra96
→ dummy or actual gesture result
→ Phone SSH -L
→ real Phone displaying or printing JSON
```

For Week 7:

- Real ESP32, Laptop, Ultra96, and Phone participate.
- Real IMU and flex sensors are not required.
- Dummy packets may be produced on the ESP32.
- Full AR animation is not required.
- A basic Phone component displaying received JSON is sufficient.
- Later teaching-team instructions remain authoritative.

## 15. Explicitly unresolved implementation work

This architecture baseline does not authorize implementation of:

- The final Phone application protocol.
- The Phone SSH integration mechanism.
- The final BLE packet or GATT UUID layout.
- The final application-layer cryptographic design.
- Result-routing identifiers or registration logic.
- The final sensor representation or sampling contract.
- The final inference-window dimensions, stride, gap tolerance, or normalization.
- Any multi-user behavior.

These items require separate review and approval before implementation.
