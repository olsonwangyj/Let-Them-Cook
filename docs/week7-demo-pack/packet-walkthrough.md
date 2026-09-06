# Follow one dummy packet

Week 7 uses **real connections carrying predictable test values**. The physical ESP32 generates the values; no sensor or AI inference is needed to prove transport. The default protected firmware sends one 32-byte BLE notification per sample, approximately 10 times per second.

## An illustrative packet

Run this from the project directory without hardware or network access:

```powershell
& 'D:\Anaconda\python.exe' -m tools.week7_demo packet
```

It prints [packet-example.json](packet-example.json). This is an explanatory fixture: device **1**, boot **7**, sequence **42**, uptime **4200 ms**. Actual boots are generated on the ESP and will differ. The shared identity is **`1:7:42`**.

| Byte offsets | Field | Example | Representation |
|---|---|---|---|
| 0–1 | Magic | `W7` | ASCII `57 37` |
| 2 | Version | 1 | uint8 |
| 3 | Device ID | 1 | uint8 |
| 4–7 | Boot ID | 7 | uint32 little-endian |
| 8–11 | Sequence | 42 | uint32 little-endian |
| 12–15 | Uptime | 4200 ms | uint32 little-endian |
| 16–31 | Dummy values | Eight values below | Eight signed int16 little-endian |

For channel index `i = 0..7`, `value[i] = (seq % 2000) - 1000 + 10*i`. Thus sequence 42 contains:

```text
[-958, -948, -938, -928, -918, -908, -898, -888]
```

The exact 32 bytes are:

```text
57 37 01 01 07 00 00 00 2a 00 00 00 68 10 00 00
42 fc 4c fc 56 fc 60 fc 6a fc 74 fc 7e fc 88 fc
```

The layout is Python struct `<2sBBIII8h`. A 32-byte notification requires ATT MTU at least **35** because ATT notification overhead is three bytes; the protected physical runs measured **517**. Firmware suppresses oversized or unauthenticated submissions. There is no ESP Wi-Fi path or custom application fragmentation.

## What travels over each connection

1. **ESP → Laptop, protected BLE:** the 32 raw bytes above. The Laptop decodes and validates the schema and dummy pattern.
2. **Laptop → Ultra96 ingestion, TLS inside Laptop-owned SSH:** a `SENSOR_BATCH` JSON object. The Laptop preserves device, boot, sequence, uptime and values, and adds configured `session_id="week7-demo"`.
3. **Ultra96 → Laptop, same ingestion connection:** an `INGEST_ACK` with the same device, boot and sequence, and `status="accepted"`. A duplicate may receive `status="duplicate"` without a second result.
4. **Viewer → Ultra96 Gateway, independent TLS/SSH:** the viewer first sends `SUBSCRIBE` and requires `SUBSCRIBED` before production starts.
5. **Ultra96 → viewer, that independent connection:** a `GESTURE_RESULT`, here `result_id="1:7:42"`, `gesture="OPEN"`, `confidence=1.0`.

Dummy inference is `[REST, FIST, OPEN, POINT][seq % 4]`; `42 % 4 = 2`, hence OPEN. The confidence is a fixed test field, not a measured accuracy. Session selects the demo association; it is not a secret. Boot ID distinguishes restarts for correlation and is not a security identity.

Every TCP/TLS application message uses **four-byte big-endian UTF-8 body length + JSON body**, maximum body 16,384 bytes. JSON text is explanatory at the console: on the wire, it has the binary length prefix and no newline delimiter. BLE multi-byte integers remain little-endian.

| Example message | JSON body bytes | Four-byte prefix (hex) |
|---|---:|---|
| SENSOR_BATCH | 158 | `00 00 00 9e` |
| INGEST_ACK | 108 | `00 00 00 6c` |
| GESTURE_RESULT | 147 | `00 00 00 93` |
| SUBSCRIBE | 52 | `00 00 00 34` |
| SUBSCRIBED | 53 | `00 00 00 35` |

These sizes describe this exact compact JSON fixture. A different boot/sequence or whitespace changes JSON byte length; it does not change the fixed BLE packet size. The generator calculates the correct prefix for each encoded body.

**Network boundary:** Ultra96 exposes only SSH TCP **22**. Ingestion `127.0.0.1:8888` and Gateway `127.0.0.1:9999` are internal listeners. Laptop 18888 and viewer/Phone 19999 are local forward endpoints on their respective devices. Every client validates the TLS CA and service identity `ultra96.week7.internal` through its own SSH path.

## Show the teacher a complete match

With the actual Phone receiver ready, `tools.week7_demo sender` displays `packet` and `ack` JSONL events using the existing protected bridge. The packet event contains reconstructed BLE bytes and decoded JSON **after** the ACK has been validated; it is not a radio sniffer or a second transmission. This sender never subscribes to results. Phone results are displayed and saved on the Phone itself. Follow the [operator commands](README.md#5-actual-phone-mode-complete-this-on-the-device).

Compare exact sets of `device:boot:sequence`, not merely counts. An ACK proves ingestion acceptance; a matching independent result proves result delivery within the recorded streams. ACK/result arrival order may differ because the connections are independent. A new same-session viewer replaces the previous viewer; stop the desktop subscriber before the Phone run.

## Portable recorded example

[recorded-demo100.jsonl](recorded-demo100.jsonl) is a **saved actual protected ESP/Ultra96/desktop run**, not a live replay and not Phone evidence. Its 100 traces are `1:738264655:0` through `:99`, recorded after the user's reported USB reconnection/RESET. The run lasted 14.110 seconds. Its source and SHA-256 records are in [evidence-index.json](evidence-index.json); the full [continuation report](../week7-continuation-report-2026-09-07.md#user-operated-usb-reconnection-and-reset-follow-up) supplies physical and remote provenance.

```powershell
& 'D:\Anaconda\python.exe' -m tools.week7_demo audit 'docs\week7-demo-pack\recorded-demo100.jsonl' --minimum-count 100
```

Expected: exit **0**, `audit_passed=true`, `matched=100`, no missing/unexpected/duplicate saved IDs. The auditor validates schemas, dummy result consistency, sessions, exact ID sets, minimum count and the completed runner summary. It rejects incomplete, malformed, mismatched or fault-marked evidence. Its output is explicitly an **offline log correlation** result; it cannot certify the physical route from a file, measure end-to-end latency, or promote saved desktop data to a Phone pass.

The Phone receiver's JSONL is emitted after its duplicate suppression and contains no per-result timestamp. To claim sustained Phone delivery, preserve timed on-device observations and status alongside the trace files. Zero duplicate saved rows does not establish zero duplicate wire arrivals.
