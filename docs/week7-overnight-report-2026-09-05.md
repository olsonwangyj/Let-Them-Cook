# Week 7 overnight execution report — 2026-09-05

> **Evidence boundary:** This is not a Gate A–M blanket sign-off. Each claim below
> is limited to its recorded unit, physical-hardware, or inspection evidence.
> The whole-range review and disposition of its findings are recorded in Section
> 11.

## 1. Executive summary

This isolated overnight branch implemented and physically exercised a test-only
Gate D ATT-MTU/notification-boundary probe, then repaired two Gate C cleanup
problems exposed during physical regression and a third deadline problem found
by independent review. The Gate D evidence established an ATT
MTU of 517 and an exact 514-byte notification-value boundary on the tested
DFR0478/Windows connection. At code HEAD `2274b06`, the final fresh Laptop suite
passed 41/41 tests, the fresh external PlatformIO build passed, the real Gate D
probe passed, and ten of ten real Gate C target-20 runs exited 0 with 20–22
counters received and every reported anomaly, cleanup, and reconnect count zero.

Earlier at `d59f38e`, a real target-1,000 run exited 0 with
`received_count=1001`, `elapsed=103.5s`, and all reported anomaly/cleanup counts
zero. The 600-second Gate C soak also exited naturally with exit 0 after 600.609
seconds, receiving 5,976 counters with every supplied anomaly, cleanup, and
reconnect count zero. Neither run induced an ESP power loss, so they do not prove
the Gate C power-loss/reconnect criterion.

No SSH tunnel was created. No Ultra96 application service was reached or tested.
No Phone or Unity receiver was used. No partial or full end-to-end test occurred.
No credential was sent, stored, or copied into this report.

## 2. Scope, topology, and implementation guardrails

### Authorized overnight scope

- Add Gate D diagnostic-only GATT control and notification characteristics next
  to the existing Gate B/C counter characteristic.
- Add a Windows/Bleak Gate D probe that tests a safe value, `MTU-3`, and
  `MTU-2`, and reports corruption, unexpected notifications, queue drops, and
  cleanup failures.
- Preserve the existing diagnostic counter path.
- Diagnose and repair Gate C teardown failures without making cleanup unbounded.
- Stop at the next manual or architectural approval boundary.

### Guardrails preserved

- ESP32-to-Laptop remains BLE/GATT. The ESP32 remains the BLE Peripheral/GATT
  Server and the Laptop remains the BLE Central/GATT Client.
- The selected deployment topology remains Laptop TLS/TCP through the Laptop's
  own SSH local forward (`-L`) to an Ultra96 loopback ingestion service.
- The intended result path remains Ultra96 to Phone/Unity over the Phone's own,
  independent SSH `-L` and application connection.
- There is no ESP32 Wi-Fi, direct Phone-to-Laptop application connection,
  externally exposed Ultra96 application port, SSH reverse forward (`-R`), or
  Laptop relay of `GESTURE_RESULT`.
- Gate D instrumentation is explicitly diagnostic. It does not select a final
  BLE UUID, `SENSOR_BATCH`, sensor schema, byte order, sampling rate, batch size,
  fragmentation scheme, security policy, or production packet contract.
- Four-byte big-endian length plus UTF-8 JSON remains Proposed, not approved.
  No Gate F parser/server was implemented from that proposal.
- Pairing, bonding, link/attribute security, HMAC/HKDF/AES-GCM, TLS
  certificate identity/trust, mTLS, Phone inner protocol, registration,
  association, and routing remain unresolved.
- No password, private key, VPN secret, certificate secret, or raw
  `known_hosts` content appears here.

### Claim boundary

The phrases “hardware-tested” and “real run” below refer only to the physical
DFR0478/COM3 and Windows BLE adapter evidence expressly recorded in the source
reports or transcribed into this report. They do not imply that an SSH tunnel,
Ultra96, Phone, Unity, or an end-to-end path participated.

## 3. Isolation, branch, base, and `main`

Final pre-publication repository inspection recorded:

| Item | Observed state |
| --- | --- |
| Primary worktree | `D:\LetThemCook` |
| Primary branch and HEAD | `main` at `f6bc999cd25d5092f18edb176bd14305ab534e60` |
| Primary worktree status | Clean: `## main...origin/main` |
| Isolated worktree | `D:\LetThemCook-worktrees\week7-stage-d-onward` |
| Isolated branch and code HEAD | `feature/week7-stage-d-onward` at `2274b0603a7fcd399deb968061e912c8048b63b4` |
| Approved base | `f6bc999cd25d5092f18edb176bd14305ab534e60` |
| Merge base with `main` | `f6bc999cd25d5092f18edb176bd14305ab534e60` |
| Behind/ahead versus `main` | `0 5` from `git rev-list --left-right --count main...HEAD`; zero behind and five local implementation commits ahead |
| Isolated worktree at latest pre-publication check | Only this report was untracked; focused review-fix confirmation subsequently approved its report-only commit |

