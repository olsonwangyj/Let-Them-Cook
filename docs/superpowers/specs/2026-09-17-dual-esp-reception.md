# Dual ESP32 reception — approved option 1

The user selected simultaneous reception from two ESP32 gloves with zero measured loss during normal connected operation. Temporary disconnections are reported, automatically retried, and do not interrupt the other glove. Historical samples from an outage are not replayed as live gestures.

## Scope and acceptance

- Keep the current protected Week 7 BLE/TLS contracts, 32-byte dummy packets, and 10 Hz firmware rate. Device 1 and device 2 must have distinct explicitly selected BLE addresses.
- One coordinator runs two independently owned BLE/queue/TLS paths concurrently. Preserve the existing single-device CLI and tests. A blocked ACK or reconnect on one path must not prevent reception or forwarding on the other.
- Queues stay bounded and absorb brief stalls. Overflow, expired packets, mismatched identity, missing/duplicate/out-of-order sequences, transport ambiguity, or disconnected intervals prevent a clean zero-loss result; none may be silently called success.
- Normal shutdown stops notifications, obtains final source counters, drains accepted queued packets within a bounded deadline, then closes transport. Shutdown must not discard an otherwise healthy tail and then report success.
- Each ESP numbers a generated sample before attempting BLE submission, so a failed submission cannot reuse and conceal a missing sample ID. No offline history or retransmission protocol is added.
- A protected read-only source statistics characteristic makes start/end reconciliation possible. UUID is `6e1c0006-7a45-4dc4-b678-3f2d5a9c1001`. Its 24-byte value is Python format `<4sB3xIIII`: magic `W7S1`, device ID, three zero reserved bytes, boot ID, next sample sequence, sensor submissions, sensor submission failures, all integers little-endian. Snapshot under the same firmware state mutex. Require authenticated read permission in the normal profiles.
- Read source counters before subscribing and after successful notification stop but before disconnect. In an uninterrupted same-boot capture, the generated interval is `[start.next_seq, end.next_seq)` modulo uint32. Reconcile first/last IDs, contiguous received count, and acknowledged count with this interval. This proves a bounded capture, including its first and last sample; a successful notification submission by itself does not prove delivery.
- Firmware profiles `firebeetle32-left` and `firebeetle32-right` select IDs 1 and 2 respectively while retaining authenticated security. Existing default/diagnostic profiles remain available. Existing firmware without source statistics cannot pass the new dual acceptance command; report the needed firmware update clearly.
- A new `python -m laptop.dual_bridge` command supports physical addresses, CA/port/session, duration, queue/freshness settings, and explicit two-device mock input. Default observation is 600 seconds, with bounded initial connection time and bounded drain/cleanup. Reports distinguish synthetic from physical input and contain per-device source/receive/ACK/drop/gap/reconnect accounting.
- Start the timed observation after both streams are active. A clean run requires nonzero traffic from both, sufficient sustained coverage at the configured expected rate (at least 90% of expected samples during the common observation), no silence beyond the configured freshness interval, complete source-to-ACK reconciliation, no unfinished work, and no anomalies. A fault/recovery run is useful evidence but must not become a clean zero-loss pass.
- Physical tests and firmware uploads require the actual devices. Unit/fake-BLE/local-TLS tests cannot establish the real adapter's capacity or physical zero loss. Do not flash, pair, connect to campus systems, or claim physical acceptance as part of software implementation.

## Interfaces and boundaries

`laptop.bridge.Bridge` remains the per-device connection owner. Add only the lifecycle/identity/source-audit seams needed by the dual coordinator, with defaults preserving the existing single-device behavior. Keep pure source-statistics parsing and constant-space sequence reconciliation in a small dedicated module. Keep coordinator and CLI in `laptop/dual_bridge.py`.

The new firmware statistics helper is portable C++11 so host tests can exercise serialization and sequence/submission accounting. Existing sensor and result schemas do not change, so the installed native iPhone remains compatible. The iPhone's latest-result display is intentionally independent of sensor-capture completeness; it is not an all-packet evidence logger.

## Verification

Use real queue/codec/coordinator logic with fake hardware only at the Bleak boundary. Verify two concurrent streams with identical sequence ranges but different device IDs, a stalled device writer while its peer progresses, independent BLE recovery, identity mismatch, missing start/tail packets, overflow, normal draining, incomplete source snapshots, cancellation, and exact two-stream delivery to a real local TLS Week7Server. Run relevant existing bridge/transport/firmware regressions, compile both protected firmware variants when tooling is available, then obtain independent code review.
