# Week 7 continuation evidence report — 2026-09-05

## Scope and repository state

This is a supplement to `docs/week7-overnight-report-2026-09-05.md`; that
historical overnight report is unchanged.  It covers continuation work after
`796a31baee8f81d6203d4fb98a606268035e2ce4` through the evidence code HEAD
`c737dc5545696103587a0cbb9c90da9e9bf0c99f`.

All work was performed in the isolated linked worktree
`D:\LetThemCook-worktrees\week7-stage-d-onward` on
`feature/week7-stage-d-onward`.  At evidence collection, `main` and local
`origin/main` both remained
`f6bc999cd25d5092f18edb176bd14305ab534e60`; no push or merge occurred.
The continuation code commits are `021b07d` (Gate D teardown hardening),
`8f26f29` (its review-test fix), and `c737dc5` (the generic queue primitive).

## Task 2 — Gate D cleanup hardening

### Root cause and implementation

Before `021b07d`, `MtuProbe.run()` directly awaited `stop_notify()` and
`disconnect()` in `finally`.  A Windows/Bleak cleanup operation that delayed
or resisted cancellation could postpone the disconnect attempt past the shared
one-second cleanup goal; direct awaits also provided no child task to retain
and later consume on outer cancellation.

`021b07d` applies the existing Gate C discipline to the Gate D diagnostic:
one cleanup deadline, a 0.25-second reserve for disconnect, and a retained,
shielded task for each cleanup coroutine.  The supervisor waits only for its
allocated remainder.  On timeout it records a cleanup error, cancels and
retains the child without waiting for cancellation-resistant completion, then
continues to disconnect; its done callback consumes the eventual result.
Outer cancellation takes the same retain/cancel path and is re-raised.  The
task also made the fake scanner execute the production advertisement predicate
and made the 514-byte fixture wrap modulo 256.

### RED, GREEN, mutation, and review evidence

The RED run, after installing the declared `bleak==3.0.1` dependency into the
active environment without changing repository files, was:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest laptop.tests.test_mtu_probe
```

It ran 10 tests in 15.520 seconds and failed the three intended cases:
cancellation-resistant `stop_notify` supervision, outer-cancellation child
retention, and a single shared grace across two slow cleanup operations.
The restored GREEN command was the same command and passed 10/10 in 14.842
seconds.  The then-full suite was:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s laptop/tests
```

It passed 46/46 in 22.492 seconds; the fresh-venv controller rerun passed
46/46 in 22.944 seconds.  `git diff --check 796a31b..8f26f29` exited zero.

The task review initially found two Important test-evidence defects: the
disconnect-start assertion could permit less than the required 0.25-second
reserve, and the 514-byte test did not require production to classify the
boundary as exact/successful.  `8f26f29` corrected both.  Its temporary,
restored production-only mutations were caught by the focused tests:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest laptop.tests.test_mtu_probe.MtuProbeTests.test_cancellation_resistant_stop_is_supervised_before_reserved_disconnect
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest laptop.tests.test_mtu_probe.MtuProbeTests.test_att_mtu_517_observes_modulo_256_boundary_payload
```

The first failed when the disconnect reserve was weakened from 0.25 to 0.1
seconds; the second failed when production payload generation was truncated at
256 bytes.  Both mutations were restored before GREEN.  Scoped re-review then
found both Important issues addressed and no Critical or Important breakage.

### Current-code hardware regression and limit

The current-code real Gate D command was:

```text
C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m laptop.mtu_probe
```

with `PYTHONDONTWRITEBYTECODE=1`.  It exited zero: Windows ATT MTU was 517,
20 and 514 bytes were exact, 515 was absent at the Laptop, and every anomaly
and cleanup count was zero.  This is current-code hardware evidence for Gate
D.  It does **not** physically induce or prove the delayed-cancellation fault
branch: that branch is fake/unit-tested only, and the supervisor is not a hard
process-level bound because `asyncio.run()` shutdown may still await a
non-cooperative native operation.

## Task 3 — bounded telemetry queue groundwork

`c737dc5` adds `BoundedTelemetryQueue`: an in-memory FIFO for opaque items
with a positive built-in-integer capacity, non-blocking enqueue, exact
drop-oldest eviction when full, cumulative eviction counting, async
`dequeue()`, immediate `dequeue_nowait()`, and occupancy accessors.  Its scope
is deliberately protocol-neutral.

It has no BLE behavior, Ultra96 behavior, transport, codec, timing, sensor,
session, freshness threshold, TCP writer, bridge, packet format, replay
mechanism, or logging policy.  It neither selects a protocol contract nor
claims Gate H, bridge, integration, hardware, or end-to-end behavior.

The focused RED command was:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest laptop/tests/test_bounded_telemetry_queue.py
```