The observed worktree topology came from `git worktree list --porcelain`; branch
and commit relationships came from `git rev-parse`, `git merge-base`, and
`git rev-list`. The exact bootstrap/worktree-creation command was not present in
the supplied evidence and is intentionally not reconstructed.

All implementation commits are local to `feature/week7-stage-d-onward`. Nothing
was pushed, merged, or edited in the `main` worktree while producing this report.
The implementation commits and report publication are intentionally separate.
At the final pre-publication check this report was uncommitted; focused
review-fix confirmation then approved it for its own local report-only commit.

## 4. Local commits and changed files

The history in `f6bc999..HEAD`, in chronological order, is:

| Local commit | Time (+08:00) | Subject | Files |
| --- | --- | --- | --- |
| `3dc29b7facc91bac51687b90bb1d29855316f12f` | 2026-09-05 01:23:29 | `feat: add Gate D MTU diagnostic probe` | `firmware/esp32/src/main.cpp`; new `laptop/mtu_probe.py`; new `laptop/tests/test_mtu_probe.py` |
| `d106c7f757339e4a0cfdff077def2b8f7b5b9ddf` | 2026-09-05 01:30:31 | `fix: account for late MTU probe notifications` | `laptop/mtu_probe.py`; `laptop/tests/test_mtu_probe.py` |
| `b6c5c0be91fb797a49edbd1bad32b92d75830d8a` | 2026-09-05 01:47:43 | `fix: extend Windows BLE cleanup grace` | `laptop/ble_counter_receiver.py`; `laptop/tests/test_ble_counter_receiver.py` |
| `d59f38e1846347182a7bd611eab815c1d4cb4da7` | 2026-09-05 01:52:40 | `fix: skip cleanup for unsubscribed BLE clients` | `laptop/ble_counter_receiver.py`; `laptop/tests/test_ble_counter_receiver.py` |
| `2274b0603a7fcd399deb968061e912c8048b63b4` | 2026-09-05 02:08:19 | `fix: bound cancellation-resistant BLE cleanup` | `laptop/ble_counter_receiver.py`; `laptop/tests/test_ble_counter_receiver.py` (+127/-1 in this commit) |

Net committed delta from the approved base through code HEAD `2274b06`: five
tracked files, 924 insertions, and 23 deletions:

- Modified: `firmware/esp32/src/main.cpp`
- Modified: `laptop/ble_counter_receiver.py`
- Added: `laptop/mtu_probe.py`
- Modified: `laptop/tests/test_ble_counter_receiver.py`
- Added: `laptop/tests/test_mtu_probe.py`

No other tracked file is part of the local implementation commit range. The only
intended report-preparation change is
`docs/week7-overnight-report-2026-09-05.md`; it remains separate until the planned
report-only local commit.

## 5. Chronological command, result, and log evidence

Evidence in this section comes from committed code/tests, the local SDD ledger
and task reports, and controller-observed console output transcribed during this
execution. The final controller commands and outcomes are also retained in the
SDD ledger under “Final controller evidence transcript.”

### 5.1 Baseline and prerequisite inspection

The SDD ledger records a fresh baseline of 30/30 Laptop tests passing and a
fresh PlatformIO build passing with RAM 39,060/532,480 bytes (7.3%) and flash
1,125,769/1,310,720 bytes (85.9%). It also records the physical DFR0478 CH340 on
COM3, the Intel BLE adapter, and read-only endpoint observations of ATT MTU 517.
The exact bootstrap, baseline-test, and baseline-build command lines were not
captured in the supplied evidence; none is invented here.

Recorded tool/runtime versions are Python 3.12.4, Bleak 3.0.1, OpenSSH for
Windows 9.5p2, and Git 2.46.0. The fresh external firmware build described in
Section 5.7 used PlatformIO Core 6.1.19, Espressif32 platform 7.1.0, Arduino
framework 3.20017.241212, and BLE library 2.0.0.

The Gate G prerequisite work was read-only. OpenSSH for Windows 9.5p2 was
present; existing host-key entries were observed but their contents are
deliberately omitted. DNS resolution was observed. A non-interactive,
strict-host-key, key-only ProxyJump probe failed before authentication with a
banner-exchange timeout. A later direct TCP/22 check reached the bastion, and a
strict SSH attempt reached authentication but key-only login was denied. The
exact SSH and reachability commands were not captured and are intentionally not
reconstructed. No credential was sent and no tunnel was created.

### 5.2 Gate D RED, implementation, and first hardware pass

The focused RED command is recorded exactly as:

```text
C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m unittest laptop.tests.test_mtu_probe -v
```

It exited 1 with `ModuleNotFoundError: No module named 'laptop.mtu_probe'`.
After the minimal implementation, the same focused suite was reported as four
tests passing in 4.141 seconds, exit 0.

Before the firmware change, a bounded real Laptop probe against the existing
Gate B firmware failed as intended because the Gate D control characteristic
did not exist:

```json
{"error":"required Gate D write control characteristic is missing"}
```

