# Week 7 system reports plan

> **For agentic workers:** Use bounded parallel research and document ownership; review and integrate in this task. Steps use checkbox syntax for tracking.

**Goal:** Deliver two source-grounded reports explaining the complete communication system and how to test and demonstrate it.

**Architecture:** Document the existing two-ESP BLE → Windows → Ultra96 → native Unity iPhone implementation. Explain independent per-device queues and pipelined ACK handling, direct board-to-phone results, and measured delivery limits without changing runtime behavior.

**Tech Stack:** Markdown and Mermaid; existing ESP32 C++, Python asyncio/Bleak/TLS, and native Swift/Unity code.

**Spec:** The user's request in this task: architecture and code/file explanation; executable testing and Week 7 demo instructions; commit, merge, and push all resulting documentation.

## Constraints

- Use revision `79a8c0d` as the initial source baseline; verify remote state before integration.
- The selected physical path uses two protected ESP32 dummy streams at 10 Hz each, Windows BLE, board loopback ports 8888/9999, and the native Unity iPhone receiver.
- Distinguish source/ACK/server-write evidence from aggregate operator-reported Phone counts.
- Preserve historical failures and the limits of live-only operation and manual foreground recovery.
- Do not include passwords, private keys, or local credential contents.
- Commands must identify the machine, directory, prerequisites, expected output, and stop procedure.
- Document authored files individually; explain generated/vendor trees as groups.
- No live BLE, firmware flash, remote board mutation, or iPhone action is needed to author these reports.

## Tasks

- [x] Research and write `docs/week7-system-technical-report.md`: topology, protocols, code flow, concurrency, reliability, security, file inventory, and worked examples.
- [x] Research and write `docs/week7-testing-and-demo-guide.md`: setup, startup order, commands, acceptance, recovery, troubleshooting, evidence capture, and a professor-facing demo script.
- [x] Independently audit file coverage and interface facts against tracked source.
- [x] Verify command syntax with CLI help and bounded local synthetic checks; check all relative links and Markdown structure.
- [x] Add report entry points to `README.md` and `ios-visualizer/README.md`, preserving historical guides as references.
- [x] Review both reports and prepare the documentation for integration.

**Authorized integration:** commit these five Markdown files, fast-forward merge into `main`, push, and verify the remote hash. Git history and the publication receipt record that final action; this plan is part of the commit being published.

## Validation commands

Run from the repository root; these help commands do not open hardware connections:

```powershell
python -m laptop.dual_bridge --help
python -m tools.ssh_tunnel --help
python -m ultra96.server --help
python -m tools.week7_demo --help
python -m tools.rehearse_week7 --help
git diff --check
```

Any local rehearsal uses fresh disposable fixture PKI and local ports. It is labeled synthetic and does not replace the recorded physical acceptance report.

## Verification performed for this documentation change

- Independent source/file review: all 154 baseline files outside the imported export are individually covered; generated/vendor export trees are grouped and their authored integration surfaces identified.
- All 255 local Markdown links resolve; code fences are balanced. All 25 PowerShell examples parse with PowerShell 7.6.5, and all five shell examples pass Git Bash syntax checking.
- CLI help agrees with the documented entry points/options. Five worked JSON messages validate against the board protocol; the binary example round-trips as 32 bytes.
- Isolated local synthetic rehearsal: 100 generated messages, 100 ACKs and 100 subscriber results, with a passing verdict.
- Isolated dual CLI rehearsal: 32 generated messages per device, 64 exact result IDs at a local independent subscriber, clean final report, exit 0, and saved JSON identical to stdout.
- Recorded demo audit: 100 matching unique IDs and `audit_passed: true`; this is archived evidence, not a new physical run.
- Independent review corrections addressed before integration. No runtime source, firmware, board deployment or installed app changes were required.
