# iPhone: verified startup update and a fresh 100-result capture

The original iPhone run delivered all 100 results with exact Laptop/Ultra96 ID
correlation. Its first subscription timed out before the first result; after
resubscription, it received all 100 without another logged reconnect. The
original log and its qualification are preserved in the
[continuation report](week7-continuation-report-2026-09-07.md).

The updated standalone Python receiver gives the first result byte 30 seconds
to arrive, then retains a single five-second deadline for the remaining prefix
and body. Subsequent results retain five-second frame/idle deadlines, including
after reconnect. TLS and SUBSCRIBED retain five-second deadlines. Overall
`--duration` remains authoritative. This is decision 31; the packet contract,
TLS identity and original immutable setup ZIP are unchanged. The old receiver
remains available at `~/week7-phone/receiver.py`.

This update passed 22 Phone tests and a 215-passed/2-skipped full Python suite.
Its new on-iPhone acceptance is still pending. Keep the tested iPhone's iSH
app visible and screen awake, both VPNs connected, and the ESP powered by USB.
Use the existing independently verified Laptop ingestion and Phone Gateway
forwards over SSH port 22. No desktop subscriber should run during capture.

## 1. Download the two public files

In the same iSH shell that holds the current verified `$week7_ssh_socket`, paste
only this SCP block and complete any interactive password prompts. Do not paste
the next block until the normal shell prompt returns. The directory contains
only `receiver.py` and `capture100.sh`; no credentials or private keys.

```sh
scp -F "$HOME/.ssh/week7-ish-password.conf" \
  -o "ControlPath=$week7_ssh_socket" \
  -r week7-ultra96:/var/tmp/cg4002-week7-yanjie-20260907/phone-startup-b16c746255c9 \
  "$HOME/week7-phone/"
```

If iSH or the VPN was restarted, first re-establish the scoped SSH master and
strict application TLS check using the current continuation instructions.
Do not assume an old PID or environment variable is still valid. The known
`/home/xilinx` chdir/.bashrc warnings do not prevent successful SCP; require
both files to transfer and verify their hashes below.

## 2. Verify before running

These expected SHA-256 hashes were independently checked on the Laptop and
Ultra96 before publication. The original source syntax was checked against
Python 3.8 grammar, and `/bin/sh -n` checked the capture shell syntax.

```sh
python3 - <<'PY'
import hashlib
from pathlib import Path

folder = Path.home() / "week7-phone/phone-startup-b16c746255c9"
expected = {
    "receiver.py": "b16c746255c9d91655b4da35cea6d5d240a260f4c289ca7b52c2e4441420e881",
    "capture100.sh": "d704700e5e184a0c02e47378577679de0d7b71d31d7b0cae81ce260911d3df39",
}
for name, digest in expected.items():
    assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest, name
print("UPDATE READY")
PY
```

If this fails, retain the actual error and do not source the capture file.

## 3. Stage the Laptop sender

The prepared command is outside Git at
`D:\LetThemCook-builds\iphone-startup-update-20260908\phone100-laptop-startup30-command.txt`.
It preserves a fresh evidence directory and records an intentional six-second
delay after the operator's Enter press, before starting the unchanged real BLE
sender. This exercises a startup wait longer than the original five seconds.
The sender's own elapsed time excludes that explicitly recorded delay.

In Laptop PowerShell:

```powershell
& ([scriptblock]::Create((Get-Content -Raw -LiteralPath 'D:\LetThemCook-builds\iphone-startup-update-20260908\phone100-laptop-startup30-command.txt')))
```

Leave it waiting at Enter. Then, on iPhone after `UPDATE READY`, source the
verified capture file in the same shell so the fresh `$week7_run_dir` remains
available afterward:

```sh
. "$HOME/week7-phone/phone-startup-b16c746255c9/capture100.sh"
```

As soon as the Phone prints `subscribed session=week7-demo`, press Laptop Enter.
The Laptop will explicitly wait six seconds and then start BLE. Keep both
devices in place and let the commands finish. The capture helper displays
stdout/stderr immediately with `tee`, retains the full original combined log,
and saves the receiver exit independently of `tee`'s exit.

## 4. Retain and audit the complete attempt

Require sender exit 0, capture exit 0, receiver exit 0 and Phone summary
`received=100,reconnects=0`. Count alone is insufficient. Transfer the complete
new Phone evidence directory using its printed path and the existing scoped
SSH route. Compare all validated result IDs with the complete new sender ACKs
and actual board acceptance. Retain original status lines/source hashes when
deriving result-only JSONL; the ID auditor alone does not establish timing or
absence of Phone reconnects. Any overshoot, missing ID, timeout or reconnect
remains in the saved attempt and must not be trimmed into a passing run.

This 100-result check does not replace the remaining 600-second Phone soak,
VPN/tunnel interruption, app restart, screen-lock/background observations,
Phone TLS-negative checks, device/OS inventory or teammate Unity integration.