That run exited 1. Its exact invocation was not recorded.

The firmware was then built and uploaded to the real DFR0478. PlatformIO
reported `Hard resetting via RTS pin`, so no manual RESET/BOOT action was needed.
The first physical Gate D pass exited 0 and reported:

```json
{"cleanup_error_count":0,"queue_drop_count":0,"trials":[{"outcome":"exact","payload_exact":true,"received_length":20,"requested_length":20},{"outcome":"exact","payload_exact":true,"received_length":514,"requested_length":514},{"outcome":"laptop_absence","payload_exact":false,"received_length":null,"requested_length":515}],"unexpected_notification_count":0,"value_boundary":514,"windows_att_mtu":517}
```

Correlated physical ESP serial evidence recorded:

```text
ble_connected boot_id=2795988355 counter=0 uptime_ms=52347
ble_mtu_changed conn_id=0 negotiated_mtu=517 uptime_ms=52348
mtu_probe_submitted requested_length=20 negotiated_mtu=517 allowed_length=514 boot_id=2795988355 uptime_ms=54264
mtu_probe_submitted requested_length=514 negotiated_mtu=517 allowed_length=514 boot_id=2795988355 uptime_ms=54293
mtu_probe_rejected requested_length=515 negotiated_mtu=517 allowed_length=514
ble_disconnected boot_id=2795988355 counter=0 uptime_ms=58642
ble_advertising_restarted boot_id=2795988355 counter=0 uptime_ms=58642
```

This is evidence of exact 20-byte and 514-byte delivery and explicit
pre-submission rejection/absence at 515 bytes on this connection. Firmware log
word `submitted` is not treated as a delivery acknowledgement; the Laptop's
exact-byte observations provide the delivery evidence.

The accompanying Gate C regression received five counters with no reported
gap, duplicate, out-of-order, malformed, queue-drop, or cleanup error and exited
0. The full Laptop suite then passed 34 tests in 5.792 seconds. A fresh external
PlatformIO build passed in 14.64 seconds. The report preserves only a redacted
external build-directory path, so this report does not fabricate the full
command.

### 5.3 Gate D review and `d106c7f` fix round

Review found that a primary GATT error could hide a teardown failure and that a
late callback during teardown could escape anomaly accounting. Focused RED
evidence reported five tests with one failure and one error in 6.174 seconds,
exit 1. After the fix, the focused suite passed five tests in 6.201 seconds,
exit 0, and the full Laptop suite passed 35 tests in 7.932 seconds, exit 0.

A fresh real Gate D run after `d106c7f` exited 0:

```json
{"cleanup_error_count":0,"error":null,"queue_drop_count":0,"trials":[{"outcome":"exact","payload_exact":true,"received_length":20,"requested_length":20},{"outcome":"exact","payload_exact":true,"received_length":514,"requested_length":514},{"outcome":"laptop_absence","payload_exact":false,"received_length":null,"requested_length":515}],"unexpected_notification_count":0,"value_boundary":514,"windows_att_mtu":517}
```

The task review was then clean for the Gate D task. Two minor unit-test gaps were
explicitly deferred and remain open:

- The fake scanner does not exercise the exact advertised-service predicate.
- Payload tests do not cover modulo-256 pattern wrap at the real 514-byte
  boundary.

### 5.4 Gate C cleanup investigation and `b6c5c0b`

A fresh real Gate C regression received 21 sequential counters without a stream
anomaly but exited 1 because cleanup exceeded the former shared 250 ms grace.
Five reproductions yielded four passes and one cleanup failure. Eight direct
Windows/Bleak timing observations put `stop_notify` at 31–109 ms and
`disconnect` at 94–125 ms; installed Bleak 3.0.1 WinRT includes a deliberate
100 ms delay in `disconnect()`.

The focused test command recorded for the cleanup-latency case was:

```text
python -m unittest laptop.tests.test_ble_counter_receiver.LifecycleBoundTests.test_windows_cleanup_latencies_fit_within_one_shared_deadline -v
```

The task report states that this and the other Task 2 commands used
`C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe` with
`PYTHONDONTWRITEBYTECODE=1`; it does not preserve the exact shell syntax used to
set that environment value. Before the production change, the focused test
failed for the intended reason with two cleanup timeouts in 0.291 seconds. After
changing the shared deadline from 0.25 to 1.0 seconds and reserving 0.25 seconds
for disconnect, the test passed in 0.404 seconds. The strengthened lifecycle
class passed 11 tests in 4.503 seconds, and the full Laptop suite passed 36 tests
in 10.884 seconds.

### 5.5 First real repetition set and `d59f38e` lifecycle correction

Ten real target-20 runs used the recorded invocation:

```text
python -m laptop.ble_counter_receiver --target-received 20
```

Eight runs exited 0. Runs 6 and 7 exited 1 after retries encountered a connected
device missing the required diagnostic GATT service; cleanup then attempted
`stop_notify` despite subscription never completing, producing one or two
cleanup errors. Those failures were retained as failures; they were not counted
as passes or dismissed as noise.

