# Integration journal: Communications (CG4002 B07)

**Owner:** olsonwangyj (Yoz), Communications owner and integration lead.
**Covers:** every piece of integration work that crosses the Communications subsystem: gloves → laptop (BLE) → Ultra96 (SSH and TLS) → the model runner on the board → phone → game.
**Why it exists:** from Week 9 the team keeps an integration journal (Siqiang's request in the team chat, 2026-10-25): the integration activities carried out, the challenges or failures, how they were investigated, the solutions considered, the changes made, the later iterations, tests and retests, and the decisions that affect more than one subsystem. This file is the Communications part, kept in full detail. Each week opens with a one-page summary that can be copied into the team's shared journal; the detailed record follows it.
**How it relates to the other documents:** the hand-off document ([communications-handoff.md](communications-handoff.md)) records the current state, the design and its reasons; this journal records how the integration got there, week by week. Where the two disagree on a fact, check the evidence named in the entry; the code governs both.
**Kept current by:** `AGENTS.md` rule 9. Every code change, deployment change, integration run and cross-subsystem decision gets an entry here in the same piece of work.
**Last updated:** 2026-10-27 (Weeks 9 and 10 reconstructed after the fact, see "Sources"; Week 11 kept as it happens).

---

## How to read this journal

- Times are Singapore time (+08:00) unless marked `Z` (UTC).
- Commits are on the fork's `main` unless "team main" (`B07-CG4002/Let-Them-Cook`) is named. Pull requests are written "team PR #n" (team repo) or "fork PR #n" (`olsonwangyj/Let-Them-Cook`).
- Paths that start with `.comms-local/` are on the owner's Windows laptop (`D:\LetThemCook\.comms-local\`, git-ignored, in no repository). "Project library" means the file library of the owner's Claude project.
- Marks:
  - **[Owner's report]**: what the owner said or read off a screen (for example the phone's `Received` count); not measured by Communications tooling.
  - **[Inferred]**: a conclusion drawn from the evidence but not tested directly.
  - **[Not confirmed]**: stated somewhere, but no evidence for it was found while writing.
  - **[Proposal]**: designed or suggested, not built or not agreed.
- Teaching weeks run Monday to Sunday: **Week 9 = 12 to 18 October 2026, Week 10 = 19 to 25 October 2026, Week 11 starts on Monday 26 October 2026.** This rests on the owner's statement of 2026-10-25 that Week 11 starts on Monday 2026-10-26; the repository holds no semester calendar.

### Sources used for Weeks 9 and 10

Weeks 9 and 10 were written on 2026-10-25 from:

- the git history of the fork and of the team main (fetched on 2026-10-25; the newest team commit is `851080b`, 2026-10-23);
- the hand-off document: the change log (section 14), the hardware rows (6.1), the deployment state (6.3) and the open items (13);
- the run folders `.comms-local/B07-*/` (`run.log`, `report.json`, `exit-code.txt`; the verdicts and phone lines of every Week 10 run were re-read on 2026-10-25), the deployment records `.comms-local/deployments/`, the check evidence `.comms-local/checks/`, and the local helpers and runbook in `.comms-local/cnn-full-20261020/` and `.comms-local/integration-20261022/`;
- the reports in the project library: `board-trial/wen-ree-runner-trial.md`, `board-trial/full-cnn-switch-check.md`, `e2e-check/model-to-game-chain.md`, `two-player/four-glove-feasibility.md`, `one-player-two-hands/two-hands-different-gestures.md`, `ble-link-starvation/one-glove-starved-link.md`, `comms-todo/comms-todo-and-doc-check-20261023.md`;
- the owner's messages in the project chat (teammates' messages appear only where the owner relayed them).

One correction came out of this reconstruction: the hand-off document said the service restart at about 09:57 on 2026-10-22 had no record on the laptop. It has one (`deployment-20261022T015740Z.json`), and that deploy used the older `20261018_v2` weights (W10-11). The hand-off document was corrected the same day.

---

## Week 9 (Monday 12 October to Sunday 18 October 2026)

### One-page summary

**Starting point.** The Week 7 chain (two ESP32 boards → laptop → Ultra96 → iPhone, protocol version 2, 32-byte packets carrying 8 dummy values) last ran end to end on 2026-10-01. No teammate component was on it, and the server certificate on the Ultra96 had expired on 2026-10-06.

