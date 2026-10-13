# Communications quickstart

This checkout contains the two-FireBeetle communications source and operator tools. In the deployed demo, two ESP32 boards send dummy sensor packets over authenticated BLE to one Windows laptop. The laptop opens an SSH forward and two TLS ingestion streams to Ultra96. Ultra96 acknowledges each accepted input to the laptop and sends simulated gesture results over a separate SSH/TLS connection owned by the installed iPhone app.

## Before a physical run

- Use Windows with Python 3.10 or newer, PlatformIO for firmware uploads, Bluetooth enabled, and the institutional VPN route to Ultra96. Install laptop dependencies with `python -m pip install -r laptop/requirements.txt`.
- Have two distinct FireBeetle32 boards, a programming USB cable, and independent power for each board during the BLE demonstration. Keep their serial pairing passkeys off camera and out of saved logs.
- The matching Ultra96 service and native Unity iPhone app must already be deployed. The app needs its public CA and its own VPN/SSH credentials. This source handoff does **not** include the exported Unity Xcode project or a prebuilt app; rebuilding the deployed app needs the team's separate export. See [iOS source and build boundary](../ios-visualizer/README.md).
- The iPhone client pins the original jump/board SSH host keys and CA fingerprint, and verifies the TLS service name `ultra96.week7.internal`. Laptop `--jump`, `--target` and `--ca` overrides do not change the phone route. A different Ultra96 deployment requires verified new trust values in the iOS source and a rebuilt, installed app; retain certificate and host-key verification.
- Run all commands below from the repository root. Confirm available options with `python flash.py --help` and `python demo.py --help`.

## Flash and pair the boards

If the matching firmware is already on both boards and the dummy fixtures have not changed, use the saved mapping and proceed to the next section. For first setup or after editing [`common/dummy_fixtures.json`](../common/dummy_fixtures.json):

```powershell
python flash.py --ports
python flash.py
python flash.py --boards
```

`flash.py` generates the firmware fixture header, builds both protected profiles, then asks for the first physical board (LEFT / device 1) and a different second board (RIGHT / device 2). It uploads them one at a time through the programming USB cable and saves their Bluetooth addresses locally. Label each board after its successful upload. For later fixture changes, connect the existing LEFT board first and RIGHT board second to retain their roles.

On initial Bluetooth setup, use the private serial monitor and pairing mode one board at a time:

```powershell
python flash.py --monitor COMx
python flash.py --pair left
python flash.py --pair right
```

Replace `COMx` with the actual port shown by `--ports`; run the monitor in a separate terminal while pairing. Existing authenticated bonds are reused. After setup, disconnect both boards from laptop USB and power them independently.

## Run and check the end-to-end demo

The configured Ultra96 service must already be running. `python demo.py service` checks the **original project deployment only**: it uses a fixed original SSH account and board source path. Its `--start` mode has the same fixed target and must only be used for that owned deployment after the port checks pass. A teammate using another account or board must check and deploy that service through their own authorized route.

Laptop, Ultra96 and phone must use the same session. All three default to `ltc-comms`: `demo.py run`, `demo.py live`, `demo.py service --start` and the phone source. To use another session, pass `--session-id <name>` to each laptop command or set `$env:LTC_COMMS_SESSION`; the CLI option takes precedence. The phone app has its session compiled in, so it must be rebuilt to change. A session mismatch prevents ACK/subscription acceptance.

In terminal A, open and keep the SSH tunnel using your authorized SSH identities:

```powershell
python demo.py tunnel --jump 'YOUR_JUMP_USER@stujump.comp.nus.edu.sg' --target 'YOUR_BOARD_USER@makerslab-fpga-35.ddns.comp.nus.edu.sg'
```

The `tunnel` defaults embed the original operator's jump account; override them for a teammate run. The local tunnel listens on `127.0.0.1:18889` and forwards to the board's loopback ingestion port 8888. On the already deployed iPhone app, tap **Week 7 Connect**, wait for **Subscribed**, and record its starting **Received** count. Keep other result subscribers closed: the server has one active phone subscriber.

In terminal B, capture both physical boards:

```powershell
python demo.py run --ca 'C:\path\to\verified-public-ca.pem'
```

The `--ca` value is the verified **public** CA certificate, kept outside this repository; no CA or server private key is needed on the laptop. The default CA path in `demo.py` names the original operator’s private directory, so pass `--ca` explicitly on another machine.

The default run lasts 60 seconds at 10 Hz per board. It saves a report and packet evidence under `.comms-local/`, then displays the saved report and matching sensor/ACK examples. Check both devices' source, receive, send and ACK counts, the `clean` result, and the process exit code. Compare the **observed** iPhone count increase with the accepted result total; an ingestion ACK alone does not prove phone display.

For a 120-second keyboard demonstration, press `1` or `2` while this command is running to send a command to the matching board:

```powershell
python demo.py live --ca 'C:\path\to\verified-public-ca.pem'
```

For optional rate and BLE file tests, use `python demo.py run --ca 'C:\path\to\verified-public-ca.pem' --rate 50` or `python demo.py run --ca 'C:\path\to\verified-public-ca.pem' --file path\to\sample.bin --file-device 2`. These are separate tests; their reports, observed throughput and any fault losses should be reported separately from the clean 10 Hz demo. Reopen saved evidence with `python demo.py report "<saved capture directory>"`.

For the instructor's full live sequence, see the [English](archive/assessment-week7/B07-CO-live-demo-guide.en.md) or [Chinese](archive/assessment-week7/B07-CO-live-demo-guide.zh-CN.md) guide. The [v2 protocol](co-protocol-v2.md) defines packet/control/file behavior; the [video operator script](archive/assessment-week7/B07-CO-video-operator-script.zh-CN.md) and [presentation](archive/assessment-week7/B07-CO-video-presentation.en.md) cover recording.

## Source and deployment identifiers

Since 2026-10-14 the source no longer accepts the Week 7 identifiers. Both boards, the Ultra96 service and the phone app must run builds of the current source.

| Identifier | Value | Note |
|---|---|---|
| BLE sensor magic | `LC` (`4C 43`) | A board on Week 7 firmware (`W7`) is refused by the laptop; flash it with `python flash.py`. |
| BLE source statistics | `LCS1` | Week 7 firmware answers `W7S1`, which is refused. |
| Network session | `ltc-comms` | Laptop, Ultra96 and phone must agree. The service started for Week 7 and the app installed for Week 7 use `week7-demo`; restart the service from this source and rebuild the app. |
| TLS service identity | `ultra96.week7.internal` | Kept: it is written into the server certificate and checked by every client. Changing it needs a new certificate and a rebuilt app. |
| Local capture and board mapping | `.comms-local/` | The old `.week7-local/` folder is no longer read. Captures recorded with Week 7 firmware hold `W7` packets and do not pass `demo.py report`; review them from commit `ec398b6`. |
| Native C bridge | `CommsStart`, `CommsCopyDisplay`, `CommsStop` | The `Week7*` wrappers are kept for the Week 7 Unity export only. |

The `CommsNative` UI names its button **Communications Connect**; the Unity app installed for Week 7 shows **Week 7 Connect**. The archived B07 live and video guides describe the Week 7 deployment and show its packet and session values; they are history and no longer match this checkout.

The `phone/` Python, Android Unity C# and iSH helpers are retained as reference and diagnostic clients. The active installed iPhone path for this demo is the Swift `ios-visualizer/CommsNative` client linked into the Unity export; use its setup and result display for phone acceptance.
