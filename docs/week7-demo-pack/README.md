# Week 7 teacher demo pack

Use this pack to demonstrate deterministic dummy packets travelling through real connections: **ESP32 → protected BLE → Laptop → its SSH/TLS connection → actual Ultra96 → the iPhone's independent SSH/TLS connection → Python receiver**. The replacement Phone's latest **100/100** regression has zero reconnects and zero checked sender error/drop/gap/callback counters. A separate **6,100/6,100** capture has zero Phone reconnects and one retained sender callback discard. Controlled local-forward restoration and receiver restart are verified. Full-run physical foreground observation, SSH-master/VPN loss, physical app/screen lifecycle and teammate visualizer integration remain unverified; no full Gate M pass is claimed.

Open [the teacher brief](teacher-brief.html), [printable PDF](teacher-brief.pdf), [talk track](teacher-script.md), and [packet walkthrough](packet-walkthrough.md). [packet-example.json](packet-example.json) is an illustrative fixture, not a captured measurement. Detailed procedures remain in the [communications runbook](../week7-runbook.md) and [Phone runbook](../week7-phone-runbook.md); the [selected design](../week7-selected-design-2026-09-06.md) governs current defaults.

The operator used actual **iPhones** for the recorded tests. Use the
[iPhone quickstart](../week7-iphone-quickstart.md) and [startup update](../week7-iphone-startup-update.md)
for the iSH procedure. The updated receiver ran on the replacement Phone with
zero reported reconnects; the earlier Phone's retry remains part of its history.
This rerun does not independently establish the earlier timeout's cause or a
deliberate startup wait beyond five seconds.

The [direct SSH import](../week7-iphone-ssh-import.md) can provision the same
public iPhone setup bundle from Ultra96 over its existing SSH port 22.

### Verified iPhone evidence, 2026-09-08

**Latest regression after controlled recovery.** The [original Phone log](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/post-recovery-phone100-agent-20260908-231307/phone100.combined.log) contains 100 ordered results, IDs `1:2375739948:6503` through `:6602`, with `received=100,reconnects=0`. The [supplemental audit](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/post-recovery-phone100-agent-20260908-231307/supplemental-audit.json) reports `content_passed=true`, exact Packet/ACK/Phone correlation and zero checked sender error/drop/gap/callback counters. Sender and receiver exit files are 0; capture exit 0 is recorded in [Phone command output](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/post-recovery-phone100-agent-20260908-231307/phone-ssh.stdout.log), but separate capture/wrapper exit files are absent. The board snapshot check in [the evidence index](evidence-index.json) matches those 100 IDs exactly; this separate check does not change the preserved supplemental audit's board field. Source/ACK spans are 9.900/9.750 s; sender elapsed time is 14.078 s. Original Phone log: 17,087 bytes, SHA-256 `216db268e40b058faa5b7cf79415cf46f5594154547cf8890295b8096b328169`. Output was also sent to iSH's console throughout this short capture; physical screen observation remains unconfirmed.

**Controlled local-forward recovery and receiver restart.** The [fault audit](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/forward-recovery-agent-20260908-230910/fault-audit.json) records cancellation of the Phone's application forward, verified listener absence and an actual `ConnectionRefusedError`, followed by restored TLS, re-subscription and 100 exact IDs `1:2375739948:6403` through `:6502`. Its receiver reports the expected one reconnect, all checked sender counters are zero, and recorded exits are 0. Fresh Python receiver execution is demonstrated by this test and the following regression. The separate board snapshot matches both consecutive 100-ID ranges. This tested local-listener restoration before data production; it did not interrupt an active application channel, terminate the SSH master, toggle VPN, switch the iOS app or lock the screen, and does not establish lossless outage recovery.

**Earlier replacement-Phone baseline and long capture.** The [100-result original log](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/phone100-OMIcKh/phone100.combined.log) contains exactly 100 ordered results, IDs `1:2375739948:201` through `:300`, with `received=100,reconnects=0`. The saved receiver and sender exits are 0; sender duration is 13.578 seconds. Its [supplemental audit](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/phone100-OMIcKh/supplemental-audit.json) passes exact saved-ID correlation but retains `content_passed=false` because `callback_generation_dropped=1`. Separate capture/wrapper exits were not saved for this short run. The [board snapshot](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/phone100-OMIcKh/phone100-OMIcKh.server.log), filtered to those 100 IDs, matches each once. Original Phone log: 16,887 bytes, SHA-256 `26db4a18b395e39ce567ccb9ccc8dd42cf5e5ae7e79af4a5f54bf24ea15fff50`.