**What was done.** The Communications subsystem entered the team repo (team PR #15, 10-13) and its Week 7 compatibility code was removed (team PR #18, 10-14). Protocol version 3 was built for real data (team PR #19, 10-16): a 38-byte packet that carries the glove's 11 real sensor values, a model interface on the board, real labels and confidence to every receiver, and a per-result function, `CommsNextResult`, for the game. Siqiang's sensor module (10-15) was built into the glove firmware, and "gating" was added, because by Siqiang's answer a glove sends only while the movement detector says MOVING. The version-3 service and a renewed certificate were deployed to the Ultra96 with a new one-step deploy tool (10-16). On 10-17 the acceptance run passed at 10 Hz and 50 Hz: both boards through the Ultra96 to the iPhone, with every sample acknowledged and every result received. On 10-18 the game's iOS export was linked with the Communications client and installed, and dummy results reached the game's action code (1210 written by the board, 1210 received by the game). The same day Siqiang's two gloves were flashed with the Communications firmware and passed together through the Ultra96 at 50 Hz. Wen Ree's FPGA runner needs `sudo`, so a separate-process bridge and a deploy option that starts the runner were built. The evening ended with one command, `python demo.py start`, that runs the whole laptop side with a live view and a board view.

**Failures and how they were solved.** (1) The left glove's gz channel was always 0: traced to a read offset in the glove module (the temperature skipped as 4 bytes instead of 2) and fixed with one line at the owner's request (team PR #24). (2) The iPhone app could not save its settings: a root-owned folder in the app's container; the client now falls back to the old folder (team PR #20). (3) Connect in the game failed with the same kind of permission error: the setup-copy step created a root-owned folder; the script was fixed. (4) The first deploy failed off the NUS VPN: the jump host then refuses password logins; the tool now says so. (5) The first acceptance attempt ran without the SSH tunnel: an operator step, now documented.

**Decisions that affect more than one subsystem.** Communications passes when the data is delivered, not on accuracy (D39). Only the newest protocol version is supported, and every component is upgraded together. Gating follows Siqiang's answer (reversed for the runner in Week 10). Wen Ree's runner runs as a separate program that Communications' deploy tool starts. Jie Ling writes the game's calls and sends the iOS export; the owner links the Communications client into it. Teammates deliver code through GitHub.

**End of the week.** The chain works with real gloves (gated) and the dummy model; Wen Ree's model and the game's real actions are not on it yet.

### Day by day

| Date | What happened | Evidence |
|---|---|---|
| Mon 10-12 | Siqiang merged the IDLE/MOVING logistic-regression detector and recorded samples (team PR #16, 22:09). This detector later decides when a glove sends (W9-3). No Communications commit that day. | team main `bfb8b84`, `02a99c3` |
| Tue 10-13 | Team PR #15 merged (17:58): the Communications subsystem imported into the team repo with stable names (prepared on 10-08 in `caf330e` and `d227a84`). Jie Ling's Unity AR visualiser merged (team PR #17, 15:43). The owner became integration lead; code ownership recorded for agents (`845c1d5`). | `880abba`, `b87ffc7`, hand-off 2.4 |
| Wed 10-14 | Early morning: the Week 7 compatibility code removed (`28db0b3`, `b414696`), the certificate tool learned to renew the server certificate from the existing CA (`aa18643`), the hand-off document written. Evening: team PR #18 (the compatibility removal) merged (21:16, `5a004c6`); interface proposals to the teammates, the division of work and the schedule up to the V1 session on Tue 10-20 recorded (`971fc52`); protocol version 3 built on the branch `comms/protocol-v3` (`a34c467`, `57a3fbd`, `a4b907b`, `3b94990`); the right test board flashed with version 2, then version 3, and checked against a service on the laptop; the server certificate renewed locally. | hand-off 14 (10-14 rows) |
| Thu 10-15 | Siqiang pushed the sensor module (team `51593be`, 11:11) and answered questions A to F. Gating, 36-byte source statistics, the 600 s ingest idle limit, the `-glove` firmware environments, `flash.py --glove` and the capture exporter built; the Swift client compiled and tested on Linux, the C# reference core compiled. 841 tests passed. Nothing ran on hardware (the right board had been unplugged in the middle of a flash). | hand-off 14 (10-15 rows) |
| Fri 10-16 | Team PR #19 (version 3) merged (11:37, `7d8317a`). On the Mac: the Swift package tested on macOS (73 tests) and built for iOS. On the laptop: the right board reflashed; the first hardware run of gating; the version-3 service and the renewed certificate deployed to the Ultra96 (13:06; the deploy tool's first real run); rehearsals through the real Ultra96 passed (576 = 576, 563 = 563); the 600 s idle limit confirmed. On the iPhone: the rebuilt app installed (13:13), the settings-save failure fixed, `Subscribed` at about 14:45. Team PR #20 merged (15:25, `be97a04`). Later: the `gloveBegin()` retry (D38) and the pass criterion D39. | `deployment-20261016T050629Z.json`, `.comms-local/checks/2026-10-16-*` |
| Sat 10-17 | Jie Ling's team PR #21 merged (00:58, `a1da5d6`): the game's `CommsBridge.cs` calls the Communications client; the old port-5005 receiver removed. 01:40 the left test board flashed with version 3; 01:51 to 02:00 the acceptance run (failed once without a tunnel, then passed at 10 Hz and 50 Hz). | `.comms-local/B07-20261016T1750*`, `T1757*`, `T1759*` |
| Sun 10-18 | 12:30 to 13:00 (cloud): the separate-process bridge and the deploy option `--runner` for Wen Ree's runner (D41, D42). 13:25 the phone app's signing profile renewed; a two-board run gave 1207 = 1207 on the phone. 13:40 the fork PR #3 tested on Windows. 14:31 to 14:57 the game's export linked, installed and subscribed; 1210 dummy results reached the game; fork PR #4 and team PR #22 merged. 15:36 Wen Ree's team PR #23 (recorders; the gyro read fixed in the firmware copy of the glove module). 17:14 to 19:27 Siqiang's gloves flashed, gz = 0 traced and fixed, both gloves passed together. 19:40 to 23:44 `python demo.py start` and the board monitor built (committed as `2b3be2b`). | hand-off 14 (10-18 rows); `.comms-local/checks/2026-10-18-*` |

### Issues, investigations and changes

#### W9-1. The server certificate on the Ultra96 had expired

- **What happened.** The certificate deployed to the board in September expired on 2026-10-06 15:11:29 UTC (read from the laptop's copy; the board's copy was not read before it was replaced).
- **Investigation.** Found on 10-14 while writing the hand-off document. The CA itself was still valid, and the phone and the laptop trust the CA, not the server certificate.
- **Options considered.** A new CA (every client would need the new CA), or a new server certificate from the existing CA (no client change).
- **Change.** The certificate tool gained a renewal option that issues a new server certificate from the existing CA (`aa18643`, 10-14). The renewed certificate (valid until 2026-11-13 14:27:35 UTC) was deployed with the version-3 service on 10-16.
- **Retest.** On 10-16 the iPhone passed the TLS check against the renewed certificate (`Subscribed`), and the laptop's rehearsals passed.
- **Status.** Solved. Renew again in early November.

#### W9-2. Version 2 could not carry real data or real results

- **What happened.** Version 2 carried 8 dimensionless dummy values in 32 bytes; real gloves produce 11 values (`ax, ay, az, gx, gy, gz, yaw, pitch, roll, flex1, flex2`). The board had no place to hand samples to a model, and the phone showed only the latest result as text, which cannot give the game every result.
- **Options considered.** Keep version 2 beside a new format (interoperability), or replace it everywhere. The owner chose replacement on 10-14: only the newest version is supported, and every component is upgraded together.
- **Change (10-14 evening).** Version 3: a 38-byte packet (16-byte header and 11 int16 values with a fixed scale per value; the scales were to be checked against Siqiang's real output), `LCS3` source statistics, the board model interface (`start(emit)`, `on_sample`, a thread-safe `emit`, loaded with `--model`), model labels and real confidence on every receiver, `CommsNextResult` for the game, and two tools: `tools.deploy_service` (one-step deploy with rollback) and `tools.check_board`. An adversarial review found nine defects, fixed in `a4b907b`. The specification became `docs/co-protocol-v3.md`.
- **Retest.** The right test board passed with version 3 against a service on the laptop (10-14); the full suite passed; on 10-16 the Ultra96 ran version 3 (W9-1); the acceptance run of 10-17 passed (W9-7).
- **Status.** Done; in the team main since team PR #19 (10-16).

#### W9-3. Siqiang's gloves send only while moving ("gating")

- **What happened.** Siqiang's answer E (10-15): the final glove code sends data only while the movement detector says MOVING, and nothing while IDLE. The Week 7 design assumed a constant stream, and the board closed an ingest connection after 5 s of silence.
- **Options considered.** Carry the IDLE/MOVING state in every packet (format change, constant stream), or skip IDLE ticks on the glove. The owner asked that the firmware call Siqiang's decision function; the agent chose the details (decisions D20 to D31).
- **Change.** The firmware asks the glove module once per sample and skips IDLE ticks without using a sequence number; the source statistics grew to 36 bytes with a "gated" flag and idle, unread and refused counters; the laptop judges a gated glove's coverage by its ticks; the board lets a silent ingest connection wait 600 s instead of 5 s and evicts the longest-silent connection when full; a build switch `-DCOMMS_GLOVE_SEND_ALL=1` sends every tick (for recording). New `-glove` firmware environments build Siqiang's unchanged module, and `python flash.py --glove` flashes it.
- **Issues found in Siqiang's module and reported to the owner (hand-off 7.1, points 1 to 5):** the include path; the classifier is not reset after a failed reading; one failed calibration read makes `gloveBegin()` fail; `gloveBegin()` accepts only WHO_AM_I `0x70`. Point 3 was mitigated on the Communications side by retrying `gloveBegin()` at boot (W9-6).
- **Retest.** 10-16: the right test board with a gated dummy module passed (900 = 900 = 900, 2140 idle ticks); the real Ultra96 kept a silent ingest connection for 590 s and closed it between 600 and 620 s. 10-18: both real gloves passed together with gating, the first hardware run of the gated coverage rule (coverage 0.989 and 0.988).
- **Status.** Done. In Week 10 the gloves were switched to the always-send build for Wen Ree's runner (W10-3); the gated build stays in the code.

#### W9-4. The first deploy failed off the NUS VPN

- **What happened.** 10-16: with the laptop on Wi-Fi without the NUS VPN, the jump host `stujump` was reachable but offered only public-key login, so the deploy failed at the first hop.
- **Change.** `tools/deploy_service.py` prints a hint to connect the VPN when the jump host offers no password login (one new test; 843 passed).
- **Retest.** The deploy passed with the VPN on (13:06).
- **Status.** Solved; recorded as a pitfall (hand-off 9.2).

#### W9-5. The iPhone app could not save its settings

- **What happened.** 10-16, the first Connect after the rebuilt app was installed over the Week 7 app: `Could not save the public setup. Try again while the iPhone is unlocked.`
- **Investigation.** A diagnostic build showed `NSCocoaErrorDomain 513` with POSIX 13 (permission denied). The app container's `Library/Application Support` was owned by root, while the older `Application Support/Week7` inside it belonged to the app and was writable.
- **Options considered.** Ask for a clean reinstall (loses the saved setup), or fall back to the writable old folder.
- **Change.** `ConfigurationStore.writableTarget()` saves into `Application Support/Comms`, or, when that folder cannot be created for lack of permission and the old `Week7` folder is writable, into `Week7`; the save message now shows the underlying error (D37; three new tests, 76 on macOS).
- **Retest.** The fixed app was reinstalled; `Subscribed` at about 14:45.
- **Status.** Solved; in the team main since team PR #20 (15:25). The root-owned folder was most likely made by an earlier `devicectl` copy into the container [Inferred, from what happened on 10-18 in W9-8].

#### W9-6. A glove whose sensor fails once at boot would never send

- **What happened.** Point 3 of W9-3: one failed calibration read makes `gloveBegin()` fail, and the firmware then sends nothing.
- **Change.** The firmware retries `gloveBegin()` up to three times at boot, 500 ms apart (D38, 10-16, decided by the agent at the owner's request).
- **Retest.** On the right test board, which has no sensors, the `-glove` build made three tries (`attempts=3`) and still advertised and answered commands; the plain build passed its check again.
- **Status.** Done. Not yet seen on a real glove whose first try fails and a later one succeeds.

#### W9-7. Acceptance run: both boards through the Ultra96 to the iPhone

- **What happened.** 10-17 01:51, the first `python demo.py run`: `CAPTURE NOT PASSED`; both boards streamed, but nothing was acknowledged (`transport_errors` 11).
- **Investigation.** No SSH tunnel was listening on `127.0.0.1:18889`: the owner had not yet opened `python demo.py tunnel`. An operator step, not a fault.
- **Change.** None in code; recorded as a pitfall (hand-off 9.2).
- **Retest.** 01:57 at 10 Hz: `CAPTURE PASSED`, left 602 = 602 = 602, right 602 = 602 = 602, and the phone's `Received` went from 0 to 1204, equal to `Phone expected increase` [Owner's report for the phone count]. 01:59 at 50 Hz: `CAPTURE PASSED`, left 3032 and right 3003, and the phone's `Received` rose to 7239 = 1204 + 6035 [Owner's report].
- **Status.** Passed. By D39 this was Communications' acceptance with dummy data and the dummy model.

#### W9-8. Getting results into Jie Ling's game on the phone

- **What happened.** 10-18. The game cannot be built from Git alone (its content package `.tgz` is not in Git), and Unity was not installed on the owner's Mac.
- **Options considered.** Install Unity on the owner's Mac (about 4 GB, a Unity ID), or have Jie Ling export the iOS Xcode project and send it. The owner chose the export; the linking step goes into the repository as a script, and the export itself is not committed.
- **Changes and the problems met on the way.**
  1. New `ios-visualizer/tools/link_commsnative.py` and `build_game_ios.sh`: link the Communications client into the export, sign, build, install and launch. On Jie Ling's export `ConnectionTest_V2.zip` the client's package path pointed at Jie Ling's own checkout and `UnityFramework` lacked its package dependency; the script now repairs both.
  2. New `copy_phone_setup.sh`: copies the public setup (user names, the CA certificate; never a password) from the Communications test app into the game, so Connect opens prefilled.
  3. Connect in the game then failed with `NSCocoaErrorDomain 513` (W9-5's kind of error): `devicectl device copy to` creates missing destination folders as root. The script now copies a folder that holds `Comms/` over `Application Support`, so `Comms` belongs to the app, and checks the owner afterwards.
- **Retest.** The game reached `Subscribed`. A 60 s two-board run at 10 Hz with the dummy model: `CAPTURE PASSED` (left 607, right 603), `Phone expected increase` 1210, and the game's `Received` was 1210 [Owner's report]; the game's console logged 318 `Chop pressed` lines raised from Communications results (the dummy label `POINT` maps to Chop). The game's Play button "did nothing" when tapped: by the game's design a menu item is chosen by pointing the tracked hand at it and pressing Select, so this is not a Communications issue.
- **Status.** Done; fork PR #4 and team PR #22 merged (14:57). Separately, the phone app's free signing profile was renewed (13:25; expiry 2026-10-25 13:25:57) and a two-board run gave 1207 = 1207 on the phone.

#### W9-9. The left glove's gz channel was always 0

- **What happened.** 10-18 17:14 to 17:53, the first run of Siqiang's left glove on the Communications firmware: every channel followed the motion except gz, which was exactly 0 in all 719 samples; a second run gave gz = 0 in all 2024 samples while the owner turned the glove about its vertical axis.
- **Investigation.** The glove's whole flash had been backed up before the first flash (`.comms-local/glove-backup/`). Siqiang's own sketch was written back, and its USB output showed gz between about -250 and +250 deg/s, so the IMU works. Reading the module: it skipped the temperature register as 4 bytes instead of 2 (a second `(void)readInt16();`), which shifts the gyroscope values by one (the reported gx was the real gy, and so on).
- **Options considered.** Report it to Siqiang and wait, or fix the one line. The owner asked for the fix directly ("发现了问题直接帮他改了把"): a one-line exception to the rule that teammates' files are not edited.
- **Change.** The extra read deleted in `hardware/gloves/integration_files/glove_sensor.cpp` and the firmware copy synced. Wen Ree had fixed the same line in the firmware copy in the team main that afternoon (`1609d10`, team PR #23); team PR #24 carried the fix to Siqiang's source (merged on 10-19, `45c2dd5`).
- **Retest.** A 60 s single-glove run through the Ultra96: 1653 received, 0 gaps, gz between about -250 and +250 deg/s (1497 distinct values in 1656 samples). Then the right glove alone (2019 received, all 11 channels varying) and **both gloves together**: `CAPTURE PASSED`, left 2165 and right 1711 generated = received = acknowledged, gated, 0 gaps, the first run of both real gloves together.
- **Side issue.** Writing Siqiang's sketch back erased the glove's BLE bond, so the stale Windows bond was removed and the glove paired again; pairing works only with the serial monitor open first (hand-off 9.2).
- **Status.** Solved. Siqiang's agreement with the fix is [Not confirmed].

#### W9-10. Wen Ree's runner needs `sudo`, so it cannot run inside the board service

- **What happened.** 10-18, Wen Ree's answer (relayed by the owner): the FPGA inference runner needs `sudo` and PYNQ's Python, so it will run as a separate program beside the board service; Wen Ree asked for the format.
- **Options considered.** The in-process interface of W9-2 (the service runs without `sudo`, so it cannot load the overlay), or a separate process with a small line-based format.
- **Change.** `ultra96/model_bridge.py` (D41): the service's model, a Unix socket on the board, a `hello` line, then one `sample` line per sample and one `result` line per result, a 1024-line queue, bad lines skipped and counted. At the owner's request ("Cannot just write code to start at once?"), `tools.deploy_service --runner` starts the runner with `sudo` after the service, asking for the `sudo` password once (D42). The owner cut the message to Wen Ree down to the plain format, without the example script.
- **Retest.** Linux tests and a two-process run in the cloud (8 of 8 results); on Windows three problems fixed (`f0885a6`); a four-reviewer review confirmed 8 problems, all fixed (for example: a runner started by hand and the new one took the bridge's connection from each other; now the launcher checks the PID and reports `conflict`).
- **Status.** End of Week 9: draft fork PR #3, not deployed. Started on the board on 10-19 (W10-2).

#### W9-11. The logging was hard to use

- **What happened.** 10-18, the owner: the existing logging is hard to use; the owner wanted a live, readable view per glove, one log file per run, one command to start and stop everything, passwords typed by the owner and never stored, no change to the packet format and no slower data path.
- **Change (evening).** `python demo.py start`: one OpenSSH login with both forwards, both gloves at 50 Hz, a live view that refreshes in place, one `run.log` per run with a summary, and the unchanged `CAPTURE PASSED` check (`tools/live_session.py`, `tools/live_view.py`, `laptop/dual_bridge.py --supervised`). A read-only board view (`ultra96/monitor.py`, `laptop/board_monitor.py`; a `MONITOR` request on the existing port 9999, D40) shows the board's counts, including the results written to the phone. That count is also the delivery tally that D39 needs for a real model, which does not answer every sample.
- **Retest.** 970 tests passed; nothing ran on hardware that day.
- **Status.** Committed as `2b3be2b` (23:44); deployed and first run on 10-19 (W10-1).

### Decisions that affect more than one subsystem (Week 9)

| Date | Decision | Who | Affects |
|---|---|---|---|
| 10-14 | Only the newest protocol version is supported; upgrading means reflashing, redeploying and reinstalling together. Teammates deliver code through GitHub, not over Telegram. | Owner | All |
| 10-14 | Proposed to the teammates (final when they confirm): the model gets the 11 values as physical floats; the game takes one result at a time through `CommsNextResult`; Jie Ling writes the Unity calls; the real-data packet is version 3. | Owner, proposal | Wen Ree, Jie Ling |
| 10-15 | A glove sends only while Siqiang's detector says MOVING; the firmware calls that decision for each sample, so the state does not travel in the packet. Reversed for the runner on 10-19 (W10-3). | Siqiang's answer, owner's request | Siqiang, Wen Ree |
| 10-16 | D39: Communications passes when the data is delivered (every sample acknowledged; every result the model emits reaches the phone unchanged). The number of results, labels, accuracy and the game's actions are not Communications' criterion. | Owner | All |
| 10-18 | Wen Ree's runner is a separate program; Communications provides the socket format and starts the runner with its deploy tool (D41, D42). Wen Ree no longer needs to provide in-process functions. | Owner, with Wen Ree's answer | Wen Ree |
| 10-18 | Jie Ling sends the iOS export; the owner links the Communications client into it with a script kept in the repository; the export is not committed. | Owner | Jie Ling |
| 10-18 | The gyro read fixed in Siqiang's file, as a one-line exception to the ownership rule. | Owner | Siqiang |

### Tests on hardware (Week 9)

| When | Run | Result | Evidence |
|---|---|---|---|
| 10-16 | Right test board, plain build, `tools.check_board` | 50 Hz, 3022 = 3022 = 3022 | `.comms-local/checks/2026-10-16-right-board-gating/` |
| 10-16 | Right test board, gated dummy | 900 = 900 = 900, 2140 idle | same |
| 10-16 | Synthetic and BLE rehearsals through the real Ultra96 | 576 = 576; 563 = 563 (about 10 Hz) | `.comms-local/checks/2026-10-16-ultra96-v3/` |
| 10-17 | Left test board, current firmware | 50 Hz, 3025 = 3025 = 3025 | `.comms-local/checks/2026-10-17-left-board/` |
| 10-17 | Acceptance, 10 Hz and 50 Hz, phone subscribed | Passed; phone 1204, then 6035 more [Owner's report] | `.comms-local/B07-20261016T175715*`, `T175920*` |
| 10-18 | Two test boards after the phone app's renewal | Passed; phone 1207 = 1207 [Owner's report] | `.comms-local/B07-20261018T053818*` |
| 10-18 | Two test boards into the game | Passed; game 1210 = 1210 [Owner's report]; 318 Chop actions in the console | hand-off 6.1 |
| 10-18 | Left glove alone; after the gyro fix | 1877 acknowledged, gz = 0; then 1653, gz varying | `.comms-local/checks/2026-10-18-left-glove/` |
| 10-18 | Both real gloves together, gated, through the Ultra96 | `CAPTURE PASSED`, 2165 and 1711, 0 gaps | `.comms-local/B07-20261018T112604*` |

### Open at the end of Week 9

- Wen Ree's runner was not yet delivered to the team repo (it arrived overnight, W10-2); the bridge was a draft (fork PR #3).
- `python demo.py start` and the board view had not run on hardware; the Ultra96 still ran the service of 10-16, which has no board monitor.
- The gyro fix in Siqiang's source waited for team PR #24.
- Whether Wen Ree's labels match the game's table was not yet checked.
- The phone app's free profile would expire on 2026-10-25.

---

## Week 10 (Monday 19 October to Sunday 25 October 2026)

### One-page summary

**What was done.** Week 10 put every teammate's part on the chain and held the V1 integration. On Monday the board service was redeployed with the board monitor, Wen Ree's eight-class runner (delivered overnight in team PRs #26 and #27) was started on the Ultra96 by Communications' deploy tool, and both gloves were switched to the always-send build the runner needs. The first end-to-end run with the runner lost about a third of the samples and gave no result; the cause was on the BLE side, and it was fixed that night with a send queue on the glove that packs 1 to 6 samples into each notification. Just after midnight on Tuesday the whole chain passed: gloves → laptop → Ultra96 with Wen Ree's runner → game, 333 results written by the board and 333 received by the game. The V1 session that afternoon (13:26 to 14:45, four runs) did not pass the capture check: gloves restarted and disconnected, the phone was switched on and off, and one glove's BLE link was starved for 76 s. The owner's assessment: the game is basically playable with the real AR, but the accuracy and the latency are not good. The Communications code of that day was tagged `comms-v1-20261020` (`d2f9a16`) as the rollback point. On Wednesday Wen Ree's full-CNN runner replaced the Conv1-only runner. On Thursday the gloves were reflashed, Wen Ree's standardized weights were deployed, and the team integration ran four times: three passed (the longest 27 min, every sample acknowledged), and the runner's results reached the board and the game. After it: Wen Ree's firmware pull request (early BLE authentication) was reviewed and merged into the fork, the cause of the starved link was found, and the tools gained options so that teammates can run them with their own NUS accounts.

**Failures and how they were handled.** Two always-send gloves lost a third of the samples (fixed: glove send queue). Receive gaps over 100 ms make the runner drop its window (recorded; three remedies proposed; fixing deferred until after the integration by the owner). One glove's link is sometimes starved while both are connected (cause found; two fixes proposed, not built; on site, restart that glove). The runner's labels did not match the game's table (fixed in Jie Ling's export). `demo.py run` defaulted to 10 Hz, at which the runner never fills a window (fixed: 50 Hz). The runner's files in `/tmp` would be lost on a reboot (fixed: a persistent copy). The deploy tool could not start the runner the way Wen Ree starts it (fixed: `--runner-module`).

**Decisions that affect more than one subsystem.** The gloves send every tick for the runner (reverses Week 9's gating for this use). The game uses the runner's label names. The latency remedies wait until after the integration. The full-CNN runner, then the standardized weights, for the 10-22 integration. Only the Communications bridge runs on the board. The two-player version was looked at and dropped on 10-22; a one-player version in which each hand makes its own gesture is being considered. Teammates use their own jump-host accounts. On 10-23 Wen Ree's new hardware and model plans (three flex sensors per glove, per-hand models) were assessed for Communications; the owner asks Siqiang and Wen Ree only for their delivery dates for now.

**End of the week.** The chain works with all four parts. Open: the 100 ms gaps (latency), the starved link, a phone-count comparison with the full-CNN runner, the three-flex packet change, the new board runner, the gloves not yet on the merged firmware, the phone apps' expired profiles and the certificate (expires 2026-11-13).

### Day by day

| Date | What happened | Evidence |
|---|---|---|
| Mon 10-19, night | 02:50 the owner redeployed the Ultra96 service with the board monitor (from `2b3be2b`). 02:56 and 02:59 the first two `python demo.py start` runs: not passed (W10-1). 03:05 to 03:20 team PR #25 (`demo.py start` and the run logging) merged (`6d164d3`). 03:21 to 04:02 Wen Ree merged team PRs #26 (eight-class model, Ultra96 socket inference) and #27 (an adapter to the Communications model interface). | `deployment-20261018T185037Z.json`; `.comms-local/B07-20261018T185624*`, `T185948*` |
| Mon 10-19, morning | Reading PRs #26 and #27: three things to settle before the runner joins the chain: the labels, continuous glove data, and files in `/tmp`. The owner had messages drafted asking Wen Ree to confirm both points with Siqiang and Jie Ling, and asking Siqiang to review the gyro fix. 08:45 to 09:45 (cloud): the deploy tool cannot start the runner as Wen Ree starts it; `--runner-module` and `--runner-cwd` added (W10-2). | hand-off 14; project library `board-trial/wen-ree-runner-trial.md` |
| Mon 10-19, day | 10:23 Jie Ling's export `SinkTest_V1` and message: the code now says `PICKUP` and `DROP`; pouring is not written yet; grab, drop and chop work. Installed on the owner's iPhone; its scene still stored the old names (W10-4). 17:40 team PR #24 merged. 17:50 Wen Ree's runner started on the Ultra96 by the deploy tool for the first time (W10-2). 17:59 fork PR #3 merged into the fork's `main` (995 tests passed). 18:01 Jie Ling's second export `SinkTest_V1 2`: the scene has `PICKUP`, `DROP` and `POURING`; installed 18:08. | `deployment-20261019T095048Z.json`; `8096c22` |
| Mon 10-19, evening | 18:11 `tools.stage_model_runner` added. 18:15 and 18:53 both gloves flashed with the always-send build; `demo.py run` and `live` now default to 50 Hz (W10-3). 18:25 a code audit of the chain from the model's results to the game's actions finished (W10-3, W10-4). 19:09 to 19:18 the runner staged and redeployed from the copy; `demo.py start` with the game: about 66 % of the samples, no result (W10-5). 19:24 the investigation paused at the owner's request and the issue recorded. 21:40 to 23:40 the cause found and fixed with the glove send queue (`de3bd56`); 8 two-glove captures, a 5-minute and a 20-minute capture passed with no loss. | `.comms-local/checks/2026-10-19-*`; `.comms-local/B07-20261019T111629*`; project library `e2e-check/model-to-game-chain.md` |
| Tue 10-20, night | 00:19 to 00:23 the first passing end-to-end run with the runner and the game: 333 written, 333 received [Owner's report for the game's count]. 00:30 the 100 ms gap issue recorded; the owner: record it now, fix it after the integration (W10-6). 00:40 to 01:10 the fork merged the team main (`7eade4f`) and team PR #28 (the 29 Communications files the team main lacked, including the send queue and the bridge) merged (`f71aa9f`); fork `main` at `d2f9a16`. | `.comms-local/B07-20261019T161928033026Z-caa9e0ff/`; `0811d33` |
| Tue 10-20, day | 12:15 the owner asked about the two bridges sharing one socket path (W10-2). 13:24 the runner redeployed from its persistent Conv1-only copy. 13:26 to 14:45 the V1 session with the team: four runs, none passed (W10-7). 14:53 the owner: "游戏基本上可以玩，就是准确度和延迟不太行" (the game is basically playable; accuracy and latency are not good). Local `main`, the fork's `main` and the board all at `d2f9a16`; tag `comms-v1-20261020` made and pushed to the fork. | `deployment-20261020T052348Z.json`; `.comms-local/B07-20261020T*` |
| Wed 10-21 | 09:23 Wen Ree merged team PR #29 (all CNN layers on the FPGA). 12:58 the owner relayed Wen Ree's request to switch the board to `src.socket_worker_full`; Wen Ree's board test had replaced the FPGA configuration, so the old runner needed a redeploy anyway. 15:07 the owner: Siqiang takes the gloves to flash them, and they are flashed back on 10-22 [Owner's report]. 16:45 the owner: the team decided to use the new version on 10-22. 17:30 to 18:20 the full-CNN runner staged and deployed (W10-9). 21:20 to 22:00 block diagrams of Communications and of Wen Ree's model for the professor's check on 10-22 (project library `comms-diagram/`, `ai-diagram/`). 23:22 to 23:26 Wen Ree merged team PR #30 (standardized eight-gesture model and new weights). | `deployment-20261021T100657Z.json`; `model-runner-stage-20261021T100657Z.json`; `.comms-local/cnn-full-20261020/` |
| Thu 10-22, night | 00:20 to 00:45 preparation: a startup runbook in Chinese and two read-only helpers (`.comms-local/integration-20261022/`), the Communications paths checked equal to the tag, 1031 tests passed; a fresh full-CNN redeploy by the owner; found that `flash.py --glove` builds the gated image (W10-10). | `deployment-20261021T164151Z.json` |
| Thu 10-22, morning | 09:13 to 09:25 both gloves reflashed with the always-send build. 09:32 a block diagram of the whole project. 09:35 to 09:39 Wen Ree's standardized weights uploaded and deployed. 09:47 to 11:07 the team integration: four runs, three passed; deploys at 09:57:40 and 10:02:32 between runs (W10-11). | `.comms-local/B07-20261022T*`; `deployment-20261022T*.json` |
| Thu 10-22, day | 10:53 to 11:21 a kit for teammates to run the Communications tools with their own accounts (W10-12). 11:20 to 11:25 a two-player (four-glove) feasibility check (W10-14). 14:47 Wen Ree merged team PR #31 into the team main: early BLE authentication in the Communications firmware (W10-13). 14:54 the owner: no two-player mode; one player whose two hands can make different gestures (W10-14). 15:07 the documents updated for the integration (`db60ca5`). 22:00 to 22:17 team PR #31 reviewed (safe to merge); three small Communications fixes prepared (W10-12). | project library `two-player/`, `one-player-two-hands/`; `.comms-local/teammate-kit/` |
| Fri 10-23 | 01:31 to 02:23 the cause of the starved link found in the data of 10-20 and recorded (W10-8; `f9da7fb`). 14:59 the owner relayed Wen Ree's update on hardware and model plans (W10-14). 15:10 Wen Ree merged team PR #32 (an independent-hand pipeline on the laptop). 15:17 to 15:51 the Communications impact and to-do list written; the owner's decisions on what to ask and what to record (W10-14, W10-15). 15:40 the small fixes committed (`d69891f`); 15:48 the team main up to `6449882` (team PR #31) merged into the fork (`1705dfb`; 1046 tests passed, all six firmware environments built); 16:00 documents (`2c2a2d1`); 16:35 pushed to the fork. | `.comms-local/checks/2026-10-23-pr31-merge/`; project library `ble-link-starvation/`, `comms-todo/` |
| Sat 10-24 | No Communications activity recorded. | — |
| Sun 10-25 | 13:25:57 the phone apps' free signing profiles expired; not renewed, by the owner's decision of 10-23 (W10-15). 19:28 confirmed that the fork's `main` is `2c2a2d1` and nothing is left to push. 20:00 Siqiang asked the team to keep an integration journal from Week 9; Wen Ree reminded the team of the individual weekly reports and proposed the usual Tuesday 1 pm meeting [as relayed by the owner]. This journal was started. Later the owner confirmed that the team sessions used Jie Ling's iPhone (W10-15). | project chat |

### Issues, investigations and changes

#### W10-1. The first `demo.py start` runs on the real Ultra96 did not pass

- **What happened.** 10-19 02:56: the run scanned the addresses in `.comms-local/boards.json`, which still named the owner's test boards, and found no glove. 02:59: both gloves connected and the board view worked, but the left glove restarted at 03:00:51 (a new boot id after a 23.9 s silence), so its counters could not be reconciled, and the right glove lost 14 samples in one burst (sequence numbers 168 to 181).
- **Investigation.** The run folders; the board wrote all 1820 results it made to the phone.
- **Change.** `boards.json` set to the gloves (the old map kept as `boards-test-boards-20261014.json`); the live view now names the address it scanned when a glove is not found and explains an empty `BLE attempt failed:`; a launcher test no longer depends on this machine's `boards.json`.
- **Retest.** Later runs found the gloves without typed addresses.
- **Status.** The board map is solved. Why the left glove restarted was not investigated [Not confirmed: power or battery are possible, and they are Siqiang's].

#### W10-2. Running Wen Ree's runner from Communications' deploy tool

- **What happened.** Wen Ree starts the runner as `cd /tmp/cnn_conv1d/ai_integration && sudo -E <PYNQ python> -m src.socket_worker --weights … --bit …`. The deploy tool's `--runner` ran `python <script>` from the script's own folder, which cannot import `src.*` or find the relative weights path. The runner's files lay in `/tmp`, which the board clears on a reboot.
- **Changes.** (1) `--runner-module` and `--runner-cwd` (10-19 morning, D42 extended): the launcher runs `python -m <module>` in the given folder and refuses a missing folder or module before it touches the previous runner. (2) `tools.stage_model_runner` (18:11): copies the runner folder out of `/tmp` into `BOARD_ROOT/model-runner/cnn_conv1d` with hash checks and prints the deploy command for the copy.
- **Retest.** 10-19 17:50 the first start on the board: the runner ran as root, its log began `Loaded bitstream` and `Inference: FPGA Conv1; remaining layers on Ultra96 CPU`, so `sudo -S` with a typed password and PYNQ's environment through root's login shell both work. 19:09 the staged copy (25 files) deployed and connected.
- **A second bridge on the same socket.** Wen Ree's team PR #27 added `src/comms_adapter.py`, which uses the same socket path as `ultra96/model_bridge.py`. The Communications bridge leaves its socket file behind when it stops, and the adapter refuses to start while that file exists. The board has only ever run the Communications bridge, so this has had no effect; the owner confirms with Wen Ree that it stays that way [Not confirmed with Wen Ree yet].
- **Status.** Done.

#### W10-3. What the runner needs from the gloves and the laptop

- **What happened.** The runner builds a 2 s window of 50 points from both gloves, needs a sample within 35 ms of each point, and clears both gloves' history after a receive gap over 100 ms (team main `src/socket_worker.py:31`, `:44`, `:46`). Week 9's gated gloves send nothing while still, and `demo.py run` and `live` defaulted to 10 Hz (100 ms between samples).
- **Investigation.** A code audit of the whole chain from the runner's results to the game's actions (10-19, project library `e2e-check/model-to-game-chain.md`) fed Wen Ree's window code with simulated arrival times: 47 of 47 windows at 50 Hz, 0 of 47 at 10 Hz, and 0 of 47 when packets arrive in bunches 80 ms apart. It also checked every hop (the hello line, the result fields, the label rule, `result_id`, the units, the FPGA input range) and found them consistent.
- **Changes.** Both gloves flashed with the always-send build (`-DCOMMS_GLOVE_SEND_ALL=1`; the owner approved: "是", then "刷"): left 18:15, 2941 = 2941 = 2941 with the glove lying still; right 18:53, 3010 = 3010 = 3010. `demo.py run` and `live` default to 50 Hz (`0e403ac`; `--rate 10` keeps the old baseline).
- **Found for Jie Ling (not Communications' code).** The game's repeat cooldown defaulted to 0, so one chop gesture, which appears in several consecutive 0.2 s windows, could chop several times; and an `IDLE` result reset the cooldown's last label before the mapping check. Drafts for Jie Ling were written [Not confirmed whether they were sent or acted on].
- **Status.** Done for Communications.

#### W10-4. The runner's labels did not match the game's table

- **What happened.** The runner emits `PICKUP`, `DROP`, `CHOP`, `WASH`, `THROW`, `FIREEXT`, `POURING` and `IDLE`; the game's table expected `PICKUPHOLD`, `PLACEDOWN` and `POUR`, and the game ignores unknown labels.
- **Options considered.** Rename in the model, rename in the game, or translate in the Communications bridge (offered by the agent). The owner left it to the two owners: messages were drafted asking Wen Ree to confirm the label set with Jie Ling.
- **What changed (Jie Ling's side).** Jie Ling's first export (10-19 10:23) changed the code but not the table serialized in the Menu scene, which the game actually reads (found by unpacking the export on the Mac). The second export (`SinkTest_V1 2`, 18:01) had `PICKUP`, `DROP` and `POURING` in the scene and kept the dummy labels for testing. Communications passes labels unchanged (it checks only their characters), so no Communications code changed.
- **Status.** Solved in the export installed on the owner's iPhone on 10-19, which ran the owner's own tests. The team sessions of 10-20 and 10-22 ran the game on Jie Ling's iPhone with Jie Ling's own build [Owner's report, 2026-10-25]; Communications did not check that build's label table, and the team main's `vis/` code still listed the old names on 10-23 (hand-off 2.3), so whether `PICKUP`, `DROP` and `POURING` triggered actions in those sessions is [Not confirmed].

#### W10-5. Two always-send gloves lost about a third of their samples

- **What happened.** 10-19 19:16, the first end-to-end run with the runner and the game: left 1850 and right 1896 samples in 55 s, about 66 % of the expected count, in bursts of about 16 samples about once a second; the runner never had a full window, so 0 results, and the game's `Received` stayed 0 [Owner's report].
- **Investigation.** The loss also happened without the VPN, SSH and the Ultra96 (against a service on the laptop): two of three captures failed, so it was on the BLE side and intermittent. Each glove alone passed at 50 Hz, and two gated gloves had passed on 10-18. The cause, checked against the ESP-IDF 4.4.7 source and every capture: with both gloves connected, the laptop's Intel controller often served each glove's link only every second 15 ms connection event, about 33 notifications a second, while the firmware sent one notification per sample (50 a second); the BLE stack's queue on the glove filled, the send call failed, and each refused sample used up its sequence number. A glove's own counters confirmed it (`failures=999`, exactly the 999 gaps of a failing run).
- **Options considered.** A lower rate (30 Hz passed, below the 33 per second limit, and the runner's window would accept it); moving the gloves or switching off the laptop's Wi-Fi; or sending several samples per notification.
- **Change.** A send queue on the glove (`firmware/esp32/include/comms_send_queue.h`): 32 samples; up to 6 per notification; at most 2 notifications in flight; the sequence number taken only when the stack accepts the notification; a full queue drops its oldest sample as a counted failure. The firmware also asks for 251-byte link-layer packets, gives the serial port a larger transmit buffer (the once-a-second report had blocked the send loop for about 30 ms), and refuses to build on an ESP-IDF other than 4.4. The laptop splits each notification into its packets (`common/sensor.py`, `laptop/bridge.py`). A review by four reviewers found five minor issues; three were taken. 1028 tests passed.
- **Retest.** 8 two-glove captures of 45 s, one of 5 min and one of 20 min (60,032 and 60,007 samples) passed with no loss. Then end to end through the VPN, the Ultra96 with the runner and the game (10-20 00:19, 180 s): `CAPTURE PASSED`, 9033 and 9008 samples with none missing, 333 results (all eight labels) written to the phone, and the game's `Received` rose by exactly 333 [Owner's report].
- **Status.** Solved; in the team main through team PR #28.

#### W10-6. Receive gaps over 100 ms make the runner drop its window

- **What happened.** After the fix no sample is lost and each glove's clock steps 20 ms, but the laptop's controller now and then skips several of a glove's link slots, and the waiting samples then arrive together. Measured at the laptop: one gap of 105.6 ms in the 20-minute local capture (97 over 70 ms), and one of 120.5 ms in the 3-minute end-to-end run through the VPN, where Wi-Fi on the same chip also carries the tunnel.
- **Why it matters.** The runner times samples by its own receive time; each gap over 100 ms clears both gloves' history, which means about 2 s without results. Players feel it as a gesture that sometimes gets no response.
- **Options considered [Proposal, none built].** (1) A playout stage in `ultra96/model_bridge.py` that hands each sample to the runner at its glove-clock spacing after a fixed delay of about 120 to 150 ms (costs that much latency; changes the receive times the runner sees, so Wen Ree must agree). (2) Wen Ree widens the 100 ms limit to about 300 ms (one number in the runner). (3) Wen Ree times samples by the gloves' `uptime_ms` instead of receive time.
- **Decision.** The owner, 10-19 night: record the issue first and fix it after the integration. On 10-23 option (2) was suggested as the cheapest, since Wen Ree is writing a new board runner anyway [Proposal; not yet raised with Wen Ree, Not confirmed].
- **Status.** Open.

#### W10-7. The V1 session of Tuesday 10-20 did not pass the capture check

- **Set-up.** 13:24 the runner redeployed from its persistent Conv1-only copy; both gloves on the always-send build with the send queue; the owner at the laptop with the team; the game on Jie Ling's iPhone [Owner's report, 2026-10-25]. The numbers below are from the run folders (no agent watched the runs).
- **What happened.**
  1. 13:26, 40 min: 116,591 (left) and 115,901 (right) samples received, 0 dropped on the laptop; 5 and 7 disconnects, each with a new boot id (the gloves restarted), silences up to 22.4 s, and 567 and 13 sequence gaps, so the final counters could not be reconciled; 1273 and 1368 results; at least 1886 written to the phone and 755 not (4 new phone subscriptions).
  2. 14:11, 560 s: 28,160 and 27,592 received and acknowledged, 361 and 385 results, none written to the phone (not subscribed at the start or the end).
  3. 14:33: stopped during start-up.
  4. 14:34, 564 s: left 28,233 with none missing; right 27,201, 2 disconnects and new boots; 462 and 403 results, at least 598 written and 267 not.
- **Investigation (that afternoon, by the owner's request).** The owner said the phone and the gloves had been switched on and off several times during run 1 [Owner's report]. Reading run 1: while every device was connected, delivery was complete; the results not written fell in the times the phone was off; the left glove lost about a fifth of its samples for 76 s (13:41:15 to 13:42:31) after a failed Windows reconnect. The analysis also put most of the slowness on the runner's 2 s window and its resets, and estimated the Communications part at about 0.1 to 0.3 s [an agent's estimate from run 1; not re-checked here; end-to-end latency has not been measured].
- **The owner's assessment (14:53).** The game is basically playable with the real AR; the accuracy and the latency are not good [Owner's report].
- **Change.** No code change. The Communications code of that day was checked identical in local `main`, the fork and on the board (`d2f9a16`; the team main differed only by Wen Ree's data and report commit `4b4e092`) and tagged `comms-v1-20261020` as the rollback point (pushed to the fork, not the team repo).
- **Status.** The 76 s loss was explained on 10-23 (W10-8); the latency is W10-6; the glove restarts are open.

#### W10-8. One glove's BLE link is sometimes starved while both are connected

- **What happened.** In run 1 of 10-20 the left glove lost 567 samples in 76 s and the model gave no result; from 13:59:06 to 13:59:13 the right glove lost 13.
- **Investigation (10-23 night, from `packets.jsonl` and `run.log` of that run).** A glove alone gets about 50 notifications a second of 1 sample each; both gloves normally about 30 each of about 1.7 samples; the starved glove got about 7 a second, every one full (6 samples). Its connection interval was still 15 ms, so the connection parameters were not the cause. When the right glove disconnected at 13:42:31 the left glove went straight back to normal, and after the right glove reconnected both were normal for the next 8 minutes. The right glove's own episode had no failed reconnect before it, so the reconnect failure seen first was a coincidence. Mechanism [Inferred; no air capture was made]: both links use the same 15 ms interval, and when their anchor points collide the laptop's single controller keeps favouring one link until a link is rebuilt. Why samples are lost: 7 notifications of 6 samples carry 42 samples a second, below the 50 a glove makes, so the 32-sample queue overflows.
- **Options considered [Proposal, neither built].** (1) A watchdog in `laptop/bridge.py`: when a glove's notifications have all been full for about 2 s and its sequence numbers have gaps, disconnect and reconnect that glove (no flashing; costs about 6 to 8 s of that glove). (2) Up to 12 samples per notification in the firmware, so a link served 7 times a second still carries 84 samples (needs measuring on hardware, reflashing both gloves, and telling Wen Ree first, because team PR #31 touched the same firmware). The two can be combined.
- **Workaround on site.** Restart the glove that loses samples.
- **Status.** Open. Not seen in the four runs of 10-22. Team PR #31 does not fix it (it changes only the authentication order on a reconnect). Continued in Week 11: not reproduced on 10-28 with two version-4 boards (W11-5); option (1), the laptop watchdog, built that night (W11-6).

#### W10-9. Switching the board to Wen Ree's full-CNN runner

- **What happened.** 10-21, Wen Ree's request: all network layers now run on the FPGA (24 of 24 board predictions matched software); switch the startup to `src.socket_worker_full` with the new bitstream; the socket format and the eight labels are unchanged. Wen Ree's board test had replaced the FPGA configuration, so even the old runner needed a redeploy.
- **Options considered.** Keep the Conv1-only runner for 10-22 (it had passed end to end; the owner had no gloves on 10-21 to test the new one), or switch. The owner first leaned to the old runner ("明天联调不需要准确性，证明能跑通就行": the integration needs only to show the chain works); at 16:45 the owner said the team had decided to use the new version.
- **Investigation.** The Communications code needed no change: the bridge and the deploy tool run the new runner with a different command (checked by a dry run and a simulated run). `tools.stage_model_runner` could not stage it, because its file list was the Conv1-only folder's, and the old `--control-address` argument must not be passed (the new IP has a different address).
- **Change.** A local, untracked helper (`.comms-local/cnn-full-20261020/stage_and_deploy.py`) staged the seven files the runner needs from the team main `41a9146` with `git archive` (not from `/tmp`), checked all seven hashes on the board, kept the Conv1-only copy as the fallback, and deployed. On 10-22 `tools.stage_model_runner --runner full` was added for the next time (W10-12).
- **Retest.** 18:06 deployed; the runner log showed `Loaded FULL CNN bitstream`. No glove data until 10-22.
- **Status.** Done.

#### W10-10. `flash.py --glove` builds the gated image

- **What happened.** 10-22 00:20, while checking the talking points for the professor: `python flash.py --glove` builds the gated image, because the `-glove` environments do not set `COMMS_GLOVE_SEND_ALL`; the always-send build that the runner needs takes `PLATFORMIO_BUILD_FLAGS=-DCOMMS_GLOVE_SEND_ALL=1` set in the same shell.
- **Change.** The step written into the runbook for that morning and into detail chapter 06 (workflow G); the 09:13 reflash used it (`gated=0` on the serial port). Team PR #31 later made the `-glove` environments always-send by default; a gated build now takes `-DCOMMS_GLOVE_SEND_ALL=0`.
- **Status.** Solved.

#### W10-11. The team integration of Thursday 10-22

- **Set-up.** Both gloves reflashed with the always-send build (left 2954 = 2954 = 2954, right 2980 = 2980 = 2980). 09:38 Wen Ree's standardized weights (team main `722fba2`) uploaded with a hash check and deployed with the full-CNN runner. The owner ran the four runs with the team; the game ran on Jie Ling's iPhone [Owner's report, 2026-10-25]; the numbers are from the run folders.
- **What happened.**
  1. 09:47, 540 s: not passed. 26,839 and 26,787 samples received and acknowledged, 157 results per glove; at the end both gloves had a BLE error and a disconnect within 3 s of each other (09:56:54 and 09:56:57), and afterwards neither advertised.
  2. 09:59, 134 s: `CAPTURE PASSED`, 6720 and 6726, 41 and 50 results, all 91 written to the phone (the phone was not subscribed at the end).
  3. 10:14, 1647 s (27 min, the longest run so far through the Ultra96): `CAPTURE PASSED`, 82,360 and 82,345 with none missing, 276 and 304 results.
  4. 10:59, 431 s: `CAPTURE PASSED`, 21,545 and 21,614, 102 and 88 results.

  All eight labels were seen; no result was refused; no sequence gap occurred in any run (so no starved link).
- **Deploys between the runs (corrected on 2026-10-25).** At 09:57:40 the service and runner were redeployed with the older `20261018_v2` weights (record `deployment-20261022T015740Z.json`: service PID 165847, runner PID 165854), so run 2 ran against the v2 weights. At 10:02:32 the owner deployed the standardized weights again (`deployment-20261022T020232Z.json`: runner PID 165934), which served runs 3 and 4. The hand-off document had called the 09:57 deploy an unrecorded restart; the record shows it was a deploy with the v2 weights. Who chose the weights for each run is [Not confirmed].
- **Investigation.** Run 1's data before the end was clean (longest silence 0.19 s) and the gloves stopped advertising afterwards, which looks like both gloves losing power or restarting, not a Communications fault [Inferred]. The phone's subscription changed in every run (1 to 3 new subscriptions; not subscribed at the end of runs 2 to 4), so between 0 and 183 results per run were made while no phone was subscribed, and the phone-count comparison of D39 could not be made. The owner said the phone (Jie Ling's iPhone) had been switched off during the runs [Owner's report]; no Communications fault was found behind it.
- **Status.** Done, by the owner's report ("我们现在已经做完联调了"). Still to do: one run with the phone subscribed from start to end to compare the phone's count with the board's for the full-CNN runner.

#### W10-12. Teammates running the Communications tools

- **What happened.** 10-22: Wen Ree wanted to run `python demo.py start` and watch real glove data go into the model and the results come back. The jump host takes each person's own NUS account; the board uses the shared `xilinx` account; some commands and helpers had the owner's account built in.
- **Change.** A teammate kit (`.comms-local/teammate-kit/`: the public CA certificate, the two host keys, the glove addresses, and an English guide, `GUIDE.md`, also in the project library) with every command, the packages to install and where each file goes; the private keys are never shared. Three small fixes (prepared 10-22 evening, committed on 10-23 as `d69891f`): `requirements-dev.txt` lists `bleak==3.0.1`; the jump account defaults to `LTC_JUMP_USER` (else the owner's) in `demo.py tunnel`, `start` and `service` (`--jump`), `tools.deploy_service --jump-user` and `tools.stage_model_runner --jump-user`; `tools.stage_model_runner --runner full` stages the full-CNN runner from a commit with hash checks.
- **Retest.** Unit tests only; the full-CNN staging upload has not run against the real board.
- **Status.** Done. On 10-23 Wen Ree had set up from the guide [Owner's report]. Whether a glove keeps bonds with two laptops is untested.

#### W10-13. Wen Ree's pull request changed the Communications firmware

- **What happened.** 10-22 14:47, Wen Ree merged team PR #31 into the team main. It changes Communications-owned firmware files: an authentication event that arrives before the connect callback is now kept (early BLE authentication, new `comms_early_auth.h`); both `-glove` environments become always-send; the platform is pinned to `espressif32@6.12.0`.
- **Investigation.** Reviewed at the owner's request on 10-22 evening: no bug found, safe to merge; the laptop needs no change; the pinned platform uses the same core and compiler as before.
- **Change.** Merged into the fork's `main` on 10-23 (`1705dfb`, the `.gitignore` conflict resolved by keeping both sides; `2c2a2d1` for the documents).
- **Retest.** 1046 tests passed before and after; `tools.sync_glove_module --check` exit 0; all six firmware environments built (evidence `.comms-local/checks/2026-10-23-pr31-merge/`).
- **Status.** Merged. The gloves do not run it yet; it takes effect at the next reflash.
- **Not merged: team PR #32** (Wen Ree, 10-23): an independent-hand pipeline on the laptop (`src/hand_ai/`, a seven-label right-hand model on 11 channels). It connects to the gloves itself with `bleak` and imports Communications modules (`common.sensor`, `common.control`, `laptop.controls`, `laptop.source_audit`), and it adds `tests/test_hand_ai.py` and `tests/test_hand_ai_gui.py` to the Communications-owned `tests/` folder. Because it connects to the gloves directly, it presumably cannot run at the same time as `demo.py start` [Inferred, not tested].

#### W10-14. Changes of scope: two players, two hands, three flex sensors

- **Two players, four gloves (10-22 morning).** The owner asked whether the laptop and the design could take four gloves. Assessment (project library `two-player/four-glove-feasibility.md`): the architecture needs no change (one channel per glove); the laptop probably has about twice the BLE capacity needed but must be tested; `device_id` 1 and 2 are built into about 15 places; the bigger risk is the runner, which would reset more often with four links. **Dropped the same day** by the owner (14:54).
- **One player, each hand its own gesture (10-22 afternoon).** Assessment (project library `one-player-two-hands/two-hands-different-gestures.md`): Communications already carries each result's `device_id` (1 = left glove, 2 = right glove) to the game, so it needs no change; the work is a one-hand model with per-hand windows (Wen Ree) and per-hand actions and held items in the game (Jie Ling). The owner decided not to send drafts: the teammates explore it themselves.
- **Wen Ree's update (10-23, relayed by the owner).** Hardware: one IMU on the palm and three flex sensors (thumb, index, middle) per glove. AI: separate left and right models, so two hands can act at once; `FIREEXT` removed for now; some actions such as washing may need both hands. Pending: multiplayer may still be possible; Wen Ree prefers an Android phone; a new bitstream and `.hwh` will likely come, because both the hardware and the model changed. Also proposed by Wen Ree: accept an action only after three consecutive predictions at confidence 0.70 or more; emit `PICKUP`, `DROP` and `THROW` once per action; treat `CHOP`, `WASH` and `POURING` as ongoing states; keep the two hands independent.
- **Communications impact [Inferred, nothing built].** A third flex sensor means 12 values per glove, so the packet changes (about 40 bytes instead of 38), and the firmware, the laptop, the board and the tests change on the same day as the gloves. Per-hand models need no Communications change. By reading team PR #32, the post-processing goes into Wen Ree's runner, and ongoing actions are repeated labels every 0.2 s, which the current result format already carries. An Android phone would need a new phone client [not decided].
- **Settled in the owner's discussion of 10-23.** The packet format is Communications' to define, so only its content needs asking: Siqiang, when the three-flex code will be pushed and whether the third flex reads 0 to 1 like the others; Wen Ree, the order of the 12 values and when the new board runner is ready (whether these questions have been sent is [Not confirmed]). The owner chose not to start a 12-value branch yet, and that plans not yet decided stay out of the hand-off document until code changes; this journal records them as plans.
- **Status.** Open; waits for Siqiang's and Wen Ree's code.

#### W10-15. The phone apps' signing profiles

- **What happened.** The free Personal Team profile of the Communications test app and of the game on the owner's iPhone expired on 2026-10-25 13:25:57.
- **Decision (owner, 10-23).** Re-sign only when the owner next tests with the owner's own iPhone; integration normally uses Jie Ling's iPhone, and Jie Ling can build the game on Jie Ling's own Mac (a guide was written on 10-20). The build script copies the connection setup from the Communications test app on that phone, so that app must stay installed even after it expires.
- **Which phone ran which session (the owner, 2026-10-25).** Every team integration session (10-20, 10-22) ran the game on Jie Ling's iPhone; the owner's iPhone is used only for the owner's own tests (in this journal: 10-16 to 10-18, the run of 10-19 at 19:16 and the run of 10-20 at 00:19). The hand-off document had said the owner's iPhone for the team sessions and was corrected the same evening.
- **What it changes.** For Communications' delivery checks, nothing: the samples are counted on the laptop and the board, and the board counts the results it writes to whichever phone is subscribed. It does matter for two things: the expired profiles on the owner's iPhone do not affect team sessions; and in team sessions the game build, its label table and the phone count (D39) are on Jie Ling's iPhone, so a phone-count comparison needs Jie Ling's `Received` count read before and after a run.
- **Status.** Not renewed, by decision.

### Decisions that affect more than one subsystem (Week 10)

| Date | Decision | Who | Affects |
|---|---|---|---|
| 10-19 | Both gloves send every tick (always-send build) for the runner; reverses Week 9's gating for this use. | Owner (flashing approved), Siqiang and Wen Ree asked to confirm | Siqiang, Wen Ree |
| 10-19 | The game uses the runner's label names (`PICKUP`, `DROP`, `POURING`); Communications passes labels unchanged. | Jie Ling and Wen Ree, at the owner's request | Wen Ree, Jie Ling |
| 10-19/20 | The remedies for the 100 ms gaps wait until after the integration. | Owner | Wen Ree |
| 10-20 | Rollback point: tag `comms-v1-20261020` on `d2f9a16`. | Owner | All |
| 10-21 | The full-CNN runner for the 10-22 integration; on 10-22 the standardized weights. | Team (owner's report); who chose the weights is not recorded | Wen Ree |
| 10-20/23 | Only the Communications bridge runs on the board, not Wen Ree's adapter (current practice; to be confirmed with Wen Ree). | Owner | Wen Ree |
| 10-22 | Two-player version dropped; one-player, two-hands version considered; teammates explore their parts themselves. | Owner | Wen Ree, Jie Ling |
| 10-22 | Teammates run the Communications tools with their own jump-host accounts. | Owner | All |
| 10-23 | Wen Ree's firmware change (team PR #31) accepted into the fork. | Owner | Wen Ree |
| 10-23 | Ask Siqiang and Wen Ree only about the three-flex code (date, range, order) and the new runner's date; no 12-value branch yet; plans stay out of the hand-off document until code changes. | Owner, in discussion | Siqiang, Wen Ree |
| 10-23 | The phone apps are re-signed only when the owner tests with the owner's own iPhone. | Owner | Jie Ling |

### Tests on hardware (Week 10)

| When | Run | Result | Evidence |
|---|---|---|---|
| 10-19 02:59 | `demo.py start`, both gloves (gated), real Ultra96 | Not passed: left glove restart, 14 lost on the right | `.comms-local/B07-20261018T185948*` |
| 10-19 18:15, 18:53 | Each glove alone, always-send | 2941 and 3010, no loss | `.comms-local/checks/2026-10-19-*-glove-send-all/` |
| 10-19 19:16 | End to end with the runner, before the fix | About 66 % of samples, 0 results | `.comms-local/B07-20261019T111629*` |
| 10-19 22:40 to 23:30 | Two gloves with the send queue, local service | 8 × 45 s, 5 min, 20 min: all passed, no loss | `.comms-local/checks/2026-10-19-two-glove-ble/` |
| 10-20 00:19 | End to end with the runner and the game | Passed; 333 written = 333 received [Owner's report] | `.comms-local/B07-20261019T161928033026Z-caa9e0ff/` |
| 10-20 13:26 to 14:45 | V1 session, four runs | None passed (W10-7) | `.comms-local/B07-20261020T*` |
| 10-22 09:13 to 09:25 | Each glove after the reflash | 2954 and 2980, no loss | hand-off 6.1 |
| 10-22 09:47 to 11:07 | Team integration, four runs | Three passed; the longest 27 min (W10-11) | `.comms-local/B07-20261022T*` |

### Open at the end of Week 10 (carried into Week 11)

1. **Latency:** receive gaps over 100 ms reset the runner's window (W10-6). Raise option (2) or (3) with Wen Ree for the new board runner, or build the playout stage.
2. **Starved link** (W10-8): not fixed; on site, restart the affected glove. The watchdog needs no flashing.
3. **Phone count with the full-CNN runner** (D39): one run with the phone subscribed from start to end.
4. **Gloves on the merged firmware** (team PR #31): reflash both; check `gated=0`.
5. **Three flex sensors** (W10-14): the packet change waits for Siqiang's code and Wen Ree's channel order; every component switches on the same day.
6. **New board runner and bitstream from Wen Ree:** stage with a new entry or `--runner full`, then redeploy.
7. **Glove restarts and disconnects** (10-19, 10-20, 10-22 run 1): cause unknown [Not confirmed: battery, power or wiring are Siqiang's].
8. **Certificate:** the server certificate expires on 2026-11-13 14:27:35 UTC; renew in early November.
9. **Phone apps:** profiles expired on 10-25; re-sign before the owner's next test with the owner's own iPhone.
10. **Team PR #32** is not in the fork (it adds teammate tests under `tests/`).

### Figures for the team journal

Pictures are allowed in the team journal. Made in Week 10 and kept in the project library (not re-checked against the code for this journal):

- `comms-diagram/comms-block-diagram-v2.png`: the Communications block diagram prepared for the professor's check on 10-22.
- `project-diagram/project-block-diagram.png`: the whole project, one colour per subsystem.
- `ai-diagram/ai-block-diagram.png`: Wen Ree's model and FPGA diagram (Wen Ree's part).

No screenshot of the `demo.py start` live view was kept; the same information is in each run's `run.log`.

---

## Week 11 (Monday 26 October to Sunday 1 November 2026)

### One-page summary

To be written when the week ends. Up to Tuesday 10-27: Wen Ree delivered the three-flex sensor version 4 (40-byte packets, 12 values), an independent-hand model runtime (one model per hand, seven labels) and a board-tested FPGA overlay for it (team pull requests #33 to #36), and handed Communications a summary of what to integrate. Communications merged it into the fork, tested it, and built and tested on the laptop the launch options for version 4, the hand12 runner that feeds the per-hand results to the game through the existing result path, and its staging for the board, for the integration planned for Thursday 10-29. On Wednesday 10-28, after midnight: version 4 streamed over BLE with no loss on two test boards, and the starved link of W10-8 did not appear; at the owner's request the laptop got a watchdog that reconnects a starved link, and the per-hand delivery moved into Wen Ree's own worker (he agreed to that edit), replacing Communications' adapter; then the whole chain ran on the laptop with both boards, every result reaching the subscriber. Before dawn the owner typed the logins: Wen Ree's worker was deployed on the Ultra96 with the version-4 service, and both test boards ran through the board with every sample accepted and every result the worker sent recorded by the service. Not yet with the phone (its certificate needs renewing), trained bundles, the gloves or the game.

### Day by day

| Date | What happened | Evidence |
|---|---|---|
| Mon 10-26 | 19:07 Wen Ree merged team PR #33 (opt-in three-flex firmware support in Communications firmware files, a three-flex recording pipeline, a triage capture and its findings). No Communications work. | team main `4b8c2bf`; `docs/TRIAGE_FINDINGS_20261026.md` |
| Tue 10-27 | 01:14 team PR #34 (Wen Ree's fixed-point precision sweep). 16:03 team PR #35 (the independent-hand runtime, the hand-event reference contract, the opt-in v4 transport in Communications laptop and Ultra96 files, the board-verified `cnn_hand12_v1` overlay); 16:39 team PR #36 (recording collection planner). By Wen Ree's record the board ran his synthetic hand12 test that day and he then restored the paired runner by hand (W11-3). Wen Ree's handover zip reached the owner on Telegram (W11-1). Evening, by an agent at the owner's request: 20:33 the pending journal work committed (`a369042`); 20:34 the team main merged into the fork (`97db189`; W11-1); the left test board flashed with the dummy three-flex build (W11-5); 21:38 the Communications code committed (`c66a100`; W11-2 to W11-4); the BLE measurement deferred, the laptop's Bluetooth being off (W11-5); documents. | `97db189`, `c66a100`; `.comms-local/checks/2026-10-27-hand12-merge/` |
| Wed 10-28 | From 23:40 on 10-27 to 00:19 the version-4 BLE measurement on both test boards, the right board reflashed with the three-flex build at about 00:00 when the owner moved the cable (W11-5). After midnight the owner asked for the laptop watchdog for the starved link (W11-6) and changed the hand12 runner plan: Wen Ree's worker delivers, the adapter goes (W11-7); both built by agents in separate worktrees, each reviewed twice and fixed (00:39 to 01:11), cherry-picked onto local `main` (`b7f4b13`, `8bd6b1f`, `e79963c`, `abc71ab`; full suite 1554 passed, 16 skipped). The owner allowed downloads; numpy 2.2.6 installed into WSL's Python. 01:17 to 01:23 the overall run on the laptop with both boards (W11-8); documents (`00d859e`). 04:36 to 05:44, at the owner's request, the owner typing every password: the board checked, the hand12 worker staged and deployed with the version-4 service (05:06), redeployed at threshold 0 (05:14), a read-only overnight SSH session opened (05:19), both test boards run through the Ultra96 for 120 s and 600 s (W11-9); the phone not subscribed (its certificate, by the owner's report); documents (`03e5046`). Morning: local `main` pushed to the fork; the code merged into the team main through team PR #37 (`521c7e5`) and back into the fork (`9ace0b2`; W11-10). | `.comms-local/checks/2026-10-27-v4-ble-gap/`, `.comms-local/checks/2026-10-28-overall/`, `.comms-local/checks/2026-10-28-ultra96/`; `deployment-20261027T204020Z.json`, `deployment-20261027T211405Z.json` |

### Issues, investigations and changes

#### W11-1. Merging Wen Ree's three-flex and independent-hand work

- **What happened.** Wen Ree's team pull requests #33 to #36 (team main `5e3f78e`) changed Communications files: the firmware (`-DCOMMS_FLEX3_GLOVE=1`, two `-glove-flex3` environments), `common/control.py`, `laptop/bridge.py`, `laptop/source_audit.py`, `laptop/controls.py`, `laptop/goodput.py`, `ultra96/protocol.py`, `ultra96/model.py`, `ultra96/model_bridge.py` and `ultra96/server.py` (all opt-in, default version 3), and added files of his own in Communications folders (`common/sensor_v4.py`, `common/hand_contract.py`, `ultra96/hand_admission.py`, `tools/hand_*.py`, `tools/precision_*.py`, 18 test files, documents in `docs/`). His handover zip (`ai-comms-handover-20261027.zip`) held navigation notes, an AI prompt and three of his documents; the three documents equal the repository's byte for byte (git blob hashes compared). The prompt asks Communications to build a structured `HAND_EVENT` path through the bridge, the service and the phone.
- **Investigation.** The merge had two conflicts, both additive (`.gitignore`, `.gitattributes`), resolved by keeping both sides. On the merged tree: 1319 passed, 16 skipped, 1 failed. The failure is Wen Ree's `tests/test_hand_ai_lab.py` timeline test: it reads a UTF-8 file with `read_text()`, so with the laptop's GBK locale codec (`UnicodeDecodeError: 'gbk' codec can't decode byte 0x94`); it passes with `PYTHONUTF8=1`. His handover checks passed: `test_hand_v4_transport.py` (11), `test_hand_contract.py` (28), `tools.hand_v4_transport_check` (real TLS loopback, both versions) and `tools.hand_contract_demo`.
- **Options considered.** For delivering his events: his structured `HAND_EVENT` (new message type, format-2 hello, event IDs and leases through the bridge, the service and both phone apps), or a compat mode on the existing result path. **The owner chose the compat mode** for Thursday (task list of 10-27): one `v` 3 result per pulse, state start, state refresh or idle, `device_id` = the hand, no state end.
- **Change.** Merge commit `97db189` (after `a369042`). Wen Ree's files in Communications folders are recorded in the hand-off document as his (12.2, 12.3, 12.5).
- **Status.** Merged locally; pushed to the fork on 10-28 (W11-10). For Wen Ree: the locale bug in his test [not sent].

#### W11-2. Sensor version 4 through the Communications launch path

- **What happened.** Wen Ree's transport switches codec only where `sensor_version=4` is passed; `demo.py`, `laptop.dual_bridge`, `tools.check_board`, the deploy tool and the evidence tools did not pass it (his `docs/HAND_V4_TRANSPORT.md` says so). With version 4 the service also wrote results at `v` 4, which both phone apps refuse.
- **Change** (`c66a100`). `--sensor-version 4` in `demo.py start|run|live`, `laptop.dual_bridge`, `tools.check_board` (also `--address` and a `SEQUENCE` line with the gaps), `tools.deploy_service` (and `demo.py service --start`, which restarts a deployment with its own version); the packet check, the CSV export and the live view read version 4; `flash.py --flex3` and new dummy `firebeetle32-left-flex3`/`right-flex3` environments for bare boards; results stay at `v` 3 in version 4 (`ultra96.protocol.RESULT_VERSION`, the owner's decision). Version-3 command lines and defaults are unchanged.
- **Retest.** `tests/test_v4_launcher.py` (37) and `tests/test_v4_service.py` (9), among them `demo.py start --sensor-version 4` end to end on loopback and a real-TLS version-4 service publishing `v` 3 results; Wen Ree's version-4 tests and check still pass. All ten firmware environments build with no warnings.
- **Status.** Built and tested on the laptop; over BLE since 10-27/28 (W11-5); on the Ultra96 since 10-28 (W11-9, deployed with `--sensor-version 4`). Not run with a phone.

#### W11-3. Replacing a runner that was started by hand

- **What happened.** By Wen Ree's record (`docs/HAND_FPGA_BOARD_RESULTS_20261027.md`), after his hand12 board test he restored the paired full-CNN runner by hand as PID 177087 (start ticks 611890431). The deploy tool's launcher stops only the runner it started itself, so a new runner would fight the hand-started one for the bridge connection.
- **Options considered.** Document that the owner stops it by hand before the deploy, or let the deploy name it. Built the second, as the task allowed ("handle or document stopping it").
- **Change** (`c66a100`). `tools.deploy_service --replace-runner PID:START_TICKS`: the launcher (root) checks each named process before stopping anything (Python, a runner module in its arguments, not PID 1, not itself, not the service); after stopping its own recorded runner it sends that PID SIGTERM, and SIGKILL only while it still has the same start ticks; a gone or reused PID counts as already gone. `python demo.py service` lists hand-started runners with their start ticks.
- **Retest.** `tests/test_model_runner_launch.py` and `tests/test_deploy_service.py` on Windows; the Linux script, now 55 checks, passed in WSL (Python 3.10.12), with a hand-started runner stopped by SIGTERM and a non-runner refused without any signal.
- **Status.** Run on the board on 10-28 (W11-9): `python demo.py service` showed 177087 with those ticks, and the deploy replaced it.

#### W11-4. The hand12 runner and its staging

- **What happened.** Wen Ree's `src/socket_worker_hand.py` only observes; nothing fed his per-hand events to the game.
- **Change** (`c66a100`). `ultra96/hand_runner.py` (Communications) runs his `HandEngine` and `EventEncoder` unchanged, one of each per hand, with his backend (NumPy, or the FPGA overlay), in the model slot of the bridge; compat delivery as decided in W11-1; a hand is reset on a 1 s silence or a new `boot_id` (a glove reconnect or restart), the other hand untouched; each bridge connection gets a new worker epoch; JSON-line logs with the source identity and runner-local timings of every result. `tools.stage_model_runner --runner hand12` uploads the adapter, his runtime, the `common/` modules they import and the overlay (SHA-256 checked against his board-verified pair) from a commit, and a bundle (`--bundle`; a synthetic one needs `--allow-synthetic`), and prints the deploy command with `--sensor-version 4` and `--replace-runner`.
- **Investigation.** One interface point in his code [for Wen Ree]: `HandEngine.add` stamps a reset's `state_end` with the sample's arrival time, which can be earlier than a prediction the encoder already took, and `EventEncoder.consume` then raises `Invalid local event time`. The adapter hands such a record over at the latest time already taken and counts it; only `state_end` records are affected, and they are not forwarded.
- **Retest.** `tests/test_comms_hand_runner.py` (35, fake clock and a scripted backend that reads the gesture from the window's `flex3` value) and `tests/test_comms_hand_loopback.py` (7, a real-TLS version-4 service, the real bridge over a socket pair, both hands at 50 Hz real time, a subscriber): both hands independent; duplicates and a held pulse; CHOP to POURING gives one result at the transition sample; a reconnect or restart of one hand resets only that hand; a bridge reconnect; stale samples and an inference slower than 0.5 s give no result; IDLE only when confident. Staging dry run with a synthetic bundle made by his `tools.hand_hls_prepare --synthetic` (`.comms-local/hand12-synthetic-bundle-20261027`). The code was written by four agents in parallel, each reviewed independently (12 findings, all low, all fixed). Full suite after: 1516 passed, 16 skipped (`PYTHONUTF8=1`).
- **Status.** Superseded on 10-28 (W11-7): the adapter is deleted, and the same delivery now runs inside Wen Ree's worker. Trained LEFT/RIGHT bundles are Wen Ree's [pending].

#### W11-5. The bare-board BLE measurement at 50 Hz

- **What happened.** The owner connected two bare ESP32 boards by USB; only one CH340 port appeared (COM3, the left test board, factory MAC `38:18:2b:19:82:ac`), so the second cable carries power only. The board was flashed with `firebeetle32-left-flex3` (image 1,130,256 bytes, hash verified) and printed `comms_ready device_id=1 packet_bytes=40 packet_version=4 rate_hz=50 protected=1`. The BLE run could not start: the laptop's Bluetooth radio was powered off. Switching it on is a system setting that the agent does not change, and the owner was in Remote Control mode.
- **Prepared.** A harness that streams the board through the merged version-4 bridge into a local version-4 service for several minutes and reports sequence gaps, notification rates and batch sizes per 10 s (the W10-8 starvation signature is about 7 full six-packet notifications a second); `tools.check_board left --sensor-version 4 --address 38:18:2B:19:82:AE --duration 300` does the official check.
- **Run (10-27 23:40 to 10-28 00:19, by an agent at the owner's request, after the owner switched Bluetooth on).** All against a service on the laptop with throwaway certificates and the built-in dummy model; no VPN, SSH or Ultra96. "Generated" is the board's own source counter (the `LCS3`/`LCS4` statistics), read at the end of each run.
  1. Left board alone, version 4, 300 s: 14,813 generated = received = acknowledged, 0 `seq` gaps, 50.0 notifications per second of 1 sample each in every 10 s window, ATT MTU 517, connection interval 15 ms, longest receive silence 47 ms; all 14,813 results came back at `v` 3.
  2. Right board alone, version 3 (still its plain build), 330 s: 16,309 = 16,309 = 16,309, 0 gaps, longest silence 63 ms. This was meant as the first two-link run; the left half never started (below).
  3. Two links, two processes: the left board (version 4) and the right board (version 3) at the same time, 294 s of overlap: 14,806 and 16,284, each generated = received = acknowledged, 0 gaps; 49.4 and 50.0 notifications per second (the left one had 177 notifications of 2 samples); no starved second; longest silences 47 and 78 ms.
  4. The owner moved the programming cable to the right board (factory MAC `38:18:2b:18:9d:68` read first), which was flashed with `firebeetle32-right-flex3` (image 1,130,256 bytes, every hash verified) and printed `comms_ready device_id=2 packet_bytes=40 packet_version=4 rate_hz=50 protected=1`. The left board, now on the charge-only cable, restarted with a new `boot_id`.
  5. Both boards at version 4 through one dual bridge (`python demo.py run --sensor-version 4`, the Thursday shape), 600 s: 30,003 and 30,004 generated = received = acknowledged, coverage 1.000, `clean`, 0 gaps, 0 disconnects, longest silences 63 and 47 ms, 50 notifications per second each (3 of 2 samples in all); 60,007 results at `v` 3, none refused; no starved second.
  6. Four more dual runs of 90 s, each with fresh connections (a new pair of links gets new anchor points, the suspected trigger of W10-8): 4,503 to 4,519 samples per board and run, all generated = received = acknowledged, 0 gaps, no starved second, longest silences 47 to 63 ms.
  In all: 20.7 minutes of two-link time over six fresh pairs of connections, with no starved second and no lost sample.
- **What failed, and how it was found.** (1) The first two-link attempt ran only the right board: in the agent's shell line an `&&` chain put the variable assignments into the background job, so the left process started with an empty script path and exited at once; rerun with a script. (2) The analysis first showed 14 one-sample gaps on the left board in run 3 while the bridge's own counters showed none: on Windows `time.monotonic` ticks every 15.6 ms, so several notifications share one arrival time, and sorting the capture by arrival time and batch index interleaved them. The capture file is already in arrival order; read in file order, the gaps disappear. The same 15.6 ms steps explain why every silence figure above is a multiple of about 16 ms.
- **Checking the detector.** The per-second analysis (a starved second: under 15 notifications, at least 80 % of them full) run on the 10-20 capture of W10-8 finds 72 starved seconds on the left glove (the 76 s episode) and 4 on the right (the 7 s episode), and counts exactly the 567 and 13 lost samples recorded there; so a starved link would have shown in the runs above.
- **Findings.** (1) Version 4 at 50 Hz loses nothing over one link or two. (2) It keeps the firmware's limits (at most 6 packets per notification, 240 bytes, a 32-sample queue; `comms_send_queue.h`), so the arithmetic of W10-8 is unchanged: a link served 7 times a second still carries only 42 of 50 samples. (3) In every two-link run both links stayed in the fast state (each link served at every 15 ms event, 1 sample per notification), whereas on 10-19 and 10-20 about 30 notifications per second of 1.7 samples was normal. Tonight the laptop carried no VPN, SSH tunnel or other Wi-Fi traffic, and its Intel chip shares one radio between Bluetooth and Wi-Fi [Inferred: the conditions of 10-20, a run through the VPN, were not reproduced].
- **Whether a starvation fix is needed.** Version 4 does not need one of its own, but it does not remove the W10-8 risk either: not seeing it in 21 minutes on a quiet radio does not show it is gone (10-20 had two episodes in 40 minutes, 10-22 none in four runs). So the laptop-side watchdog is worth having on Thursday, and the owner asked for it the same night (W11-6). The firmware alternative (12 packets per notification) is not needed for Thursday: it would mean reflashing every glove and agreeing it with Wen Ree first.
- **Evidence.** `.comms-local/checks/2026-10-27-v4-ble-gap/` (`left-alone/`, `right-alone-v3/`, `two-link-1-left-v4/`, `two-link-1-right-v3/`, `dual-v4-1/` to `dual-v4-5/`, each with its capture, `summary.json` or the run's `report.json`, and `analysis.json` or `joint.json`; `flash-right-flex3.log`, `right-flex3-boot.log`; `scripts/` with the harness and analysis scripts; `README.txt`).
- **Status.** Measured. The starvation fix itself is W11-6.

#### W11-6. A laptop watchdog for the starved link (W10-8, continued)

- **What happened.** After midnight on 10-28, while the measurement of W11-5 was running, the owner asked: "fix BLE packet loss on the laptop side: if a glove shows full 6-sample notifications plus seq gaps for ~2 s, drop and reconnect it. Test with simulated gaps." This is fix (1) of W10-8.
- **Options considered.** The two of W10-8: (1) a laptop watchdog, no flashing; (2) up to 12 samples per notification in the firmware (reflash every glove, and tell Wen Ree first). The owner chose (1). Inside (1): the cooldown between two reconnects of one glove (10 s, short, because a starved glove gives the model nothing anyway: Wen Ree's `HandWindow` resets on every `seq` gap; the cooldown only stops the bridge hammering the Windows Bluetooth stack), and whether to keep the samples already received when the watchdog drops a link (kept, as at a normal stop).
- **Change** (`b7f4b13`, `8bd6b1f`; written by an agent in its own worktree, then reviewed twice independently: no defect, one missing test added). `laptop/link_watchdog.py`: per connection, a notification is full at `min(6, (MTU - 3) // packet size)` packets; when every notification has been full for 2 s, at least 8 of them, with at least one `seq` gap, the watchdog fires, at most once per connection and not again within 10 s (inside the cooldown it records `held`). `laptop/bridge.py` then drops that glove's link and reconnects it (`starved_reconnects`, `starved_held`; evidence `BLE_link_starved` and `BLE_starved_reconnect`); `laptop/dual_bridge.py --starvation-window` (0 turns it off) and `--starvation-cooldown`; `tools/live_view.py` names both counters among the failure reasons. On by default in every capture and check.
- **Retest.** `tests/test_link_watchdog.py` (43): healthy patterns, pauses and full notifications without gaps never fire; a starved pattern (7 full notifications a second with gaps) fires at exactly 2.0 s; through the real `enqueue` and `ble_loop` with a fake glove in version 3 and 4 a starved link is dropped and rebuilt, healthy ones never are; the cooldown; stop and off cases. Full suite after the merge: 1554 passed, 16 skipped. On hardware: quiet in the overall run of W11-8 (`starved_reconnects` 0, `starved_held` 0).
- **Status.** Built. Not yet seen on a real starved link, which W11-5 could not reproduce; how long a real starved reconnect takes is not measured (6 to 8 s for a glove reconnect on 10-20).

#### W11-7. The hand12 runner moves into Wen Ree's worker (W11-4, continued)

- **What happened.** After midnight on 10-28 the owner changed the plan of W11-4: "Wen Ree agreed I may edit src/socket_worker_hand.py (exception to the src/ rule, this file only). Instead of a separate adapter runner, make that worker send results back to model_bridge in the existing runner format v1, compat mode (pulse/state_start/state_refresh/idle -> one v3 GESTURE_RESULT, device_id = hand, no state_end). Keep his HandEngine/EventEncoder logic unchanged. Drop any adapter code you already wrote." [Owner's report of Wen Ree's agreement]
- **Change** (`e79963c`, `abc71ab`; written by an agent in its own worktree, reviewed twice, fixed). `src/socket_worker_hand.py`, the only file under `src/` changed (the exception is recorded in `AGENTS.md`): in socket mode the worker feeds every engine record to one `EventEncoder` (as his worker has one `HandEngine` for both hands) and sends each `pulse`, `state_start`, `state_refresh` and `idle` event back to the bridge as one result line for its source sample; `state_end` and `reset` are recorded only; a second result for one sample is dropped; the arrival-time quirk of W11-4 is handled the same way; `--observe-only` keeps the old behaviour and replay is unchanged. A hand is reset by his engine itself on a reconnect or restart of its glove (a new `boot_id`, a `seq` jump or a receive gap over 0.5 s); the adapter's own 1 s reset is gone. `--out` may name a folder (a new file per start). `ultra96/hand_runner.py`, `tests/test_comms_hand_runner.py` and `tests/test_comms_hand_loopback.py` deleted; `tools.stage_model_runner --runner hand12` stages the worker (and refuses a copy without the compat delivery, such as the team repo's), `tools.deploy_service` pairs it with sensor version 4, and the launcher and `demo.py service` recognise it.
- **Investigation (the reviews).** Both reviewers found that the first version served one bridge connection and then exited, unlike every runner the bridge expects (D42): after a service restart without a new runner the model slot would have stayed empty and the game would have had no results. Fixed: socket mode now waits for the socket, connects again 1 s after each end, gives each connection a new `worker_epoch`, keeps the backend and its overlay loaded, and ends only on SIGTERM or Ctrl+C. A smaller finding: records said "forwarded" before the send; they now say it only after `sendall` returned.
- **Retest.** `tests/test_comms_socket_worker_hand.py` (32, with a real-TLS loopback through the real model bridge); Wen Ree's tests unchanged and passing; a WSL check with a real Unix socket and a real SIGTERM; the full suite (1554 passed, 16 skipped); the overall run of W11-8.
- **Status.** Built. On the board with the FPGA backend since 10-28 (W11-9, a synthetic bundle). Not run with trained bundles, the gloves or the game. For Wen Ree [not yet told]: his worker now delivers (his `docs/INDEPENDENT_HAND_RUNTIME.md` still calls it observe-only; the change is in the team main since team PR #37, W11-10); the arrival-time quirk; his state timeout (0.6 s) equals three confirmations at 0.2 s, so a transition can end the old state by timeout a few milliseconds before the confirmed transition (the compat results are the same).

#### W11-8. The whole chain on the laptop with both boards

- **What was done** (10-28 01:17 to 01:23). Both dummy three-flex boards through `python demo.py run --sensor-version 4` (the dual bridge with the watchdog on) into `ultra96.server --sensor-version 4 --model ultra96.model_bridge` in WSL (Linux, a real Unix model socket, as on the Ultra96), Wen Ree's worker in WSL (NumPy backend, the synthetic bundle, `--threshold 0.0` so that the synthetic model's arbitrary confidences give events: a plumbing test, not a model test) and a desktop subscriber; throwaway certificates, no VPN, SSH or Ultra96; 300 s. numpy was installed into WSL's Python for it (the owner allowed downloads).
- **Result.** The capture `clean`: 15,008 and 15,003 samples generated = acknowledged, 0 gaps, 0 disconnects, `starved_reconnects` 0 and `starved_held` 0. The service accepted 30,011 samples and the bridge passed all 30,011 to the worker (none dropped). The worker forwarded 73 results for the left hand (37 `THROW` pulses, 36 `IDLE`) and 1,419 for the right (one `WASH` state and its refreshes every 0.2 s): 1,492 = the bridge's 1,492 results = the service's `model_results` 1,492 (0 refused, 0 duplicate, 0 late) = the subscriber's 1,492 `v` 3 `GESTURE_RESULT`s, each naming its hand, no duplicate. One `state_end` was recorded and, as designed, not sent; 0 collisions, 0 encoder errors, 0 unsent.
- **What failed.** Only the harness: the subscriber script exited 1 when the service was stopped before the subscriber's own deadline.
- **Evidence.** `.comms-local/checks/2026-10-28-overall/` (`README.txt`, `overall-1/` with the capture, the service, worker and subscriber logs and the worker's record file, `scripts/`).
- **Status.** Passed. Done on the Ultra96 on 10-28 (W11-9); with the phone still to do.

#### W11-9. Wen Ree's worker on the Ultra96, and both boards through it

- **What happened.** Early on 10-28 the owner asked for the deploy and typed every password ("i will help you key in the password, you deploy it"). About 04:36 `python demo.py service` (its first try timed out: the jump-host password must be typed within 60 s of the prompt, because OpenSSH's `ConnectTimeout` for the outer hop covers the login on the jump host) showed the version-3 service PID 165927 and Wen Ree's hand-started full-CNN runner `177087:611890431`, as his record said (W11-3). 04:38 the worker staged: `tools.stage_model_runner --runner hand12 --bundle .comms-local/hand12-synthetic-bundle-20261027 --allow-synthetic --replace-runner 177087:611890431`, 29 files from local `main` `00d859e` into `BOARD_ROOT/model-runner/hand12_v1`, each SHA-256 equal. The deploy tool, started at 04:40, waited at its first password prompt until the owner typed the passwords at about 05:06: the version-4 service PID 178358 and the worker PID 178365 (default threshold 0.7), `running` and `connected`. The launcher's own recorded runner was stopped with SIGTERM and 177087 then counted as already gone [Inferred: the launcher's pidfile recorded 177087, the only runner process listed]; the service log shows 177087 connecting to the new service for 3 ms before it went.
- **Investigation.** At the default threshold the synthetic bundle almost never gives a result: in W11-8's record (the same bundle on the same dummy data) the left hand's confidence never passed 0.7 (0 of 1,468 predictions) and the right one's 60 times, three in a row once. A run through the board would have tested almost nothing.
- **Options considered.** Run at 0.7 and accept a few results; redeploy at threshold 0 as on the laptop (W11-8). Chosen by the agent: threshold 0, a plumbing test only; a trained bundle is deployed without it.
- **Change (deployment, no code).** 05:14 redeploy with `--runner-arg=--threshold --runner-arg 0.0` (stamp `20261027T211405Z`): service PID 178412 (`BOARD_ROOT/source-co-v4-20261027T211405Z`), worker PID 178423; the previous worker reconnected to the new service for 0.15 s before the launcher stopped it (the reconnect of W11-7 at work). Both workers recorded `bundle_verified` and `hardware_artifacts`: the overlay's SHA-256 (`b8d04073…`, `935975fe…`) equal to Wen Ree's board-verified pair. 05:19 a read-only overnight session for the checks: OpenSSH in WSL with a master connection (`ControlMaster`), both hops pinned to the host keys of the owner's Windows `known_hosts`, passwords only (typed by the owner), carrying the tunnel's two forwards (18889 → 8888, 19999 → 9999); later commands reuse it without a password. Its config is in WSL `~/.b07ssh/` (a copy in the evidence folder); the first try failed because WSL had restarted and emptied `/tmp`, where it was first written.
- **Retest.** Both dummy three-flex boards through the real Ultra96 with `python demo.py run --sensor-version 4 --left-address 38:18:2B:19:82:AE --right-address 38:18:2B:18:9D:6A`, the board read through the session (the worker's record, the service's event log, one board-monitor update): run 1, 05:30 to 05:32 +08:00, 120 s: `CAPTURE PASSED`, left 6,003 and right 6,007 samples generated = received = acknowledged, 0 gaps, 0 disconnects, the watchdog quiet; on the board the service accepted 12,010 and the bridge passed all 12,010 to the worker (`model_samples`); the worker made 584 predictions per hand on the FPGA and forwarded 581 results (left 35: 17 pulses, 17 idles, 1 state start; right 546: 1 state start, 545 refreshes) = the service's 581 `model_result`s (35 and 546 by hand), none refused; the 2 state ends were recorded and not sent; longest model call 3.1 ms; run 2, 05:33 to 05:44 +08:00, 600 s: `CAPTURE PASSED`, left 30,003 and right 30,003 samples generated = received = acknowledged, 0 gaps, 0 disconnects, `starved_reconnects` 0; on the board the service accepted 60,006 and the bridge passed all 60,006 to the worker; the worker forwarded 2,891 results (left 159: 79 pulses, 79 idles, 1 state start, right 2,732: 1 state start, 2,731 refreshes) = the service's 2,891 `model_result`s (159 and 2,732 by hand), 0 refused; 2 state ends recorded and not sent; longest model call 4.2 ms. The phone was not subscribed: the owner offered to connect it, then reported that its certificate needs updating first [Owner's report; Inferred: the free signing profile, which expired on 2026-10-25, W10-15], to be done in the morning. A laptop subscriber was not used, because the service keeps one subscriber and a new `SUBSCRIBE` closes the previous one (it would push the phone off); so every result was counted as `result_no_subscriber`. `demo.py run`'s `Phone expected increase` assumes the built-in dummy model (one result per sample) and does not apply.
- **Evidence.** `.comms-local/checks/2026-10-28-ultra96/` (`README.txt`; `run-1/`, `run-2/` with the captures, `demo.log` and one board-monitor snapshot each, `monitor-after.json`; `board/` with the stage and deployment records, the service, runner and worker logs and records copied from the board, and the event counts; `scripts/` with the board count script, the monitor snapshot script and the SSH config); `.comms-local/deployments/deployment-20261027T204020Z.json`, `deployment-20261027T211405Z.json`, `model-runner-stage-20261027T203804Z.json`.
- **Status.** Passed with the synthetic bundle. The board runs version 4 only (the current version-3 gloves cannot use it until a version-3 redeploy), with results that mean nothing. Still to do: the phone (after its certificate), Wen Ree's trained bundles (staged under a new `--name`, deployed without `--threshold`), the three-flex gloves, the game. For Wen Ree [not yet told]: his full-CNN runner no longer runs on the board.

#### W11-10. The week's Communications work into the team repo

- **What happened.** On the morning of 10-28 the owner asked: "push", then "push and merge". Local `main` (`03e5046`) was pushed to the fork. The team main had not moved since `5e3f78e`.
- **Change.** A branch `comms/hand12-v4` from the team main `5e3f78e` with every Communications path that differed from it, and Wen Ree's `src/socket_worker_hand.py` (his agreement, W11-7), taken unchanged from local `main`: 34 files, one commit `9ef2d24` (the version-4 launch path of W11-2, `--replace-runner` of W11-3, the watchdog of W11-6, the compat delivery and staging of W11-7, and the three fixes of 10-22, `d69891f`, which had not gone to the team before). Left out as fork-only: `docs/`, `AGENTS.md`, `CLAUDE.md`, `ios-visualizer/` with `tests/test_ios_export_patch.py`, and the Xcode export's lines in `.gitignore` and `.gitattributes`. Team pull request #37 (<https://github.com/B07-CG4002/Let-Them-Cook/pull/37>) opened and merged at once (`521c7e5`; the team repo has no CI). The team main then merged into local `main` (`9ace0b2`; the tree did not change) and pushed to the fork.
- **Retest.** On the branch: the full suite with the Linux deploy test in WSL, 1537 passed, 15 skipped (1554 on local `main`, which also has the fork-only tests).
- **Status.** Done. The team main has the version-4 launch path and the worker that delivers results. Not changed: the help text of `tools/stage_model_runner.py` still says the team repo has the observe-only worker (now untrue; to fix with the next code change). For Wen Ree [not yet told]: that the change to his worker is in the team main.

### Decisions that affect more than one subsystem (Week 11)

| Date | Decision | Who | Affects |
|---|---|---|---|
| 10-27 | For the Thursday integration the per-hand events reach the game in compat mode: one `v` 3 result per pulse, state start, state refresh or idle, `device_id` = the hand, no state end; Wen Ree's structured `HAND_EVENT` is not carried yet. | Owner | Wen Ree, Jie Ling |
| 10-27 | Results stay at `v` 3 when the sensor version is 4, so the phone apps need no change. | Owner | Jie Ling |
| 10-27 | Communications writes and runs the hand12 runner (an adapter around Wen Ree's unchanged engine) in the model slot. Superseded on 10-28 by the next row but one. | Owner | Wen Ree |
| 10-28 | The laptop drops and reconnects a glove whose notifications have all been full, with `seq` gaps, for 2 s (on by default; W11-6). | Owner | Wen Ree (his model sees a reconnect pause instead of a starved stream) |
| 10-28 | The hand12 runner is Wen Ree's own `src/socket_worker_hand.py` with Communications' compat delivery, not a separate adapter; Wen Ree agreed that Communications may edit that one file (W11-7). | Owner, with Wen Ree's agreement [Owner's report] | Wen Ree |
| 10-28 | The Ultra96 runs the version-4 service with Wen Ree's hand12 worker, replacing the version-3 service and his full-CNN runner (W11-9); version-3 gloves cannot use it until a version-3 redeploy. | Owner (asked for the deploy) | Wen Ree, Siqiang, Jie Ling |
| 10-28 | The week's Communications code, with the compat delivery in Wen Ree's worker, goes into the team main (team PR #37, W11-10). | Owner ("push and merge") | Wen Ree, Siqiang, Jie Ling |
| 10-28 | For the test with the synthetic bundle the worker runs at threshold 0; a trained bundle is deployed at Wen Ree's default (0.7). | Agent (plumbing test only) | Wen Ree |

### Tests on hardware (Week 11)

| When | Run | Result | Evidence |
|---|---|---|---|
| 10-27 evening | Left test board flashed with `firebeetle32-left-flex3`, boot output over USB | `packet_version=4 packet_bytes=40 rate_hz=50`; no BLE run (Bluetooth off) | hand-off 6.1 |
| 10-27 23:40 | Left board alone, version 4, 50 Hz, 300 s, local service | 14,813 = 14,813 = 14,813, 0 gaps, 50 notifications/s of 1 sample, MTU 517, 15 ms, longest silence 47 ms, all results `v` 3 | `.comms-local/checks/2026-10-27-v4-ble-gap/left-alone/` |
| 10-27 23:52 | Left (version 4) and right (version 3) boards together, two processes, 294 s | 14,806 and 16,284, each generated = received = acknowledged, 0 gaps, no starved second | `…/two-link-1-*` |
| 10-28 00:00 | Right test board flashed with `firebeetle32-right-flex3` | `packet_version=4 packet_bytes=40 rate_hz=50 device_id=2` | `…/flash-right-flex3.log`, `right-flex3-boot.log` |
| 10-28 00:01 | Both boards, version 4, one dual bridge (`demo.py run --sensor-version 4`), 600 s | 30,003 and 30,004, coverage 1.000, `clean`, 0 gaps, 0 disconnects; 60,007 results `v` 3, none refused | `…/dual-v4-1/` |
| 10-28 00:12 | Four dual version-4 runs of 90 s, fresh connections each | 4,503 to 4,519 per board and run, all equal, 0 gaps, no starved second | `…/dual-v4-2/` to `dual-v4-5/` |
| 10-28 01:17 | The whole chain on the laptop: both version-4 boards, dual bridge with the watchdog, service and model bridge in WSL, Wen Ree's worker (synthetic bundle, `--threshold 0.0`), subscriber, 300 s | `clean`, 15,008 and 15,003 equal, 0 gaps, watchdog quiet; 1,492 results forwarded = published = received at `v` 3, none refused | `.comms-local/checks/2026-10-28-overall/overall-1/` |
| 10-28 05:06 | Hand12 worker staged and deployed on the Ultra96 with the version-4 service; redeployed at threshold 0 at 05:14 | `deployed`, the worker `running` and `connected`, overlay SHA-256 equal to Wen Ree's pair; 177087 replaced | `deployment-20261027T204020Z.json`, `deployment-20261027T211405Z.json` |
| 10-28 05:30 | Both version-4 test boards through the Ultra96 to Wen Ree's worker (FPGA, synthetic bundle, threshold 0), 120 s, no subscriber | `CAPTURE PASSED`, 6,003 and 6,007 equal, 0 gaps; 12,010 accepted = passed to the worker; 581 results forwarded = recorded by the service, none refused | `.comms-local/checks/2026-10-28-ultra96/run-1/` |
| 10-28 05:33 | The same, 600 s | `CAPTURE PASSED`, 30,003 and 30,003 equal, 0 gaps; 60,006 accepted, all 60,006 passed to the worker; 2,891 results forwarded = 2,891 recorded by the service, 0 refused | `.comms-local/checks/2026-10-28-ultra96/run-2/` |

### Open (Week 11, so far)

1. ~~The 50 Hz version-4 BLE gap measurement (W11-5), once Bluetooth is on.~~ Done on 10-27/28: no loss over one or two links; the starvation of W10-8 was not reproduced, so its watchdog (W11-6) is a safeguard.
2. Wen Ree's trained LEFT/RIGHT bundle for the hand12 runner; until then only a synthetic bundle.
3. ~~Staging and deploying the hand12 runner (Wen Ree's worker, W11-7) on the board, replacing PID 177087 (W11-3); then the run of W11-8 on the Ultra96.~~ Done on 10-28 with the synthetic bundle (W11-9). Still: the run with the phone, once its certificate is renewed (the owner); the trained bundles staged under a new `--name` and deployed without `--threshold`.
4. Telling Jie Ling that ongoing actions arrive as repeated results with no end message; telling Wen Ree the findings (W11-1, W11-4, W11-7), that his worker now carries the compat delivery, and that his full-CNN runner no longer runs on the board (W11-9).
5. The three-flex gloves from Siqiang, flashed with `python flash.py --glove --flex3`.
6. ~~Pushing the fork; whether any of `c66a100` and of the 10-28 commits (including the change to Wen Ree's `src/socket_worker_hand.py`) goes to the team repo.~~ Done on 10-28 at the owner's request: pushed, and merged into the team main through team PR #37 (W11-10).
7. Whether the watchdog (W11-6) fires on a real starved link, and what that reconnect costs; not reproduced so far (W11-5).

---

## Adding an entry

`AGENTS.md` rule 9 asks for an entry with every code change, deployment change, integration run and cross-subsystem decision, in the same piece of work as the change and its other document updates.

1. Find the current teaching week (Monday to Sunday; Week 11 is 26 October to 1 November 2026). Start a new `## Week N (…)` section when a week begins, and write its one-page summary when the week ends.
2. Add one line to the week's "Day by day" table: the date and time, what happened, and the evidence (commit, pull request, run folder, deployment record).
3. For anything that failed, was investigated or changed, add or extend an issue under "Issues, investigations and changes" with the next number (`W11-1`, `W11-2`, …), using these headings where they apply: **What happened**, **Investigation**, **Options considered**, **Change**, **Retest**, **Status**. Continue an issue from an earlier week by its number (for example "W10-6, continued").
4. Add a row to "Decisions that affect more than one subsystem" for any decision that changes what a teammate sends, receives or must do, with who decided.
5. Add hardware runs to "Tests on hardware" with their numbers and evidence folder.
6. Mark what was not measured or not confirmed: [Owner's report], [Inferred], [Not confirmed], [Proposal]. Write teammates' plans as plans, not as decisions.
7. Write in English. Times in +08:00. Use names for teammates.