Two focused RED tests then required a missing-GATT case and a
`start_notify`-failure case to skip `stop_notify`, still disconnect once, and
avoid a false cleanup error. The report abbreviates the multi-test command with
ellipsis, so an exact command is not reconstructed here. Both tests failed for
the intended `stop_notify_calls` mismatch before the fix. After `d59f38e`, the
two focused tests passed in 0.160 seconds, the lifecycle suite passed 13 tests in
4.687 seconds, and the full Laptop suite passed 38 tests in 10.993 seconds.

The Task 2 report explicitly states that no follow-up hardware run had been done
when that report was closed. The following later controller evidence fills part
of that gap.

### 5.6 Post-`d59f38e` physical Gate C evidence

- Ten of ten real target-20 runs exited 0.
- Each run received 20 or 21 counters.
- Every reported anomaly and cleanup count in all ten runs was zero.
- One separate real target-1,000 run exited 0 with
  `received_count=1001`, `elapsed=103.5s`, and every reported anomaly and
  cleanup count zero.
- The ten short runs used `PYTHONDONTWRITEBYTECODE=1` and:

```text
C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m laptop.ble_counter_receiver --target-received 20 --scan-timeout-seconds 8 --reconnect-delay-seconds 0.1
```

- The target-1,000 run used the same command with `--target-received 1000`.
- The separate 600-second duration soak used the exact command below with
  `PYTHONDONTWRITEBYTECODE=1`:

```text
C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m laptop.ble_counter_receiver --duration-seconds 600 --scan-timeout-seconds 8 --reconnect-delay-seconds 0.1
```

It exited 0 and reported the following supplied summary values:

```text
cleanup=0 duplicate=0 elapsed=600.609 gap=0 malformed=0
observations connection=[2.328] scan=[0.313] subscription=[0.032]
out_of_order=0 queue_drop=0 received=5976 reconnect=0
```

The soak process exited naturally. Because `reconnect=0`, this is ten-minute
stability evidence, not evidence of recovery after an induced power loss.

### 5.7 Fresh external firmware build at `d59f38e`

A fresh build at HEAD `d59f38e` used an output directory outside the repository
and exited successfully in 14.78 seconds. It used external
`PLATFORMIO_BUILD_DIR=C:\Users\Yanjie Wang\AppData\Local\Temp\cg4002-week7-final-d59f38e-20260905`
with `platformio run --project-dir firmware\esp32`. Recorded versions and sizes
were:

| Build item | Result |
| --- | --- |
| PlatformIO Core | 6.1.19 |
| Espressif32 platform | 7.1.0 |
| Arduino framework | 3.20017.241212 |
| BLE library | 2.0.0 |
| RAM | 39,084/532,480 bytes (7.3%) |
| Flash | 1,127,613/1,310,720 bytes (86.0%) |
| Elapsed | 14.78 seconds |

Because a further TDD correction was already in progress when this evidence
arrived, this `d59f38e` build is intermediate evidence, not a substitute for the
later build at final code HEAD.

### 5.8 Independent finding and `2274b06` cancellation-resistant cleanup

Independent Task 2 review initially returned **With fixes**. The finding was that
`asyncio.wait_for` could wait for delayed WinRT-like cancellation past its
nominal timeout, consume the shared cleanup reserve, and prevent a timely
disconnect attempt.

The correction in `2274b06` supervises a separately retained, shielded cleanup
task. On the supervisory timeout it returns control, cancels and observes the
retained child, and allows the disconnect attempt to start within the shared
deadline. Outer task cancellation is still re-raised rather than swallowed.

RED evidence recorded the cancellation-resistant scenario at 1.297 seconds,
over the required 1.15-second bound, without a timely disconnect. Separate
task-retention checks were also RED with two failures. GREEN evidence then
recorded:

- Focused cancellation/retention cases: 3/3 passed in 3.047 seconds.
- Gate C lifecycle suite: 16/16 passed in 7.743 seconds.
- Full Laptop suite: 41/41 passed in 14.121 seconds.

The exact focused and lifecycle command lines were not supplied and are not
reconstructed. Independent re-review of `2274b06` subsequently returned
**APPROVED**: the Important finding was addressed and there were no new Critical
or Important findings. That re-review also recorded 16/16 lifecycle tests,
41/41 full-suite tests, and a passing diff check.

### 5.9 Post-`2274b06` real Gate C and Gate D regressions

Ten of ten real Gate C target-20 runs exited 0. Every supplied anomaly, cleanup,
and reconnect count was zero. Exact received and elapsed values were:

| Run | Received | Elapsed seconds | Exit | Anomaly/cleanup/reconnect counts |
| ---: | ---: | ---: | ---: | --- |
| 1 | 21 | 6.344 | 0 | all zero |
| 2 | 21 | 8.500 | 0 | all zero |
| 3 | 21 | 8.046 | 0 | all zero |
| 4 | 21 | 8.437 | 0 | all zero |
| 5 | 21 | 8.281 | 0 | all zero |
| 6 | 22 | 8.703 | 0 | all zero |
| 7 | 21 | 8.157 | 0 | all zero |
| 8 | 20 | 8.313 | 0 | all zero |
| 9 | 21 | 8.703 | 0 | all zero |
| 10 | 21 | 10.312 | 0 | all zero |