The [6,100-result original log](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/phone6100-agent-20260908-225451/phone6100.combined.log) contains exactly 6,100 ordered unique results, IDs `1:2375739948:302` through `:6401`, with `received=6100,reconnects=0`. All six saved process/capture/wrapper exits are 0. The [supplemental audit](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/phone6100-agent-20260908-225451/supplemental-audit.json) and [board snapshot](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/phone6100-agent-20260908-225451/phone6100-OPiFjB.server.log) establish exact Packet/ACK/Phone/board ID agreement. Source uptime spans **609.900 s**; ACK activity spans **609.781 s**, with maximum ACK gap **0.360 s**. Sender elapsed time is **616.704 s**; the local orchestrator elapsed time is **618.250 s**. These are distinct measurements and none is a Phone inter-result or end-to-end latency measurement. Original Phone log: 1,037,192 bytes, SHA-256 `2421f7706a807cf6bfe485d817ce7df3b1f6fcfb08bca2dfab6b1c0d096455ea`.

The long run also retains `callback_generation_dropped=1`, its sole nonzero checked bridge counter and the sole strict all-counters-zero failure. Exact-ID correlation passes while the supplemental audit reports `content_passed=false`; show both outcomes. Phone JSONL is post-deduplication and has no per-result timestamps. The [console helper record](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/evidence/phone6100-agent-20260908-225451/console-display.json) reports writing 3,393 lines over 339.476 seconds during the latter portion; it does not prove physical screen visibility or full-run foreground continuity. Operator confirmation, SSH-master/VPN loss and physical app/screen lifecycle checks remain pending. The separate controlled local-forward test above verifies only its stated scope. Unity/app integration and full Gate M remain unverified.

Actual [Phone TLS checks](D:/LetThemCook-builds/iphone-control-20260908/w7-fd3c60de/phone-tls-security-check-after-compat.stdout.json) accepted TLS 1.3 with the trusted identity, rejected a wrong name (verification code 62) and rejected an untrusted CA (code 20). Temporary maintenance access controls commands inside iSH; it does not control the iOS UI. Public provenance and original/derived hashes are in [the evidence index](evidence-index.json).

**Earlier Phone capture, retained history.** The [original Phone log](D:/LetThemCook-builds/iphone-live-20260907/phone100-20260908-185338/phone100.DDMJjm/phone100.combined.log) contains 104 lines: subscription, `TimeoutError`, a new subscription, 100 ordered results, then `received=100,reconnects=1`. There is no further logged reconnect after results begin; receiver exit is 0. The exact IDs are `1:2375739948:0` through `1:2375739948:99`. The **14.078-second duration belongs to the sender**, not an independently timed Phone observation.

The [full Phone audit](D:/LetThemCook-builds/iphone-live-20260907/phone100-20260908-185338/phone-full-audit.json) retains the startup retry and verifies all 100 results against sender ACKs; the board accepted each expected ID once. The original combined log is 16,727 bytes, SHA-256 `72bcbcc14bd542816258dd04625e2438a3a99eac0736de536abdf73e33c4c1a8`. Its [derived result JSONL](D:/LetThemCook-builds/iphone-live-20260907/phone100-20260908-185338/phone100.DDMJjm/phone100.results.derived.jsonl) contains only original lines 4–103. Preserve the full combined log and status when showing the derived-file audit: an exact-ID pass does not erase the timeout or prove zero duplicate wire arrivals, Phone timing, a 600-second run, lifecycle reliability or Unity integration.

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

The latest replacement-iPhone 100-result regression has zero receiver reconnects and zero checked sender counters. The separate 6,100-result capture retains its one callback-generation discard; both are recorded above. For another run, use the iPhone quickstart; the Termux commands below remain the Android alternative. Stop the desktop runner and any simulator; close the desktop viewer forward. Keep Laptop ingestion terminal A. Do not start `tools.rehearse_remote_week7` alongside the Phone: it includes a subscriber that will replace the Phone.

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

4. Prepare the Laptop command first. Immediately after Phone status prints `subscribed session=week7-demo`, run the producer below in the operator's PowerShell terminal. The originally installed receiver used a five-second frame/idle deadline; the earlier original-iPhone run retried once before data arrived. Keep the complete startup status on every rerun and distinguish any newer startup-grace version from this original observation.

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

