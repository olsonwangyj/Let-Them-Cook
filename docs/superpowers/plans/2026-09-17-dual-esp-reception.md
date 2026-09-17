# Dual ESP32 Reception Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Run and measure two simultaneous ESP32 streams without concealing packet loss, while reconnecting each independently.

**Architecture:** Reuse one Bridge owner per explicitly identified ESP, with independent bounded queues and TLS connections. Add source snapshots and constant-space sequence accounting to reconcile each finite uninterrupted capture. Coordinate startup, common observation, notification stop, queue drain and shutdown.

**Tech Stack:** Python 3.10+ Windows Bleak 3.0.1; stdlib asyncio/TLS; existing Arduino ESP32/PlatformIO; portable C++11 host tests; pytest.

**Spec:** `docs/superpowers/specs/2026-09-17-dual-esp-reception.md`

## Global Constraints

- Keep protected BLE, SSH-only board access, TLS trust, existing sensor/result schemas and single-device behavior.
- Keep firmware and default synthetic rate at 10 Hz; distinguish generated sample IDs from successful submissions.
- Source statistics UUID `6e1c0006-7a45-4dc4-b678-3f2d5a9c1001`; 24-byte `<4sB3xIIII`, magic `W7S1`, device, reserved zero bytes, boot, next sequence, submitted, failures.
- Bounded queues/tasks/cleanup and explicit per-device failure accounting; no outage replay or unlimited memory.
- No physical uploads, pairing, campus connections, or hardware-success claims.

### Task 1: Dual receiver, source accounting, and executable acceptance command

**Files:** Modify `laptop/bridge.py`; create `laptop/source_audit.py`, `laptop/dual_bridge.py`, `tests/test_source_audit.py`, `tests/test_dual_bridge.py` and, if appropriate, `tests/test_dual_transport.py`.

**Interfaces:** Existing Bridge/BridgeConfig and codecs are consumed. Produce `SourceStats` parser/audit, independent Bridge lifecycle hooks with opt-in source reconciliation, `DualBridge` coordinator and `python -m laptop.dual_bridge` CLI. Existing APIs keep their default semantics. Source fields match the global binary contract verbatim.

- [x] Write failing behavior tests: decode literal source bytes, reject wrong identity/schema, reconcile generated interval including a missing last packet, and track modulo wrap with constant memory. Example independent fixture: `b'W7S1' + bytes([2,0,0,0]) + bytes.fromhex('07000000030000000300000000000000')` represents device 2, boot 7, next sequence 3, submitted 3, failed 0.
- [x] Run `python -m pytest tests/test_source_audit.py -q` and verify failure is the missing behavior; implement the parser/audit and rerun.
- [x] Write dual behavior tests using real Bridge objects and injected fake Bleak scanner/client boundaries. Assert that device 2 is acknowledged while device 1's ACK is held by an event; both use overlapping sequence numbers safely. Assert stop drains a burst and source counters match received/ACKed counts. Assert wrong device IDs and unavailable source stats cannot pass.
- [x] Run `python -m pytest tests/test_dual_bridge.py -q` before implementation. Implement independent lifecycle, per-device accounting, bounded startup/observation/drain and explicit CLI validation.
- [x] Add real local TLS integration using the repository PKI fixture and `Week7Server`; two sources must deliver exact device-tagged sets. Test a temporary disconnect without stopping the healthy peer, and retain a failing clean-run verdict for the fault.
- [x] Run new suites plus `tests/test_bridge.py`, `tests/test_bridge_disconnect_cleanup.py`, `tests/test_bridge_transport_cleanup.py`, `tests/test_transport.py`. Record commands/results and review concerns.

### Task 2: Source counters and two protected firmware identities

**Files:** Modify `firmware/esp32/src/main.cpp` and `firmware/esp32/platformio.ini`; create `firmware/esp32/include/week7_source_stats.h`, `firmware/esp32/test/host_source_stats.cpp`, `tests/test_firmware_source_stats.py`.

**Interfaces:** Consume unchanged `week7_packet.h`. Produce the protected read-only source-statistics characteristic with the exact global layout. Allocate sequence IDs at each eligible generated sample, account successful/failed sensor submissions independently, and expose the next sequence even after submission failure. Explicit left/right build profiles set ID 1/2.

- [x] Write a host test where sample 0 submission fails, sample 1 succeeds, and the next sequence is 2 with submitted=1 and failed=1. Check exact serialized bytes and uint32 wrap behavior, and invalid buffer/device validation.
- [x] Run `python -m pytest tests/test_firmware_source_stats.py -q` to observe the missing helper; implement the portable helper, integrate source generation and the mutex-protected BLE read callback, then rerun.
- [x] Add protected `firebeetle32-left` / `firebeetle32-right` build flags without weakening shared flags or changing packet size/rate.
- [x] Run firmware host regressions. Locate existing PlatformIO tooling and compile both protected variants if installed; report unavailable tooling precisely. Do not upload or open serial devices.

### Task 3: Integration, documentation and review

**Files:** Create `docs/dual-esp-runbook.md`; update `README.md` and completion notes in this plan/spec as justified by actual tests.

- [x] Document exact build/run commands from implemented CLI help, one-time distinct firmware/identity setup, per-device source counters, normal concurrent soak, separate fault recovery, and why physical evidence remains pending.
- [x] Run the relevant regression suite once after both changes land. Run `python -m laptop.dual_bridge --help`, both firmware builds when possible, and `git diff --check`.
- [x] Request independent spec and code-quality review; fix substantive findings with regression tests, then rerun only affected checks.
- [x] Report implementation status, actual test/build evidence, workspace location, and the remaining two-ESP physical acceptance step.

## Completion evidence — 2026-09-17

- Pulled main to `5a4617b` before implementation. Implementation lives on `codex/dual-esp-reception` in `D:/LetThemCook-worktrees/dual-esp-reception`.
- Final regression: `python -m pytest laptop/tests tests phone/tests -q` — **270 passed, 3 skipped in 103.89 s**. The three skips cover POSIX-only signal/SSH checks on Windows.
- Both protected PlatformIO profiles compiled successfully: `firebeetle32-left` and `firebeetle32-right`. Firmware host checks passed: **54 tests**.
- After the shutdown fix, two consecutive actual CLI runs against one local TLS Week7Server completed cleanly. Run 1 generated, received and acknowledged **31 samples per device**; run 2 reconciled **32 per device**. The server accepted **126 samples**, with zero duplicates or rejections. These were synthetic sources, not physical BLE.
- Independent receiver and firmware reviews passed, including cross-language source-statistics layout and final integration. Review found and drove a fix for unbounded cancellation during shutdown. Its subprocess regression now verifies failure JSON and bounded exit when an ACK read repeatedly suppresses cancellation.
- The first complete Windows run exposed two pre-existing Unix-permission assumptions in `tests/test_ios_export_patch.py`; both failed identically on unchanged main. The tests now compare the actual initial and final file modes, preserving their intended contract across platforms. All **18 iOS export tests** passed; production iOS files were unchanged.
- CLI help and whitespace checks passed. No firmware upload, physical pairing, campus connection or iPhone rebuild was performed. Both boards still need the matching firmware and an uninterrupted 600-second physical acceptance run.