The post-`2274b06` target-20 runs used `PYTHONDONTWRITEBYTECODE=1` and:

```text
C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m laptop.ble_counter_receiver --target-received 20 --scan-timeout-seconds 8 --reconnect-delay-seconds 0.1
```

The real Gate D rerun used `PYTHONDONTWRITEBYTECODE=1` and this exact command:

```text
C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m laptop.mtu_probe
```

It exited 0 with:

```json
{"cleanup_error_count":0,"error":null,"queue_drop_count":0,"trials":[{"outcome":"exact","payload_exact":true,"received_length":20,"requested_length":20},{"outcome":"exact","payload_exact":true,"received_length":514,"requested_length":514},{"outcome":"laptop_absence","payload_exact":false,"received_length":null,"requested_length":515}],"unexpected_notification_count":0,"value_boundary":514,"windows_att_mtu":517}
```

The simultaneous COM3 PlatformIO monitor recorded:

```text
ble_connected boot_id=2795988355 counter=7712 uptime_ms=2918582
ble_mtu_changed conn_id=0 negotiated_mtu=517 uptime_ms=2918583
mtu_probe_submitted requested_length=20 negotiated_mtu=517 allowed_length=514 boot_id=2795988355 uptime_ms=2921039
mtu_probe_submitted requested_length=514 negotiated_mtu=517 allowed_length=514 boot_id=2795988355 uptime_ms=2921068
mtu_probe_rejected requested_length=515 negotiated_mtu=517 allowed_length=514
ble_advertising_restarted boot_id=2795988355 counter=7712 uptime_ms=2926556
ble_disconnected boot_id=2795988355 counter=7712 uptime_ms=2926556
```

The monitor was stopped with Ctrl+C and its session ended.

### 5.10 Final controller suite and code-HEAD firmware build

The final fresh Laptop suite used `PYTHONDONTWRITEBYTECODE=1` and this exact
command:

```text
C:\Users\Yanjie Wang\.virtualenvs\let-them-cook-comms\Scripts\python.exe -m unittest discover -s laptop\tests -v
```

It reported `Ran 41 tests in 14.138s`, `OK`, and `TEST_EXIT=0`.

The fresh external PlatformIO build at code HEAD `2274b06` used:

```text
PLATFORMIO_BUILD_DIR=C:\Users\Yanjie Wang\AppData\Local\Temp\cg4002-week7-final-2274b06-20260905
platformio run --project-dir firmware\esp32
```

The first line records the exact environment value; no unevidenced shell syntax
for assigning it is implied. The build exited 0 in 14.88 seconds with RAM
39,084/532,480 bytes (7.3%) and flash 1,127,613/1,310,720 bytes (86.0%). It used
PlatformIO Core 6.1.19, Espressif32 platform 7.1.0, Arduino framework
3.20017.241212, and BLE library 2.0.0. The build directory was outside the
repository.

### 5.11 Process audit and targeted cleanup

The first final-process filter found two SSH child processes left from the 00:52
non-interactive prerequisite probe and their old PowerShell parent. This is
recorded explicitly; the processes had remained after the probe. Their creation
times and command lines were inspected to identify the exact children and parent.
Neither SSH child contained `-L`, and neither was a tunnel.

Only those verified SSH child processes and that exact parent shell were
stopped. The follow-up audit returned:

```text
NO_MATCHING_TEST_OR_TUNNEL_PROCESSES
```

The exact numeric process IDs are intentionally omitted from this durable
report; the inspected process relationship and clean re-audit marker are
retained in the SDD ledger. No credential or sensitive command-line value is
included.

## 6. Verification claim matrix

“Yes” means supported by the evidence identified in this report. “Pending” or
“No” must not be promoted to “Yes” by inference.

