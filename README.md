# Let Them Cook — CG4002 Communications

Week 7 runs two protected ESP32 BLE dummy streams concurrently through a Windows bridge to Ultra96. Ultra96 returns ingestion acknowledgements to the laptop and sends gesture results directly to the native Unity iPhone receiver over its own SSH/TLS connection.

Start with the two current reports:

- [System technical report](docs/week7-system-technical-report.md): architecture, parallel processing, packet formats, code walkthroughs, and a file-by-file guide.
- [Testing and Week 7 demo guide](docs/week7-testing-and-demo-guide.md): which commands to run on each machine, expected observations, acceptance criteria, troubleshooting, and a professor-facing demonstration.

The [updated iPhone acceptance report](docs/phone-post-update-test-2026-09-21.md) records successful two-ESP tests at 10 Hz per device, including a 10-minute run with an operator-reported iPhone count of 12,003 matching the source total. These results establish observed delivery under the tested conditions; the system does not replay data across outages, and the iPhone requires manual reconnection after backgrounding or locking. The [dual-ESP runbook](docs/dual-esp-runbook.md) provides additional bridge details, live progress examples, and saved JSON reports using `--report`.

**Additional presentation material:** the earlier [Week 7 demo pack](docs/week7-demo-pack/README.md) includes a [printable three-page brief](docs/week7-demo-pack/teacher-brief.pdf), packet bytes/JSON examples, and a portable recorded 100-packet demonstration. Use the new testing and demo guide for the current two-ESP/native iPhone procedure. `python -m tools.week7_demo packet` explains the fixture without hardware; `sender` displays single-ESP protected BLE packet/ACK evidence without a subscriber; `audit` compares saved IDs, including separate Phone results. Label recorded demonstrations as recorded evidence.

- [Foundational Week 7 architecture and design decisions (September 6)](docs/week7-selected-design-2026-09-06.md)
- [Earlier setup, deployment and physical acceptance runbook](docs/week7-runbook.md)
- [Android/Unity receiver setup](docs/week7-phone-runbook.md)
- [Historical iOS delivery and decisions as of September 14](docs/week7-continuation-report-2026-09-14.md)
- [iOS visualizer Xcode export and Mac setup](ios-visualizer/README.md)
- [Autonomous GPT-6 Mac execution prompt](docs/week7-mac-agent-prompt.md)
- [Ultra96 and actual iPhone Python evidence](docs/week7-continuation-report-2026-09-07.md)
- [Earlier local, firmware and BLE evidence](docs/week7-continuation-report-2026-09-06.md)
- [Original A–M gate definitions](docs/week7-development-plan.md)

Runtime: Windows BLE/pairing requires Python >=3.10 with `bleak==3.0.1` (tested on 3.12). Ultra96 and standalone Phone Python receivers require Python >=3.8 and use the standard library. Provisioning/tests additionally use pytest, cryptography and optional pyserial. Firmware uses PlatformIO `firebeetle32`; its normal profile requires authenticated Secure Connections bonding.

```powershell
python -m pip install -r laptop/requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest laptop/tests tests phone/tests -q
pwsh -NoProfile -File phone/tests/run_core_tests.ps1
```

Generate PKI in a new empty directory outside the repository, then run a local synthetic rehearsal:

```powershell
python -m tools.generate_week7_pki --output-dir C:/week7-private/pki
python -m tools.rehearse_week7 --pki-dir C:/week7-private/pki --target 100 --duration 30
```

Add `--ble` after uploading protected firmware and pairing with `python -m laptop.windows_pairing`. Local rehearsal is explicitly separate from real Ultra96/SSH/Phone evidence.

The selected deployment reaches Ultra96 through SSH on TCP 22. Both application services bind to 127.0.0.1 (8888 ingestion, 9999 Gateway). The laptop uses an SSH local forward; the native iPhone opens its own nested SSH channels. The laptop receives only INGEST_ACK; GESTURE_RESULT goes directly from Ultra96 to the subscribed phone. No ESP Wi-Fi, reverse forwarding or laptop result relay is used.

The real Ultra96 deployment uses the private `/var/tmp/cg4002-week7-yanjie-20260907` hierarchy. VPN-enabled PowerShell password authentication worked on both SSH hops; see the new testing guide for startup order and live process checks. `tools.rehearse_remote_week7` is an alternative remote rehearsal with a desktop subscriber, not the current two-ESP/iPhone acceptance command. Do not run its subscriber alongside the iPhone: the board permits one active result subscriber, and the newer connection replaces the older one.
