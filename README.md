# Let Them Cook — CG4002 Communications

Week 7 implements a protected ESP32 BLE dummy stream, a bounded Windows bridge, TLS ingestion and direct result delivery on Ultra96, plus Python/Android and Unity receivers.

- [Current selected architecture and every Week 7 design decision](docs/week7-selected-design-2026-09-06.md)
- [Setup, deployment, recovery and physical acceptance runbook](docs/week7-runbook.md)
- [Android/Unity receiver setup](docs/week7-phone-runbook.md)
- [Latest Ultra96 continuation evidence and remaining work](docs/week7-continuation-report-2026-09-07.md)
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

Ultra96's only externally accessible port is TCP 22, serving SSH. Deployment keeps both application services on 127.0.0.1 (8888 ingestion, 9999 Gateway), reached through independent Laptop and Phone SSH local forwards via port 22. The Laptop receives only INGEST_ACK; GESTURE_RESULT goes directly from Ultra96 to the subscribed Phone. No ESP Wi-Fi, reverse forwarding or Laptop result relay.

The real Ultra96 deployment uses the private `/var/tmp/cg4002-week7-yanjie-20260907` hierarchy. VPN-enabled PowerShell password authentication worked on both SSH hops; see the current runbook for the longer interactive login deadlines and verified deployment paths. With two actual forwards already established, `python -m tools.rehearse_remote_week7 --ca <public-CA-path> --confirmed-remote-topology --ble --target 0 --duration 600` checks exact remote correlation and sustained coverage. This receiver is an independent desktop subscriber; actual Phone acceptance remains separate.