Before the production module existed it failed at collection with the intended
`ModuleNotFoundError`.  The restored command passed 5/5 in 0.14 seconds.  The
full GREEN command:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest laptop/tests
```

passed 51/51 in 22.64 seconds.  Fresh-venv controller verification passed
51/51 in 23.054 seconds; `git diff --check 8f26f29..c737dc5` exited zero and
the commit scope was exactly the two new queue files.  Task review found the
design spec-compliant and quality-approved.  The remaining minor is that the
documented empty-queue `dequeue_nowait()`/`queue.Empty` behavior lacks a direct
regression test.

## Fresh continuation controller evidence

The following evidence is recorded for the current code HEAD `c737dc5`:

- The full fresh-venv Laptop suite passed 51/51 in 23.054 seconds.
- A fresh external PlatformIO build used
  `C:\Users\Yanjie Wang\AppData\Local\Temp\cg4002-week7-final-c737dc5-20260905-01`
  with `platformio run --project-dir firmware\esp32`.  It succeeded in 14.59
  seconds: RAM 39,084/532,480 bytes (7.3%) and flash 1,127,613/1,310,720 bytes
  (86.0%).
- `platformio device list` reported the CH340 at COM3, VID:PID `1A86:7523`.
- The current-code Gate D command above exited zero with ATT MTU 517, exact
  20- and 514-byte trials, no 515-byte Laptop notification, and zero anomaly
  and cleanup counts.
- The current-code short Gate C command was:

  ```text
  C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m laptop.ble_counter_receiver --target-received 20 --scan-timeout-seconds 8 --reconnect-delay-seconds 0.1
  ```

  With `PYTHONDONTWRITEBYTECODE=1`, it exited zero after 21 received counters
  in 5.563 seconds.  Connection, scan, and subscription observations were
  3.109/0.188/0.031 seconds; every stream, queue, reconnect, and cleanup count
  was zero.
- The final filtered audit returned exactly
  `NO_MATCHING_TEST_OR_TUNNEL_PROCESSES`.

No RESET, power cycle, firmware upload, SSH, tunnel, Ultra96, Phone, or
end-to-end operation occurred during this continuation.  In particular, this
record does not claim any SSH/TLS, Ultra96, Phone, security, real sensor/AI,
Gate H, or end-to-end result.

## Evidence-status matrix

| Deliverable or behavior | Implemented | Unit-tested | Hardware-tested | End-to-end-tested |
| --- | --- | --- | --- | --- |
| Gate D bounded diagnostic cleanup and strengthened boundary assertions | Yes | Yes: RED/GREEN, mutations, focused/full suites | Yes: current-code regression; delayed-cancellation fault itself is fake-only | No |
| Current Gate D MTU/boundary diagnostic | Yes | Yes | Yes: MTU 517, exact 20/514, 515 absent | No |
| Gate C short counter path | Existing | Existing tests and cleanup coverage | Yes: 21 counters, exit zero; no power-loss proof | No |
| BoundedTelemetryQueue local primitive | Yes | Yes: focused 5/5 and included in 51/51 | No | No |
| Gate E codecs; F/G transport; H/I/J bridge/result/Gateway; K/L/M | No | No | No | No |

Gate D is therefore current-code hardware-tested, with the stated fake-only
fault limitation.  Gate H remains blocked even though the queue primitive now
exists.

## Gate blockers and limits

- Gate C power-loss/reconnect/new-boot acceptance remains
  `PENDING_MANUAL_HARDWARE`.
- Gate E packet choice remains `PENDING_MANUAL_APPROVAL`.
- Gate F framing, maximum size, ACK, and authenticated deployment access remain
  `PENDING_MANUAL_PROTOCOL` + `PENDING_MANUAL_CREDENTIALS`.
- Gate G credentials and TLS ports, certificates, trust, SAN/SNI, and mTLS
  remain `PENDING_MANUAL_CREDENTIALS` + `PENDING_MANUAL_TLS_DESIGN`.
- Gate H is blocked by E + G; Gate I by F/G and the unresolved result schema;
  Gate J by I and the Phone protocol; Gate K by H/I/J; Gate L by security
  approval; and Gate M by the teammate receiver, Phone, tunnel, and inner
  protocol.

Remaining risks are: (1) `asyncio.run()` shutdown may outlive the cleanup
supervisor; (2) the two fixed-sleep Gate D tests have limited timing margin;
(3) empty `dequeue_nowait()` has no direct regression coverage; (4) firmware
flash remains 86.0%; and (5) measured MTU 517/514 is link-specific rather than
a packet contract.

## Ledger rulings, in chronological order

- Ruling: Use an external linked-worktree directory instead of the unignored repository-local `.worktrees` default — this preserves the explicit prohibition on modifying `main` — cost if wrong: only the worktree location differs from the skill default.
- Ruling: Gate D may add test-only control/probe GATT characteristics beside, not in place of, the existing counter characteristic — a separate probe prevents MTU experiments from breaking Gate C and does not select a production UUID or packet format — cost if wrong: these diagnostic UUIDs and probe code will need removal or replacement.
- Ruling: Treat Windows `GattSession.max_pdu_size`/Bleak `mtu_size` as the Laptop ATT-MTU observation and validate `MTU-3` with exact real notification lengths — this follows installed Bleak/WinRT behavior, while the physical boundary trial remains authoritative — cost if wrong: the field label/reporting must change, but the exact-length trial remains valid.
- Ruling: Explicitly reject a requested probe payload larger than negotiated `MTU-3` before calling `setValue()`/`notify()` — the installed Arduino wrapper only warns and still passes the full length to ESP-IDF — cost if wrong: the conservative guard could reject a capability a different stack exposes, without affecting production contracts.
- Ruling: The latest user-supplied bastion hostname `stujump.comp.nus.edu.sg` supersedes the plan's `stfjump` spelling for safe prerequisite probes only — no repository contract will be changed until a working, verified connection is available — cost if wrong: Gate G remains PENDING_MANUAL and no tunnel is created.
- Ruling: Supervise cancellation-resistant BLE cleanup with retained shielded tasks and proceed after the supervisory timeout instead of awaiting delayed cancellation completion — this preserves the shared deadline and starts the reserved disconnect attempt under WinRT-like behavior — cost if wrong: a native cleanup operation may finish after the run summary, and process shutdown can still depend on a non-cooperative OS operation eventually settling.
- Ruling: Apply Gate C's one-second shared cleanup deadline, 0.25-second disconnect reserve, and retained shielded-task supervision to the Gate D Laptop diagnostic — this closes the report's explicit unbounded-teardown risk without changing any BLE payload or production interface — cost if wrong: the Gate D diagnostic may wait up to one second during cleanup and a cancellation-resistant native operation may still outlive the summary or delay `asyncio.run()` shutdown.
- Ruling: Implement only an opaque, configurable drop-oldest queue primitive as independent Gate H groundwork, with no freshness threshold, writer, bridge, or payload contract — the approved plan explicitly permits generic queue behavior while E and G remain blocked — cost if wrong: the isolated two-file primitive may be removed before bridge implementation and provides no Gate H acceptance evidence.
- Ruling: keep one bounded cleanup deadline but use a 1.0 s diagnostic default with a 0.25 s disconnect reserve — this accommodates the installed Bleak fixed delay and observed jitter without making cleanup unbounded — cost if wrong: target/duration runs may take up to 0.75 s longer after their stop criterion than the previous diagnostic behavior.

## Verification record

Report-source checks covered the Week 7 plan, architecture draft, unchanged
overnight report, SDD ledger, both task reports, and commits `021b07d`,
`8f26f29`, and `c737dc5`.  Before committing this report, run:

```text
git diff --check
```

No source evidence or command line in this report contains credentials.
