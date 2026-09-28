# CO missing features implementation plan

> Agentic execution: subagent-driven-development, with independent firmware, laptop and receiver ownership; shared contracts owned by the coordinator.

**Goal:** Implement missing software in CO-02 through CO-08 and preserve CO-01/CO-12. The user subsequently authorized updating the running Ultra96 service and testing both connected ESPs. Record measured physical results separately from implementation; no demonstration checklist.

**Architecture:** Retain isolated sensor pipelines and legacy version 1. Version 2 keeps the 32-byte sensor layout and allows editable random int16 fixtures. Dedicated protected BLE control characteristics carry commands, rate configuration and bounded file transfer; command ingestion uses an independently owned TLS connection.

**Tech stack:** Python asyncio, Arduino ESP32/PlatformIO, Swift, Unity C#.

**Spec:** `docs/B07-CO-subsystem-requirements.md`, narrowed by the user's instruction to implement software first.

## Contracts

- Sensor magic W7; version 1 deterministic legacy, version 2 schema-valid arbitrary eight int16 values. Device, boot, sequence, uptime and byte layout unchanged.
- Version 2 SENSOR_BATCH, INGEST_ACK and GESTURE_RESULT require `request_id`: null for streaming or uint32 for commands. Command sequence equals request ID. Result IDs are `device:boot:seq` for streams and `cmd:device:boot:request_id` for commands. SUBSCRIBE envelopes remain v1; updated receivers accept both result versions.
- Controls use UUID suffixes 0007 (write) / 0008 (notify) under the existing service namespace. Header `<2sBBBBII`: B7, control version 1, opcode, device, status, ID, offset. Requests status=0. Response opcode=request|0x80.
- Opcodes command=1, rate=2, file begin=16/chunk=17/end=18/abort=19. Status 0 success, 1 invalid, 2 busy, 3 ordering, 4 integrity, 5 conflict, 6 unsupported. Minimum MTU 64; payload max 180 and total frame <= MTU-3.
- Command payload is a full v2 sensor packet with current device/boot, seq=request ID. ESP increments each channel, wrapping 32767 to -32768, and updates uptime. Original and expected values are retained. Commands fail on timeout; no automatic retry or second event. IDs increase within a connection; firmware rejects stale evicted requests. Board keeps a bounded non-evicting command ledger so old IDs never generate another event in the server session.
- Rate payload/response uint16 LE, 1..200 Hz; changes firmware pacing. Initial rate remains 10 Hz.
- File limit 65536 bytes, laptop to ESP RAM. Begin payload uint32 length + SHA-256; chunks carry exact offset; ACK offset is next expected. End response returns receiver length and computed digest. Identical duplicate chunks allowed, wrong ordering/conflicts rejected. Disconnect aborts; incomplete transfers cannot succeed.
- Security policies and strict TCP framing remain. Version 1 retains deterministic behavior; unsupported versions reject.

## Work packages

- [x] Shared codecs and fixtures: failing tests for v2 round trip, seeded selection, range checks, control limits/transforms; implement `common/sensor.py`, `common/control.py`, editable JSON and generated firmware header.
- [x] Firmware: portable behavioral tests for protected control processing, bounded transfers and replay rejection; implement control module/GATT integration, fixture selection and rate pacing; build left/right profiles.
- [x] Board/receivers: test random choice, duplicate/conflicting/stale identities, v1/v2 exact fields, command correlation and idle framing; coordinate Python, Swift and C# changes.
- [x] Laptop: mocked real control codecs and BLE flow tests, keyboard bounded queues, per-device independent workers, TLS command ACK handling, actual rate/file options in `demo.py`, sampled decoded output and plain evidence.
- [x] Throughput: controlled monotonic time tests including silence, duplicates, malformed samples, observation boundaries; implement meter and integrate rolling/average decimal kbps without counting commands/files.
- [x] Integration: full Python suite (421 passed, 3 skipped), 57 C# checks, protected left/right firmware builds, independent review, and a physical SSH/TLS run through an isolated Ultra96 service. Final evidence-only improvements passed 88 focused tests. Native Swift build/install remains pending a Mac.
- [x] Deployment and follow-up fixes: both ESPs flashed, normal Ultra96 service updated, physical commands/files and power recovery recorded; connection timing and shutdown-tail fixes verified by 465 Python tests (3 skipped), independent review and a fresh dual-device baseline. Rate results and remaining physical limits are maintained in the deployment report.

## Decisions

Use the existing clean workspace. No demo checklist. Preserve historical reports as historical evidence. Fixture regeneration is a developer build step, not a change to the live packet schema.

The user subsequently supplied remote access and connected both ESPs for programming. Both devices were identified by MAC and flashed with protected v2 firmware. Windows required the already documented targeted bond recovery after the GATT layout change; authenticated protection was retained. The initial isolated Ultra96 test was followed by an explicitly authorized production deployment on the existing loopback ports 8888/9999, preserving certificates, the session ID and a rollback copy. Current deployment and physical evidence are recorded in [the deployment report](../../co-live-deployment-2026-09-28.md).

Physical evidence: `.week7-local/co-right-hardware.json` records three verified transformations, a 50 Hz rate-control check and 4096-byte SHA-256 transfer with the peer streaming. `.week7-local/co-v2-20260928T115551Z/report.json` records a clean 65.016-second dual run through Ultra96, 1310 sensor ingestion ACKs plus three command ACKs, and 1313 matching unique results at a Python subscriber. Sensor observation goodput was 5.118740 kbps combined. Left used v1, right used v2; this verifies mixed-version operation, not two upgraded devices or native iPhone receipt. The receiver file digest matched. Server reported zero rejected/duplicate/dropped/stale results. Firmware builds support 65536 bytes; the physically tested file was 4096 bytes.

Later physical evidence supersedes the earlier deployment limitations: both upgraded devices passed a 65.016-second baseline on the running v2 service, with six correlated commands, two verified 4096-byte transfers and 1311 unique matching Python-received results. A right-device power-loss trial observed a new boot and protected reconnection while the left continued uninterrupted. The first 25 Hz candidate exposed source submission congestion and a separate cleanup timeout; its failed report is retained. The user will build the updated native iPhone app on their Mac later.

Final verification: the corrected laptop passed 465 Python tests (3 skipped) and fresh physical baselines. The coarse and fine sweeps established a highest tested clean command setting of 70 Hz, measured at approximately 66 packets/second per ESP and 33.792 kbps combined on its 65-second repeat; 75 Hz failed from 260 right-device source submission rejections. Raw ACK/result identities and source boundaries were independently audited. Both ESPs were reset to 10 Hz without cleanup errors, and a final read-only check confirmed the running Ultra96 process, deployed source hashes, loopback listeners and TLS subscription. The live server diagnostic trace reached its bounded cap; complete client ledgers provide per-run delivery evidence. The user deferred the physical range test as well as the native iPhone build/test.
