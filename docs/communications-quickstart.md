# Communications quickstart

This checkout contains the two-FireBeetle communications source and operator tools at protocol version 3, the only version the source supports. Two ESP32 boards send 38-byte version-3 sensor packets (a 16-byte header and 11 dummy int16 values per sample) over authenticated BLE to one Windows laptop. The laptop opens an SSH forward and two TLS ingestion streams to Ultra96. Ultra96 acknowledges each accepted input to the laptop, passes each new sample to its model, and sends the model's results over a separate SSH/TLS connection owned by the iPhone app. Unless the service is started with `--model`, it uses its built-in dummy model: one random `REST`, `FIST`, `OPEN` or `POINT` result with confidence 1.0 for each accepted sample. The [protocol specification](co-protocol-v3.md) defines the formats.

## Before a physical run

- Use Windows with Python 3.10 or newer, PlatformIO for firmware uploads, Bluetooth enabled, and the institutional VPN route to Ultra96. Install laptop dependencies with `python -m pip install -r laptop/requirements.txt`. `tools.check_board` and `tools.deploy_service` also need `python -m pip install -r requirements-dev.txt`: `check_board` makes throwaway certificates with `cryptography`, and `deploy_service` connects with `paramiko`.
- Have two distinct FireBeetle32 boards, a programming USB cable, and independent power for each board during the BLE demonstration. Keep their serial pairing passkeys off camera and out of saved logs.
- Every end must run version 3: both boards, the Ultra96 service and the iPhone app. Nothing interoperates across versions, so an upgrade means reflashing both boards, redeploying the service and reinstalling the app together. On 2026-10-14 only the right board ran version 3: the left board still had version-2 firmware, the Ultra96 was not touched and should still hold the service deployed on 28 September (version 2, session `week7-demo`), and the installed app is the Week 7 build, which cannot read version-3 results. The September server certificate expired on 2026-10-06 (laptop copy; the board's copy was not checked). A renewed pair from the same CA, valid to 2026-11-13 14:27:35 UTC, was made on 2026-10-14 in `~/.codex/private/cg4002-comms-server-20261014/` on the owner's laptop and is not yet on the board, so run `tools.deploy_service` with `--server-cert-dir` pointing at it; without that option the deploy is expected to be refused. Section 6.3 of the [hand-off document](communications-handoff.md#63-actual-deployment-state-and-one-redeploy-round) lists the steps.
- The app needs its public CA and its own VPN/SSH credentials. The team repository does **not** include the exported Unity Xcode project or a prebuilt app; Jie Ling builds the game app from the team's own export (section 7.3 of the hand-off document). This fork also carries `ios-visualizer/xcode-export/`, the Week 7 export (already patched), and `ios-visualizer/tools/`, from which the owner rebuilds the test app on a Mac (hand-off section 6.3, step 4). The Swift version-3 changes (result validation, display text, `CommsNextResult`) are written but not compiled (2026-10-14); `swift test` on a Mac comes first. See [iOS source and build boundary](../ios-visualizer/README.md), which describes the team repository.
- The iPhone client pins the original jump/board SSH host keys and CA fingerprint, and verifies the TLS service name `ultra96.week7.internal`. Laptop `--jump`, `--target` and `--ca` overrides do not change the phone route. A different Ultra96 deployment requires verified new trust values in the iOS source and a rebuilt, installed app; retain certificate and host-key verification.
- Run all commands below from the repository root. Confirm available options with `python flash.py --help`, `python demo.py --help`, `python -m tools.check_board --help` and `python -m tools.deploy_service --help`.

## Flash and pair the boards

If both boards already run version-3 firmware and the dummy fixtures have not changed, use the saved mapping and go on to [Check each board](#check-each-board). A board still on version-2 firmware is refused at start-up with `invalid source statistics magic; flash this board with the current firmware`. For first setup, after a protocol change, or after editing [`common/dummy_fixtures.json`](../common/dummy_fixtures.json) (2 to 64 rows of exactly 11 int16 values):

```powershell
python flash.py --ports
python flash.py
python flash.py --boards
```

`flash.py` generates the firmware fixture header, builds both protected profiles, then asks for the first physical board (LEFT / device 1) and a different second board (RIGHT / device 2). It uploads them one at a time through the programming USB cable and saves their Bluetooth addresses locally. Label each board after its successful upload. For later fixture changes, connect the existing LEFT board first and RIGHT board second to retain their roles. To reflash one board only, identify it by its factory MAC rather than by its COM number and upload with its own PlatformIO environment (`firebeetle32-left` or `firebeetle32-right`); section 4.3 of the hand-off document gives the commands.

On boot each board prints `comms_ready device_id=<1|2> packet_bytes=38 packet_version=3 ...` on its serial port, which confirms version-3 firmware.

On initial Bluetooth setup, use the private serial monitor and pairing mode one board at a time:

```powershell
python flash.py --monitor COMx
python flash.py --pair left
python flash.py --pair right
```

Replace `COMx` with the actual port shown by `--ports`; run the monitor in a separate terminal while pairing. Existing authenticated bonds are reused; on 2026-10-14 Windows kept its bond with the right board through two reflashes. After setup, disconnect both boards from laptop USB and power them independently.

## Check each board

After flashing, check each board alone against a service on this laptop. No SSH, Ultra96 or phone is involved:

```powershell
python -m tools.check_board left
python -m tools.check_board right
```

Each run contacts only the named board, by its address in `.comms-local/boards.json` (or the built-in default address when that file does not exist); the other board may stay powered. It starts a service on the laptop with throwaway certificates and the built-in dummy model, sets the rate, sends commands, and stops the stream normally so the board's `LCS3` source statistics can be reconciled. The defaults are 65 s at 50 Hz with 3 commands (`--rate`, `--duration`, `--commands`; `--report <file>` also saves the summary). It prints `CHECK PASSED` only when generated = received = acknowledged with no error, the rate and an ATT MTU of at least 41 are confirmed, and every sample and command got its result. On 2026-10-14 the right board passed with version-3 firmware (2934 = 2934 = 2934 at 50 Hz); the left board has not been checked with version 3.

## Deploy the Ultra96 service

The Ultra96 must run the version-3 service from this checkout. `python -m tools.deploy_service` deploys it in one step for the **original project deployment only**: it connects to the fixed jump host and board, by default with the original operator's jump account (`--jump-user`) and the board account `xilinx` (`--board-user`), and it uses the fixed board folder `BOARD_ROOT` in `tools/demo_service.py`. The operator types both passwords; nothing is stored.

```powershell
python -m tools.deploy_service --dry-run
python -m tools.deploy_service --server-cert-dir 'C:\path\to\renewed-server-certificate'
```

The first command prints the plan and connects nothing. The second checks both SSH host keys against `~/.ssh/known_hosts` (no trust on first use) and uploads `common/` and `ultra96/` into a new board folder; `--server-cert-dir` names a folder holding `server-cert.pem` and `server-key.pem`. On the board it then checks that the running `ultra96.server` is this user's, runs under `BOARD_ROOT` and owns exactly `127.0.0.1:8888` and `:9999` (or that both ports are free), compiles the new code, checks that the certificate and key it will use match and do not expire within an hour, and copies the running service's code aside for rollback. A refusal in these checks leaves the running service and the certificate untouched (only the uploaded folder stays), prints the error and saves no record. After a last check of the running process, it stops the old service (SIGTERM, then SIGKILL if it has not exited after 10 s), installs the new certificate with a backup of the old pair, starts the new service in the background and waits for both listeners. Any failure from that last check onwards stops the new service, restores the previous certificate and restarts the previous code, if a service was running before. From that last check onwards a final record (`deployed`, `rolled_back`, `failed_old_still_running`, `failed_nothing_running` or `rollback_failed_nothing_running`) is always printed, saved on the board in `BOARD_ROOT/evidence/active-deployment.json` and copied to `.comms-local/deployments/`, which `demo.py service --start` follows. If the board does not answer within 2 × the start timeout + 120 s (`--start-timeout`, default 30 s), the tool stops waiting and asks you to run `python demo.py service` and read `BOARD_ROOT/evidence/active-deployment.json` before trying again; the board may still be finishing or rolling back.

Without `--server-cert-dir` the certificate already on the board is kept, and the deploy is refused if it expires within an hour. The server certificate is valid for 30 days; issue a new one from the existing CA with `python -m tools.generate_comms_pki --renew-server-from <CA folder> --output-dir <new empty folder>`. The session defaults to `ltc-comms` (`--session-id`; this tool does not read `LTC_COMMS_SESSION`). `--model MODULE --model-path DIR` starts a model module instead of the built-in dummy model. The tool does not upload the model: DIR must be an absolute folder on the Ultra96 (for example under `BOARD_ROOT`) that already holds the module, and the service puts it first on its import path. `demo.py service --start` ignores a deployment record whose `--model-path` does not start with `/`, and falls back to an older record or to the 28 September folder.

Status (2026-10-14): the tool's board-side program was verified on Linux (WSL Ubuntu, 27 of 27 checks, including a deploy over a running version-2 service and a rollback); its SSH half has not yet run against the real board. Section 6.3 of the hand-off document describes each step and the expected result.

## Run and check the end-to-end demo

The version-3 Ultra96 service must already be running. `python demo.py service` inspects the **original project deployment only**: it uses the fixed original SSH accounts and board folder, and lists the listeners, this user's processes and the folder each `ultra96.server` runs from. Its `--start` mode has the same fixed target and must only be used for that owned deployment after the port checks pass. It starts the service in the foreground of that SSH session from the folder, and with the `--model`/`--model-path`, of the service named by the newest record in `.comms-local/deployments/` that left a service running. Without such a record it falls back to the 28 September folder, which holds version-2 code, so deploy with `tools.deploy_service` first; a deployment made by hand or from another laptop leaves no record here. A teammate using another account or board must check and deploy that service through their own authorized route.

Laptop, Ultra96 and phone must use the same session. All three default to `ltc-comms`: `demo.py run`, `demo.py live`, `demo.py service --start`, `tools.deploy_service` and the phone source. To use another session, pass `--session-id <name>` to each laptop command or set `$env:LTC_COMMS_SESSION` (read by the `demo.py` commands only); the CLI option takes precedence. The phone app has its session compiled in, so it must be rebuilt to change. A session mismatch prevents ACK/subscription acceptance.

In terminal A, open and keep the SSH tunnel using your authorized SSH identities:

```powershell
python demo.py tunnel --jump 'YOUR_JUMP_USER@stujump.comp.nus.edu.sg' --target 'YOUR_BOARD_USER@makerslab-fpga-35.ddns.comp.nus.edu.sg'
```

The `tunnel` defaults embed the original operator's jump account; override them for a teammate run. The local tunnel listens on `127.0.0.1:18889` and forwards to the board's loopback ingestion port 8888. On an iPhone app built from this source, tap **Communications Connect** (the app installed for Week 7 shows **Week 7 Connect**), wait for **Subscribed**, and record its starting **Received** count. Keep other result subscribers closed: the server has one active phone subscriber.

In terminal B, capture both physical boards:

```powershell
python demo.py run --ca 'C:\path\to\verified-public-ca.pem'
```

The `--ca` value is the verified **public** CA certificate, kept outside this repository; no CA or server private key is needed on the laptop. The default CA path in `demo.py` names the original operator’s private directory, so pass `--ca` explicitly on another machine.

The default run lasts 60 seconds at 10 Hz per board. It saves a report and packet evidence under `.comms-local/`, then displays the saved report and matching sensor/ACK examples. Check both devices' source, receive, send and ACK counts, the `clean` result, and the process exit code. Compare the **observed** iPhone count increase with the printed `Phone expected increase`. That figure assumes one result per accepted sample or command, which holds only while the Ultra96 runs the built-in dummy model (the run prints a line saying so); a real model may produce results at another rate. An ingestion ACK alone does not prove phone display.

For a 120-second keyboard demonstration, press `1` or `2` while this command is running to send a command to the matching board. Each command carries one version-3 packet (a 52-byte control frame); the board adds 1 to each of the 11 values (32767 wraps to -32768), and the service answers each new command itself with one `cmd:` result; commands never reach the model:

```powershell
python demo.py live --ca 'C:\path\to\verified-public-ca.pem'
```

For optional rate and BLE file tests, use `python demo.py run --ca 'C:\path\to\verified-public-ca.pem' --rate 50` or `python demo.py run --ca 'C:\path\to\verified-public-ca.pem' --file path\to\sample.bin --file-device 2`. These are separate tests; their reports, observed throughput and any fault losses should be reported separately from the clean 10 Hz demo. Reopen saved evidence with `python demo.py report "<saved capture directory>"`.

The [protocol specification](co-protocol-v3.md) defines packet, message, control and file behavior. For the instructor's Week 7 live sequence, see the archived [English](archive/assessment-week7/B07-CO-live-demo-guide.en.md) or [Chinese](archive/assessment-week7/B07-CO-live-demo-guide.zh-CN.md) guide; the [video operator script](archive/assessment-week7/B07-CO-video-operator-script.zh-CN.md) and [presentation](archive/assessment-week7/B07-CO-video-presentation.en.md) cover recording. They describe the Week 7 deployment (32-byte packets).

## Source and deployment identifiers

Since 2026-10-14 the source no longer accepts the Week 7 identifiers, and since the move to protocol version 3 later that day it no longer accepts versions 1 or 2. Both boards, the Ultra96 service and the phone app must run builds of the current source.

| Identifier | Value | Note |
|---|---|---|
| BLE sensor magic | `LC` (`4C 43`) | A board on Week 7 firmware (`W7`) is refused by the laptop; flash it with `python flash.py`. |
| Sensor packet | Version `3`, 38 bytes (16-byte header + 11 × int16) | Version-2 packets (32 bytes, 8 values) are refused. A sensor notification needs ATT MTU ≥ 41. |
| BLE source statistics | `LCS3` | Version-2 firmware answers `LCS1` and Week 7 firmware `W7S1`; both are refused before subscribing. The 24-byte format is unchanged. |
| Network messages | `SENSOR_BATCH`, `INGEST_ACK`, `GESTURE_RESULT` at `v` 3; `SUBSCRIBE`, `SUBSCRIBED` at `v` 1 | A result label is 1 to 32 characters of `A–Z a–z 0–9 _ -`; confidence is a finite number from 0 to 1. The app installed for Week 7 accepts only older results and the four dummy labels. |
| Network session | `ltc-comms` | Laptop, Ultra96 and phone must agree. The service started for Week 7 and the app installed for Week 7 use `week7-demo`; deploy the service from this source and rebuild the app. |
| TLS service identity | `ultra96.week7.internal` | Kept: it is written into the server certificate and checked by every client. Changing it needs a new certificate and a rebuilt app. |
| Local capture and board mapping | `.comms-local/` | The old `.week7-local/` folder is no longer read. Captures recorded with Week 7 firmware hold `W7` packets and do not pass `demo.py report`; review them from commit `880abba`. Captures recorded with version-2 firmware are refused by `demo.py report` and `tools/video_evidence.py`; review them from commit `c42b386` or the team main `5a004c6`. |
| Native C bridge | `CommsStart`, `CommsCopyDisplay`, `CommsStop`, and `CommsNextResult` (per-result game input; written, not compiled, 2026-10-14) | The `Week7*` wrappers are kept for the Week 7 Unity export only. |

The `CommsNative` UI names its button **Communications Connect**; the Unity app installed for Week 7 shows **Week 7 Connect**. The archived B07 live and video guides describe the Week 7 deployment and show its packet and session values; they are history and no longer match this checkout.

The `phone/` Python, Android Unity C# and iSH helpers are retained as reference and diagnostic clients. The Python and C# receivers accept only version-3 results with the same label and confidence rules (`phone/receiver.py` is built and tested; of `CommsPhoneCore.cs` only the changed result-validation part was compiled, with the C# 5 compiler). The active iPhone path for this demo is the Swift `ios-visualizer/CommsNative` client linked into the Unity export; use its setup and result display for phone acceptance.