| Deliverable or behavior | Implemented | Unit-tested | Hardware-tested | End-to-end-tested |
| --- | --- | --- | --- | --- |
| Gate D diagnostic firmware: MTU callback, separate control/probe characteristics, `MTU-3` guard, deterministic payload | Yes | No host-side firmware unit test recorded | Yes: real DFR0478 at 20/514/515 bytes | No |
| Laptop Gate D scanner/GATT validation, ordered trials, exact payload checks, anomaly and cleanup accounting | Yes | Yes: focused suites through 5 tests; included in final 41/41 suite | Yes: final real Windows/Bleak pass at `2274b06` | No |
| Gate C single bounded cleanup deadline with 1.0 s total and 0.25 s disconnect reserve | Yes | Yes: focused latency cases and final 16/16 lifecycle suite | Yes: exercised by real Gate C runs | No |
| Gate C subscription-state cleanup guard from `d59f38e` | Yes | Yes: two focused RED/GREEN cases and 38-test suite | Regression only: post-fix real runs were clean, but missing-GATT/start-notify failure was not physically induced | No |
| Cancellation-resistant cleanup supervision from `2274b06` | Yes | Yes: focused 3/3, lifecycle 16/16, final full suite 41/41; RED timing/retention failures preserved | Regression only: post-fix real runs were clean, but delayed cancellation was not physically induced | No |
| Gate C target-1,000 counter criterion | Existing receiver plus fixes | Covered indirectly by receiver unit tests; target itself is a physical run | Yes: exit 0, 1,001 received, 103.5 s, zero reported anomaly/cleanup counts | No |
| Gate C 600-second soak | Existing duration mode; no new implementation claimed | Duration/cleanup bounds have unit coverage | Yes at `d59f38e`: exit 0, 5,976 received in 600.609 s, supplied anomaly/cleanup/reconnect counts zero | No |
| Final Gate D regression at code HEAD | Already implemented | Included in final 41/41 Laptop suite | Yes at `2274b06`: MTU 517, exact 20/514, 515 absent, zero reported counts; serial correlated and monitor ended | No |
| Gate E dummy sensor packet and codecs | No | No | No | No |
| Gates F/G Ultra96 ingestion, SSH `-L`, and TLS/TCP path | No | No | No | No |
| Gates H/I/J bridge, result generation/router, Gateway, and desktop simulator | No | No | No | No |
| Gates K/L/M partial E2E, BLE security, and real Phone/Unity path | No | No | No | No |

## 7. Gate A–M status

| Gate | Status in this report | Evidence and remaining condition |
| --- | --- | --- |
| **A — serial smoke** | **Inherited; not re-attested overnight** | Gate A firmware predates the audited commit range. Current serial logs show boot/uptime data, but the supplied overnight sources do not contain a fresh five-minute serial run plus reset and full USB power-cycle evidence. Do not issue a new Gate A pass from this report. |
| **B — BLE advertisement/counter** | **Inherited; partially corroborated** | The existing service/counter path was preserved and used by real Gate C/D runs. A dedicated fresh Gate B acceptance record covering discovery and connect/disconnect without unexpected reboot is not included. |
| **C — Bleak receiver** | **Partial; explicit power-loss recovery still untested** | At `d59f38e`, the target-1,000 run and 600-second soak exited 0 with zero supplied anomaly/cleanup counts; the soak had `reconnect=0`. At `2274b06`, 10/10 target-20 runs exited 0 with every supplied anomaly/cleanup/reconnect count zero. No supplied evidence establishes the required induced ESP power-loss, rescan, reconnect, resubscribe, and new-boot recognition test. |
| **D — ATT MTU/boundary** | **PASS on final code-HEAD physical evidence** | At `2274b06`, both physical endpoints reported MTU 517; 20 and 514 bytes arrived exactly; 515 bytes was rejected before send and absent on the Laptop; all Laptop counts were zero; the simultaneous monitor recorded the corresponding ESP events and was stopped. Deferred minor unit gaps are listed in Sections 5.3 and 9. |
| **E — approved dummy packet/codecs** | **`PENDING_MANUAL_APPROVAL`** | The plan requires explicit packet-choice approval after Gate D. No production/dummy sensor packet, golden vector, or codec was selected or implemented. |
| **F — Ultra96 loopback ingestion** | **`PENDING_MANUAL_PROTOCOL` + `PENDING_MANUAL_CREDENTIALS`** | Framing, maximum frame size, and ACK contract remain unapproved; authenticated Ultra96 access is unavailable to automation. No server/parser was implemented or tested on Ultra96. |
| **G — SSH `-L` + TLS/TCP** | **`PENDING_MANUAL_CREDENTIALS` + `PENDING_MANUAL_TLS_DESIGN`** | Exact ports, certificates, trust anchor, SAN/SNI identity, and mTLS remain unresolved. No tunnel and no plaintext fallback were created. |
| **H — BLE-to-Ultra96 bridge** | **Blocked by E + G** | No bridge was wired; no queue behavior is claimed as an integrated transport. |
| **I — deterministic Ultra96 result** | **Blocked by F/G + unresolved result schema** | No result generator/router was implemented or exercised. |
| **J — Gateway + desktop PhoneSimulator** | **Blocked by I + unresolved inner protocol** | No simulator/Gateway run occurred and no Laptop result relay was introduced. |
| **K — partial real-ESP end-to-end rehearsal** | **Blocked by H + I + J** | No partial end-to-end rehearsal occurred. Mocks would not satisfy this gate. |
| **L — BLE security + protected regression** | **`PENDING_MANUAL_SECURITY_APPROVAL`** | Pairing, bonding, encryption/authentication permissions, and recovery policy remain unresolved. No protected regression occurred. |
| **M — real Phone/Unity** | **`PENDING_MANUAL_PHONE`** | Teammate receiver, Phone-owned SSH `-L`, credential/host-key handling, and inner protocol are unavailable or unresolved. No Phone/Unity test occurred. |

