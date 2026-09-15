# Week 7 continuation: native iOS integration — 2026-09-14

## Current Mac outcome

The actual Unity Xcode export now contains a compatible native Phone subscriber.
It owns its SSH connection through Ultra96 TCP22, verifies the Week 7 TLS CA and
service hostname, subscribes using the existing framed protocol, and updates the
scene's existing TextMeshPro label. The old inbound TLS receiver is disabled.
The reusable implementation, tests and reproducible export scripts are in
[the native integration guide](../ios-visualizer/NATIVE-INTEGRATION.md).

**Baseline verified:** full unsigned arm64 Unity Debug and Release builds; 54 Swift tests; 246 Python
tests (4 platform-dependent skips, 49 subtests); 26 transport/trust tests executed
inside the iOS simulator in addition to the shared native UI test; 100-result
interoperability with the actual Python board server over
two real local SSH hops. On September 15, the actual signed Unity app also
installed and launched on the connected iPhone after the operator trusted the
developer profile. The actual app subsequently reached **Subscribed** through
the campus jump host and Ultra96, displayed a live result, and counted **100
received results** from synthetic Mac input. All 100 sender ACK IDs matched the
board acceptance log. This proves a physical Phone connection and count-level
delivery; it is not a durable trace of every Phone result ID. A repeat delivered
only 56 of 100 to the Phone when started during reconnect, and later explicit
logins were rejected. On September 16, a corrected fresh login again reached
**Subscribed**, followed by a clean **100/100** Phone count test with 100 matching
ACK/board IDs, sender exit 0 and zero reported sender errors or drops.
The subsequent update adds hop-specific authentication diagnostics and password
visibility controls. Its signed build, simulator UI check, physical install and
launch passed. After the operator fixed keyboard input and clicked Connect,
that final binary also reached **Subscribed** and received **100/100** results,
including a live **OPEN** gesture. Its 100 ordered ACK IDs exactly matched the
board log, with sender exit 0 and all error/drop counters zero. A separate
20-result visual check then displayed **FIST**; all four dummy labels have now
been observed across physical Phone runs.
**Not verified:** complete physical Unity/ARKit behavior, the actual Windows
BLE/ESP32 chain or physical lock/background recovery. Historical iSH acceptance
below remains separate.

Work began on a clean `main` at `bf38f83`, equal to fetched `origin/main`, and
continues on **`codex/ios-visualizer-week7-native`**. No merge to main or PDF was
made. The original Unity source was not found in this checkout or the bounded
Documents search; its absence does not prevent this native-export build.