The actual replacement-iPhone receiver has recorded 100 and 6,100 exact results with zero reported reconnects. The long run covers more than 600 seconds of source/ACK activity; full-run physical foreground visibility and Phone timing remain unverified. The earlier 100- and 6,100-result senders each retain one callback-generation discard; the latest post-recovery 100-result sender has zero checked counters. The original teammate-visualizer requirement needs its actual build and integration: only the portable C# core has been compiled here, while the supplied Unity component and actual app have not. These captures do not establish full Gate M acceptance.

## 6. Diagnose or demonstrate a fault separately

| Observation | Expected interpretation and next action |
|---|---|
| SSH host-key mismatch, VPN/login failure, or refused local port | No remote pass; inspect the verified route and the owned service/forward. Keep identity checks enabled. |
| Wrong CA, expired certificate, or wrong SAN | TLS must fail; repair provisioning or time, then rerun cleanly. |
| `subscribed` absent or only ACKs visible | Viewer delivery is unproven; inspect the independent viewer and same-session ownership. |
| Protected BLE unavailable or repeated authentication failure | Keep the failure; inspect the ESP/bond using the runbook. Switching to synthetic input changes the claim. |
| Intentional SSH loss, server restart, or ESP reset | Error/gap/drop counters and `passed=false` can be correct. Show fresh correlated data after recovery, then run a new clean 100-packet baseline. |

Optional fault demonstration: first save a clean pass, start a separately named duration-based run, then stop only the verified ingestion SSH owner **or** viewer SSH owner. Record the action time; restart that same forward and show fresh IDs. Viewer loss should leave ingestion ACKs flowing; disconnected results are not replayed. A server restart requires the [owned PID/cwd/argv checks](../week7-runbook.md#owned-server-termination-and-restart) and a fresh log. Do not mix these records with a clean soak.

The [evening 2026-09-07 USB-only test](../week7-continuation-report-2026-09-07.md#live-usb-only-power-loss-test-evening-2026-09-07) captured serial loss, a new boot and protected recovery, with 2,715 exact ACK/result matches across the intentional outage. The [separate physical RESET test](../week7-continuation-report-2026-09-07.md#separately-observed-physical-reset-button-recovery) retained USB serial continuity, changed boot and resumed protected delivery, with 5,832 exact matches across its intentional interruption. Both fault runs retain `passed=false`; the final clean desktop 100/100 check passed in 13.797 seconds. Capture each new demonstrated physical action during streaming, with its own time, boot transition and authenticated recovery. USB removal establishes power loss only if the ESP has no other supply. USB powers this board and exposes optional diagnostics; the demo packets reach the Laptop over wireless BLE.

## 7. Save evidence and tear down

1. Retain date, Laptop revision, actual remote source path/revision, mode/source, both endpoint owners, public trust identity, safe application logs, exit codes, audit output and the matching dedicated Ultra96 log. Save failures with their original labels. Never capture interactive passwords, pairing passkeys or private keys.
2. Stop the owned producer/viewer or Phone app. Stop each owned foreground SSH command using Ctrl+C in its own terminal. On Android, stop the display `tail`, receiver and SSH processes, then run `termux-wake-unlock`. For the iPhone's self-backgrounded SSH command, use the [quickstart's scoped control-socket shutdown](../week7-iphone-quickstart.md#6-finish-the-experiment-and-retain-its-limits), then verify the owned process exited.
3. Recheck local listeners and process identities. If a process remains, verify its current owner/command/endpoints before stopping that specific process. Do not kill every Python/SSH process or blindly reuse a historical PID. Close serial monitors after checking that the intended ESP disconnected.
4. The Ultra96 service may remain running as previously authorized. If stopping it is required, follow the verified owned-server procedure and require its `stopped` event and released listeners. Record the resulting state for the next operator.

These checks implement the team's selected engineering contract. The official written marking rubric was not available, so this pack does not claim course acceptance.
## 8. Rebuild the printable brief locally

The HTML is the source for the three-page A4 landscape PDF. Its Print / Save as
PDF button works in a browser. The existing local automated exporter is
`D:\LetThemCook-builds\teacher-brief-20260907\render.cjs`; it uses bundled
Playwright and installed Chrome, prints page-content/footer bounds, and writes
`docs/week7-demo-pack/teacher-brief.pdf` in this checkout.

```powershell
& 'C:\Users\Yanjie Wang\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' 'D:\LetThemCook-builds\teacher-brief-20260907\render.cjs'
pdfinfo 'docs\week7-demo-pack\teacher-brief.pdf'
```

After every export, require three A4 landscape pages, render each page with
Poppler `pdftoppm -png`, and inspect all three for overflow, overlap and readable
qualifications. The exporter and runtime paths are local tooling, not portable
dependencies included in a copied demo pack.