## 8. Rulings carried forward verbatim

The following are every `Ruling:` line in the current SDD progress ledger,
reproduced verbatim:

- Ruling: Use an external linked-worktree directory instead of the unignored repository-local `.worktrees` default — this preserves the explicit prohibition on modifying `main` — cost if wrong: only the worktree location differs from the skill default.
- Ruling: Gate D may add test-only control/probe GATT characteristics beside, not in place of, the existing counter characteristic — a separate probe prevents MTU experiments from breaking Gate C and does not select a production UUID or packet format — cost if wrong: these diagnostic UUIDs and probe code will need removal or replacement.
- Ruling: Treat Windows `GattSession.max_pdu_size`/Bleak `mtu_size` as the Laptop ATT-MTU observation and validate `MTU-3` with exact real notification lengths — this follows installed Bleak/WinRT behavior, while the physical boundary trial remains authoritative — cost if wrong: the field label/reporting must change, but the exact-length trial remains valid.
- Ruling: Explicitly reject a requested probe payload larger than negotiated `MTU-3` before calling `setValue()`/`notify()` — the installed Arduino wrapper only warns and still passes the full length to ESP-IDF — cost if wrong: the conservative guard could reject a capability a different stack exposes, without affecting production contracts.
- Ruling: The latest user-supplied bastion hostname `stujump.comp.nus.edu.sg` supersedes the plan's `stfjump` spelling for safe prerequisite probes only — no repository contract will be changed until a working, verified connection is available — cost if wrong: Gate G remains PENDING_MANUAL and no tunnel is created.
- Ruling: keep one bounded cleanup deadline but use a 1.0 s diagnostic default with a 0.25 s disconnect reserve — this accommodates the installed Bleak fixed delay and observed jitter without making cleanup unbounded — cost if wrong: target/duration runs may take up to 0.75 s longer after their stop criterion than the previous diagnostic behavior.
- Ruling: Supervise cancellation-resistant BLE cleanup with retained shielded tasks and proceed after the supervisory timeout instead of awaiting delayed cancellation completion — this preserves the shared deadline and starts the reserved disconnect attempt under WinRT-like behavior — cost if wrong: a native cleanup operation may finish after the run summary, and process shutdown can still depend on a non-cooperative OS operation eventually settling.

## 9. Blockers and open risks

### Immediate blockers

- Gate C cannot receive a complete gate pass without the explicit manual ESP
  power-loss/rescan/reconnect/resubscribe/new-boot test.
- Gate E requires explicit user approval of a test packet format.
- Gate F requires an approved framing/maximum-size/ACK contract and manual
  authenticated access.
- Gate G requires manual authenticated access plus an approved TLS port,
  certificate, trust, identity, and mTLS design.
- Gates H–M remain blocked by their dependency and approval chain as shown in
  Section 7.

### Remaining risks

- ATT MTU 517 and value boundary 514 are observations for this physical
  DFR0478/Windows link; they are not a universal BLE capability or a production
  payload selection.
- The Gate D Laptop probe directly awaits `stop_notify()` and `disconnect()`
  without the cancellation-resistant shared cleanup supervisor now used by the
  Gate C receiver. A stalled WinRT/Bleak teardown could therefore delay or
  prevent the diagnostic JSON summary. This does not invalidate the completed
  boundary observation or create a false pass; bounded Gate D teardown and its
  delayed-cancellation tests are deferred to a later implementation commit.
- The Gate D fake scanner still does not execute the exact advertised-service
  predicate, and the unit payload fixtures still do not wrap modulo 256 at 514
  bytes. Physical evidence mitigates but does not remove those unit-test gaps.
- A target run may consume one notification already queued after its stop
  threshold, explaining 20–22 and 1,001 received counts. That is not itself an
  anomaly, but full summaries must continue to show gaps, duplicates,
  out-of-order values, malformed packets, queue drops, and cleanup failures.
- Windows/Bleak cleanup timing is variable. The new grace is bounded but may add
  up to 0.75 seconds beyond the previous diagnostic behavior.
- A nominal `asyncio.wait_for` timeout did not guarantee prompt return when
  WinRT-like cancellation was delayed. `2274b06` addresses this with supervised,
  retained shielded tasks and passed focused, lifecycle, full-suite,
  real-hardware-regression, and focused re-review checks. The delayed-cancellation
  fault branch itself was exercised by a boundary fake, not induced on hardware.
  A native operation may still finish after the summary, and process shutdown
  may still depend on a non-cooperative OS operation eventually settling. The
  completed process audit found and removed lingering prerequisite-probe
  processes before returning a clean re-audit.
- Diagnostic GATT UUIDs/probe behavior could accidentally be treated as a
  production contract unless the test-only labeling is retained.
- The final code-HEAD build uses 86.0% of the configured flash limit. That is
  verified for the diagnostic firmware but leaves limited headroom for later
  gates.
