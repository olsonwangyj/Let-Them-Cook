# Week 7 teacher demo pack

Use this pack to demonstrate deterministic dummy packets travelling through real connections. The verified rehearsal path is **ESP32 → protected BLE → Laptop → its SSH/TLS connection → actual Ultra96 → independent SSH/TLS desktop viewer**. The original plan's final path ends on a **real Phone running the teammate's visualizer**; that physical Phone and Unity integration are still pending.

Open [the teacher brief](teacher-brief.html), [printable PDF](teacher-brief.pdf), [talk track](teacher-script.md), and [packet walkthrough](packet-walkthrough.md). [packet-example.json](packet-example.json) is an illustrative fixture, not a captured measurement. Detailed procedures remain in the [communications runbook](../week7-runbook.md) and [Phone runbook](../week7-phone-runbook.md); the [selected design](../week7-selected-design-2026-09-06.md) governs current defaults.

The pack also includes [a recorded 100-packet run](recorded-demo100.jsonl) and [its provenance and hashes](evidence-index.json). From the project root, including a copied checkout, audit this relative path without hardware or network access:

```powershell
& 'D:\Anaconda\python.exe' -m tools.week7_demo audit 'docs\week7-demo-pack\recorded-demo100.jsonl' --minimum-count 100
```

Expected: exit 0, `audit_passed=true`, `matched=100`, and no missing, unexpected or duplicate saved IDs. This is saved protected ESP/Ultra96/**desktop** evidence from the 14.110-second post-action run, not a live replay or Phone result. The PDF and JSON files can be opened from a copied pack alone; running the auditor also requires the project's Python source.

## 1. Prepare before the teacher arrives

1. Have the FireBeetle ESP32 with its protected firmware, USB power, Windows Bluetooth, the existing authenticated bond, authorized NUS VPN, and verified host keys for both SSH hops. Close other BLE clients. Do not flash or erase bonds as routine preflight; recovery instructions are in the runbook.
2. Choose the endpoint visibly: **desktop rehearsal** or **actual Phone**. A real ESP emits dummy values over real BLE. `laptop.bridge --mock` and the remote runner without `--ble` synthesize input on the Laptop and establish no BLE evidence.
3. In the operator's PowerShell terminal, initialize these variables. Use a fresh evidence directory for each attempt; passwords and raw serial output never belong there.

```powershell
Set-Location 'D:\LetThemCook-worktrees\week7-stage-d-onward'
$week7Python = 'D:\Anaconda\python.exe'
$week7Ca = 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\ca-cert.pem'
$week7Evidence = Join-Path 'D:\LetThemCook-builds' ('teacher-demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $week7Evidence -ErrorAction Stop | Out-Null
$env:PYTHONDONTWRITEBYTECODE = '1'
& $week7Python --version
git rev-parse HEAD
Test-Path -LiteralPath $week7Ca
& $week7Python -m tools.week7_demo packet
```

4. Require Python >=3.10 on this Windows BLE client, the project's installed dependencies, and correct clocks. Compare the public CA's fingerprint and validity against the trusted provisioning record; check the server certificate's validity too. The service certificate lasts 30 days. If renewal is necessary, follow coordinated provisioning in the runbook before the demo.

```powershell
openssl x509 -in $week7Ca -noout -fingerprint -sha256 -dates
openssl x509 -in 'C:\Users\Yanjie Wang\.codex\private\cg4002-week7-20260906\server-cert.pem' -noout -dates -ext subjectAltName
```

5. Keep the saved [600-second evidence](D:/LetThemCook-builds/remote-evidence-20260907/remote-protected600.jsonl) and [latest report](../week7-continuation-report-2026-09-07.md) available. Run the clean 600-second command in section 4 before the presentation, then show a fresh 100-packet run live. A short talk cannot contain a new ten-minute soak.

## 2. Verify the actual Ultra96 service

Enable VPN. In a separate PowerShell control terminal, connect through the selected jump host. Enter both passwords only at OpenSSH's interactive prompts; do not record this terminal.

```powershell
$week7Proxy = 'ssh -o StrictHostKeyChecking=yes -o BatchMode=no -o ConnectTimeout=20 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -W "[%h]:%p" yanjie@stujump.comp.nus.edu.sg'
$week7SshOptions = @('-o', 'Port=22', '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=no', '-o', 'ConnectTimeout=60', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', '-o', "ProxyCommand=$week7Proxy")
ssh @week7SshOptions xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg
```

Inside that Ultra96 shell, inspect the current deployment:

```sh
id
hostname
cat /var/tmp/cg4002-week7-yanjie-20260907/evidence/server.pid
ss -ltnp
```

Use the returned numeric PID in `ps -p PID -o pid=,uid=,args=` and `readlink -f /proc/PID/cwd`. Require uid 1000, the expected `ultra96.server` command/TLS paths, and source directory `/var/tmp/cg4002-week7-yanjie-20260907/source-db6769a`. Verify that this process owns **only loopback** application listeners `127.0.0.1:8888` and `127.0.0.1:9999`.

The last recorded service was PID **43932**, log `evidence/server-after-restart.log`, intentionally left running. This is historical state, not permission to reuse that PID blindly. If it is absent, verify both ports are free and use the runbook's owned-server start procedure. Keep unrelated board services intact.

**Ultra96 TCP 22 is its only externally accessible port and serves SSH.** Ports 8888/9999 below are remote loopback destinations inside SSH; 18888/19999 are client loopback ports. Strict SSH host-key checks apply independently to both hops. TLS verifies the CA and SAN/SNI **`ultra96.week7.internal`**, even though each client connects to `127.0.0.1`. Do not weaken either identity check.

## 3. Open the independent forwards

In **Laptop terminal A**, print the ingestion command, then copy and execute the printed `ssh` line in that terminal:

```powershell
Set-Location 'D:\LetThemCook-worktrees\week7-stage-d-onward'
& 'D:\Anaconda\python.exe' -m tools.ssh_tunnel
```

It must contain `Port=22`, `stujump.comp.nus.edu.sg`, strict trust on both hops, and `-L 127.0.0.1:18888:127.0.0.1:8888`. Keep it open and enter credentials interactively. The generator prints a command; it does not start a tunnel. Its `--run` supervisor needs working key/agent authentication and cannot answer passwords.

For **desktop rehearsal only**, in **Laptop terminal B** print and execute the independent viewer command:

```powershell
Set-Location 'D:\LetThemCook-worktrees\week7-stage-d-onward'
& 'D:\Anaconda\python.exe' -m tools.ssh_tunnel --local-port 19999 --remote-port 9999
```

It must contain `-L 127.0.0.1:19999:127.0.0.1:9999`. These must be two distinct SSH processes, each reaching the verified Ultra96 through `stujump`. Confirm local owners from another terminal:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 18888,19999 |
    Select-Object LocalAddress,LocalPort,OwningProcess
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" |
    Select-Object ProcessId,ParentProcessId,CommandLine
```

Record this run's owners and the remote identity checks. Local listeners alone do not prove the remote destination. Set `--confirmed-remote-topology` below only after these checks. For **actual Phone**, skip Laptop terminal B and use the Phone's own forward in section 5.

## 4. Run the desktop demonstration

Stop all other same-session viewers first: a new subscriber replaces the old owner. The runner completes TLS and emits `subscribed` before it starts production. It creates neither SSH tunnels nor an Ultra96 server.

Optional network baseline, using **synthetic Laptop input**:

```powershell
$week7Log = Join-Path $week7Evidence 'synthetic100.jsonl'
& $week7Python -m tools.rehearse_remote_week7 --ca $week7Ca --confirmed-remote-topology --target 100 --duration 45 2> "$week7Log.stderr.txt" |
    ForEach-Object { Write-Host $_; $_ } | Set-Content -LiteralPath $week7Log -Encoding utf8
$week7Exit = $LASTEXITCODE
$week7Exit | Set-Content -LiteralPath "$week7Log.exit.txt"
```

Live teacher run, using **the real ESP's protected BLE dummy packets**:

```powershell
$week7Log = Join-Path $week7Evidence 'protected100.jsonl'
& $week7Python -m tools.rehearse_remote_week7 --ca $week7Ca --confirmed-remote-topology --ble --target 100 --duration 45 2> "$week7Log.stderr.txt" |
    ForEach-Object { Write-Host $_; $_ } | Set-Content -LiteralPath $week7Log -Encoding utf8
$week7Exit = $LASTEXITCODE
$week7Exit | Set-Content -LiteralPath "$week7Log.exit.txt"
& $week7Python -m tools.week7_demo audit $week7Log --minimum-count 100
```

Point to one `ack` and one `result` with the same `result_id = device_id:boot_id:seq`, then show the final summary and audit. Arrival order across the two streams can differ; exact ID sets establish correlation. An ingestion ACK alone proves acceptance, not viewer delivery.

Separate clean soak, with **no deliberate interruption**:

```powershell
$week7Log = Join-Path $week7Evidence 'protected600.jsonl'
& $week7Python -m tools.rehearse_remote_week7 --ca $week7Ca --confirmed-remote-topology --ble --target 0 --duration 600 2> "$week7Log.stderr.txt" |
    ForEach-Object { Write-Host $_; $_ } | Set-Content -LiteralPath $week7Log -Encoding utf8
$week7Exit = $LASTEXITCODE
$week7Exit | Set-Content -LiteralPath "$week7Log.exit.txt"
& $week7Python -m tools.week7_demo audit $week7Log --minimum-count 5400
```

Require runner exit 0, `passed=true`, the requested count, exact ACK/result set equality, one BLE/ingestion/viewer connection, no new boot, and zero checked stream/transport/error/drop counters. The 600-second run also requires at least **5,400** unique ACKs/results and no inter-message or trailing silence above five seconds; initial setup latency is reported separately. A separately reported shutdown `callback_generation_dropped` may represent rejected late callbacks: retain and inspect it rather than hiding it. The offline audit checks saved content; it does not independently establish physical provenance, uninterrupted duration, or the runner's clean-pass criteria.

To review the already recorded soak without starting hardware:

```powershell
& $week7Python -m tools.week7_demo audit 'D:\LetThemCook-builds\remote-evidence-20260907\remote-protected600.jsonl' --minimum-count 5400
```

## 5. Actual Phone mode: complete this on the device

This is a separate physical demonstration, presently pending. Stop the desktop runner and any simulator; close the desktop viewer forward. Keep Laptop ingestion terminal A. Do not start `tools.rehearse_remote_week7` alongside the Phone: it includes a subscriber that will replace the Phone.

1. On Android, follow the [Phone runbook](../week7-phone-runbook.md) to install Termux, provision independently verified host keys and the public CA, and verify the Phone's own authorized VPN/network access. Configure `week7-jump` for `stujump.comp.nus.edu.sg` and `week7-ultra96` for `makerslab-fpga-35.ddns.comp.nus.edu.sg`, destination port 22, authorized accounts, strict checking, and the documented 20/60-second timeouts. Laptop VPN/login success does not establish Phone connectivity.
2. In **Phone Termux terminal 1**, execute the Phone-owned forward. Enter any passwords interactively; do not capture this terminal.

```sh
termux-wake-lock
ssh -p 22 -N -T -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:19999:127.0.0.1:9999 week7-ultra96
```

3. Copy only `phone/receiver.py` to `~/week7-phone/receiver.py` and the verified public CA to `~/week7-private/ca-cert.pem`. In **Phone terminal 2**, collect actual results. This forwards to the Ultra96 directly; it never connects to a Laptop address.

```sh
mkdir -p ~/week7-evidence
python ~/week7-phone/receiver.py --ca ~/week7-private/ca-cert.pem \
  --port 19999 --session week7-demo --count 100 --duration 90 \
  > ~/week7-evidence/phone100.jsonl 2> ~/week7-evidence/phone100.status.txt
printf '%s\n' "$?" > ~/week7-evidence/phone100.exit.txt
```

Use a third Phone terminal to show readiness and the live display:

```sh
tail -f ~/week7-evidence/phone100.status.txt ~/week7-evidence/phone100.jsonl
```

4. Prepare the Laptop command first. Immediately after Phone status prints `subscribed session=week7-demo`, run the producer below in the operator's PowerShell terminal. The Phone has a five-second frame/idle deadline, so avoid delaying after readiness.

```powershell
$week7Log = Join-Path $week7Evidence 'phone-sender100.jsonl'
& $week7Python -m tools.week7_demo sender --ca $week7Ca --target 100 --duration 60 2> "$week7Log.stderr.txt" |
    ForEach-Object { Write-Host $_; $_ } | Set-Content -LiteralPath $week7Log -Encoding utf8
$week7Exit = $LASTEXITCODE
$week7Exit | Set-Content -LiteralPath "$week7Log.exit.txt"
```

`sender` uses the protected `laptop.bridge` pipeline and adds packet/ACK evidence; it starts no viewer, server, or SSH process. The minimal existing producer is `& $week7Python -m laptop.bridge --ca $week7Ca --target 100 --duration 60`; it emits aggregate metrics without per-ACK trace logs, so use the logging sender for this pack. Adding `--mock` to the bare bridge changes it to synthetic input and cannot prove BLE.

5. Require 100 unique valid Phone results, Phone exit 0, and matching IDs. Copy `phone100.jsonl`, status and exit files back to this run's evidence directory using the approved transfer method, preserving their origin. Then compare both captured streams:

```powershell
& $week7Python -m tools.week7_demo audit (Join-Path $week7Evidence 'phone-sender100.jsonl') --phone-results (Join-Path $week7Evidence 'phone100.jsonl') --minimum-count 100
```

Also retain the matching accepted traces from the owned Ultra96 server log. Record the actual Phone model, OS, Termux/Python versions, SSH ownership, CA identity, display and teammate application outcome. For the separate sustained test, run the Phone with `--count 0 --duration 630` and sender with `--target 0 --duration 600`, under fresh filenames; audit with `--minimum-count 5400` and review continuity and reconnections separately. A count-free Phone exit 0 alone is insufficient. Its final idle period after the producer stops may trigger reconnects; record their timing rather than calling the whole 630 seconds uninterrupted delivery.

The Phone's raw JSONL contains results **after receiver duplicate suppression** and has **no per-result timestamps**. Exact saved ID matches prove correlation of those retained results; zero duplicate rows cannot prove zero duplicate wire arrivals. The sender's five-second ACK-silence gate measures the ingestion side only. To claim 600-second Phone continuity, retain a separately timed on-device observation of the display and receiver status across the full production interval, with interruption/reconnection times. Neither the count nor this offline audit measures Phone inter-result gaps or synchronized end-to-end latency.

The Python display can establish the minimal real-Phone connection path once observed. The original teammate-visualizer requirement additionally needs its actual build and integration. Only the portable C# core has been compiled here; the supplied Unity component and Android app have not. Do not present a desktop window, saved JSON, or the untested iPhone appendix as completed Phone evidence.

## 6. Diagnose or demonstrate a fault separately

| Observation | Expected interpretation and next action |
|---|---|
| SSH host-key mismatch, VPN/login failure, or refused local port | No remote pass; inspect the verified route and the owned service/forward. Keep identity checks enabled. |
| Wrong CA, expired certificate, or wrong SAN | TLS must fail; repair provisioning or time, then rerun cleanly. |
| `subscribed` absent or only ACKs visible | Viewer delivery is unproven; inspect the independent viewer and same-session ownership. |
| Protected BLE unavailable or repeated authentication failure | Keep the failure; inspect the ESP/bond using the runbook. Switching to synthetic input changes the claim. |
| Intentional SSH loss, server restart, or ESP reset | Error/gap/drop counters and `passed=false` can be correct. Show fresh correlated data after recovery, then run a new clean 100-packet baseline. |

Optional fault demonstration: first save a clean pass, start a separately named duration-based run, then stop only the verified ingestion SSH owner **or** viewer SSH owner. Record the action time; restart that same forward and show fresh IDs. Viewer loss should leave ingestion ACKs flowing; disconnected results are not replayed. A server restart requires the [owned PID/cwd/argv checks](../week7-runbook.md#owned-server-termination-and-restart) and a fresh log. Do not mix these records with a clean soak.

No live true USB power-loss transition was captured in the latest 180-second run. Post-action recovery and an automated RTS reset are separate evidence. If demonstrating physical USB removal or RESET, capture each action during streaming, with its own time, boot transition and authenticated recovery. USB removal establishes power loss only if the ESP has no other supply.

## 7. Save evidence and tear down

1. Retain date, Laptop revision, actual remote source path/revision, mode/source, both endpoint owners, public trust identity, safe application logs, exit codes, audit output and the matching dedicated Ultra96 log. Save failures with their original labels. Never capture interactive passwords, pairing passkeys or private keys.
2. Stop the owned producer/viewer or Phone app. Stop each owned foreground SSH command using Ctrl+C in its own terminal. On Phone stop the display `tail`, receiver and SSH processes, then run `termux-wake-unlock`.
3. Recheck local listeners and process identities. If a process remains, verify its current owner/command/endpoints before stopping that specific process. Do not kill every Python/SSH process or blindly reuse a historical PID. Close serial monitors after checking that the intended ESP disconnected.
4. The Ultra96 service may remain running as previously authorized. If stopping it is required, follow the verified owned-server procedure and require its `stopped` event and released listeners. Record the resulting state for the next operator.

These checks implement the team's selected engineering contract. The official written marking rubric was not available, so this pack does not claim course acceptance.
