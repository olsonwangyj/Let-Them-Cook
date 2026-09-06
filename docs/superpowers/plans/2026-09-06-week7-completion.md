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
- [ ] Add fixed golden binary/JSON vector and invalid length/version/range/deterministic-value tests; run and capture missing-code failure.
- [ ] Implement spec codec and firmware explicit-byte serializer; build; compare firmware serializer bytes with Python fixture where host compiler exists.
- [ ] Implement selected security with local serial passkey/bond erasure and protected CCCD/notification gating; build normal and explicit diagnostic profiles.
- [ ] Review and commit scoped files.

## Task 2: Framing/TLS/server/result/subscriber
Files common/wire.py, common/tls.py, ultra96, laptop/phone_simulator.py, tools/generate_week7_pki.py, tests/test_transport.py.
- [ ] Write negative framing tests and actual loopback TLS tests: 100 ACK/results, exact correlation, invalid identity, malformed data, dedup, subscriber reconnect/replacement, wrong-session rejection.
- [ ] Implement framing, selected schemas, TLS-only two-listener server, deterministic router, subscriber and certificate generation.
- [ ] Verify isolated tests, review and commit scoped files.

## Task 3: Laptop bridge/SSH/process recovery
Files laptop/bridge.py, tools/ssh_tunnel.py, tests/test_bridge.py, tests/test_ssh_tunnel.py.
- [ ] Write fake BLE/transport boundary tests for callback queue bounds, stale dropping, reconnect, sequence/boot metrics, invalid/uncorrelated ACK and one writer.
- [ ] Implement codec bridge with selected interfaces, correlated ACK timeout and bounded lifecycle; implement configurable secure SSH command builder/supervision.
- [ ] Run local TLS integration with fake input and, if available, actual ESP; review and commit.

## Task 4: Deployment and manual acceptance
Files docs/week7-runbook.md, docs/week7-continuation-report-2026-09-06.md, phone/Unity, README.md, original plan/architecture supersession notices.
- [ ] Probe actual SSH using existing host-key trust and supplied in-memory credentials; inspect hardware/software before deploying user-owned scoped files.
- [ ] Perform available actual hardware/TLS/100-result tests; preserve failure evidence and cleanup.
- [ ] Supply Android own-forward/Unity integration procedure, commands for every remaining physical fault test, expected metrics and acceptance checklist.
- [ ] Audit every historic unresolved issue against selected decisions, full test/build, independent review, local commits, clean Git verification.