- The plan uses `stfjump` while the progress ruling permits user-supplied
  `stujump` only for safe probes. Neither spelling should be silently frozen into
  a new repository contract without a verified working path.
- Network reachability and authentication observations do not prove a tunnel,
  TLS identity validation, Ultra96 loopback binding, application framing, or
  failure recovery.
- No current evidence covers Phone SSH lifecycle, Unity, result association, BLE
  security, or any partial/full end-to-end path.

## 10. Required manual and hardware tests

Before any broader Week 7 completion claim, record at least:

1. Exercise explicit ESP power loss during Gate C: detect disconnect, rescan,
   reconnect, rediscover, resubscribe, identify the new boot, and report timing
   and all anomalies.
2. If Gate A/B are to be newly signed off, perform their complete prescribed
   physical acceptance tests: five-minute serial stability, reset, USB power
   cycle, service/Notify discovery, submitted-counter correlation, and
   connect/disconnect without unexpected reboot.
3. Obtain explicit Gate E packet approval before writing codecs or golden
   vectors; then test valid, malformed, and oversized fixtures on both ends.
4. After protocol and access approval, test Gate F locally and on Ultra96,
   including split/coalesced, malformed, oversized, and partial frames and a
   verified `127.0.0.1`-only listener.
5. After TLS design approval, test Gate G through a real Laptop-owned SSH `-L`:
   100 correlated frames, tunnel failure/recovery, and invalid TLS identity with
   no plaintext fallback.
6. Test Gate H bounded queue/drop/staleness behavior with one TCP writer; then
   test Gate I valid/invalid deterministic results and Gate J 100-result,
   malformed-data, and reconnect behavior.
7. Perform Gate K only when H/I/J pass, using the real ESP path for ten minutes
   and separately inducing ESP, SSH, ingestion, and simulator failures.
8. Obtain and implement the Gate L security decision, verify actual protected
   state and bond recovery, and repeat C/E/K under protection.
9. Perform Gate M with a real Phone and teammate receiver using the Phone's own
   SSH `-L`; confirm direct Ultra96-to-Phone result delivery and topology
   compliance.

## 11. Stopped-process and final verification record

The `d59f38e` 600-second Gate C soak exited naturally. The post-`2274b06` Gate D
PlatformIO monitor was stopped with Ctrl+C and its session ended. The process
audit then found and removed two lingering SSH prerequisite-probe children and
their verified old PowerShell parent; neither SSH process used `-L` or formed a
tunnel. The re-audit returned `NO_MATCHING_TEST_OR_TUNNEL_PROCESSES`. The final
41-test suite exited 0, the code-HEAD external build exited 0, and focused
re-review of `2274b06` is approved.

Final Git inspection produced:

```text
git diff --check f6bc999..2274b06
DIFF_CHECK_EXIT=0

git diff --stat f6bc999..2274b06
5 files changed, 924 insertions(+), 23 deletions(-)

HEAD=2274b0603a7fcd399deb968061e912c8048b63b4
BRANCH=feature/week7-stage-d-onward
BASE=f6bc999cd25d5092f18edb176bd14305ab534e60
MAIN=f6bc999cd25d5092f18edb176bd14305ab534e60
ORIGIN_MAIN=f6bc999cd25d5092f18edb176bd14305ab534e60
LEFT_RIGHT=0 5
```

The isolated worktree contained only this untracked report, the primary
`D:\LetThemCook` worktree was clean on `main`, and `git worktree list
--porcelain` confirmed the two expected worktrees and refs. Focused review-fix
confirmation approved publication as a separate local report-only commit; no
implementation file belongs in that commit.

Reviewer `/root/final_whole_range_reviewer` reviewed committed range
`f6bc999cd25d5092f18edb176bd14305ab534e60..2274b0603a7fcd399deb968061e912c8048b63b4`
plus this report at
`D:\LetThemCook-worktrees\week7-stage-d-onward\docs\week7-overnight-report-2026-09-05.md`.
The review found no Critical issue and no Important implementation defect. Its
initial publication verdict was **WITH FIXES** for these report-only items:

- replace the pre-review/pending publication wording with the completed review
  record;
- label the successful cancellation-fix hardware check as a real-hardware
  regression rather than physical induction of the fault branch; and
- disclose that Gate D teardown does not yet have an explicit caller-side
  timeout.

Those required report changes are applied above. The review also retained as
Minor the two already-disclosed Gate D unit-test gaps and the limited residual
risk that a non-cooperative native cleanup task can finish after a summary or
delay process shutdown. Focused follow-up review returned **APPROVED**, with no
remaining Critical or Important inconsistency, and authorized the report-only
local commit.

## 12. Disposition

Current disposition: **report publication approved; feature branch retained for
manual decisions and tests**. Gate D has a final code-HEAD physical pass. Gate C
has positive target-1,000, 600-second-soak, and
post-`2274b06` 10/10 short-run evidence, but still lacks the plan-required manual
power-loss/reconnect demonstration. This report makes no Gate E–M implementation
claim and no partial or full end-to-end claim.
