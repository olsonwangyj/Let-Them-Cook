# B07 — Communication Subsystem

[01 Architecture + IDs](#b1) · [02 Packets](#b2) · [03 BLE](#b3) · [04 Laptop–Ultra96](#b4) · [05 Visualizer](#b5) · [06 Encryption](#b6) · [07 Laptop concurrency](#b7) · [08 Ultra96 concurrency](#b8)

<a id="b1"></a>
## 01 — Architecture and device IDs

![Two FireBeetles, relay laptop, Ultra96 and Visualizer](B07-video-diagrams/G01.svg)

Source: [firmware/esp32/platformio.ini](../firmware/esp32/platformio.ini#L21) · lines **21, 26**.

```ini
; L21: First uploaded board: LEFT.
-DCOMMS_DEVICE_ID=1
; L26: Second uploaded board: RIGHT.
-DCOMMS_DEVICE_ID=2
```

> Two FireBeetles send sensor data through the laptop to Ultra96. Ultra96 returns acknowledgements and sends results separately to the phone. Servers run on Ultra96. The first uploaded board becomes left, ID one; the second becomes right, ID two. Bluetooth addresses identify hardware; device IDs identify packet sources. Both boards use independent power during communication.

<a id="b2"></a>
## 02 — Packet types, format and dummy data

![Sensor packet: exact 32-byte layout](B07-video-diagrams/G03.svg)

Source: [common/sensor.py](../common/sensor.py#L11) · lines **11–12**.

```python
# L11: Little-endian sensor layout: 32 bytes.
_PACKET = struct.Struct("<2sBBIII8h")
PACKET_SIZE = _PACKET.size
```

> The little-endian sensor packet is thirty-two bytes: marker, version, device ID, boot ID, sequence, uptime and eight signed sixteen-bit values. Device, boot and sequence identify each sample.

![BLE packet types and control header](B07-video-diagrams/G04.svg)

> Control packets use a fourteen-byte header with opcode, device, status, request ID and offset. Types include sensor notifications, commands, rate changes, file operations and responses.

Source: [firmware/esp32/include/comms_packet.h](../firmware/esp32/include/comms_packet.h#L57) · lines **57–60**.

```cpp
// L57: Choose a complete fixture; keep the sensor format.
static_assert(kDummyFixtureCount > 1, "random source needs multiple fixtures");
if (!serializePacket(output, capacity, deviceId, bootId, seq, uptimeMs,
                     kDummyFixtures[randomWord % kDummyFixtureCount])) return false;
output[2] = 2;
```

Editable data: [common/dummy_fixtures.json](../common/dummy_fixtures.json#L1).

> The firmware randomly selects a complete fixture row. Editing the JSON, rebuilding and uploading both boards changes the transmitted values, as shown in the physical demonstration.

<a id="b3"></a>
## 03 — FireBeetle protocol FSM

![FireBeetle communication state machine](B07-video-diagrams/G05.svg)

> The board advertises, connects, authenticates and waits for subscription before streaming. Sensor notifications require sufficient MTU. Control writes return correlated responses. Authentication failure rejects the connection. Disconnection clears its state and restarts advertising. These states keep each board connection independent.

<a id="b4"></a>
## 04 — Laptop–Ultra96 protocol and TCP framing

![Laptop and Ultra96 connection state machine](B07-video-diagrams/G07.svg)

Source: [common/wire.py](../common/wire.py#L53) · lines **53, 58–60, 62**.

```python
# L53: Accumulate the complete length prefix.
header = await reader.readexactly(4)
# L58: Decode and bound the declared body length.
length = struct.unpack("!I", header)[0]
if not 0 < length <= MAX_FRAME_SIZE:
    raise ProtocolError("frame length outside 1..16384")
# L62: Accumulate the complete body, even across multiple TCP reads.
body = await reader.readexactly(length)
```

> The laptop connects through SSH and verified TLS, then sends SENSOR_BATCH messages. Ultra96 returns INGEST_ACK with matching session, device, boot, sequence and request identity. Errors trigger reconnection; unconfirmed packets are recorded. TCP is a byte stream. Each JSON message has a four-byte big-endian length prefix. These readexactly calls collect the complete header and body despite fragmented delivery.

<a id="b5"></a>
## 05 — Ultra96–Visualizer protocol FSM

![Visualizer subscription state machine](B07-video-diagrams/G08.svg)

> The phone opens SSH and verified TLS, sends SUBSCRIBE and waits for SUBSCRIBED. GESTURE_RESULT then updates its display and received count. Leaving the app pauses reception; returning requires Connect. Laptop acknowledgements prove Ultra96 ingestion. The filmed phone screen separately proves phone reception.

<a id="b6"></a>
## 06 — Encryption on all three channels

![BLE security, Python TLS, iPhone TLS and SSH](B07-video-diagrams/G09.svg)

### FireBeetle ↔ laptop

Source: [firmware/esp32/src/main.cpp](../firmware/esp32/src/main.cpp#L251) · lines **251–256**.

```cpp
// L251: Require Secure Connections, MITM and bonding; maximum key size: 16 bytes.
return setSecurityParam(ESP_BLE_SM_AUTHEN_REQ_MODE, ESP_LE_AUTH_REQ_SC_MITM_BOND) &&
    setSecurityParam(ESP_BLE_SM_IOCAP_MODE, ESP_IO_CAP_OUT) &&
    setSecurityParam(ESP_BLE_SM_MAX_KEY_SIZE, 16) &&
    setSecurityParam(ESP_BLE_SM_SET_INIT_KEY, ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK) &&
    setSecurityParam(ESP_BLE_SM_SET_RSP_KEY, ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK) &&
    setSecurityParam(ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH, ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH_ENABLE);
```

Source: [firmware/esp32/include/comms_security.h](../firmware/esp32/include/comms_security.h#L10) · lines **10–17**.

```cpp
// L10: Check authentication; gate notifications on connection, subscription and security.
inline bool isAuthenticated(bool success, uint8_t authMode) {
  return success && (authMode & kRequiredAuthMode) == kRequiredAuthMode;
}

inline bool canNotify(bool connected, bool subscribed, bool authenticated,
                      bool diagnostic) {
  return connected && subscribed && (authenticated || diagnostic);
}
```

> These BLE settings require Secure Connections, passkey authentication and bonding, with a maximum key size of sixteen bytes. The authentication check requires every security flag. The Bluetooth stack performs encryption; application traffic waits for an authenticated subscription.

### Laptop ↔ Ultra96

Source: [common/tls.py](../common/tls.py#L7) · lines **7–12, 16–19**.

```python
# L7: Client: TLS minimum, required certificate, hostname and trusted CA.
def client_context(ca_file):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_verify_locations(cafile=str(ca_file))
# L16: Server: matching TLS minimum and certificate/private key.
def server_context(cert_file, key_file):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=str(cert_file), keyfile=str(key_file))
```

Source: [laptop/bridge.py](../laptop/bridge.py#L350) · lines **350–353**.

```python
# L350: Use the verified context and Ultra96 hostname for the real connection.
return await asyncio.wait_for(asyncio.open_connection(
    self.config.host, self.config.port, ssl=client_context(self.config.ca_file),
    server_hostname=TLS_SERVER_NAME, limit=32768,
    ssl_handshake_timeout=self.config.io_timeout), self.config.io_timeout)
```

Source: [tools/ssh_tunnel.py](../tools/ssh_tunnel.py#L26) · lines **26–28**.

```python
# L26: Require known SSH host keys on the deployed route.
trust_options = ["-o", "StrictHostKeyChecking=yes",
                 "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
                 "-o", "BatchMode=" + ("yes" if batch else "no")]
```

> The laptop requires TLS one point two or newer, verifies the server certificate against our CA and checks its hostname. The connection uses that context. Ultra96 loads its certificate and private key. SSH carries TLS through the deployed route, with strict host-key checking.

### Ultra96 ↔ iPhone

Source: [ios-visualizer/CommsNative/Sources/CommsTransport/CommsClient.swift](../ios-visualizer/CommsNative/Sources/CommsTransport/CommsClient.swift#L88) · lines **88–92, 142**.

```swift
// L88: Phone: explicit trust roots and full certificate verification.
var configuration = TLSConfiguration.makeClientConfiguration()
configuration.trustRoots = .certificates(roots)
configuration.additionalTrustRoots = []
configuration.certificateVerification = .fullVerification
configuration.minimumTLSVersion = .tlsv12
// L142: Verify the Ultra96 hostname inside the SSH channel.
try child.pipeline.syncOperations.addHandler(try NIOSSLClientHandler(context: tls, serverHostname: "ultra96.week7.internal"))
```

Source: [ios-visualizer/CommsNative/Sources/CommsTransport/Trust.swift](../ios-visualizer/CommsNative/Sources/CommsTransport/Trust.swift#L7) · lines **7–10**.

```swift
// L7: Reject an SSH host key that does not match the configured pin.
func validateHostKey(hostKey: NIOSSHPublicKey, validationCompletePromise: EventLoopPromise<Void>) {
    guard hostKey == pinned else { validationCompletePromise.fail(TransportFailure.hostKey); return }
    validationCompletePromise.succeed(())
}
```

> The phone also uses full TLS certificate and hostname verification. Its SSH delegate rejects host keys that differ from the configured pins. Neither network channel disables verification.

<a id="b7"></a>
## 07 — Laptop concurrency and threading

![Laptop tasks, bounded queues and logging thread](B07-video-diagrams/G10.svg)

Source: [laptop/dual_bridge.py](../laptop/dual_bridge.py#L94) · lines **94–95, 106**.

```python
# L94: Create one network writer task per board.
device: asyncio.create_task(bridge.writer_loop(), name=f"writer-{device}")
for device, bridge in self.bridges.items()
# L106: Create a separate input task for that board.
inputs[device] = asyncio.create_task(coroutine, name=f"input-{device}")
```

> Each board has separate input and writer tasks.

Source: [laptop/bridge.py](../laptop/bridge.py#L128) · lines **128, 138, 633–634**.

```python
# L128: Protect callback queue state with a lock.
with self._lock:
# L138: Wake the asyncio consumer safely from a callback thread.
self._loop.call_soon_threadsafe(self._wake)
# L633: Send data and receive ACKs concurrently.
asyncio.create_task(sender(), name="pipeline-sender"),
asyncio.create_task(receiver(), name="pipeline-ack-reader"),
```

> BLE callbacks place data in a bounded queue under a lock and wake asyncio safely. Sender and acknowledgement tasks run concurrently; each acknowledgement releases a window slot.

Source: [laptop/evidence.py](../laptop/evidence.py#L33) · lines **33–34**.

```python
# L33: Write packet evidence on a separate OS thread.
self._thread = threading.Thread(target=self._write, name="packet-evidence", daemon=True)
self._thread.start()
```

> A separate thread writes logs. One slow board does not stop the other stream. These are asynchronous tasks, plus a logging thread.

<a id="b8"></a>
## 08 — Ultra96 concurrency and result delivery

![Ultra96 listeners, client tasks and result queue](B07-video-diagrams/G11.svg)

Source: [ultra96/server.py](../ultra96/server.py#L151) · lines **151, 187, 272, 273–275, 334–337**.

```python
# L151: Each listener has an accept task.
task = asyncio.create_task(self._accept(listener, gateway))
# L187: Each connection has its own client task.
task = asyncio.create_task(self._client(connection, gateway))
# L272: Queue the phone result.
self._subscriber[1].put(result)
# L273: Independently return the ingestion ACK.
ack = dict(v=message["v"], type="INGEST_ACK", **trace_fields(message))
ack["status"] = "duplicate" if duplicate else "accepted"
await write_frame(writer, ack)
# L334: Send results while monitoring subscriber disconnection.
sender = asyncio.create_task(self._send_results(writer, queue))
# After SUBSCRIBE the connection is receive-only; EOF or extra bytes end ownership.
monitor = asyncio.create_task(reader.read(1))
finished, _ = await asyncio.wait((sender, monitor), return_when=asyncio.FIRST_COMPLETED)
```

> Ultra96 uses an asyncio event loop with separate ingestion and phone listeners, and one task per connection. Ingestion validates samples, suppresses duplicates, queues a result and returns an acknowledgement. Separate tasks send phone results and monitor disconnection. The bounded queue drops old or stale results instead of blocking ingestion. This separates laptop acknowledgements from phone delivery.
