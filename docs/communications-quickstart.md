# Communications quickstart

This checkout contains the two-FireBeetle communications source and operator tools at protocol version 3, the only version the source supports. Two ESP32 boards send 38-byte version-3 sensor packets (a 16-byte header and 11 int16 values per sample) over authenticated BLE to one Windows laptop. The default firmware sends dummy fixture rows. The glove firmware (`python flash.py --glove`) sends the readings of Siqiang's glove sensor module, and only while his movement detector reports MOVING; it is built but has not yet run on a glove. The laptop opens an SSH forward and two TLS ingestion streams to Ultra96. Ultra96 acknowledges each accepted input to the laptop, passes each new sample to its model, and sends the model's results over a separate SSH/TLS connection owned by the iPhone app. Unless the service is started with `--model`, it uses its built-in dummy model: one random `REST`, `FIST`, `OPEN` or `POINT` result with confidence 1.0 for each accepted sample. The [protocol specification](co-protocol-v3.md) defines the formats.

## Before a physical run

- Use Windows with Python 3.10 or newer, PlatformIO for firmware uploads, Bluetooth enabled, and the institutional VPN route to Ultra96. Connect the NUS VPN before every login through stujump: `tools.deploy_service`, `demo.py tunnel`, `demo.py service` and the phone app. Off the VPN, stujump still answers but offers only public-key login, and nothing in Communications uses SSH keys, so a missing VPN shows as a refused login, not as an unreachable host (seen on 2026-10-16). Install laptop dependencies with `python -m pip install -r laptop/requirements.txt`. `tools.check_board` and `tools.deploy_service` also need `python -m pip install -r requirements-dev.txt`: `check_board` makes throwaway certificates with `cryptography`, and `deploy_service` connects with `paramiko`.
- Have two distinct FireBeetle32 boards, a programming USB cable, and independent power for each board during the BLE demonstration. Keep their serial pairing passkeys off camera and out of saved logs.
- Every end must run version 3: both boards, the Ultra96 service and the iPhone app. Nothing interoperates across versions, so an upgrade means reflashing both boards, redeploying the service and reinstalling the app together. The boards also need the firmware of 2026-10-15 or later, whose source statistics are 36 bytes; the laptop refuses earlier builds. State on 2026-10-16: the right board was reflashed with the current firmware (`firebeetle32-right`, the dummy module) and passed `tools.check_board right`. The left board still has version-2 firmware; reflash and check it. The Ultra96 runs the version-3 service, deployed on 2026-10-16 with `tools.deploy_service` (session `ltc-comms`, the built-in dummy model, the 600 s ingest idle limit) in place of the 28 September version-2 service, and the same run installed the renewed server certificate, valid to 2026-11-13 14:27:35 UTC. It was made from the existing CA, so the laptop's CA file and the CA the phone app pins stay valid. The installed app is still the Week 7 build: it uses session `week7-demo`, so it can no longer subscribe to the service at all, and it cannot read version-3 results; keep it closed. A redeploy without `--server-cert-dir` keeps the board's certificate; renew it before 2026-11-13 (see [Deploy the Ultra96 service](#deploy-the-ultra96-service)). Section 6.3 of the [hand-off document](communications-handoff.md#63-actual-deployment-state-and-one-redeploy-round) lists the steps.
- The app needs its public CA and its own VPN/SSH credentials. It logs in by password only, so turn on the phone's own NUS VPN before Connect. Without it, stujump offers no password login and the app stops with `Disconnected: Jump host does not offer password authentication; correct setup and reconnect`: a terminal error, with no automatic retry and the passwords cleared. Connect the VPN and log in again. A VPN drop during a session ends the same way at the app's next reconnect attempt, if stujump is still reachable. The app also disconnects and clears the passwords whenever it stops being active (it goes to the background or the screen locks), and it does not keep the screen awake, so set Auto-Lock to Never on the phone in use. All of this comes from the code; none of it has been seen on a phone yet. The team repository does **not** include the exported Unity Xcode project or a prebuilt app; Jie Ling builds the game app from the team's own export (section 7.3 of the hand-off document). This fork also carries `ios-visualizer/xcode-export/`, the Week 7 export (already patched and configured), and `ios-visualizer/tools/`, from which the owner rebuilds the test app on a Mac (hand-off section 6.3, step 4). On 2026-10-15 the Swift package, with its version-3 changes (result validation, display text, `CommsNextResult`), was compiled and tested on Linux in a Swift 6.1 container (72 tests, no failures). On 2026-10-16 it was built and tested on the owner's Mac (Xcode 26.2, Swift 6.2.3): `swift test` passed 73 tests (the 72 and `PythonBoardTests`), the preview app built for the iOS Simulator and passed its 34 transport tests and 1 UI test, and the Week 7 export built with it for an iOS device, unsigned. Nothing has been signed or installed, so the installed app is still the Week 7 build. The unsigned app is not installed as it is: the owner chooses a signing team in Xcode and runs the `Unity-iPhone` scheme on the iPhone, which rebuilds the app signed and installs it (hand-off section 6.3, step 4). See [iOS source and build boundary](../ios-visualizer/README.md), which describes the team repository.
- The iPhone client pins the original jump/board SSH host keys and CA fingerprint, and verifies the TLS service name `ultra96.week7.internal`. Laptop `--jump`, `--target` and `--ca` overrides do not change the phone route. A different Ultra96 deployment requires verified new trust values in the iOS source and a rebuilt, installed app; retain certificate and host-key verification.
- Run all commands below from the repository root. Confirm available options with `python flash.py --help`, `python demo.py --help`, `python -m tools.check_board --help`, `python -m tools.deploy_service --help`, `python -m tools.sync_glove_module --help` and `python -m tools.export_capture --help`.

## Flash and pair the boards

If both boards already run the current firmware (36-byte source statistics, 2026-10-15 or later) and the dummy fixtures have not changed, use the saved mapping and go on to [Check each board](#check-each-board). A board on older firmware (version 2, Week 7, or a version-3 build from before 2026-10-15) is refused at start-up with `source statistics must contain exactly 36 bytes; flash this board with the current firmware`. For first setup, after a protocol or firmware change, or after editing [`common/dummy_fixtures.json`](../common/dummy_fixtures.json) (2 to 64 rows of exactly 11 int16 values):

```powershell
python flash.py --ports
python flash.py
python flash.py --boards
```

`flash.py` generates the firmware fixture header, builds both protected profiles, then asks for the first physical board (LEFT / device 1) and a different second board (RIGHT / device 2). It uploads them one at a time through the programming USB cable and saves their Bluetooth addresses locally. Label each board after its successful upload. For later fixture changes, connect the existing LEFT board first and RIGHT board second to retain their roles. To reflash one board only, identify it by its factory MAC rather than by its COM number and upload with its own PlatformIO environment (`firebeetle32-left` or `firebeetle32-right`); section 4.3 of the hand-off document gives the commands.

On boot each board prints `glove_begin ok=1 module=dummy gated=0` and then `comms_ready device_id=<1|2> packet_bytes=38 packet_version=3 rate_hz=10 ... glove=dummy gated=0` on its serial port, which confirms the current version-3 firmware with the built-in dummy module. A version-3 build from before 2026-10-15 prints no `glove_begin` line and no `glove=` field.

On initial Bluetooth setup, use the private serial monitor and pairing mode one board at a time:

```powershell
python flash.py --monitor COMx
python flash.py --pair left
python flash.py --pair right
```

Replace `COMx` with the actual port shown by `--ports`; run the monitor in a separate terminal while pairing. Existing authenticated bonds are reused; on 2026-10-14 Windows kept its bond with the right board through two reflashes, and on 2026-10-16 through four more. After setup, disconnect both boards from laptop USB and power them independently.

### The real gloves

```powershell
python flash.py --glove
```

This runs the same steps in the same board order (LEFT first), with the environments `firebeetle32-left-glove` and `firebeetle32-right-glove`, and saves the gloves' Bluetooth addresses as the LEFT and RIGHT mapping, replacing the previous one, so `tools.check_board` and `demo.py run` then contact the gloves. Pair each glove as above if its board has not been paired with this laptop. The environments link Siqiang's sensor module (`glove_sensor.cpp`, `glove_sensor.h` and `movement_model_params.h` from `hardware/gloves/integration_files/`) and start at 50 Hz, the model's rate. The firmware builds copies of his files under `firmware/esp32/`, never the originals. So `flash.py --glove` runs `python -m tools.sync_glove_module --check` after generating the fixture header and before building, and stops when a copy differs from his current files (`FAILED: command exited with code 1`) or when his files are missing (code 2; merge the team main first). Refresh the copies with `python -m tools.sync_glove_module` (never edit them by hand), then flash again. To reflash one glove by hand, run the check first, then upload with `firebeetle32-left-glove` or `firebeetle32-right-glove` as section 4.3 of the hand-off document shows for one board.

What is different on a glove board:

- At power-on the module calibrates for about 5 s; hold the glove still. The board advertises only after that. It prints `glove_begin ok=1 module=external gated=1` and `comms_ready ... rate_hz=50 ... glove=external gated=1`. With no sensor found it prints `ok=0` without the calibration wait, still advertises and answers commands, and counts every send tick as unread, so it sends nothing and `tools.check_board` fails with `source statistics not clean and complete` and `nothing acknowledged`. Seen on 2026-10-16 on the right board, which has no sensors: `glove_begin ok=0 module=external gated=1` 0.71 s after reset, `comms_ready ... rate_hz=50 ... glove=external gated=1` at 1.44 s, and in `python -m tools.check_board right --duration 20 --commands 2` 2 of 2 commands answered, all 753 ticks unread, nothing sent.
- It sends a sample only while the module reports MOVING. MOVING comes at the earliest about 0.2 to 0.4 s after motion starts, and later when the 1 s window needs more motion to cross the threshold: two evaluations 0.2 s apart must both find enough motion in the module's 1 s window. IDLE comes 0.4 to 0.6 s after that window falls below the threshold, which can be up to about 1 s after the motion stops. Samples before the MOVING decision are never sent. The two gloves decide independently.
- A failed sensor read, a non-finite sample, or more than 100 ms between two module updates restarts the module's movement classifier. Sending then stops for about 1.2 s or more (the 1 s window refills, then a second evaluation 0.2 s later must agree), even mid-gesture. This firmware updates the module every 1 to 2 ms, so this happens once after boot (harmless: the window is still empty and no laptop is connected yet) and after a transient I2C failure. It is the module's design. It has been reported to the Communications owner, who decides whether to raise it with Siqiang.
- `python demo.py run` sets the rate it is given, 10 Hz by default; pass `--rate 50` for the model's rate.
- To send every sample, IDLE included (for recording), build with `-DCOMMS_GLOVE_SEND_ALL=1` ([Record glove data](#record-glove-data)); the board then reports `gated=0`.

Status (2026-10-16): built (both environments compile and link). `firebeetle32-right-glove` was flashed once onto the right board without sensors, after `python -m tools.sync_glove_module --check` passed; the board then got the plain build back. Not yet run on a glove: the calibration, the sensor readings and the MOVING decision of Siqiang's module have not run on hardware.

## Check each board

After flashing, check each board alone against a service on this laptop. No SSH, Ultra96 or phone is involved:

```powershell
python -m tools.check_board left
python -m tools.check_board right
```

Each run contacts only the named board, by its address in `.comms-local/boards.json` (or the built-in default address when that file does not exist); the other board may stay powered. It starts a service on the laptop with throwaway certificates and the built-in dummy model, sets the rate, sends commands, and stops the stream normally so the board's `LCS3` source statistics can be reconciled. The defaults are 65 s at 50 Hz with 3 commands (`--rate`, `--duration`, `--commands`; `--report <file>` also saves the summary). It prints `CHECK PASSED` only when generated = received = acknowledged with no error, the rate and an ATT MTU of at least 41 are confirmed, and every sample and command got its result. On 2026-10-16 the right board passed with the current firmware (`firebeetle32-right`): 3022 = 3022 = 3022 at 50 Hz over 65.8 s, 3 of 3 commands, ATT MTU 517, `gated=no idle=0 unread=0 refused=0`, its 36-byte statistics reconciled. On 2026-10-14 it had passed with the first version-3 build (24-byte statistics). The left board has not been checked with version 3.

The summary line also prints `gated=<yes|no|unknown> idle=<n> unread=<n> refused=<n>`. These count send ticks that sent nothing: the glove was still (idle), the module had no valid sample (unread), or scaling refused the sample (refused). None of them takes a sequence number, and none fails the check by itself, so the idle ticks of a gated board are no fault. A gated board must still send at least one sample, so move the glove while checking a real glove.

To test the movement gate without a glove, build the dummy firmware with `COMMS_DUMMY_IDLE_MS` (default 0, never idle) and `COMMS_DUMMY_MOVING_MS` (default 3000). The board then sends for the moving time and skips its send ticks for the idle time, repeating from boot, and reports a gated source:

```powershell
$env:PLATFORMIO_BUILD_FLAGS = '-DCOMMS_DUMMY_MOVING_MS=3000 -DCOMMS_DUMMY_IDLE_MS=7000'
platformio run -d firmware/esp32 -e firebeetle32-right -t upload --upload-port COMx
Remove-Item Env:PLATFORMIO_BUILD_FLAGS
python -m tools.check_board right
```

Expect `glove_begin ok=1 module=dummy gated=1` on the serial port and `gated=yes` in the summary, with about 70% of the ticks idle. Upload the board again without the flags afterwards. Status (2026-10-16): verified on the right board. The serial port showed `glove_begin ok=1 module=dummy gated=1`, and `tools.check_board right` passed: 900 = 900 = 900, 2140 of 3040 ticks idle (70%) at 50 Hz, no unread or refused tick, 3 of 3 commands answered while idle, a longest receive silence of 7.03 s (the idle phase), no disconnect.

## Deploy the Ultra96 service

The Ultra96 must run the version-3 service from this checkout. `python -m tools.deploy_service` deploys it in one step for the **original project deployment only**: it connects to the fixed jump host and board, by default with the original operator's jump account (`--jump-user`) and the board account `xilinx` (`--board-user`), and it uses the fixed board folder `BOARD_ROOT` in `tools/demo_service.py`. The operator types both passwords; nothing is stored. Connect the NUS VPN first. Off the VPN the tool stops at the first hop, uploads and changes nothing, and prints `FAILED: BadAuthenticationType: Bad authentication type; allowed types: ['publickey']` followed by `The server does not offer password login. Off the NUS VPN, stujump accepts only public keys: connect the NUS VPN and run this again.`

```powershell
python -m tools.deploy_service --dry-run
python -m tools.deploy_service --server-cert-dir 'C:\path\to\renewed-server-certificate'
```

The first command prints the plan and connects nothing. The second checks both SSH host keys against `~/.ssh/known_hosts` (no trust on first use) and uploads `common/` and `ultra96/` into a new board folder; `--server-cert-dir` names a folder holding `server-cert.pem` and `server-key.pem`. On the board it then checks that the running `ultra96.server` is this user's, runs under `BOARD_ROOT` and owns exactly `127.0.0.1:8888` and `:9999` (or that both ports are free), compiles the new code, checks that the certificate and key it will use match and do not expire within an hour, and copies the running service's code aside for rollback. A refusal in these checks leaves the running service and the certificate untouched (only the uploaded folder stays), prints the error and saves no record. After a last check of the running process, it stops the old service (SIGTERM, then SIGKILL if it has not exited after 10 s), installs the new certificate with a backup of the old pair, starts the new service in the background and waits for both listeners. Any failure from that last check onwards stops the new service, restores the previous certificate and restarts the previous code, if a service was running before. From that last check onwards a final record (`deployed`, `rolled_back`, `failed_old_still_running`, `failed_nothing_running` or `rollback_failed_nothing_running`) is always printed, saved on the board in `BOARD_ROOT/evidence/active-deployment.json` and copied to `.comms-local/deployments/`, which `demo.py service --start` follows. If the board does not answer within 2 × the start timeout + 120 s (`--start-timeout`, default 30 s), the tool stops waiting and asks you to run `python demo.py service` and read `BOARD_ROOT/evidence/active-deployment.json` before trying again; the board may still be finishing or rolling back.

Without `--server-cert-dir` the certificate already on the board is kept, and the deploy is refused if it expires within an hour. The server certificate is valid for 30 days; issue a new one from the existing CA with `python -m tools.generate_comms_pki --renew-server-from <CA folder> --output-dir <new empty folder>`. The session defaults to `ltc-comms` (`--session-id`; this tool does not read `LTC_COMMS_SESSION`). `--model MODULE --model-path DIR` starts a model module instead of the built-in dummy model. The tool does not upload the model: DIR must be an absolute folder on the Ultra96 (for example under `BOARD_ROOT`) that already holds the module, and the service puts it first on its import path. `demo.py service --start` ignores a deployment record whose `--model-path` does not start with `/`, and falls back to an older record or to the 28 September folder.

A gated glove is silent while the player is still, so the service in this checkout (deployed on 2026-10-16) keeps a silent ingest connection open for up to 600 s (`--ingest-idle-timeout`, 5 to 86400 s) instead of 5 s. When all eight client slots are taken, it closes the ingest connection that has waited longest for its next frame (at least 5 s) to admit a new client. `tools.deploy_service` starts it with the 600 s default. On the real Ultra96 on 2026-10-16 two tests each kept one ingest connection silent. The next sample was accepted after 7, 30 and 120 s in the first and after 590 s in the second; after a further 620 s of silence the board had closed the second connection. Freeing a slot ran in host tests only.

Status (2026-10-16): verified against the real board. The tool's first real run, with the NUS VPN connected and the owner typing both passwords, stopped the 28 September version-2 service (SIGTERM), installed the renewed certificate (valid to 2026-11-13 14:27:35 UTC) with a backup of the old pair, started the version-3 service (session `ltc-comms`, the built-in dummy model, the 600 s default) and ended with `status: deployed`. Its record is `.comms-local/deployments/deployment-20261016T050629Z.json` on the owner's laptop. The board's login shell printed `Could not chdir to home directory /home/xilinx: Permission denied` and a `.bashrc` permission error; both are harmless, because the tool works under `BOARD_ROOT`. One service process accepts at most 128 glove identities (`device_id`, `boot_id`): each board boot, rehearsal or probe that sends it a sample uses one. Five were used on 2026-10-16, so redeploy before V1 to restart the service. The board-side program was also verified on Linux (WSL Ubuntu, 27 of 27 checks, including a deploy over a running version-2 service and a rollback) on 2026-10-14. Section 6.3 of the hand-off document describes each step and the expected result.

## Run and check the end-to-end demo

The version-3 Ultra96 service must already be running. `python demo.py service` inspects the **original project deployment only**: it uses the fixed original SSH accounts and board folder, and lists the listeners, this user's processes and the folder each `ultra96.server` runs from. Its `--start` mode has the same fixed target and must only be used for that owned deployment after the port checks pass. It starts the service in the foreground of that SSH session from the folder, and with the `--model`/`--model-path`, of the service named by the newest record in `.comms-local/deployments/` that left a service running. Without such a record it falls back to the 28 September folder, which holds version-2 code, so deploy with `tools.deploy_service` first; a deployment made by hand or from another laptop leaves no record here. On the owner's laptop the newest record is that of 2026-10-16. A teammate using another account or board must check and deploy that service through their own authorized route.

Laptop, Ultra96 and phone must use the same session. All three default to `ltc-comms`: `demo.py run`, `demo.py live`, `demo.py service --start`, `tools.deploy_service` and the phone source. To use another session, pass `--session-id <name>` to each laptop command or set `$env:LTC_COMMS_SESSION` (read by the `demo.py` commands only); the CLI option takes precedence. The phone app has its session compiled in, so it must be rebuilt to change. A session mismatch prevents ACK/subscription acceptance.

In terminal A, with the NUS VPN connected, open and keep the SSH tunnel using your authorized SSH identities (OpenSSH asks for both passwords):

```powershell
python demo.py tunnel --jump 'YOUR_JUMP_USER@stujump.comp.nus.edu.sg' --target 'YOUR_BOARD_USER@makerslab-fpga-35.ddns.comp.nus.edu.sg'
```

The `tunnel` defaults embed the original operator's jump account; override them for a teammate run. The local tunnel listens on `127.0.0.1:18889` and forwards to the board's loopback ingestion port 8888. On an iPhone app built from this source, tap **Communications Connect** (the app installed for Week 7 shows **Week 7 Connect**), wait for **Subscribed**, and record its starting **Received** count. The app installed for Week 7 uses session `week7-demo` and can no longer subscribe to the service deployed on 2026-10-16; keep it closed. Keep other result subscribers closed: the server has one active phone subscriber, and every result goes to it.

In terminal B, capture both physical boards:

```powershell
python demo.py run --ca 'C:\path\to\verified-public-ca.pem'
```

The `--ca` value is the verified **public** CA certificate, kept outside this repository; no CA or server private key is needed on the laptop. The default CA path in `demo.py` names the original operator’s private directory, so pass `--ca` explicitly on another machine.

The default run lasts 60 seconds at 10 Hz per board. It saves a report and packet evidence under `.comms-local/`, then displays the saved report and matching sensor/ACK examples. Check both devices' source, receive, send and ACK counts, the `clean` result, and the process exit code. The report table also has `Gated` and `Idle` columns, and each progress line shows `gated=yes|no|unknown`. A gated board (a real glove) is silent while the glove is still. Its idle ticks count toward coverage: sent plus idle ticks must reach 90% of the ticks expected while its notifications were on. Silence is not judged once it has reported idle ticks. Each board must still send at least one sample for a clean run, so move both gloves; with the real gloves, also pass `--rate 50`. Compare the **observed** iPhone count increase with the printed `Phone expected increase`. That figure assumes one result per accepted sample or command, which holds only while the Ultra96 runs the built-in dummy model (the run prints a line saying so); a real model may produce results at another rate. An ingestion ACK alone does not prove phone display.

For a 120-second keyboard demonstration, press `1` or `2` while this command is running to send a command to the matching board. Each command carries one version-3 packet (a 52-byte control frame); the board adds 1 to each of the 11 values (32767 wraps to -32768), and the service answers each new command itself with one `cmd:` result; commands never reach the model:

```powershell
python demo.py live --ca 'C:\path\to\verified-public-ca.pem'
```

For optional rate and BLE file tests, use `python demo.py run --ca 'C:\path\to\verified-public-ca.pem' --rate 50` or `python demo.py run --ca 'C:\path\to\verified-public-ca.pem' --file path\to\sample.bin --file-device 2`. These are separate tests; their reports, observed throughput and any fault losses should be reported separately from the clean 10 Hz demo. Reopen saved evidence with `python demo.py report "<saved capture directory>"`.

Status (2026-10-16): `demo.py run` and `live` have not run under version 3; they need both boards on the current firmware. The path through the real Ultra96 was checked without them, with `python -m tools.rehearse_remote_comms` and a desktop subscriber in place of the phone, through an OpenSSH tunnel that forwarded both 18889 and 19999 (`demo.py tunnel` opens only the ingest forward): 60 s at 10 Hz with synthetic samples (576 ACKs, 576 results, exact match) and with the right board over BLE (563 ACKs, 563 results, exact match). The BLE check passed on its second run; the first failed only because an idle test sent two samples at the same time. Run one such check at a time: every result goes to the one subscriber, so any other input during a rehearsal shows as unexpected results and fails it. No phone has received a version-3 result yet.

The [protocol specification](co-protocol-v3.md) defines packet, message, control and file behavior. For the instructor's Week 7 live sequence, see the archived [English](archive/assessment-week7/B07-CO-live-demo-guide.en.md) or [Chinese](archive/assessment-week7/B07-CO-live-demo-guide.zh-CN.md) guide; the [video operator script](archive/assessment-week7/B07-CO-video-operator-script.zh-CN.md) and [presentation](archive/assessment-week7/B07-CO-video-presentation.en.md) cover recording. They describe the Week 7 deployment (32-byte packets).

## Record glove data

Siqiang's Bluetooth Classic recording scripts cannot connect to the Communications firmware; he can still flash his own sketch and record with those. Once the gloves run the Communications firmware, record through the chain: a capture with the tunnel and the Ultra96 service running as above, then a CSV export of its samples. `--duration` sets the capture length in seconds (default 60).

```powershell
python demo.py run --ca 'C:\path\to\verified-public-ca.pem' --rate 50 --duration 120
python -m tools.export_capture
python -m tools.export_capture '<capture folder or packets.jsonl>' --out data.csv --device 2
```

Without a path, `tools.export_capture` takes the newest `B07-*` capture under `.comms-local/` and writes `samples.csv` beside its `packets.jsonl`. It never overwrites a file. Each row is one sample: `device_id`, `glove` (`left` or `right`), `boot_id`, `seq`, `uptime_ms`, then `ax ay az` (g), `gx gy gz` (deg/s), `yaw pitch roll` (deg) and `flex1 flex2` (0 to 1), restored as int16 / scale with four decimals. A sample recorded twice is written once. `--device 1` or `2` keeps one glove. It warns when the capture dropped evidence records under load, because those samples are missing from the CSV.

A gated glove sends only while moving: pauses show as `uptime_ms` jumps, not `seq` gaps, and the start of each movement is missing. To record every sample, IDLE included, flash the gloves with `COMMS_GLOVE_SEND_ALL`, and flash them again without it afterwards:

```powershell
$env:PLATFORMIO_BUILD_FLAGS = '-DCOMMS_GLOVE_SEND_ALL=1'
python flash.py --glove
Remove-Item Env:PLATFORMIO_BUILD_FLAGS
```

Status (2026-10-15): `tools.export_capture` is built and tested on synthetic captures; no glove recording has been made yet.

## Source and deployment identifiers

Since 2026-10-14 the source no longer accepts the Week 7 identifiers, and since the move to protocol version 3 later that day it no longer accepts versions 1 or 2. Since 2026-10-15 it also refuses the 24-byte source statistics of the first version-3 firmware. Both boards, the Ultra96 service and the phone app must run builds of the current source.

| Identifier | Value | Note |
|---|---|---|
| BLE sensor magic | `LC` (`4C 43`) | A board on Week 7 firmware (`W7`) is refused by the laptop; flash it with `python flash.py`. |
| Sensor packet | Version `3`, 38 bytes (16-byte header + 11 × int16) | Version-2 packets (32 bytes, 8 values) are refused. A sensor notification needs ATT MTU ≥ 41. |
| BLE source statistics | `LCS3`, 36 bytes (flag bit 0 = gated source; idle, unread and refused tick totals) | Version-2 firmware (`LCS1`), Week 7 firmware (`W7S1`) and version-3 builds from before 2026-10-15 (`LCS3`) answer 24 bytes and are refused before subscribing: `source statistics must contain exactly 36 bytes; flash this board with the current firmware`. |
| Network messages | `SENSOR_BATCH`, `INGEST_ACK`, `GESTURE_RESULT` at `v` 3; `SUBSCRIBE`, `SUBSCRIBED` at `v` 1 | A result label is 1 to 32 characters of `A–Z a–z 0–9 _ -`; confidence is a finite number from 0 to 1. The app installed for Week 7 accepts only older results and the four dummy labels. |
| Network session | `ltc-comms` | Laptop, Ultra96 and phone must agree. The Ultra96 service deployed on 2026-10-16 uses `ltc-comms`; the service started for Week 7 used `week7-demo`. The app installed for Week 7 still uses `week7-demo` and can no longer subscribe; rebuild the app. |
| TLS service identity | `ultra96.week7.internal` | Kept: it is written into the server certificate and checked by every client. Changing it needs a new certificate and a rebuilt app. |
| Local capture and board mapping | `.comms-local/` | The old `.week7-local/` folder is no longer read. Captures recorded with Week 7 firmware hold `W7` packets and do not pass `demo.py report`; review them from commit `880abba`. Captures recorded with version-2 firmware are refused by `demo.py report` and `tools/video_evidence.py`; review them from commit `c42b386` or `5a004c6` (the team main after PR #18). |
| Native C bridge | `CommsStart`, `CommsCopyDisplay`, `CommsStop`, and `CommsNextResult` (per-result game input). Compiled and tested on Linux in a Swift 6.1 container on 2026-10-15 and on macOS on 2026-10-16; built for the iOS Simulator and, in the Week 7 export, for an iOS device on 2026-10-16 (unsigned); not yet installed on a phone | The `Week7*` wrappers are kept for the Week 7 Unity export only; its `Week7*` calls linked to them in the unsigned build of 2026-10-16. |

The `CommsNative` UI names its button **Communications Connect**; the Unity app installed for Week 7 shows **Week 7 Connect**. The archived B07 live and video guides describe the Week 7 deployment and show its packet and session values; they are history and no longer match this checkout.

The `phone/` Python, Android Unity C# and iSH helpers are retained as reference and diagnostic clients. The Python and C# receivers accept only version-3 results with the same label and confidence rules (`phone/receiver.py` is built and tested; on 2026-10-15 `CommsPhoneCore.cs` was compiled and its self-test passed, 113 checks with `phone/tests/run_core_tests.ps1` under PowerShell 7; the Unity component `CommsPhoneReceiver.cs` was only read). The active iPhone path for this demo is the Swift `ios-visualizer/CommsNative` client linked into the Unity export; use its setup and result display for phone acceptance.
