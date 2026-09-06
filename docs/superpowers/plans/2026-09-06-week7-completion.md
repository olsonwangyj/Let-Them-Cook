# Week 7 autonomous completion implementation plan

> Use superpowers:subagent-driven-development and verification-before-completion. The user has authorized decisions and execution; no further design approval checkpoint applies.

**Goal:** Complete every feasible Week 7 E–M software deliverable and leave precise physical-only acceptance work.
**Architecture:** Existing BLE diagnostics plus W7 packet, bounded Laptop writer, two-loopback-listener TLS Ultra96 process and independent Phone subscriber.
**Tech Stack:** Arduino ESP32; Python >=3.8 standard library service; Windows Bleak; OpenSSH; TLS.
**Spec:** docs/week7-selected-design-2026-09-06.md

## Constraints
Preserve no ESP Wi-Fi/no reverse SSH/no Laptop result relay. No credentials in Git. Work only in requested worktree. Freeze interfaces from spec before parallel implementation.

## Task 1: Packet/firmware/security
Files common/sensor.py, common/__init__.py, tests/test_sensor.py, tests/fixtures, firmware/esp32.
- [x] Add fixed golden binary/JSON vector and invalid length/version/range/deterministic-value tests; run and capture missing-code failure.
- [x] Implement spec codec and firmware explicit-byte serializer; build; compare firmware serializer bytes with Python fixture where host compiler exists.
- [x] Implement selected security with local serial passkey/bond erasure and protected CCCD/notification gating; build normal and explicit diagnostic profiles.
- [x] Review and commit scoped files.

## Task 2: Framing/TLS/server/result/subscriber
Files common/wire.py, common/tls.py, ultra96, laptop/phone_simulator.py, tools/generate_week7_pki.py, tests/test_transport.py.
- [x] Write negative framing tests and actual loopback TLS tests: 100 ACK/results, exact correlation, invalid identity, malformed data, dedup, subscriber reconnect/replacement, wrong-session rejection.
- [x] Implement framing, selected schemas, TLS-only two-listener server, deterministic router, subscriber and certificate generation.
- [x] Verify isolated tests, review and commit scoped files.

## Task 3: Laptop bridge/SSH/process recovery
Files laptop/bridge.py, tools/ssh_tunnel.py, tests/test_bridge.py, tests/test_ssh_trust.py.
- [x] Write fake BLE/transport boundary tests for callback queue bounds, stale dropping, reconnect, sequence/boot metrics, invalid/uncorrelated ACK and one writer.
- [x] Implement codec bridge with selected interfaces, correlated ACK timeout and bounded lifecycle; implement configurable secure SSH command builder/supervision.
- [x] Run local TLS integration with fake input and, if available, actual ESP; review and commit.

## Task 4: Deployment and manual acceptance
Files docs/week7-runbook.md, docs/week7-continuation-report-2026-09-06.md, phone/Unity, README.md, original plan/architecture supersession notices.
- [x] Probe actual SSH using existing host-key trust; jump host offers only publickey, so supplied passwords cannot authenticate. No remote deployment is claimed; the runbook gives inspection/deployment after authorized access is restored.
- [x] Perform available actual hardware/TLS/100-result, 600 s, protected MTU, reset and bond-loss tests; preserve failures and final authenticated restoration in the report.
- [x] Supply Android own-forward/Unity integration and optional foreground iOS experiment; commands for every remaining physical fault test, expected metrics and acceptance checklist.
- [x] Audit every historic unresolved issue against 24 selected decisions; full test/build, independent review, local implementation commits and final documentation/Git verification.

Local phase finished 2026-09-07 with evidence in docs/week7-continuation-report-2026-09-06.md. The following VPN-enabled continuation supersedes the old remote-access blocker; no design approval remains pending.

## VPN-enabled Ultra96 continuation — 2026-09-07

Current evidence: docs/week7-continuation-report-2026-09-07.md. Decisions 25–28 cover observed VPN/password access, interactive deadlines, owned deployment paths, exact remote acceptance and graceful shutdown.

- [x] Authenticate both SSH hops from PowerShell after VPN connection; inspect actual Python/SSL/ports/permissions without changing shared home ownership.
- [x] Deploy immutable source snapshots and only required server TLS material under a private user-owned /var/tmp directory; verify hashes, imports, key permissions and loopback-only listeners.
- [x] Implement and review longer interactive SSH deadlines, graceful SIGTERM, and a remote-only exact-correlation runner with meaningful clean-soak criteria; run Windows and Linux checks.
- [x] Verify 100 synthetic and 100 protected real-ESP results through separate actual SSH forwards; run actual TLS/schema/dedup/subscriber-replacement negatives.
- [x] Finish a clean 600 s protected real-ESP/Ultra96/independent-desktop-viewer soak and compare remote acceptance logs with exact local ACK/result IDs: 5,965 exact matches in 600.563 s.
- [x] Separately induce ingestion tunnel loss, viewer tunnel loss, server restart and ESP RTS reset; preserve non-clean metrics and recovery; final protected 100/100 passed on cf03318.
- [x] Finalize safe evidence, current runbooks, actual process/deployment state and local commits; retain the deployed server while closing test tunnels. Only physical USB/button and real Phone/teammate integration acceptance remains; final Git verification accompanies the documentation commit.
