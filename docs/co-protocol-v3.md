# CO application protocol version 2

This describes the software extension to the existing transport. Historical test reports describe the earlier deployment. Local implementation, automated validation, firmware installation and phone installation are separate states.

## Sensor data and random events

The BLE sensor value is 32 bytes: ASCII magic `LC` (`4C 43`), version, device ID, little-endian boot ID, sequence, uptime milliseconds and eight signed int16 channels. The source-statistics characteristic is 24 bytes with magic `LCS1`. Since 2026-10-14 the laptop and the firmware accept only these markers: a board that still runs Week 7 firmware (`W7`, `W7S1`) is refused until it is flashed again. Version 1 preserves the deterministic legacy formula. Version 2 accepts all schema-valid channel values and chooses random fixtures from `common/dummy_fixtures.json`.

After editing the JSON, run `python -m tools.generate_dummy_fixtures` and rebuild firmware. Python reloads fixtures when its process starts. Firmware uses ESP randomness normally; compile with `COMMS_FIXTURE_SEED` for reproducible fixture selection. `--seed` controls laptop/mock fixture selection, not firmware randomness. `COMMS_LEGACY_DUMMY=1` selects the old sensor stream; `COMMS_INITIAL_RATE_HZ` sets initial firmware rate (default 10).

Version 2 `SENSOR_BATCH`, `INGEST_ACK` and `GESTURE_RESULT` retain existing fields and require `request_id`. It is JSON null for a sensor stream or a nonzero uint32 for a command. A command has `seq == request_id`. Stream result IDs remain `device:boot:seq`; command result IDs are `cmd:device:boot:request_id`. Subscription envelopes remain version 1. Updated receivers accept both result versions, and reject unknown/duplicate fields or unsupported versions.

The session ID is `ltc-comms` everywhere by default: `demo.py run/live`, `demo.py service --start`, the server and the phone source. All three network participants must use the same session. `--session-id` or `LTC_COMMS_SESSION` changes it for the laptop commands; the phone app has it compiled in. The Ultra96 service started for Week 7 and the app installed for Week 7 use `week7-demo`, so both are replaced when this source is deployed.

Ultra96 selects a random label from REST, FIST, OPEN and POINT for each accepted v2 input. Confidence remains 1.0; these are simulated events. Legacy v1 events retain their deterministic label. Exact v2 retries do not generate another event. Conflicting identities reject. Sensor replay protection retains namespace high-water marks and 4096 recent fingerprints; stale identities outside that window reject. The server keeps at most 128 sensor boot namespaces and 4096 command identities without evicting replay protection. A new configured session/server is required when capacity is exhausted. This state is in memory, so replay protection across server restart requires a fresh session ID.

## Protected BLE controls

Controls use the existing service, UUID `6e1c0007-7a45-4dc4-b678-3f2d5a9c1001` for writes and `6e1c0008-7a45-4dc4-b678-3f2d5a9c1001` for responses. New writable attributes and response subscriptions retain authenticated encrypted BLE permissions and current-peer checks.

Every control message begins with the 14-byte little-endian header `<2sBBBBII>`:

| Field | Meaning |
|---|---|
| Magic/version | `B7`, control protocol 1 |
| Opcode | 1 command; 2 rate; 16 begin file; 17 chunk; 18 end; 19 abort |
| Device | 1 or 2 |
| Status | Request 0; response 0 OK, 1 invalid, 2 busy, 3 ordering, 4 integrity, 5 conflict, 6 unsupported |
| ID | Nonzero uint32 request/transfer identity |
| Offset | uint32 file offset; zero for commands/rate/abort |

A response sets bit 7 of the opcode. Controls require negotiated ATT MTU >=64. Payloads are at most `min(180, MTU - 3 - 14)` bytes. Each BLE write carries exactly one control message; TCP framing does not apply here.

Command payloads contain a complete v2 sensor packet addressed to the current boot. The packet carries the `LC` marker; the firmware rejects any other marker before the command changes state. ESP increments every channel by one, with 32767 wrapping to -32768, and replaces uptime with its current clock. The sensor stream keeps its own sequence and accounting. Laptop stores original/expected values, verifies the response, and forwards it over a separately owned TLS transaction. Firmware caches eight command responses per connection and rejects older evicted requests; IDs increase during that connection. Disconnect clears local control state. The board's command ledger prevents a repeated command identity from causing another event.

One control transaction is active per device. Keyboard keys `1` and `2` submit a random packet to the corresponding device without Enter. Each device has a bounded queue of eight waiting commands. Overload/disconnect rejects explicitly. Accepted commands finish or are recorded as failed; timeout is not retried automatically. Board ACK is ingestion evidence, and does not prove phone receipt.

Rate commands carry uint16 Hz (1..200) and return the accepted rate. They change ESP pacing, unlike the old `--expected-rate` option. These are configurable operating points, not measured maximum-speed claims.

On supported Windows versions, rates above 10 Hz also request the OS throughput-oriented BLE connection preference for that connection's lifetime. Reports distinguish request acceptance from the observed interval, peripheral latency and supervision timeout. The preference is released during cleanup; unsupported or denied requests remain visible as diagnostics. This trades power and available concurrent connections for throughput, so sustainable performance still requires a measured two-device capture. ATT MTU alone does not establish connection interval or link-layer data length.

## Files

The supported direction is laptop to ESP RAM, 1..65536 bytes. Begin declares uint32 length and SHA-256 digest. Ordered chunks contain file bytes at the declared offset. Responses carry the next expected offset. Identical already-received bytes may be retried; missing, out-of-order or conflicting chunks reject. End succeeds only after the entire file has arrived and the receiver has computed and matched its digest; its response returns length plus the computed digest.

The client retries an identical chunk up to twice after a timeout. Failure aborts, and disconnect or 30 seconds of receiver inactivity discards an unfinished file. Restart with a new transfer ID. Power-loss resumption is not supported. Files/commands use separate accounting from sensor goodput.

## Running the updated software

Examples from the repository, after installing matching firmware/server/receiver versions. For a teammate machine, add `--ca` with the verified public CA as shown in the [communications quickstart](communications-quickstart.md); these short forms use the original operator's CA path and the new `ltc-comms` session default:

```powershell
python demo.py run --duration 90 --keyboard
python demo.py run --duration 90 --rate 50
python demo.py run --duration 90 --file path\to\sample.bin --file-device 2
```

Both device connections continue during command/file work. A control-enabled run requires the new characteristics on both ESPs. Updated native Swift sources must be rebuilt and installed on the iPhone from a Mac before receiving v2 results. Existing firmware/installed receivers do not acquire these capabilities merely by updating the repository.

Reports include per-device and combined decimal kbps. The boundary is unique valid 32-byte sensor packets received at the laptop, including application headers and excluding BLE/TLS/SSH overhead, commands and files. Monotonic observation time includes zero-traffic periods and excludes startup/draining. Console sampling is independent of accounting. Captures retain plain `live.log`, structured `packets.jsonl`, decoded `packets.log`, configuration, `report.json` and exit status; evidence overflow is reported explicitly.