**Publication:** implementation commit `33f8c7e127e810b9c5071feac9aee8ba7a16c34b`
was pushed to [the feature branch](https://github.com/olsonwangyj/Let-Them-Cook/tree/codex/ios-visualizer-week7-native).
An independent `git ls-remote` check confirmed that exact remote commit and
unchanged `main` at `bf38f83d9ca3d621258ac32b8de9f3d789042651`. Staged whitespace
and credential checks passed; the working tree was clean after the implementation
commit. That was the initial implementation publication. Later checkpoints were also
published on the same feature branch, most recently `912713945142eb914fdd7702f435dbd82af3339d`
before the September 16 authentication/input follow-up. That follow-up was
published as `2643c8e5d73139fac1b96c4f31b04cf5efe65883`; an independent remote check
confirmed its exact feature-branch head and unchanged main. Remaining
physical actions are listed below.

After the user requested continuation, device/signing discovery again returned
no physical device and zero valid identities. One further runtime check
was completed: the existing transport tests now run inside iOS itself using an
XCTest fixture bundle. The 26 simulator tests passed; the 27 macOS transport
tests, including actual Python board interoperability, also passed again. These
are additional platform executions of existing tests, not new physical hardware
acceptance. Production app source and the Unity export did not change.
The setup UI test also passed again using the new simulator build location.
Follow-up commit `cbbc212b5d30f2f2725fc083ce93b3b27e154802` was pushed to the
same branch and independently confirmed with `git ls-remote`; main remained
unchanged. The remaining actions at that point still required a physical device, accounts or
the existing live hardware/private setup.

## Physical setup continuation — September 15

The operator supplied a connected iPhone Air (`iPhone18,4`, iOS 26.6.1), signed
into their own Apple account in Xcode, selected their Personal Team and enabled
Developer Mode. Their project signing changes remain local and are preserved;
no personal team, signing identity or device identifier is included in this
publication. The available laptop is now this Mac; Windows and ESP32 hardware
are unavailable for this session.

The actual Unity Debug build succeeded with automatic development provisioning
using Xcode's standard `~/Library/Developer/Xcode/DerivedData/Week7UnityDevice`
directory. Strict deep signature verification passed. The provisioning profile
matches the app, includes the connected device, enables development debugging
and expires September 22, 2026. Installation via `devicectl` succeeded. The first
launch was denied by iOS security; after the operator completed developer trust,
`devicectl` reported a successful launch and a separate process query confirmed
the Unity app running. The operator then confirmed **Week 7 Connect** is visible
on the actual phone. This establishes installation, startup and the setup entry
point; later live result rendering is recorded below. Complete Unity/ARKit
behavior remains unverified.

The first signed build failed because Finder metadata was attached to framework
directories under the Documents checkout. Only `com.apple.FinderInfo` on the
two imported framework roots was removed after saving a local attribute backup.
Other attributes and framework contents were preserved. Building generated
products in Library then passed; no signing check was bypassed. The three
compiler-generated diagnostic rewrites were restored after building.

Private local evidence is in `.week7-local/evidence/`: the signed build log
`xcode-signed-device-library-private.log`, `physical-install-private.json`,
`physical-console-private.log` (initial denied launch),
`physical-console-trusted-private.log` and `physical-processes-private.json`.
These files may contain personal signing/device metadata and remain ignored.

The Mac reached `stujump.comp.nus.edu.sg:22` without an active VPN and received
an SSH banner. A subsequent SSH handshake matched the enrolled Ed25519 host key,
but the server advertised only `publickey` authentication and refused the
unauthenticated probe. That initial two-hop attempt therefore did not reach an
authenticated board connection. After the operator connected the Mac VPN,
both pinned hosts accepted password authentication and the public archive was
retrieved successfully. For this retrieval, passwords were entered only into SSH's terminal prompts;
they were not written to local credential files or included in project changes.
The failed attempt's owned empty socket directory and pending record were
cleaned up without changing any host or authentication policy.
The ignored local helper at `.week7-local/physical-connection/retrieve-ca.command`
downloads the exact
historical public archive from the [SSH import guide](week7-iphone-ssh-import.md),
enforces both enrolled Ed25519 keys, verifies the ZIP hash and exact five entries,
then extracts only the CA after its DER fingerprint matches enrollment.
The retrieved archive passed its exact SHA-256, five-entry allowlist and CRC
checks; its sole CA matched the enrolled DER fingerprint. The public CA and
documented usernames were copied over USB into the actual app's previously
absent `Library/Application Support/Week7` directory. Reading the CA back from
the phone confirmed byte-for-byte equality and the enrolled DER fingerprint.
No password, private key or system-wide trust profile was transferred. The app's
normal `loadCA()` still validates the enrollment before displaying the setup.
This establishes verified transfer; it does not establish use of the Files
picker. The app subsequently loaded and verified the CA, and the operator
connected the Phone VPN independently of the Mac.

The existing `xilinx`-owned Ultra96 process is running the documented server
from `/var/tmp/cg4002-week7-yanjie-20260907/source-db6769a`, bound only to
`127.0.0.1:8888` and `127.0.0.1:9999`. Its public certificate identifies
`ultra96.week7.internal` and is valid through October 6, 2026. No restart or
server configuration change was needed. A temporary pinned Mac SSH master and
loopback-only `18888 → 127.0.0.1:8888` forward are prepared for synthetic input;
no Mac result subscriber was started. Actual Phone subscription and delivery
were pending at that checkpoint. The idle Mac master later expired while
Mirroring needed operator input; its stale record and owned empty socket
directory were cleaned up. The scoped master and forward were later
re-established for the synthetic sender tests below.

Local ignored evidence under `.week7-local/physical-connection` includes
`retrieval-wmlcmdvp/week7-iphone-setup.zip.verified.json`, `board-preflight.txt`
and `board-log-baseline.json`. The `.week7-local/evidence` directory contains
`jump-reachability-private.log`, `phone-public-setup-copy-private.json` and
`phone-ca-readback-private.json`. No password is included. The operator has
also confirmed the iPhone VPN is connected; the app was brought back to the
foreground for its own SSH login.

The operator authorized entry of the supplied SSH passwords through iPhone
Mirroring. After the operator unlocked Mirroring and locked the phone, the
actual app visibly displayed its Unity status label and **Verified Week 7 CA
imported** with the enrolled fingerprint. Settings also showed **Connected**
for the selected **NUS VPN For Student** profile. Mirroring reports the camera
unavailable from the Mac, so this observation cannot certify live ARKit/camera
behavior. No camera permission or protection was changed.

The first submitted app login returned **SSH password authentication rejected**.
That installed version's error did not distinguish SSH hops or a rejected
password from a server that excludes password authentication. A bounded board auth-log read
showed the successful Mac login but no later Phone board attempt, consistent
with failure at the jump hop. A corrected keyboard-entry retry was prepared but
not submitted: Mirroring disconnected while typing and returned to its Mac
login screen. No Phone subscription or gesture delivery was established at
that earlier checkpoint. Local
`physical-connection/phone-mirroring-checkpoint.json` records these observations
without passwords. The later successful test and subsequent failures follow.

### Actual Phone result test — September 15–16

After Mirroring was unlocked and the credentials were entered, the actual
Unity app visibly reached **Subscribed**, with **Received: 0**. The Phone owned
its SSH → SSH → TLS → SUBSCRIBE connection. The Mac used only the board's
ingestion port through its separate pinned SSH forward; no Mac result subscriber
was started. The existing `ObservedBridge` mock generated 100 synthetic packets
with a fresh boot ID, using the real ingestion protocol and public CA.

| Run | Sender and board evidence | Actual Phone observation | Assessment |
| --- | --- | --- | --- |
| First, September 15 at 15:46 UTC | 100 accepted ACKs and exactly matching board IDs `1:2250398211:0` through `1:2250398211:99` | **Subscribed**, live **REST**, ID `1:2250398211:80`, confidence 1.0 at count 81; subsequently **Received: 100** | Physical subscription, live rendering and 100-result count established. The local reporting helper raised a `TypeError` after all ACKs, exited 1 and produced no aggregate summary; this failure is retained. |
| Repeat with reporting fix | 100 accepted ACKs, 100 matching board IDs for boot `1075570325`, process exit 0; all reported error/drop/duplicate counters zero | Count increased from 100 to **156**, with live **POINT**, ID `1:1075570325:91`, confidence 1.0 at count 148 | Sender passed, but Phone delivery was only **56/100**. Input started while the Phone was reconnecting; the 44-result shortfall is consistent with that startup timing and is not a passing delivery repeat. |
| Fresh login, September 16 local time | 100 accepted ACKs and exactly matching board IDs `1:2744570014:0` through `1:2744570014:99`; sender exit 0, all reported error/drop/duplicate counters zero | Fresh **Subscribed / Received: 0**, live **POINT**, ID `1:2744570014:55`, confidence 1.0 at count 56; final **Subscribed / Received: 100** | Clean physical count-level repeat passed after verified credential entry. |
| Final updated app, September 16 at 01:29 local time | 100 accepted ACKs and exactly matching ordered board IDs `1:4029935889:0` through `1:4029935889:99`; sender exit 0, all 14 reported error/drop/duplicate counters zero | Fresh **Subscribed / Received: 0**, live **OPEN**, ID `1:4029935889:82`, confidence 1.0 at count 83; final **Subscribed / Received: 100** | Final binary with hop-specific errors and password visibility controls passed the physical count-level test after the operator fixed keyboard input. |

The helper's reporting fix renamed its observation timing field so it no
longer collided with `elapsed_seconds` in the bridge summary. It changed only
the ignored local test helper, not the app or board. Original failed-run logs
remain intact. Evidence is under `.week7-local/physical-connection/`:
`physical100-sender.jsonl`, `physical100-board.log`,
`physical100-correlation.json`, `physical100-repeat-sender.jsonl`,
`physical100-repeat-board.log`, `physical100-repeat-correlation.json`,
`physical100-final-sender.jsonl`, `physical100-final-board.log` and
`physical100-final-correlation.json`, `physical100-updated-sender.jsonl`,
`physical100-updated-board.log` and `physical100-updated-correlation.json`.
Phone screen observations are captured in the task's Mirroring tool output;
the app retains a latest result and unique count, not a complete result history.
Consequently the 100-ID sender/board match must not be described as a saved
100-ID Phone trace. REST and POINT were observed on earlier runs, and OPEN and
FIST on the final updated app.

A separate visual check sent 20 valid FIST packets for boot `3878925323`, using
sequence numbers `1, 5, …, 77` so each result kept the FIST label visible. The
Phone displayed **FIST**, ID `1:3878925323:57`, confidence 1.0 at count 115; its
count rose from **100 to 120**, ending **Subscribed**. All 20 accepted ACK IDs
exactly matched the board log and the sender exited 0. The 57 sequence gaps were
intentional in this visual fixture; this is separate from the clean consecutive
100-result gate and is not a zero-gap run. Other sender error/drop counters
were zero. Evidence is `physical-fist-sender.jsonl`, `physical-fist-board.log`
and `physical-fist-correlation.json` in the same ignored local directory. This
completes observation of all four dummy labels across physical Phone runs.

During the quiet interval, the live result cleared and the app cycled through
its established-stream idle reconnect behavior. A bounded board authentication
log read showed repeated successful Phone logins and closures consistent with
that behavior. Later explicit credential re-entry attempts, including a fresh
app launch and the operator's VPN reconnect, returned **SSH password
authentication rejected** with count zero. That version's error did not identify
the SSH hop or distinguish wrong input from unavailable password authentication.
Mirroring input was unreliable during these retries; their individual causes
were not established. Direct physical entry was initially requested, but the operator asked
the agent to complete the login instead. After restoring Mirroring, the agent
found an incorrect unsaved board username in the reopened form, replaced it,
visually verified board user `xilinx` and jump user `yanjie`, and entered the
supplied passwords into their separate secure fields. The app immediately
reached **Subscribed** and the fresh test above passed. This resolved that
login and repeat test; it does not establish the cause of every earlier failed
attempt or physical network-fault/lock recovery.

The diagnostic review found that four distinct authentication failures shared
one misleading message. A small follow-up now identifies the SSH hop and
distinguishes a server that does not offer password authentication, an unaccepted
password offer, unavailable credentials and an empty password. Password
failures remain terminal; trust validation, credential storage and retry policy
are unchanged. Eleven focused Swift tests passed, including actual two-hop
fixture rejection at each hop and no automatic credential retry. The clean
physical run for boot `2744570014` used the previously installed app.

A subsequent diagnostic build identified a concrete input mismatch in later
Mirroring retries: an exclamation mark arrived as full-width Unicode `U+FF01`
instead of ASCII `U+0021`. A temporary local probe recorded only encoding
metadata, not the complete password. This explains those observed jump-hop
failures; it does not retrospectively establish every earlier failure's cause.
The probe was removed from production source and from the final rebuilt app.
No password trimming, normalization or substitution was added.

The setup form now offers accessible Show/Hide controls for each password,
preserving the exact text and caret selection. Password fields request an
ASCII-capable keyboard with smart substitutions disabled. These are input
hints, not a guarantee about external keyboard conversion. Clearing a field
also re-masks it, including on dismissal, deactivation and successful Connect;
disabling the jump host clears and disables its password control.

The final signed Unity Debug build passed, strict deep signature verification
passed, and the updated app installed and launched on the actual iPhone. The
existing simulator setup/background-clearing UI test also passed with the new
controls. The operator subsequently reported fixing the keyboard. Mirroring's
click tool returned `noWindowsAvailable` even while screenshots and keyboard
input worked, so the operator selected the board password field and later
clicked Connect; the agent entered both supplied passwords using the secure app
fields and Tab navigation. No passwords were stored in project files. The final
app reached **Subscribed** and passed the new 100-result run above. Independent
review confirmed all 100 ordered ACK/board IDs and the zero-error sender summary.
The operator offered to handle subsequent scrolling and field selection.

Ignored evidence includes `evidence/xcode-password-entry-final-private.log`,
`evidence/ios-ui-password-entry-private.log`,
`evidence/physical-password-entry-final-install-private.json` and
`evidence/physical-password-entry-final-launch-private.json`, all under
`.week7-local/`. Personal signing/device metadata remains local.

With Mac and iPhone alone, synthetic input can test the real Phone result path.
It does not establish ESP32/BLE acceptance.
The protected physical bridge currently depends on Windows authenticated-pairing
checks; do not disable those checks to substitute Mac BLE.

## Mac decisions and reasons

These extend IOS-01..12 below and the selected communications contract. The
user explicitly delegated routine design/implementation/approval decisions.

| ID | Decision | Reason / consequence |
| --- | --- | --- |
| IOS-13 | Work in the clean existing checkout on a new feature branch | Preserves the requested Mac location and avoids duplicating the 1.47 GB export; main stays unchanged. |
| IOS-14 | Install Git LFS and verify the original baseline before edits | Initial checkout contained 275 LFS pointers. Hydration, LFS fsck and all 3,480 baseline hashes then passed. |
| IOS-15 | Link a native Swift package into UnityFramework and patch existing generated lifecycle bodies | Detached C# cannot update this export. Start/Update/OnDestroy retain existing registration and serialized layout; Update invokes the actual assigned TMP label. |
| IOS-16 | Use app-owned SwiftNIO SSH, optionally nested through the existing campus jump host | Both SSH destinations remain pinned to TCP22. The Phone does not depend on foreground iSH or the Laptop for results. Dependencies and resolved revisions are pinned. |
| IOS-17 | Carry TLS within a direct-tcpip stream to board 127.0.0.1:9999 | Preserves the existing board route and TLS protocol while removing the need for a Phone TCP19999 listener. No board application port becomes externally reachable. |
| IOS-18 | Pin both already enrolled Ed25519 host keys and the documented Week 7 CA SHA-256 | CA import rejects even a valid unrelated public certificate. TLS still validates the full chain, validity and `ultra96.week7.internal`; trust rotation needs independent verification. |
| IOS-19 | Use foreground password entry for both SSH hops, with memory-only revocable storage | The existing physical route used passwords; Windows private credentials are unavailable here. Deferred authentication cannot recover passwords after stop. No credential files or account changes are introduced. |
| IOS-20 | Stop on app deactivation/background and require explicit reconnect on return | Prevents reliance on unproven iOS background lifetime. This also stops for system UI that deactivates the app. Passwords are cleared; uninterrupted background reception is not promised. |
| IOS-21 | Keep only the newest display result, with 2-second monotonic freshness and 4,096-ID dedup | Bounds memory and avoids displaying queued old data. Count reflects accepted unique results within the current explicit Connect session, not persistent exactly-once delivery. |
| IOS-22 | Adopt the current Python client's 30-second initial first-byte grace, then one 5-second frame budget | Allows operator-controlled BLE startup without permitting slow partial frames. Established streams keep 5-second deadlines. |
| IOS-23 | Retry transient network/SSH forwarding failures with 0.5..5-second backoff; make auth/trust/schema failures terminal | Allows recovery without repeated wrong-password attempts or accepting untrusted peers. User corrects setup and explicitly reconnects after terminal failure. |
| IOS-24 | Own every allocated connection candidate and revoke callback generations before teardown | Review found multi-address connection and cancellation races. Regression tests verify that pending candidates close and retired callbacks cannot update fresh UI. |
| IOS-25 | Stretch the delivered TMP label using runtime RectTransform anchors and font autosizing | The original fixed 200×50 rectangle could not fit status/result/count. The existing label now uses 90% canvas width, 70% height and 18..36 font autosizing without scene/metadata binary edits. |
| IOS-26 | Fail closed when replaying patches onto unknown or incomplete exports | Exact receiver hashes and the complete Xcode package-reference chain are checked before writes. Reviewed patch upgrades and idempotent reapplication are tested. |
| IOS-27 | Remove 16 inherited Unity symbol-upload settings and two remaining target-level teammate signing attributes; disable symbol upload by default | A local build should not publish to a teammate account. The 16 entries held one repeated 64-character token; validity was not tested. Earlier Git history still contains it; an authorized owner should revoke/rotate it if active. No history rewrite was attempted. |
| IOS-28 | Install iOS support and add a small simulator host for the same native UI module | The SDK was present but Xcode could not build storyboards until platform support was installed. The host verifies native UI behavior; it does not replace physical Unity acceptance. |
| IOS-29 | Fix only the Mac-specific mock in the existing iSH test | The mock incorrectly intercepted macOS `/var` symlink resolution. It now delegates non-/proc links to the real function; Phone runtime code is unchanged. |
| IOS-30 | Preserve the original import manifest and exclude regenerated compiler diagnostics from delivery | The manifest remains provenance. Native source/configuration changes are explicit; build-time profile/trace/compile-data rewrites are restored rather than published as product edits. |
| IOS-31 | Execute the existing transport/trust tests in an iOS XCTest host using generated fixture PKI | macOS-only OpenSSL process creation previously prevented iOS execution. A locked pool provides distinct, short-lived authorities; test copies are cleaned up and production trust is unchanged. |
| IOS-32 | Use Xcode's standard Library DerivedData directory for simulator tests | A repository-derived absolute debug-framework path under Documents stalled the loader on a macOS privacy request before main. Moving generated test products to Library resolved it without changing privacy controls. |

## What changed in the actual app

`Week7Core` validates bounded UTF-8 frames and exact schemas; tests include
malformed UTF-8/BOM, duplicate decoded keys, invalid integer forms/ranges,
non-finite numbers, wrong sessions and deterministic result mismatches.
`Week7Transport` owns SSH/TLS, subscription, deadlines and recovery.
`Week7Bridge` supplies CA import, native settings and the C ABI display mailbox.
No asynchronous worker retains a managed Unity object pointer.

The enabled delivered `NetworkManager` receiver references the existing
`Text (TMP)` component in `Data/level0`. Only generated method bodies and native
build configuration changed. No scene or IL2CPP metadata binary was edited.
The legacy ListenLoop is also disabled, so direct invocation cannot reopen port 5005.

The setup button uses the export's existing UIWindowScene lifecycle. The form
persists only public CA/configuration and usernames in protected app storage,
excluded from backup. Passwords are never encoded into settings. The native
client makes no remote shell requests and sends no application bytes after
SUBSCRIBE. There is no plaintext, hostname bypass or accept-any-host-key mode.

## Verification evidence on this Mac

Toolchain: macOS 26.5.1/arm64, Xcode 26.2 (17C52), Swift 6.2.3, iPhoneOS 26.2 SDK,
iOS 26.3.1 simulator runtime, Git LFS 3.8.0. Python tests use the ignored
`.week7-local/venv` with Python 3.13; the real board rehearsal uses the available
`python3` CLI and standard-library server. New temporary test PKI and owned
server processes are cleaned up; those host/simulator tests contacted no
institutional accounts. The subsequent physical tests used the operator's
authorized campus and board accounts as recorded above.

| Check | Result and evidence |
| --- | --- |
| Import provenance | `IMPORT_OK`: 3,480 files / 1,470,729,976 bytes before edits; LFS fsck passed. `.week7-local/evidence/import-baseline.txt`, `lfs-fsck.txt`. |
| Full native suite | `swift test --package-path ios-visualizer/Week7Native`: **54 passed**, 0 failed. `.week7-local/evidence/swift-final.txt`. |
| Existing and export Python suite | `.week7-local/venv/bin/python -m pytest -q`: **246 passed**, 4 skipped, 49 subtests. `.week7-local/evidence/python-final.txt`. |
| Reproducible export integration | **18 tests passed**, including compiled C++ lifecycle/layout/display harness, patch upgrade/idempotence and rejection of broken Xcode wiring. Included in the Python total. |
| Actual Python board/native interoperability | **100 ordered unique results**, IDs `1:7:0` through `1:7:99`, native SSH→SSH→TLS; board accepted 100 / subscribers 1 with zero duplicates, rejections, drops, stale or disconnected results. Included in the Swift total; `swift-python-board-green.log`. |
| Negative/lifecycle tests | Both wrong SSH pins, wrong password/CA/hostname, expired leaf, invalid subscription/result schema, prefix/body/idle deadlines, reconnect, multiple address candidates, credential revocation and stop during pending/live work. Included in the Swift total. |
| Actual Unity Debug and Release apps | Both `xcodebuild … -scheme Unity-iPhone -configuration Debug/Release … CODE_SIGNING_ALLOWED=NO`: **BUILD SUCCEEDED**. `xcode-final-debug.log`, `xcode-final-release.log`; all three `_Week7Start`, `_Week7CopyDisplay`, `_Week7Stop` symbols resolved in both app-bundled UnityFramework binaries. |
| Shared native UI simulator | **1 UI test passed**, including blank-setup rejection and password clearing on background. `native-ui-final.log` and the matching `.xcresult` under `.week7-local/PreviewDerivedData/Logs/Test/`. Settings were also visually inspected in landscape. |
| Native iOS transport runtime follow-up | **26 tests passed**, zero failures, inside iOS 26.3.1 simulator: two-hop/direct SSH, verified TLS, wrong trust/password/hostname, expired leaf, framing, deadlines, reconnect and cancellation. `ios-transport-simulator-final.log`; `.xcresult` in `~/Library/Developer/Xcode/DerivedData/Week7NativePreview/Logs/Test/`. |
| Native UI follow-up | **1 UI test passed again**, including blank setup and password clearing on background, using the Library build location. `ios-ui-continuation-final.log`; matching `.xcresult` alongside the transport result. |
| macOS transport follow-up | **27 tests passed**, zero failures after adapting test PKI loading. `transport-macos-fixture-adaptation.log`; production package source was unchanged. |
| Simulator fixture safety | Twelve unique CAs/leaves; ten valid chains; two expired and twelve unrelated-CA rejections; expected hostnames/key matching; 0700 directories/0600 files; foreign content preserved and symlink output rejected. `ios-test-pki-verification.json`. |
| Fixture bundle isolation | All twelve disposable server keys reside only in the XCTest bundle under the simulator preview host's `PlugIns`; neither actual Unity Debug nor Release app contains fixture resources or test bundles. `ios-fixture-bundle-audit.json`. |
| Final provenance/bundle audit | Exactly 3,476 baseline files unchanged and four reviewed imported source/configuration edits. Both app bundles retain the native bridge, correct display/encryption metadata and no PFX/P12. `import-final-delta.txt`, `app-verification.json`; final LFS fsck passes. |
| Independent whole-change review | No remaining high/medium findings. Earlier callback/candidate/deadline/credential/layout/reapply findings were fixed with regression tests; a README table formatting issue was corrected. Separate follow-up fixture/generator/Xcode review found no actionable issues. |
| Initial device/signing discovery, September 14 | `xcrun devicectl list devices`: **No devices found**. `security find-identity -v -p codesigning`: **0 valid identities**. Superseded by the signed physical installation above. |

Full logs and Unity builds remain in the ignored `.week7-local` directory on this
Mac; follow-up simulator products/results are under the Library path above.
They are local evidence, not a claim of remote hardware acceptance. Imported
Unity/native dependencies emit deprecation and unavailable original debug-path
warnings; the original vendor files were not broadly refactored.

## Exact next human actions

1. **Completed September 15:** Apple sign-in/team selection, device pairing,
   Developer Mode, signing, installation and developer trust. The actual app
   launched and the operator confirmed **Week 7 Connect** is visible.
2. **CA transfer and first physical connection completed September 15:** the existing public
   Week 7 CA is in the actual app's storage and passed phone readback verification.
   Its SHA-256 is
   `4dfba4905c171e68c3623dbc952154149076ed89004b85d475e858cc550760ec`.
   The app displayed the verified CA, subscribed and counted 100 synthetic
   results; a fresh September 16 login and clean 100-result repeat also passed.
   **Final updated app also verified September 16:** after the operator fixed
   keyboard input and clicked Connect, the app subscribed and received all 100
   results, including a live OPEN label. For a later reconnect, open **Week 7
   Settings**, verify board user `xilinx`
   and jump user `yanjie`, enter the passwords, and Connect. After a fresh
   **Subscribed / Received: 0**, start the mock
   immediately within the 30-second initial grace. Capture a clean repeat;
   do not start while Connecting. For future devices, Files import remains
   the normal setup path.
3. When Windows and ESP32 are available, stop competing subscribers. Check the
   existing board service and start the Windows BLE
   bridge per the [Week 7 runbook](week7-runbook.md), then power/pair the ESP32
   dummy firmware. After Subscribed, capture 100 unique results. Pass: app count,
   board/Windows trace IDs and REST/FIST/OPEN/POINT mapping agree; no malformed
   or stale label appears. Save observed Phone evidence and board/bridge logs.
4. Interrupt and restore network access, then perform an observed lock/return
   trial. Expected: the app clears the live result, stops its channels and
   forgets passwords when deactivated. Enter passwords and Connect again;
   fresh subscription/results must resume without an old-generation label.
   Record this physical result separately; screen-lock recovery is still pending.
5. Have the authorized owner review/revoke the previously imported Unity upload
   token if it was active. Obtain original Unity source for a future source-level
   integration if desired; it is not required to test this native-export build.

These are the remaining physical/account/private-input actions. No routine
coding approval is pending. App-owned campus authentication and real Phone TLS
have now succeeded on multiple explicit sessions, including the final updated
app. Physical network-fault/lock
recovery, camera/ARKit behavior and
complete ESP32→BLE→Windows→Ultra96→iPhone acceptance remain unverified.

## Historical import and Mac handoff

The following preserved report describes the import before native integration.
Its statements that integration/builds were pending are historical.

The user requested a clearer name for the teammate's `unity/` folder, a commit
and push, and an autonomous GPT-6 Mac prompt for work while they sleep. This task
packages that handoff; it does not claim an iOS build or start physical tests.
No PDF was created or changed.

Start with [the copyable Mac execution prompt](week7-mac-agent-prompt.md) and
[the imported iOS delivery](../ios-visualizer/README.md). Earlier communications
implementation and physical evidence remain in the
[September 7–9 continuation](week7-continuation-report-2026-09-07.md).

## Git and provenance

Initial state in `D:\LetThemCook`: branch `main`, HEAD and fetched `origin/main`
both `4eb30c63c0e1dc39408296ae1c64a4d321264211`; only `unity/` was untracked.
The earlier feature branch had already been merged into main. The user explicitly
authorized this delivery commit and push.

The original delivery contained **7,250 files / 1,471,799,877 bytes**. All originals
were copied outside Git and compared byte-for-byte before changes:
`D:\LetThemCook-builds\ios-visualizer-import-20260914\original-unity`.
The adjacent private original manifest and sanitization log preserve provenance.
Do not publish that unsanitized backup.

The published baseline is **3,480 imported files / 1,470,729,976 bytes**, plus
README, SHA-256 inventory and verifier. **275 files / 705,180,769 bytes** use Git
LFS; 19 executable modes are required for macOS scripts/native build tools.

## Decisions and reasons

| ID | Decision | Reason / consequence |
| --- | --- | --- |
| IOS-01 | Rename root `unity/` to `ios-visualizer/`, export to `xcode-export/`, reference files to `reference/` | States platform and artifact type, distinct from `phone/unity/`. Internal Xcode relative paths stay intact. |
| IOS-02 | Preserve the full native export and its generated compiler/dependency inputs | Original Unity Editor source was not delivered. Dropping IL2CPP, Data, Libraries or frameworks would remove available Mac build inputs. |
| IOS-03 | Use Git LFS for files >=5 MiB and binary files >=64 KiB; preserve baseline bytes with `-text` | UnityRuntime is 239,610,632 bytes, above the normal GitHub blob limit. LFS hydration and SHA-256 checks expose incomplete downloads. |
| IOS-04 | Exclude the PFX private key, Apple metadata, Xcode user state and personal signing screenshot; retain originals privately | Publication does not require credentials or teammate account state. The old Phone server cannot start unchanged without its key. |
| IOS-05 | Replace the old password with `REMOVED` in reference C#, serialized scene and generated metadata, preserving seven-byte length | The credential was duplicated in app data. Removing only the PFX or editing only the reference is insufficient. Mac runtime validation remains necessary. |
| IOS-06 | Clear eight teammate signing-team values while retaining automatic signing | The Mac must use the user's existing authorized identity; teammate provisioning does not automatically transfer. |
| IOS-07 | Retain the reviewed public certificate as reference only | Self-signed localhost certificate is not the existing Week 7 board CA. |
| IOS-08 | Preserve the board protocol and require a compatible Phone TLS client | Teammate code is a TLS server on 5005 using newline strings. Port changes alone cannot fix roles/framing. Only board TCP22 is externally reachable. |
| IOS-09 | Mac agent decides implementation details and continues all independent work while user sleeps | Explicit user autonomy supersedes routine approval checkpoints. True account/device prompts become recorded actions without blocking unrelated work. |
| IOS-10 | Prefer original Unity source if available; investigate a documented native export adapter otherwise | Detached C# edits cannot update generated app code. A native diagnostic fallback proves its own path, not teammate Unity UI acceptance. |
| IOS-11 | Future Mac work uses a `codex/ios-visualizer-*` branch, cohesive commits and pushes | Overnight integration remains reviewable without automatically merging a large implementation to main. |
| IOS-12 | Shorten the Mac prompt and reference existing technical documentation | User requested a shorter prompt after checking official OpenAI guidance. Keep the goal, context, constraints, autonomous decisions, evidence and stopping criteria; let the agent choose implementation steps. |

No new design approval is pending. These decisions supplement the 35 existing
communications/security decisions without rewriting physical acceptance.

The compact prompt revision follows OpenAI's
[GPT-6 guidance on prompts and persistence](https://learn.chatgpt.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
and [Codex best practices](https://learn.chatgpt.com/guides/best-practices), checked
2026-09-14. Technical constraints remain in this report, the import README and
linked runbooks. The revision changes documentation only; validation consists of
reviewing retained requirements, checking referenced paths and `git diff --check`.

## Inspection findings

- Unity **6000.5.10f1** Xcode/IL2CPP export, **iOS 15+, arm64, iphoneos**.
  Original `Assets/`, `Packages/`, `ProjectSettings/` are absent. Simulator support
  and actual Xcode compatibility remain untested.
- Reference and generated `Assembly-CSharp.cpp` implement a Phone TLS server on
  all interfaces:5005 with newline reads, no subscription, unbounded queue/lines,
  and incomplete active-client cancellation/lifecycle behavior.
- The PFX was decoded locally and confirmed to contain a private key matching
  the public self-signed `CN=localhost` certificate. Three password occurrences
  were sanitized. Bounded scans found no other copies of raw private key bytes,
  private PEM headers or additional common credential-token patterns. This is
  not a general security guarantee for all third-party binaries.
- Generated diagnostics retain original source paths and third-party licenses.
  No provisioning profile was found. Ignores exclude future PFX/P12/private-key/
  provisioning files and caches while retaining the required IL2CPP `build/` input.

## Verification and delivery

- `python ios-visualizer/verify-import.py`: **PASS**, all 3,480 baseline file sizes
  and SHA-256 values match. Six verifier cases pass: valid input, same-length
  corruption, truncation, unhydrated LFS pointer, missing file and escaping path.
- Independent staged-content audit: **PASS**, every baseline path is staged;
  every normal blob and every LFS-backed file matches its manifest hash/size;
  all 19 executable modes are `100755`. The 275 LFS paths reference 247 distinct
  objects. Largest ordinary imported Git blob: 5,041,340 bytes.
- Staged import scan: old password absent, no private-key containers or private
  PEM markers, no Apple archive metadata or Xcode user-state files.
- Independent review: **no actionable findings**. All 704 Xcode `SOURCE_ROOT`
  file references resolve after renaming; compiler inputs remain included;
  symbol scripts retain LF endings. Actual iOS compilation was not available.
- **22 local documentation links** resolve; first-party staged whitespace check
  passes. Imported vendor whitespace is preserved instead of reformatted.
- Existing communications runtime was not changed, so its historical test-suite
  results are not presented as a new run. Import checks do not certify app
  correctness.

Delivery commit **`e49c7777908a84c8e3a962de8503217d2829e979`** was pushed to
`origin/main`. Git LFS reported **247/247 distinct objects, approximately 698 MB,
uploaded successfully**; the Git push completed with exit 0. A subsequent remote
branch query matched the delivery commit, the working tree was clean, and
`git lfs fsck` passed. This report update is a follow-up documentation commit on
the same branch. No iOS build or physical result is implied by publication.

## Next work and remaining physical acceptance

Execute the [Mac prompt](week7-mac-agent-prompt.md). It covers environment/LFS
checks, framed TLS client integration, Phone-owned SSH via board TCP22, build and
signing automation where authorized, negative tests, bounded queues/lifecycle,
independent review, decision logging and an exact next-action report. Use the
actual Mac checkout location; Windows paths and credentials are not automatically
available there.

Historical actual iPhone acceptance used Python/iSH: a clean 100-result capture,
a 6,100-result soak with one callback-generation discard, and controlled local
forward recovery. **Unity app acceptance remains pending.** Screen-lock recovery
is **pending, not passed**; its final Phone capture is uncollected. Do not claim
the iSH tunnel survives switching to foreground Unity.

Eventual human actions may include supplying original Unity source if unavailable,
signing/Apple account/Keychain consent, Phone trust/unlock/Developer Mode, VPN MFA,
ESP power/reset and observed lock/background tests. The Mac agent must finish
everything independent of those and leave short steps, expected output, evidence
locations and pass criteria. No physical tests were started during this import.
