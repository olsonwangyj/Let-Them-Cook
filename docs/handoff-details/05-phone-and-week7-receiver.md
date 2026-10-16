# Detail chapter 5: Phone client and the Week 7 receiver

> This is a detail chapter of the hand-off document [`../communications-handoff.md`](../communications-handoff.md). It was checked against local `main` (commit `dc582c7`, which was `25fe4e4` before the history rewrite described in hand-off 6.2; same files) on 2026-10-14, and updated the same day for the owner's rules and the owner's proposed direction recorded in hand-off sections 3.1, 7, 8 and 13. On the evening of 2026-10-14 it was updated again for protocol version 3, on the local branch `comms/protocol-v3` (code commits `a34c467`, `57a3fbd`, `a4b907b` and `3b94990`; hand-off 6.2 and 6.5). All version-3 phone-side code changes are in `57a3fbd`; the board-side result rules came in `a34c467`; `a4b907b` and `3b94990` changed no phone code. The only later phone-side code change is the Linux build fix `6583f9d` (2026-10-15); `15de82e` and the gating commits changed no phone code. On 2026-10-15 every line citation was re-checked against `3b94990`, and citations into other documents against their working-tree versions. On the afternoon of 2026-10-15 it was updated for that day's commits up to `d582ce6`: the Swift package now compiles and passes its tests on Linux (`6583f9d`), the C# reference compiles in full and its self-test passes, and movement gating (`5d2e52f`) changes nothing on the phone except how many results arrive. Every line citation was re-checked against `d582ce6`. A later check that afternoon found that the Linux test command needs `ios-visualizer/reference/` beside the copied package. A review early on 2026-10-16 (+08:00) found that the command in this chapter still mounted only the package; it was corrected and rerun in full at `4c6ab4c`, which changed no phone file after `d582ce6` (72 tests, 0 failures; see "How to run and verify"). The same review corrected what gating means for the phone (laptop commands still give results while both gloves are still) and the glove module's decision timing. On 2026-10-16 (+08:00) hand-off 6.3 steps 3 and 4 ran on the owner's Mac (a separate clone from the Windows laptop, at `e555f77`) as far as an unsigned build, and this chapter was updated for that run: `swift test` passed 73 tests on macOS; the `NativePreview` app built for the iOS Simulator and its two test schemes passed (34 transport tests, 1 UI test); `patch_export.py` and `configure_xcode.py` changed nothing; the stale origin hash in the export's `Package.resolved` was replaced, so that Xcode keeps the tested pins; and the Week 7 export then built unsigned for an iOS device. No Swift source changed. Nothing was signed, installed on the iPhone or run on hardware. Status words follow hand-off 6.5: **verified** = run or measured (the place is named); **built** = compiled and tested on the laptop only; **compiled and tested on Linux (72 tests) and macOS (73 tests), built for iOS; not installed** = the status of the Swift package since 2026-10-16 (see "Build status of the Swift and C# code"); **written, not compiled** = no compile of the current version is recorded (`CommsPhoneReceiver.cs`; until 2026-10-16 also the `#if os(iOS)` Swift code and `NativePreview`); **provisional** = waits for a teammate's answer. Nothing of version 3 has run on the Ultra96, on the iPhone, or with both gloves together. `comms/protocol-v3` was pushed to the fork on 2026-10-16, and its code-only counterpart `comms/protocol-v3-team` is the team pull request #19, open and not merged (hand-off 6.2). The `Package.resolved` fix and the documents of the Mac run were not pushed when this chapter was updated. Interface shapes and teammate dates in this chapter are proposals until the teammates confirm them. The code is the source of truth: where this chapter and the code disagree, follow the code.

## Purpose and boundaries

- This chapter covers the path from the board's result gateway (board loopback `127.0.0.1:9999`) to the iPhone screen, and the receiver built for the Week 7 demo.
- The current phone client is the Swift package `ios-visualizer/CommsNative`. It dials out from the iPhone itself. It listens on no port and accepts no incoming connection. The route:

  ```text
  iPhone --TCP--> stujump:22 (first SSH layer) --direct-tcpip--> Ultra96:22 (second SSH layer) --direct-tcpip--> board loopback 127.0.0.1:9999 (TLS)
  ```

- The phone does not get results from the laptop. The `INGEST_ACK` the laptop receives shows only that the board accepted the input. It does not show that the phone received a result. Right after `demo.py` prints `CAPTURE PASSED` and `Phone expected increase`, it states that this count holds only while the board runs the built-in dummy model and that phone receipt is not checked there (`demo.py:214-218`).
- What Communications delivers here. The installed Week 7 build delivers three things: the connection status, the latest result (`gesture` and `result_id`), and the number of distinct results accepted in the current session, as four lines of text that the Unity main thread polls every frame. This text is a status display: it holds only the latest result, so results that arrive between two polls can be lost. The source on `comms/protocol-v3` adds, since 2026-10-14 (compiled and tested on Linux in a Swift 6.1 container since 2026-10-15; compiled and tested on macOS and built for iOS on 2026-10-16; not installed): the received confidence on line 3, and a fourth C function, `CommsNextResult`, that hands the game results one at a time from a bounded queue (see "Per-result function `CommsNextResult`" below and hand-off document section 7.3). The function is the owner's direction of 2026-10-14, final when Jie Ling confirms; its queue limits are provisional.
- Communications ends at these bridge functions. It passes every result through as it is and does not merge, split, filter or reinterpret results (hand-off document section 3.1). Mapping labels to game actions, cooldowns, repeated firing, handling of low confidence, and every script in `vis/` are Jie Ling's work. The label names, how often a label is produced, and whether several identical labels in a row mean one action or several are for Wen Ree and Jie Ling to agree between themselves.
- "Week 7 receiver" means the combination of two things: the `CommsNative` Swift client on the iPhone, and the bridge in the Unity export project `ios-visualizer/xcode-export/` that calls `Week7Start`, `Week7CopyDisplay` and `Week7Stop`. A patch script produced that bridge by rewriting four methods in the generated code. The bridge only writes four lines of text into a TextMeshPro label. It never triggers a game action. Names in it that contain `week7` stay unchanged.
- Movement gating (2026-10-15, `5d2e52f`; built, not yet run on hardware; [detail chapter 2](02-firmware.md)) changes nothing on the phone. No phone-side message, field or limit, and no Swift or C# code, changed. The board's result gateway (port 9999) is unchanged; only the laptop-to-board ingest side got the 600 s idle limit and idle eviction ([detail chapter 4](04-ultra96-service-and-certificates.md)). A gated glove sends samples only while its movement detector reports MOVING, and the board produces results only for the samples and laptop commands it receives. The phone therefore gets fewer results. While both gloves are still, only the `cmd:` results of laptop commands arrive (`ultra96/server.py:331-336`), because commands do not go through the glove module (hand-off 4.2). See "Known limits" for what that looks like on the screen.
- `phone/receiver.py`, `phone/unity/*.cs` and `laptop/phone_simulator.py` are reference and diagnostic subscribers. Each needs a separate SSH local forward on the same machine (default `127.0.0.1:19999`). None of them is the receiver deployed on the iPhone.
- `phone/ish_control.py` is a maintenance script for the iSH route. That route is abandoned (the `archive/runbooks/` row of the Archive table in `docs/README.md`).
- V1 uses the jump-host route, which was verified on site. The direct-connection switch `useJump` in the code has been used only in loopback tests and was not verified on site.

### Interfaces with teammates

This chapter does not repeat the interface list. For the model entry and exit points requested from Wen Ree, and for the calling method given to Jie Ling, section 7 of the hand-off document (7.2 and 7.3) is authoritative; who does what at each hand-over is the table in hand-off section 3.1. Communications needs no API from the game. The three C functions `CommsStart`, `CommsCopyDisplay` and `CommsStop` exist in the source since the rename of 2026-10-08; the installed Week 7 build was made from the earlier `Week7Native` source (last changed in `618c2ee`), which exports the same three functions only under their Week 7 names, `Week7Start`, `Week7CopyDisplay` and `Week7Stop`; the binary was not inspected. The game can follow the Week 7 receiver as an example. The rest of what the game needs from Communications is in the source since 2026-10-14: the per-result function `CommsNextResult`, the received `confidence` value, and accepting model labels (hand-off 6.5, D8 and D14). Since 2026-10-15 it is compiled and tested on Linux in a Swift 6.1 container (72 tests). On 2026-10-16 it passed its 73 tests on macOS on the owner's Mac, built for the iOS Simulator, and built unsigned for an iOS device inside the Week 7 export (hand-off 6.3, steps 3 and 4; see "Build status of the Swift and C# code"). It reaches a phone only after the app is signed, built and installed; that is still to do.

Division of work at the phone-to-game hand-over (the owner's proposal of 2026-10-14, final when Jie Ling confirms; hand-off 3.1 and 7.3): Jie Ling does everything in Unity and the iOS build on their own Mac and iPhone: the C# that calls the Communications functions (pushed to `vis/`), the game logic, exporting the project, adding `CommsNative` to the Xcode project, building, and installing the app, all before the integration session on Tue 10-20. olsonwangyj pushes `CommsNative` (with `CommsNextResult`) to the team repo (`ios-visualizer/CommsNative`; since 2026-10-16 it is in the team pull request #19, not merged), sends short steps for adding it to the Xcode project, and helps whenever something goes wrong. No export is pushed or passed around. Teammates deliver code by pushing it to the team repo on GitHub, not over Telegram (the owner's rule). Patching the generated code of an export, as the Week 7 receiver did, is no longer used.

This chapter keeps only the technical facts tied directly to the phone code:

- The rules a caller of the C functions must follow: see "Caller rules" under "Cautions and known limits".
- The fields available from the four lines of text: see "Display text" under "Data formats and constants". The text is for status and testing, not game input.
- The per-result function: see "Per-result function `CommsNextResult`" under "Data formats and constants".
- The source accepts version-3 results with any well-formed model label and a confidence from 0 to 1. The installed Week 7 app still accepts only results of version 1 or 2 with the 4 dummy labels and confidence 1, so a version-3 result or a model label makes it disconnect with a terminal error. See "Extension point: model labels and real confidence".
- A search of `vis/Assets/Scripts` (2026-10-14, evening; repeated at `d582ce6` on 2026-10-15) finds no `CommsStart`, `CommsNextResult`, `Week7Start` or `DllImport`. The Week 7 call sites come from editing the C++ that IL2CPP generated, and they apply only to that one export.

## Components and files

`CommsNative` has three modules:

| Module | Responsibility | Dependencies |
|---|---|---|
| `CommsCore` | Building and validating frames and messages; the display state machine and the per-result queue. No networking, no UIKit | Foundation only |
| `CommsTransport` | Owns the whole connection: two SSH hops, direct-tcpip, TLS, SUBSCRIBE, deadlines, error classification, retries, password lifetime | `CommsCore`; NIOCore, NIOPosix, NIOTLS, NIOSSH, NIOSSL, Crypto |
| `CommsBridge` | Hard-coded trust values; the setup screen; storage of public settings; foreground and background handling; the C functions exported to Unity | `CommsCore`, `CommsTransport`; system frameworks UIKit, CryptoKit, Security (Apple); on Linux test builds swift-crypto's `Crypto` in place of CryptoKit, and no Security (`Package.swift:24-25`, `Configuration.swift:2-10`) |

File by file:

| File | Responsibility |
|---|---|
| `ios-visualizer/README.md` | Directory description and the four C functions. Line 3 says the export project is not in the repository; that holds only for the team repo. Lines 11 and 26 say the installed Week 7 build uses the `Week 7 Connect` button and session `week7-demo` and cannot read version-3 results; line 13 gives the build status of the version-3 Swift changes |
| `ios-visualizer/NATIVE-INTEGRATION.md` | Tests, preview and integration steps on a Mac, the source test on Linux, the C functions for Unity (with `CommsNextResult` and its C# declaration), and how to observe the installed app |
| `ios-visualizer/CommsNative/Package.swift` | Package definition: platforms iOS 15 and macOS 13; three modules, three test targets; static library product `CommsNative` (entry target `CommsBridge`); exact versions of four dependencies: swift-nio 2.102.0, swift-nio-ssh 0.15.0, swift-nio-ssl 2.37.4, swift-crypto 4.5.2. Since `6583f9d`, `CommsBridge` also links swift-crypto's `Crypto`, on Linux only (`Package.swift:23-25`); the Apple builds compiled unchanged with the macOS and iOS SDKs on 2026-10-16 (Xcode 26.2). The manifest says `swift-tools-version: 5.10`, but the pinned dependencies need Swift 6.1 tools, so Swift 6.1 is the minimum |
| `ios-visualizer/CommsNative/Package.resolved` | Dependency lock, including the transitive dependencies swift-asn1 1.7.2, swift-atomics 1.3.1, swift-collections 1.6.0, swift-system 1.8.1. `swift test` on macOS and the `NativePreview` builds of 2026-10-16 used these versions. The Unity export keeps its own copy, which must hold the same pins (see the `ios-visualizer/xcode-export/` row) |
| `Sources/CommsCore/Protocol.swift` | Builds the SUBSCRIBE frame (version 1); validates SUBSCRIBED (version 1) and GESTURE_RESULT (version 3 only: 10 keys, the label rule, the confidence rule); `GestureResult`, with `confidence` and `nextResultJSON`; streaming frame decoder `FrameDecoder`; strict flat JSON parser `FlatJSON`. The version-3 changes are compiled and tested on Linux (Swift 6.1) and on macOS (2026-10-16), and compiled for iOS |
| `Sources/CommsCore/DisplayState.swift` | Locked display state: status text, latest result, count, deduplication table, generation, 2-second expiry, and the per-result queue behind `CommsNextResult` (`pendingCapacity` 32, `pendingLifetime` 2 s, `takeNext`, counters `pendingDropped` and `pendingExpired`). The queue is compiled and tested on Linux (Swift 6.1) and on macOS (2026-10-16), and compiled for iOS |
| `Sources/CommsTransport/SSHRoute.swift` | Route configuration type `SSHRoute`; defaults for ports, timeouts and retries in `TransportOptions`; failure reason texts |
| `Sources/CommsTransport/Credentials.swift` | Revocable password holder `CredentialVault`; password-free copy of the endpoints `RouteEndpoints` |
| `Sources/CommsTransport/Trust.swift` | Pinned host key comparison; password authentication (offered only once per connection); conversion between SSH channel data and a byte stream |
| `Sources/CommsTransport/Subscriber.swift` | Sends SUBSCRIBE after the TLS handshake completes; receives and validates frames; enforces the frame deadline |
| `Sources/CommsTransport/CommsClient.swift` | Builds the nested SSH and TLS; overall deadline; error classification; back-off retry; stop |
| `Sources/CommsBridge/Configuration.swift` | Hard-coded host names, host keys and CA fingerprint (`EnrolledTrust`); username validation; CA import validation; reading and writing the public settings. Since `6583f9d` it imports CryptoKit where it exists and swift-crypto's `Crypto` (the same `SHA256` API) otherwise, and imports Security only where it exists; without Security (Linux test builds) the `SecCertificateCreateWithData` parse is skipped and the fingerprint check alone admits the CA (`Configuration.swift:1-10,57-61`). The Apple branches (CryptoKit, Security, the `SecCertificateCreateWithData` parse) compiled and passed `ConfigurationTests` on macOS on 2026-10-16; the `.completeFileProtection` branch compiled for iOS the same day |
| `Sources/CommsBridge/DisplayMailbox.swift` | Assembles the state into four lines of text; copies only when the text changed; hands out the oldest waiting result for `CommsNextResult`; exports 7 C symbols: `CommsStart`, `CommsCopyDisplay`, `CommsNextResult`, `CommsStop` and the three `Week7*` wrappers. The 2026-10-14 changes are compiled and tested on Linux (Swift 6.1) and on macOS (2026-10-16); the two `#if os(iOS)` branches (`DisplayMailbox.swift:58-59,80-82`) are not compiled there, the `#else` branch at lines 60-61 is. The iOS branches compiled for iOS on 2026-10-16 (the `NativePreview` simulator build and the unsigned device build of the Week 7 export). The unsigned device build defines all 7 symbols in `UnityFramework` (`nm -gU`) |
| `Sources/CommsBridge/IntegrationController.swift` | Session management on the main thread: attaches the button, presents the form, creates and stops the client, handles foreground and background. The session ID `ltc-comms` is written here. The whole file is inside `#if os(iOS)`, so the Linux and macOS builds do not compile it. It compiled for iOS on 2026-10-16 (simulator and device builds), and the `NativePreview` UI test exercised it on the simulator |
| `Sources/CommsBridge/SetupViewController.swift` | Setup form: four input fields, jump host switch, CA import, Connect, Disconnect, password clearing. The whole file is inside `#if os(iOS)`. With its version-3 change (line 51) it compiled for iOS on 2026-10-16 (simulator and device builds), and the `NativePreview` UI test drove the form on the simulator |
| `Tests/CommsCoreTests/ProtocolTests.swift` | Protocol and framing tests: version-3 results with model labels and command identities; versions 1, 2 and 4 refused; the label rule (including a combining sequence and full-width letters); confidence values in range and out of it; `nextResultJSON` key order and exponent-form confidence; fields, types, uint32 boundary values, duplicate keys, malformed JSON, Unicode session IDs, split and coalesced frames, no resynchronisation after an invalid prefix. 13 tests; passed on Linux (Swift 6.1) and on macOS (2026-10-16) |
| `Tests/CommsCoreTests/DisplayStateTests.swift` | Display state tests: 2-second expiry, deduplication, generation, eviction at 4096, time ordering, concurrent duplicate callbacks counted once. Per-result queue: each result handed out once in arrival order; at most 32, the oldest dropped and counted; expiry 2 s after arrival; emptied by `begin` and `stop`, kept by reconnect statuses; a result that does not fit stays queued; concurrent accept and take. 15 tests; passed on Linux (Swift 6.1) and on macOS (2026-10-16) |
| `Tests/CommsBridgeTests/ConfigurationTests.swift` | Settings have no password field; private keys and unrelated certificates are rejected; username validation; legacy directory fallback rules; a CA in the legacy directory must also pass the fingerprint check. 6 tests; passed on Linux (Swift 6.1), where the fingerprint check alone rejects the unrelated certificate, and on macOS (2026-10-16), where the Security parse runs as well |
| `Tests/CommsBridgeTests/DisplayMailboxTests.swift` | Copies only changed text; a small buffer is not overrun; the exact four lines with the received confidence; `CommsNextResult` returns 0, minus (bytes + 1) for a null or small buffer, or the byte count, and writes nothing past the terminating 0; empty after stop; expiry after 2 s. 4 tests; passed on Linux (Swift 6.1) and on macOS (2026-10-16) |
| `Tests/CommsTransportTests/LocalPeers.swift` | Test fixtures: two SSH servers on loopback, one TLS server, throwaway certificates. The fixture result is a version-3 result with the model label `WASH` and confidence 0.93; the malformed fixture is `{"v":3}`. Its `#if os(iOS)` parts (the bundled fixture pool used by `NativePreview`) are not compiled on Linux or macOS; they compiled and served the transport tests on the iOS Simulator on 2026-10-16 |
| `Tests/CommsTransportTests/TransportTests.swift` | Transport tests: two hops (the received result's `result_id`, label `WASH` and confidence 0.93 are checked, `TransportTests.swift:18`) and direct (delivery only); a failing IPv6 candidate does not affect IPv4; cancellation closes all candidate connections; wrong host key (board and jump host); wrong password (identified per hop, no automatic retry); wrong CA; wrong host name; expired certificate; reception continues after idle; frame deadline; reconnect; stop. 26 tests; passed on Linux (Swift 6.1), on macOS and on the iOS Simulator (2026-10-16) |
| `Tests/CommsTransportTests/TrustTests.swift` | Password vault revocation, per-hop passwords, failure reason texts, exact host key comparison. 8 tests; passed on Linux (Swift 6.1), on macOS and on the iOS Simulator (2026-10-16) |
| `Tests/CommsTransportTests/PythonBoardTests.swift` | macOS only (`#if os(macOS)`, so neither compiled nor run on Linux): starts the real `python3 -m ultra96.server` (built-in dummy model), sends 100 version-3 samples and receives 100 results over two loopback SSH hops; checks that every label is a dummy label, confidence 1 and `request_id` null, and the board's `model_*` counters (100 samples to the model, 100 results, no errors, rejections or duplicates). 1 test; passed on macOS on 2026-10-16 (3.985 s), with `python3` from `PATH` (on the owner's Mac `/usr/bin/python3`, Python 3.9.6). Before that only its embedded Python ingest program had run, on the laptop against the real Python service (100 results) |
| `NativePreview/Sources/App.swift` | Simulator host app: calls `commsStart`, `commsCopyDisplay` and `commsStop` (the Swift functions behind `CommsStart`, `CommsCopyDisplay` and `CommsStop`; not `CommsNextResult`), polls every 0.05 s and shows the text. Built for the iOS Simulator on 2026-10-16 |
| `NativePreview/UITests/SetupTests.swift` | UI test `testSetupValidationAndBackgroundClearsPasswords` (1 test): an empty username is rejected; pressing Home clears the password fields. Passed on the iOS Simulator on 2026-10-16 (scheme `CommsNativePreview`) |
| `NativePreview/project.yml` | XcodeGen project definition: preview app, UI tests, transport tests that run on iOS. XcodeGen 2.46.0 generated the project from it on 2026-10-16 (the generated `CommsNativePreview.xcodeproj` is Git-ignored) |
| `NativePreview/tools/generate_test_pki.py` | Generates 12 sets of throwaway test certificates (8 valid, 2 with host name `wrong-host.internal`, 2 expired) into the Git-ignored `.comms-local/CommsFixturePKI`. Calls only `/usr/bin/openssl`; runs on a Mac (ran on the owner's Mac on 2026-10-16) |
| `ios-visualizer/tools/patch_export.py` | After hash checks, replaces the bodies of four `TlsDataReceiver` methods in the export project. Ran on the owner's Mac on 2026-10-16: `EXPORT_PATCH_OK: already applied`, no file changed |
| `ios-visualizer/tools/configure_xcode.py` | Links the local package `../CommsNative` into `UnityFramework`; clears the inherited symbol upload token and the `DevelopmentTeam` target attributes (not a `DEVELOPMENT_TEAM` build setting); edits `Info.plist`; adds a switch for symbol upload. Ran on the owner's Mac on 2026-10-16: it printed its success line and changed no file, because the export was already configured |
| `ios-visualizer/verify-import.py` | Checks the size and SHA-256 of the import baseline against the manifest; on a Git LFS pointer, suggests `git lfs pull`. Applies only to a freshly imported, unpatched project |
| `ios-visualizer/import-manifest.json` | Import baseline manifest from 2026-09-14: 3,480 files (including 2 under `reference/`), 1,470,729,976 bytes; also lists 19 files that need execute permission |
| `ios-visualizer/reference/TlsDataReceiver.cs` | Archived copy of Jie Ling's original receiver script: the phone acts as a TLS server listening on 5005 and reads lines. The certificate passphrase in the script was replaced with a placeholder (IOS-05). Not part of any build |
| `ios-visualizer/reference/teammate-localhost-cert.pem` | The public self-signed certificate that goes with that script. The Swift tests use it as the "unrelated certificate" (`ConfigurationTests.swift:16,75`) |
| `ios-visualizer/xcode-export/` | Jie Ling's Unity 6000.5.10f1 iOS export, 3,479 tracked files, 275 of them in Git LFS. Patched, and linked with `CommsNative`. Its `Unity-iPhone.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` still carried the origin hash of the old `Week7Native` package graph, so when Xcode first opened the project on 2026-10-16 it treated the file as out of date, resolved again and moved two transitive packages past the tested pins (swift-asn1 1.7.2 to 1.7.3, swift-collections 1.6.0 to 1.7.3). The committed file already listed the pins of `CommsNative/Package.resolved` (swift-asn1 1.7.2, swift-collections 1.6.0, the rest unchanged). The commit with these documents keeps those pins and replaces the stale origin hash with the one Xcode 26.2 computes for the current graph, so Xcode keeps the tested pins (hand-off 6.5, D32); only that one line changed. Scheme `Unity-iPhone`, configuration `ReleaseForRunning`, bundle identifier `com.CookingCompany.unityTutorial`, iOS 15.0 or later, device only (arm64), so it cannot be built for the simulator. On 2026-10-16 it built unsigned for a generic iOS device (see "How to run and verify"); it was not signed or installed |
| `phone/receiver.py` | Standalone Python subscriber, standard library only. Connects to the local forward port, accepts only version-3 results under the same label and confidence rules as the iPhone, and prints each result |
| `phone/ish_control.py` | Starts a temporary key-only sshd inside iSH and requests a reverse forward through the existing SSH master connection, for remote maintenance. The route is abandoned |
| `phone/unity/CommsPhoneCore.cs` | C# core with no Unity dependency: protocol validation (version 3; `GestureResult.Confidence`), frame reading and writing, certificate chain validation, freshness queue, reconnect loop. The whole file compiled on 2026-10-15: inside the self-test (PowerShell 7, 113 checks passed) and on its own at C# 7.0 against the .NET 10 libraries (0 errors, 0 warnings) |
| `phone/unity/CommsPhoneReceiver.cs` | Unity component (Android reference): runs the core in a background task; dequeues on the main thread and fires `UnityEvent<string>`. Needs Unity; checked by reading only |
| `phone/tests/test_receiver.py` | Python receiver tests: protocol (version 3 only, the label and confidence rules, command correlation), frames, deadlines, idle, close, real loopback TLS |
| `phone/tests/test_ish_control.py` | iSH script tests, all with stubs; no device contact. One test pins the config file name and host alias that already exist on the phone (`test_ish_control.py:40-46`) |
| `phone/tests/CoreSelfTest.cs` | Self-test of the C# core: version-3 contract, frames, freshness queue, TLS trust, reconnect and idle. Rewritten for version 3; passed 113 checks on 2026-10-15 (PowerShell 7) |
| `phone/tests/run_core_tests.ps1` | Compiles and runs the C# self-test with PowerShell 7 (`pwsh`). Ran on 2026-10-15: `PASS 113` |
| `tests/test_v3_events.py` | Version-3 stream and command correlation on the board; also passes each result through the Python receiver's `validate_result` |
| `tests/test_ios_export_patch.py` | Tests for the two export tools, including compiling and running the four replaced methods |
| `laptop/phone_simulator.py` | Stand-in subscriber on the laptop, for watching results when no phone is available |

(Paths in the table that start with `Sources/` or `Tests/` are under `ios-visualizer/CommsNative/`. `NativePreview/` is under `ios-visualizer/`.)

### Build status of the Swift and C# code

Swift (2026-10-15 on Linux, 2026-10-16 on the Mac): **compiled and tested on Linux (72 tests) and macOS (73 tests), built for iOS; not installed.**

Linux (2026-10-15):

- Where: the Docker image `swift:6.1` (Swift 6.1.3, Linux x86_64) on the owner's Windows laptop. `swift build --build-tests` and `swift test` ran on a copy of `ios-visualizer/CommsNative`, not in the working tree. The copy needs `ios-visualizer/reference/teammate-localhost-cert.pem` at `<parent of the copy>/reference/`: two `ConfigurationTests` read it from there (`ConfigurationTests.swift:15-16,74-75`). A copy of the package alone fails those two tests ("The file doesn't exist"; 72 tests, 2 failures, seen on 2026-10-15).
- Result: 72 tests, 0 failures, in six runs. By suite: `ConfigurationTests` 6, `DisplayMailboxTests` 4, `DisplayStateTests` 15, `ProtocolTests` 13, `TransportTests` 26, `TrustTests` 8. This covers the version-3 validation, `GestureResult.confidence`, the display text, the per-result queue and `CommsNextResult`.
- One fix was needed, `6583f9d`: CryptoKit and Security exist only on Apple platforms. `Configuration.swift` now imports CryptoKit where it exists and swift-crypto's `Crypto` (the same `SHA256` API) otherwise. It imports Security only where it exists, and on Linux skips the Security certificate parse; the fingerprint check still admits only the enrolled CA (`Configuration.swift:1-10,57-61`). `Package.swift` links `Crypto` into `CommsBridge` on Linux only (`Package.swift:23-25`). The Apple builds compiled unchanged on the Mac on 2026-10-16 (below).
- Not compiled on Linux: everything inside `#if os(iOS)` (all of `IntegrationController.swift` and `SetupViewController.swift`, the iOS branches of `DisplayMailbox.swift` and `Configuration.swift`, the iOS fixture pool in `LocalPeers.swift`); the Apple imports and the Security parse in `Configuration.swift`; `PythonBoardTests` (`#if os(macOS)`); and `NativePreview/`. Nothing was built for iOS or macOS on the Windows laptop: it has no Apple SDK. All of these compiled on the Mac on 2026-10-16.

Mac (2026-10-16): the owner's Mac, a separate clone from the Windows laptop, with `comms/protocol-v3` at `e555f77` checked out from the fork. Apple silicon, macOS 27.0.1, Xcode 26.2 (Swift 6.2.3), iOS SDK 26.2, iOS Simulator runtime 26.3 with an iPhone 17 Pro simulator, XcodeGen 2.46.0. The commands are under "How to run and verify".

- macOS: `swift test --package-path ios-visualizer/CommsNative` built the package for macOS (arm64) with the pins of `CommsNative/Package.resolved`: 73 tests, 0 failures. By suite: `ConfigurationTests` 6, `DisplayMailboxTests` 4, `DisplayStateTests` 15, `ProtocolTests` 13, `PythonBoardTests` 1, `TransportTests` 26, `TrustTests` 8, that is the 72 tests of the Linux run plus `PythonBoardTests`, which started the real Python board service and checked 100 unique results through both SSH hops. This compiled the Apple branches of `Configuration.swift` (CryptoKit, Security, `SecCertificateCreateWithData`), with no warning or error in the package's own sources. It does not compile the `#if os(iOS)` code.
- iOS Simulator: the `NativePreview` app built for the iOS Simulator (arm64, Debug). That compiled `IntegrationController.swift`, `SetupViewController.swift`, `DisplayMailbox.swift` and `Configuration.swift` for iOS with 0 errors and 0 warnings from those files: the first iOS compile of the `#if os(iOS)` code (including the iOS branches of `CommsStart` and `CommsStop` and the `.completeFileProtection` branch) since the changes of 2026-10-14 (version 3). On the iPhone 17 Pro simulator (iOS 26.3), the scheme `CommsNativeTransport` passed 34 tests (`TransportTests` 26, `TrustTests` 8, with the iOS fixture pool of `LocalPeers.swift` and the generated test PKI), and the scheme `CommsNativePreview` passed its 1 UI test (`SetupTests`, 17.6 s), which drives the setup form through `IntegrationController` and `SetupViewController`.
- iOS device: after the stale origin hash in its `Package.resolved` was replaced (see the `ios-visualizer/xcode-export/` row above), the Week 7 export built unsigned for a generic iOS device (configuration `ReleaseForRunning`, arm64). It ran the IL2CPP step, compiled `CommsNative` for iOS (the `CommsBridge` batch `Configuration.swift`, `DisplayMailbox.swift`, `IntegrationController.swift`, `SetupViewController.swift`) and linked `UnityFramework`. `nm -u` on `libGameAssembly.a` (the patched IL2CPP code) lists `_Week7Start`, `_Week7CopyDisplay` and `_Week7Stop` as undefined; `nm -gU` on `UnityFramework` shows that it defines those three and `_CommsStart`, `_CommsCopyDisplay`, `_CommsStop` and `_CommsNextResult`, and `nm -u` shows that it leaves no `Week7` or `Comms` symbol undefined. So the patched receiver's calls resolve to the `CommsNative` wrappers in the app's `UnityFramework`; nothing in the export calls `_CommsNextResult`. The build had 21 warnings, none in Communications sources.
- Not proven by the Mac run: signing, installing on the iPhone, any run on a device, BLE, Ultra96 or iPhone delivery, ARKit. No test calls `CommsNextResult` on iOS: `DisplayMailboxTests` ran on Linux and macOS only.
- Minimum toolchain: Swift 6.1, because the pinned dependencies need Swift 6.1 tools. The Mac therefore needs Xcode with Swift 6.1 or newer; the run of 2026-10-16 used Xcode 26.2 with Swift 6.2.3.

C# reference (2026-10-15):

- `phone/tests/run_core_tests.ps1` compiles `CommsPhoneCore.cs` together with `CoreSelfTest.cs` and runs the self-test. With PowerShell 7.6.7 (on .NET 10) it printed `PASS 113 C# contract/frame/freshness checks`, in four runs, and once more while this chapter was updated.
- `CommsPhoneCore.cs` was also compiled on its own as a library at C# 7.0 (`LangVersion` 7.0, target `net10.0`, warning `SYSLIB0057` suppressed as in the self-test script): 0 errors, 0 warnings. This compiled against the .NET 10 libraries, not against .NET Standard 2.1, the API level Unity uses, so an API missing from .NET Standard 2.1 would not show here. No C# change was needed.
- `CommsPhoneReceiver.cs` needs Unity. It was checked by reading only.
- One behaviour difference was noted: the Android reference empties its result queue on every automatic reconnect, while the iOS `CommsNextResult` queue keeps its results across one (they still expire 2 s after arrival). See "Precedent in the code" under "Per-result function `CommsNextResult`".

How to rerun both is under "How to run and verify".

### Files only on the fork, not in the team repo

The team repo `upstream/main` (`51593be`, Siqiang's glove sensor module of 2026-10-15, which touches only `hardware/`, on top of `5a004c6`, PR #18 merged on top of `880abba`, which was `ec398b6` before the history rewrite described in hand-off 6.2) contains `CommsNative/`, `NativePreview/`, `ios-visualizer/README.md`, `NATIVE-INTEGRATION.md`, `reference/teammate-localhost-cert.pem`, the whole of `phone/`, and `laptop/phone_simulator.py`. The following exist only on olsonwangyj's fork:

- `ios-visualizer/tools/patch_export.py`, `ios-visualizer/tools/configure_xcode.py`;
- `ios-visualizer/verify-import.py`, `ios-visualizer/import-manifest.json`;
- `ios-visualizer/reference/TlsDataReceiver.cs`;
- all 3,479 files of `ios-visualizer/xcode-export/`;
- `tests/test_ios_export_patch.py`;
- the whole of `docs/`. A teammate who clones the team repo therefore cannot see the design records cited in "Why it is designed this way".

`tests/test_ios_export_patch.py` also uses `git cat-file` to fetch the import baseline from repository history (`test_ios_export_patch.py:18-31`). It therefore runs only in a fork clone with full history.

The version-3 changes of 2026-10-14 (the phone side: `Protocol.swift`, `DisplayState.swift`, `DisplayMailbox.swift`, `SetupViewController.swift`, their tests, `phone/receiver.py`, `phone/unity/*.cs` and `phone/tests/`) and the Linux build fix of 2026-10-15 (`6583f9d`: `Package.swift`, `Configuration.swift`) are on the branch `comms/protocol-v3`; hand-off 6.2 records whether they have been merged or pushed. With the owner's approval of 2026-10-15, `comms/protocol-v3` was pushed to the fork on 2026-10-16 and the fork's `main` was fast-forwarded to it; both are at `e555f77` on the fork. The team repo still holds the version-2 phone code until the team pull request is merged. The branch `comms/protocol-v3-team`, rebuilt on 2026-10-15 from `upstream/main` (`51593be`) in commits `abaff6f`, `d2aa85a`, `09dc603` and `8dbcaf2`, with `44d0f71` added on 2026-10-16 (the code of `4c6ab4c` and the iOS notes of `4d97242`), holds the same `CommsNative`, `NativePreview` and `phone/` code without the fork-only files. It was pushed to the fork at `44d0f71` on 2026-10-16 and is the team pull request #19 (<https://github.com/B07-CG4002/Let-Them-Cook/pull/19>), open and not merged when this chapter was updated (hand-off 6.2). At `44d0f71` its `ios-visualizer/README.md` and `NATIVE-INTEGRATION.md` are the same as at `e555f77`: they give the Swift 6.1 minimum and the corrected Linux test command, and do not yet record the Mac run of 2026-10-16. Unless a later change to either file, such as the update for that Mac run, is copied onto the team branch as well, the pull request gives Jie Ling outdated status and requirements. Copying the update there needs the owner's go-ahead; it is still the owner's decision and has not been done. The `Package.resolved` fix of 2026-10-16 is in the fork-only `xcode-export/` and does not go to the team branch.

## Data formats and constants

### Route and ports

| Segment | Target | Port constant | Authentication | Identity check |
|---|---|---|---|---|
| TCP + first SSH layer (jump-host route) | `EnrolledTrust.jumpHost` = `stujump.comp.nus.edu.sg` | `jumpPort` = 22 | Password (jump host username and password) | Host key must equal `EnrolledTrust.jumpKey` |
| direct-tcpip + second SSH layer | `EnrolledTrust.boardHost` = `makerslab-fpga-35.ddns.comp.nus.edu.sg` | `boardPort` = 22 | Password (board username and password) | Host key must equal `EnrolledTrust.boardKey` |
| direct-tcpip + TLS | `127.0.0.1` (board loopback) | `servicePort` = 9999 | No client certificate | Chain to the imported CA; host name `ultra96.week7.internal`; validity period; TLS 1.2 minimum |

- Direct route (`useJump` off): TCP connects straight to `boardHost:22`, skipping the first hop. Everything else is the same. Not verified on site; V1 does not use it.
- The originator address of every direct-tcpip channel is fixed at `127.0.0.1:0` (`CommsClient.swift:172`).
- All server-initiated child channels are rejected (`CommsClient.swift:162-166`). The client requests no shell and no exec. It opens only direct-tcpip channels.
- Extended data in an SSH channel is a protocol error. Only ordinary channel data is forwarded (`Trust.swift:36-52`).
- Host names, both host keys and the CA fingerprint are hard-coded in `EnrolledTrust` in `Configuration.swift:14-20`. The app UI cannot change them.
- Ports cannot be changed either. The public initializer the app uses always takes the default `TransportOptions` (`CommsClient.swift:29-31`, `SSHRoute.swift:28-38`). The initializer that can inject ports is only for test fixtures.
- All clients share one single-threaded NIO event loop group (`CommsClient.swift:10`). All network callbacks run on that thread.
- TLS trusts only the imported CA, does full verification, and requires TLS 1.2 or later (`CommsClient.swift:86-93`).
- Before each connection starts, the client also checks that the board host name, board username and board password are not empty, and that the CA text is at most 65,536 bytes and does not contain `PRIVATE KEY` (`CommsClient.swift:84-85`). If a check fails, it reports `invalid connection configuration`.

### Frames

| Offset | Length | Type | Meaning |
|---|---|---|---|
| 0 | 4 | uint32 big-endian | Body byte count, 1 to 16,384 |
| 4 | N | UTF-8 JSON object | Body. No BOM, no trailing newline |

- The decoder buffers only one incomplete frame, at most 16,388 bytes (`Protocol.swift:130-131`).
- A length of 0 or more than 16,384 fails the decoder permanently. It does not resynchronise (`Protocol.swift:149-155`). The caller can only reconnect.
- When the connection drops, a half frame in the buffer is discarded and the event is handled as a connection close.

### Messages

| Message | Direction | Fields (exactly these; one extra or one missing is rejected) |
|---|---|---|
| SUBSCRIBE | phone to board | `v`=1, `type`=`SUBSCRIBE`, `session_id` |
| SUBSCRIBED | board to phone | `v`=1, `type`=`SUBSCRIBED`, `session_id` |
| GESTURE_RESULT | board to phone | `v`=3, `type`, `session_id`, `device_id`, `boot_id`, `seq`, `request_id`, `result_id`, `gesture`, `confidence` (10 keys) |

- The session ID is hard-coded in the app as `ltc-comms` (`IntegrationController.swift:74`). The `session ltc-comms` in the form's description line is a separate literal (`SetupViewController.swift:51`). To change the session ID, change both, then rebuild and reinstall the app.
- The SUBSCRIBE body is `{"v":1,"type":"SUBSCRIBE","session_id":"ltc-comms"}`, 51 bytes. The frame prefix is `00 00 00 33`.
- Protocol version 3 is the only version (since 2026-10-14, branch `comms/protocol-v3`; specification `docs/co-protocol-v3.md`). The subscription envelopes stay at `v` 1, because they never carried the packet version and did not change (hand-off 6.5, D5). Every result has `v` 3: the board sets it on command echoes and on model results alike (`ultra96/server.py:333,367`). A result with `v` 1, 2 or any other value is refused, and on the iPhone that is a terminal error. The installed Week 7 app is the opposite case: it accepts only versions 1 and 2 (see "Current deployment state").

GESTURE_RESULT field rules (`Protocol.swift:48-87`; compiled and tested on Linux, Swift 6.1, and on macOS):

| Field | Type | Allowed values |
|---|---|---|
| `v` | integer | 3 |
| `type` | string | `GESTURE_RESULT` |
| `session_id` | string | Equal to the configured session ID, Unicode scalar by scalar, with no normalisation |
| `device_id` | integer | 1 or 2 |
| `boot_id` | integer | 0 to 4,294,967,295 |
| `seq` | integer | 0 to 4,294,967,295 |
| `request_id` | null or integer | Always present. `null` for model results; for the echo of a laptop command, a uint32 greater than 0 that equals `seq` |
| `result_id` | string | `<device_id>:<boot_id>:<seq>` when `request_id` is null; otherwise `cmd:<device_id>:<boot_id>:<seq>`. Compared Unicode scalar by scalar |
| `gesture` | string | 1 to 32 Unicode scalars, each one of `A–Z`, `a–z`, `0–9`, `_`, `-` (`CommsProtocol.maximumGestureLength` = 32). The rule counts and checks Unicode scalars, not Swift `Character`s, so a combining sequence such as `E` + U+0301 is two scalars and fails. The model classes `PICKUPHOLD`, `PLACEDOWN`, `CHOP`, `WASH`, `THROW`, `FIREEXT` and the dummy labels `REST`, `FIST`, `OPEN`, `POINT` all pass. The phone does not know the label set |
| `confidence` | number | A JSON number token (never `true`, `false`, a string or `null`), finite, from 0 to 1 inclusive. `0`, `1`, `1.0`, `1e0`, `100e-2` and `-0` pass; `-0.01`, `1.0000001` and `2` fail; `1e999` already fails in the parser as not finite. The value is kept as a `Double` in `GestureResult.confidence` |

The same label and confidence rules are applied by the board before it sends a result (`ultra96/protocol.py:31-40`, see [detail chapter 4](04-ultra96-service-and-certificates.md)) and by the two reference receivers (see "Reference implementation constants"). Communications checks the shape of a result, not its meaning (hand-off 5, item 17).

Parser rules:

- Session ID: 1 to 128 Unicode scalars, none below U+0020 (`Protocol.swift:89-94`).
- Integers: only plain digit tokens, at most 10 digits, and the value must fit in uint32. `42.0`, `42e0`, `-0`, `042`, `+42` and quoted numbers are all rejected (`Protocol.swift:116-122`).
- At most 10 fields per object; a version-3 result has exactly 10. Duplicate keys are detected after escape decoding, and a duplicate is rejected (`Protocol.swift:202`).
- Values can only be strings, numbers or `null`. Booleans, arrays and nested objects are rejected (`Protocol.swift:206-211`). `null` is valid only for `request_id`.
- Numbers: the parser keeps the lexical token, so `42` and `42.0` stay distinct, and rejects a token that is not finite as a `Double` (`Protocol.swift:279-304`).
- A BOM before the body is rejected (`Protocol.swift:98-101`). Control characters inside strings are rejected. Unpaired surrogate escapes are rejected.
- Allowed whitespace: tab, line feed, carriage return, space.

### Timeouts, retries, capacities

| Constant | Value | Purpose | Location |
|---|---|---|---|
| `connectTimeout` | 10 s | TCP connect timeout; also the overall deadline from the start of the connection to receipt of SUBSCRIBED | `SSHRoute.swift:34`, `CommsClient.swift:96-100` |
| `frameTimeout` | 5 s | Wait for SUBSCRIBED after sending SUBSCRIBE; one frame from its first byte to its last | `SSHRoute.swift:35`, `Subscriber.swift:32,43,56` |
| Idle deadline after subscribing | none | No timer runs while no frame is in progress | `Subscriber.swift:41-43` |
| `retryMinimum` | 500 ms | Wait before the first retry | `SSHRoute.swift:36` |
| `retryMaximum` | 5 s | Upper limit of the wait. The wait doubles after each failure: 0.5, 1, 2, 4, 5, 5 s, and so on | `SSHRoute.swift:37`, `CommsClient.swift:210-212` |
| Retry count limit | none | Retries continue as long as the client is alive | `CommsClient.swift:208-212` |
| Retry wait reset | when a valid result arrives | Receiving SUBSCRIBED does not reset it | `CommsClient.swift:149` |
| Result retention | 2 s | 2 s after local receipt, the displayed result is cleared | `DisplayState.swift:141` |
| Deduplication table | 4,096 `result_id` values | Ring buffer; when full, the oldest entry is evicted | `DisplayState.swift:94-101` |
| Per-result queue capacity (`pendingCapacity`) | 32 results | When 32 wait and another result is accepted, the oldest is dropped and counted in `pendingDropped`. Provisional; compiled and tested on Linux and macOS | `DisplayState.swift:28,106-109` |
| Per-result queue lifetime (`pendingLifetime`) | 2 s from arrival on the phone | A waiting result is dropped and counted in `pendingExpired` once the latest observed time is 2 s or more past its arrival. Checked on every accepted result, every snapshot (`CommsCopyDisplay`) and every `CommsNextResult` call; a result that `accept` refuses does not trigger the check; no timer. Provisional; compiled and tested on Linux and macOS | `DisplayState.swift:29,105,145,158,166-173` |
| `CommsNextResult` buffer | 512 bytes (hand-off 7.3) | Allocated by the caller. The longest possible object (a 32-character label, a `cmd:` identity with the largest numbers, a 17-digit confidence) is under 150 bytes | hand-off 7.3 |
| CA file limit | 65,536 bytes | Checked at import, at load and before connecting | `Configuration.swift:49,89`, `CommsClient.swift:85` |
| Username limit | 128 bytes | Must not be empty; no whitespace or control characters | `Configuration.swift:38-43` |
| Week 7 display buffer | 2,048 bytes | Stack buffer in the generated code | `patch_export.py:112` |
| Preview app polling interval | 0.05 s | Only in `NativePreview` | `App.swift:38` |

### Error classes

| Class | Includes | What happens next |
|---|---|---|
| Terminal | Host key mismatch; password rejected; server does not offer password authentication; password empty; password already cleared; invalid configuration; invalid SSH stream data; TLS certificate verification failure (wrong CA, wrong host name, expired); any frame, JSON, field or session validation failure, including a result of version 1 or 2, a label that breaks the label rule and a confidence outside 0 to 1 | Status becomes `Disconnected: <reason>; correct setup and reconnect`. The client deactivates. The route and passwords are cleared. No retry. The user must enter the passwords again and tap Connect |
| Retryable | Connection closed; 10 s connection deadline; 5 s frame deadline; unclean TLS shutdown or a TLS shutdown failure; EOF or syscall error during the TLS handshake; EOF during additional certificate chain validation; every other error not listed as terminal (for example a DNS or TCP failure, or a refused direct-tcpip channel) | Status becomes `Disconnected: <reason>; retrying`. The displayed result is cleared. After the wait, the whole route reconnects from the start and sends SUBSCRIBE again. The passwords stay in memory and are reused |

Basis: `CommsClient.swift:186-212`. The class depends on the error type. In `TransportFailure`, `hostKey`, `password`, `invalidConfiguration` and `invalidData` are terminal. In `NIOSSLError`, everything is terminal except unclean shutdown, shutdown failure, EOF during the handshake, EOF during additional certificate chain validation, and a syscall error during the handshake (`CommsClient.swift:194-196`). `NIOSSLExtraError` (for example a host name mismatch) and `CommsProtocolError` are terminal. Every other type is retryable.

After a terminal error, `IntegrationController` still holds the deactivated client. So the button text stays `Communications Settings`, and when the form opens again the notice line reads `A session is active. Connect restarts it; Disconnect stops it.` (`IntegrationController.swift:63,81`, `SetupViewController.swift:97`). Entering the passwords again and tapping Connect creates a new client.

### All status strings

| Status text | When it appears | Location |
|---|---|---|
| `Disconnected` | Initial value after the process starts; the user tapped Disconnect | `DisplayState.swift:33`, `IntegrationController.swift:84` |
| `iPhone setup required` | `CommsStart` called on a non-iOS platform (macOS tests) | `DisplayMailbox.swift:61` |
| `Tap Communications Connect to configure this iPhone` | `CommsStart` has finished installing; not connected yet | `IntegrationController.swift:25` |
| `Connecting` | After tapping Connect; at the start of every reconnect | `IntegrationController.swift:67-68`, `CommsClient.swift:80` |
| `Subscribed` | A valid SUBSCRIBED arrived. It means only that the subscription handshake with the Ultra96 succeeded; it does not prove that results are flowing (that shows only as `Received` rising). The status stays `Subscribed` while no results arrive | `CommsClient.swift:146` |
| `Disconnected: <reason>; retrying` | Retryable error | `CommsClient.swift:208` |
| `Disconnected: <reason>; correct setup and reconnect` | Terminal error | `CommsClient.swift:202` |
| `Paused — return and connect again` | The app resigns active (screen lock, switch to another app, and so on) | `IntegrationController.swift:28` |
| `Stopped` | `CommsStop` was called | `DisplayMailbox.swift:79`, `IntegrationController.swift:102` |

All values of `<reason>` (`SSHRoute.swift:45-71`, `CommsClient.swift:200`):

| Reason text | Class |
|---|---|
| `SSH host key rejected` | terminal |
| `Board does not offer password authentication`, or the same with `Board` replaced by `Jump host` | terminal |
| `Board did not accept password authentication`, or the same with `Board` replaced by `Jump host` | terminal |
| `Board credentials are unavailable`, or the same with `Board` replaced by `Jump host` | terminal |
| `Board password is empty`, or the same with `Board` replaced by `Jump host` | terminal |
| `invalid SSH stream data` | terminal |
| `invalid connection configuration` | terminal |
| `connection deadline exceeded` | retry |
| `frame deadline exceeded` | retry |
| `connection closed` | retry |
| `SSH, TLS or protocol verification failed` | Shared by every error that is not a `TransportFailure`. Whether it is terminal or retried depends on the error type |

### Display state machine (`DisplayState`)

The queue effects in this table (the last part of each row, and `takeNext`) are in the source since 2026-10-14; since 2026-10-15 they are compiled and tested on Linux, and since 2026-10-16 on macOS (`DisplayStateTests`).

| Operation | Called by | Effect |
|---|---|---|
| `begin(status:)` | The user taps Connect | Generation +1; activate; clear the result; reset `Received` to 0; empty the deduplication table. Empty the per-result queue and reset `pendingDropped` and `pendingExpired` to 0 |
| `stop(status:)` | Install; resign active; Disconnect; tapping Connect (stops the old session first); `CommsStop` | Generation +1; deactivate; clear the result. `Received` is not reset. Empty the per-result queue without counting the discarded results; the two counters are kept |
| `accept(result, generation:)` | Each valid result | If accepted: record it in the deduplication table, `Received` +1, replace the shown result with this one, record the arrival time. Then drop expired queue entries, drop the oldest if 32 still wait (`pendingDropped` +1), and append the result with its arrival time |
| `clear(generation:, status:)` | Every connection status except `Subscribed`, including the terminal `…; correct setup and reconnect` | Clear the result, set the status. The deduplication table, the count and the per-result queue are kept; queue entries still expire |
| `setStatus(_, generation:)` | Only for `Subscribed` | Changes only the status; keeps the result and the queue |
| `snapshot()` | Each `CommsCopyDisplay` | Clears the result once it is 2 s old; drops expired queue entries (`pendingExpired` +1 each); returns status, result, count, `pendingCount`, `pendingDropped` and `pendingExpired` |
| `takeNext(capacity:)` | Each `CommsNextResult` | Drops expired queue entries, then returns `.empty`, `.needs(bytes + 1)` (the oldest result stays queued) or `.taken(bytes)` (the oldest result is removed). Builds the JSON under the lock, so the size check and the removal see the same result |

`clear` and `setStatus` take effect only while active and only when the generation matches (`DisplayState.swift:120,131`). `accept` rejects a result in these cases: not active; generation mismatch; time not finite; time earlier than the previous accepted result; already 2 s old measured against the latest time observed; `result_id` already seen (`DisplayState.swift:90-92`). A rejected result is not counted anywhere and never enters the queue, so the queue holds only results that passed de-duplication. Arrival times in the queue are in order, because `accept` refuses an earlier time, so expired entries are always at the front (`DisplayState.swift:166-173`).

When `Received` resets to 0: only in `begin()`, which runs after the user taps Connect in the form and the public settings save successfully. Automatic reconnects do not reset it. Resigning active does not reset it. `CommsStop` does not reset it. After the app process restarts, it starts from 0. `pendingDropped` and `pendingExpired` follow the same rule (`DisplayState.swift:65-67`).

### Display text

The text from `CommsCopyDisplay` is always four lines. In the source since 2026-10-14 (`DisplayMailbox.swift:14-18`; compiled and tested on Linux and macOS, where `DisplayMailboxTests` checks the exact four lines):

```text
Communications
<status>
<gesture>  |  <result_id>  |  confidence <received confidence>
Received: <count>
```

The installed Week 7 build shows older text. It was built from the Week 7 source before the rename to `Comms*` on 2026-10-08 (its button still reads `Week 7 Connect`, and it accepted version-2 results on 2026-09-28). In that source (`Week7Native`, from `33f8c7e` to its last change, `618c2ee` on 2026-09-28, which accepts versions 1 and 2) line 1 is `Week 7 • DUMMY inference`. The renamed source up to just before version 3 (`caf330e` to `c42b386`) had `Communications • DUMMY inference`; no installed build is known to come from it. In all of these, line 3 ends with the literal `confidence 1.0`, whatever the board sent. The screen of the installed app was not checked for this chapter.

- With no valid result, line 3 is `No live result`.
- The separator on line 3 is "two spaces, vertical bar, two spaces". A label cannot contain a space or `|`, so splitting line 3 on the separator is unambiguous.
- The confidence is the received value, printed with Swift's default formatting of a `Double` and not rounded: `1` and `1.0` both print as `1.0`, very small values print in exponent form, and a model's float32 0.93 arrives and prints as `0.9300000071525574` (hand-off 6.5, D17).
- The paused status contains `—` (U+2014), which is multi-byte in UTF-8. In the older texts, line 1 also contains `•` (U+2022).
- The text shows neither the queue for `CommsNextResult` nor its counters.

Fields available from these four lines:

| Field | Position | Notes |
|---|---|---|
| `gesture` | line 3, segment 1 | Any label that passed the label rule. With the board's built-in dummy model, and on every `cmd:` result, one of `REST`, `FIST`, `OPEN`, `POINT`, chosen at random |
| `result_id` | line 3, segment 2 | `<device_id>:<boot_id>:<seq>`; a command result is `cmd:<device_id>:<boot_id>:<seq>` |
| confidence | line 3, segment 3 | Source: the received value from `GestureResult.confidence` (`Protocol.swift:11`). Installed build: the literal `confidence 1.0` |
| `device_id` | only by parsing `result_id` | For an ordinary result, take the first segment. For a command result, drop the `cmd:` prefix first, then take the first segment (`Protocol.swift:63`). `CommsNextResult` gives it as its own key |
| status | line 2 | See "All status strings". `Subscribed` does not prove that results are flowing |
| `Received` | line 4 | Number of distinct results accepted since this Connect |

These four lines are a status display. Line 3 holds only the latest result and the next result overwrites it, so results that arrive between two polls can be lost: if `CHOP` and then `PLACEDOWN` arrive between two frames, the poller sees only `PLACEDOWN`, while `Received` still counts both. Comparing `result_id` stops a caller acting twice on one result, but it cannot recover an overwritten one. The game's actions are one-shot, so the game input is `CommsNextResult`, not this text (hand-off 4.6 and 7.3).

### C bridge

| Symbol | C signature | Exact semantics |
|---|---|---|
| `CommsStart` | `void CommsStart(void)` | Clears the memory of "text already delivered", so the next `CommsCopyDisplay` always returns the current text. On iOS it also queues an install action on the main queue: set the status to `Tap Communications Connect to configure this iPhone`, register the resign-active and become-active notifications, attach the button. It starts no network connection. If already installed, a further call only clears the memory. On a non-iOS platform it only sets the status to `iPhone setup required` |
| `CommsCopyDisplay` | `int32_t CommsCopyDisplay(char* buffer, int32_t capacity)` | Takes one snapshot and builds the four lines of text. If the text differs from the last delivered text and its UTF-8 byte count is less than `capacity`, it writes those bytes and a trailing 0, remembers the text, and returns the byte count (excluding the trailing 0). Otherwise it returns 0 and does not write to the buffer. It returns 0 when `buffer` is null or `capacity` is not greater than 1. It never returns a negative number |
| `CommsNextResult` | `int32_t CommsNextResult(char* buffer, int32_t capacity)` | Not in the installed app. Compiled and tested on Linux and macOS; built for iOS on 2026-10-16 (the unsigned Week 7 export build defines it, but that export never calls it). Takes the state lock only, never the display lock. First drops queue entries that have waited 2 s or more (counted in `pendingExpired`). If no result waits, it returns 0 and writes nothing. Otherwise it builds the compact JSON of the oldest waiting result. If `buffer` is null (whatever `capacity` is), or `capacity` is less than the byte count + 1 (including 0, 1 and negative values), it writes nothing, leaves the result at the front of the queue and returns −(byte count + 1), the capacity needed including the trailing 0. Otherwise it writes the bytes and a trailing 0, removes the result from the queue, and returns the byte count (excluding the trailing 0). It never blocks. Details in "Per-result function `CommsNextResult`" |
| `CommsStop` | `void CommsStop(void)` | Immediately sets the status to `Stopped`, invalidates the current generation (so every late callback has no effect) and empties the per-result queue, all before it returns. On iOS it also queues an uninstall action on the main queue: stop the client and clear the passwords, remove the notification observers, dismiss the form, remove the button |
| `Week7Start`, `Week7CopyDisplay`, `Week7Stop` | one-to-one with `CommsStart`, `CommsCopyDisplay`, `CommsStop` | Each only forwards to the matching `Comms*` function. The generated code in the Week 7 export calls these three names. There is no `Week7*` wrapper for `CommsNextResult`; the Week 7 export never calls it |

Basis: `DisplayMailbox.swift:10-95`, `DisplayState.swift:150-173`, `Protocol.swift:18-25`, `IntegrationController.swift:21-34,101-108`.

The symbols come from the static library `CommsNative`, which must be linked into `UnityFramework`. In an export whose C# already calls these functions but which is not yet linked with `CommsNative`, the Xcode build reports `Undefined symbol: _CommsStart` and similar; that is expected until `CommsNative` is added to the Xcode project (hand-off 7.3). The installed Week 7 build has no `CommsNextResult` symbol; a game build that calls it must link a `CommsNative` built from `comms/protocol-v3` or later. The unsigned device build of the Week 7 export of 2026-10-16, linked with the current `CommsNative`, defines all seven symbols in `UnityFramework` (`nm -gU`), and its patched code needs only the three `Week7*` ones (`nm -u` on `libGameAssembly.a`). The caller allocates the buffers; Week 7 uses 2,048 bytes for the text, and hand-off 7.3 proposes 512 bytes for `CommsNextResult`. The C# declarations are the same as in hand-off document section 7.3. They were derived from the `@_cdecl` signatures and have not yet been compiled in Unity. The symbols exist only in the iOS build. A call in the Unity Editor or on another platform throws, so call sites go inside `#if UNITY_IOS && !UNITY_EDITOR`. Hand-off document section 7.3 settles this; it is not a question for Jie Ling.

```csharp
[DllImport("__Internal")] static extern void CommsStart();
[DllImport("__Internal")] static extern int  CommsCopyDisplay(byte[] buffer, int capacity);   // returns the UTF-8 byte count, excluding the trailing 0; 0 means no change
[DllImport("__Internal")] static extern int  CommsNextResult(byte[] buffer, int capacity);    // byte count of one JSON object; 0 = nothing waiting; negative = -(capacity needed), nothing written
[DllImport("__Internal")] static extern void CommsStop();
```

### Per-result function `CommsNextResult` (in the source; compiled and tested on Linux and macOS, built for iOS; not installed)

The owner's direction of 2026-10-14, proposed to Jie Ling and final when Jie Ling confirms (hand-off 7.3 and 13). It was implemented in the Swift package on the evening of 2026-10-14, ahead of the Sat 10-17 plan, without a Swift toolchain (hand-off 6.5, D14). On 2026-10-15 it was compiled and its tests passed on Linux in a Swift 6.1 container (`DisplayStateTests` and `DisplayMailboxTests`, part of the 72 tests; see "Build status of the Swift and C# code"). On 2026-10-16 the same tests passed on macOS on the owner's Mac, and it was built for iOS: in the `NativePreview` app for the iOS Simulator and in the unsigned device build of the Week 7 export (hand-off 6.3, steps 3 and 4). No test calls it on iOS, it has never run on a phone, and it is not in the installed app. The owner pushes `CommsNative` with it to the team repo and tells Jie Ling (hand-off 6.4, by Sun 10-18). On 2026-10-16 it was pushed to the fork and is in the team pull request #19, which was not merged when this chapter was updated (hand-off 6.2). Jie Ling can write the C# against the declaration now. The queue limits are provisional for V1 and are revisited once Wen Ree says how often results come (hand-off 13).

```c
int32_t CommsNextResult(char* buffer, int32_t capacity);
```

```csharp
[DllImport("__Internal")] static extern int CommsNextResult(byte[] buffer, int capacity);
```

| Item | Rule in the source |
|---|---|
| What one call does | Drops the waiting results that have expired, then removes the oldest result still waiting and writes it into the buffer as one compact UTF-8 JSON object with a trailing 0 |
| JSON object | Exactly four keys in this order: `{"result_id":"<id>","gesture":"<label>","confidence":<number>,"device_id":<1 or 2>}`, for example `{"result_id":"1:305419896:42","gesture":"CHOP","confidence":0.93,"device_id":1}`. Built by `GestureResult.nextResultJSON` (`Protocol.swift:18-25`). No escaping is needed: the parser has already limited `result_id` to digits, colons and `cmd:`, and the label to `A–Z a–z 0–9 _ -`. The confidence uses the same `Double` formatting as the display (`1` becomes `1.0`; small values in exponent form, still valid JSON). All bytes are ASCII |
| Return value | The byte count written, not counting the trailing 0. 0 when no result is waiting (nothing written). −(byte count + 1) when `buffer` is null or `capacity` is less than the byte count + 1: nothing is written and the result stays at the front of the queue. A null buffer counts as too small whatever `capacity` says |
| Buffer | 512 bytes (hand-off 7.3). The longest possible object is under 150 bytes, so with 512 bytes a negative return does not happen |
| How to call | In a loop each frame while it returns a positive number, on the main thread, from the same single object that polls `CommsCopyDisplay`, inside `#if UNITY_IOS && !UNITY_EDITOR`. It never blocks |
| Promise | Results wait in arrival order, de-duplicated by `result_id`, and each result that is not dropped can be taken out at most once. It does not promise that every result is delivered (see the limits and "What it does not change") |
| Content | Every result exactly as the board sent it, with the confidence unrounded. No merging, splitting, filtering or reinterpreting (hand-off 3.1) |
| Limits (provisional V1) | At most 32 results wait (`DisplayState.pendingCapacity`); when a 33rd is accepted, the oldest is dropped (`pendingDropped` +1). A result is dropped once the phone's latest observed time is 2 s or more past its arrival (`DisplayState.pendingLifetime`; `pendingExpired` +1). Expiry is checked on every accepted result, every `CommsCopyDisplay` and every `CommsNextResult`, so results nobody takes out do not pile up. At 50 results a second, 32 places last only about 0.64 s if the game stops reading. Revisited after Wen Ree's answer on how often results come |
| When the queue is emptied | When the session stops (Disconnect, the app becoming inactive, `CommsStop`): emptied without counting. When a new Connect starts: emptied, and both counters reset to 0, like `Received`. An automatic reconnect keeps the queue, and so does a terminal error, because both reach `DisplayState.clear`; the entries still expire after 2 s |
| Counters | `pendingCount`, `pendingDropped` and `pendingExpired` are in the display snapshot (`DisplayState.swift:9-13`). Neither the four lines of text nor any C function shows them; today only the tests read them |

What it does not change:

- It is a bounded queue, not replay. A result the board dropped, a result lost with a connection, and a result produced while the phone was not subscribed are not recovered.
- `CommsCopyDisplay` stays as the status display. Its latest-only text can still lose results between polls.
- Gaps in the `seq` part of `result_id` are normal (see "Known limits").
- Whether several identical labels in a row (for example several `CHOP`) mean one action or several is for Wen Ree and Jie Ling to agree. What the game does with each result is Jie Ling's.

Precedent in the code: the Android reference receiver already drains a queue with the same limits on the Unity main thread. `FreshResultQueue` holds 32 entries, drops the oldest when full, drops entries older than 2 s on dequeue, and counts both in one counter, `Dropped` (`phone/unity/CommsPhoneCore.cs:323-361`). `CommsPhoneReceiver.cs` creates it with `(32, 2 s)` and dequeues in a loop each frame, firing one event per result (`CommsPhoneReceiver.cs:44,60-66`). It also clears the queue at the start and end of every connection, automatic reconnects included (`CommsPhoneCore.cs:338,387,426`). `CommsNextResult` differs there: it keeps its queue across an automatic reconnect. It also counts the two kinds of drop separately and expires entries on every call, not only on dequeue.

### Setup screen

| Element | Text or identifier | Behaviour |
|---|---|---|
| Main screen button | `Communications Connect`; changes to `Communications Settings` after connecting; identifier `comms.setup` | Opens the form. Indigo capsule button, 10 pt below the top of the safe area and 12 pt in from the right (`IntegrationController.swift:42-59`) |
| Form title | `Communications Visualizer`; the system Done button at the top right | Done clears the passwords and closes the form. It does not disconnect |
| Description lines | `session ltc-comms` (`SetupViewController.swift:51`; until 2026-10-14 the source had `DUMMY gestures · session ltc-comms`); the foreground notice `The iPhone connects through its own SSH session. Keep the app in the foreground. Leaving the app stops reception and clears passwords.`; `Board: <board host name>`; below the jump host switch, `Jump host: <jump host name>` (`SetupViewController.swift:51-53,82`) | Read-only |
| Input fields | `Board username`, `Board password`, `Jump username`, `Jump password` | Both usernames are prefilled with the last saved values. Both password fields are masked and have a show/hide button. The identifier is `comms.` plus the name without spaces, for example `comms.Boardusername` |
| Switch | `Use campus jump host`, on by default | Turning it off disables the two jump host fields and clears the jump password |
| Certificate line | Not imported: `CA not imported. Only the enrolled public Communications CA is accepted.` Imported: `Verified Communications CA imported.`, then `SHA-256: <fingerprint>` on the next line | Read-only |
| Button | `Import verified public CA` | Clears the passwords first, then opens the system file picker (single selection, copy mode) |
| Button | `Connect` | Validates, saves the public settings and connects; on success, clears the passwords and closes the form |
| Button | `Disconnect` | Disconnects; clears the passwords; the notice line shows `Disconnected` |

Texts the notice line can show:

- `Enter passwords when ready to connect.`
- `A session is active. Connect restarts it; Disconnect stops it.`
- `CA verified. Enter passwords and connect.`
- `Enter the required passwords. They remain in memory only.`
- `Enter the required usernames without spaces or control characters.`
- `Import one public CA certificate in PEM format (maximum 64 KiB). Private keys are not accepted.`
- `This certificate does not match the enrolled Communications CA. Obtain the verified public ca-cert.pem from the Communications setup.`
- `Could not read this file. Import the verified public CA PEM.`
- `Could not save the public setup. Try again while the iPhone is unlocked.`
- `Disconnected`

CA import validation (`Configuration.swift:47-66`): at most 65,536 bytes; no substring `PRIVATE KEY`; exactly one BEGIN marker and one END marker; after trimming leading and trailing whitespace, the text starts with the BEGIN marker and ends with the END marker; the text between them is valid Base64; the system parses the decoded DER as a certificate (only where the Security framework exists, so on the iPhone and in the macOS test build but not in the Linux test build); the SHA-256 of the DER equals the hard-coded fingerprint. If any check fails, the file is rejected. A failed import leaves the existing CA unchanged.

Password lifetime:

- Passwords exist only in the input fields and in the `CredentialVault` inside `CommsClient`. They are not written to a file and are not part of the settings.
- The input fields are cleared when: Done is tapped; the form disappears; Import CA is tapped; Connect succeeds; Disconnect is tapped; the app resigns active. Turning off the jump host switch clears the jump password.
- `CredentialVault` is cleared on: `stop()`; a terminal error; deallocation.
- As soon as the app resigns active, it disconnects and clears the passwords. Returning to the foreground does not reconnect automatically. The passwords must be entered again.

### App data directory

| Path (under Application Support in the app container) | Content | Read and write |
|---|---|---|
| `Comms/public-settings.json` | Three keys: `boardUser`, `jumpUser`, `useJump` | Written each time Connect is tapped and the form validation passes |
| `Comms/comms-ca.pem` | The public CA that passed the fingerprint check | Same as above |
| `Week7/public-settings.json`, `Week7/week7-ca.pem` | Legacy directory | Read-only. Read only when the matching file in the new directory does not exist |

- Writes are atomic. On iOS they add `completeFileProtection`. The directory is marked as excluded from backup (`Configuration.swift:93-106`).
- Loading the CA repeats the fingerprint check (`Configuration.swift:88-92`).
- If the settings file in the new directory exists but is corrupt, empty settings are returned. There is no fallback to the legacy directory.
- If saving fails, `onConnect` throws before it disconnects the old session. The old session is therefore unaffected, and the notice line shows `Could not save the public setup. Try again while the iPhone is unlocked.` (`IntegrationController.swift:66`, `SetupViewController.swift:173`).

### Export patch constants

| Item | Value |
|---|---|
| Patched file | `xcode-export/Il2CppOutputProject/Source/il2cppOutput/Assembly-CSharp.cpp` |
| Patched class | `TlsDataReceiver_t47A6D7DD24307D9353B230F8ADB4F931DBCB4C6E` |
| Three pinned SHA-256 values | Original import, previous patch, current patch; see `patch_export.py:20-22`. In the current working copy, this file's hash equals "current patch" (`0cabc95f…`; checked again on the owner's Mac on 2026-10-16, before and after `patch_export.py`) |
| Local package reference | `XCLocalSwiftPackageReference`, ID `A7E700000000000000000002`, `relativePath = ../CommsNative` |
| Product dependency | `XCSwiftPackageProductDependency`, ID `A7E700000000000000000003`, `productName = CommsNative` |
| Build file | `PBXBuildFile`, ID `A7E700000000000000000001` |
| Link target | `UnityFramework` (target ID `9D25AB9C213FB47800354C27`, Frameworks phase ID `9D25AB99213FB47800354C27`) |
| Project root object | `29B97313FDCFA39411CA2CEA` |
| Symbol upload switch | Environment variable `WEEK7_ALLOW_SYMBOL_UPLOAD`. Unless it equals `YES`, `process_symbols.sh` exits at once |
| `Info.plist` | `CFBundleDisplayName` = `Week 7 Visualizer`; `CFBundleVersion` = `1`; `NSLocalNetworkUsageDescription`; `ITSAppUsesNonExemptEncryption` = true |

The four replaced methods (`patch_export.py:55-136`):

| Method | Behaviour after replacement |
|---|---|
| `Start` | If the label is not null: anchors set to (0.05, 0.10) to (0.95, 0.80), offsets set to zero, font size 36, auto-sizing 18 to 36. Then calls `Week7Start()` |
| `ListenLoop` | Empty function. The original inbound TLS server on 5005 no longer runs |
| `Update` | 2,048-byte buffer on the stack. Calls `Week7CopyDisplay(display, 2048)`. Returns at once if the return value is not greater than 0 or not less than 2048. Otherwise adds the trailing 0, builds a string from the UTF-8 bytes and writes it to the label |
| `OnDestroy` | Calls `Week7Stop()` |

`patch_export.py` behaviour:

- If the file hash already equals "current patch", it writes nothing and prints `EXPORT_PATCH_OK: already applied`.
- It accepts only two starting points: "original import" and "previous patch". Any other hash gives `Unknown receiver source; expected the verified sanitized import.`.
- Each method signature must appear exactly once, and each method body hash must match. The hash of the result must equal "current patch". Otherwise it reports an error and writes nothing.
- The write is an atomic replace that keeps the file permissions. If the original file changes during validation, it gives up (`patch_export.py:178-202`).
- On failure, its output starts with `EXPORT_PATCH_FAILED:` and it returns 1.

`configure_xcode.py` behaviour:

- Clears `USYM_UPLOAD_AUTH_TOKEN` and the `DevelopmentTeam` target attributes in the project (`configure_xcode.py:119-120`). It does not touch a `DEVELOPMENT_TEAM` build setting, so a team that Xcode writes there stays (see "How to run and verify", export project). In the current export both are empty.
- If the project does not yet contain `CommsNative`, it inserts the package reference at five anchors. Each anchor must appear exactly once; otherwise it reports `Unexpected Xcode export anchor; inspect before adapting` (`configure_xcode.py:121-148`).
- It then checks, link by link, the whole reference chain from the project root object to the local package product (`configure_xcode.py:62-85`).
- It rewrites `process_symbols.sh` to add the switch, then checks with a regular expression that the switch is at the start of the file (`configure_xcode.py:150-156`).
- It rewrites `Info.plist` (`configure_xcode.py:157-165`).
- It prepares all three files first, then replaces them atomically together. If any of the files changes during validation, it abandons all of them (`configure_xcode.py:88-108`).
- It can be run repeatedly. On success it prints `Configured local CommsNative package; signing stays operator-owned.`. On failure its output starts with `XCODE_CONFIGURE_FAILED:` and it returns 1. On the owner's Mac on 2026-10-16 it succeeded and left `project.pbxproj`, `Info.plist` and `process_symbols.sh` byte-identical.
- It does not touch the export's `Package.resolved` (see the `ios-visualizer/xcode-export/` row under "Components and files").

`patch_export.py` and `configure_xcode.py` both accept `--export <directory>`, default `ios-visualizer/xcode-export` (`patch_export.py:207-211`, `configure_xcode.py:175`).

### Reference implementation constants

| Implementation | Defaults and behaviour |
|---|---|
| `phone/receiver.py` | Connects to `127.0.0.1`; `--port` default 19999; `--session` default `ltc-comms`; `--ca` required; `--count` default 0 (never stops); `--duration` optional. Sends SUBSCRIBE and expects SUBSCRIBED at `v` 1 (`SUBSCRIPTION_VERSION`). Accepts only `GESTURE_RESULT` with `v` 3 (`RESULT_VERSION`) and exactly the 10 keys of `RESULT_FIELDS`; `device_id` 1 or 2; the `request_id` and `result_id` rules; the label rule as `GESTURE_PATTERN.fullmatch` on `[A-Za-z0-9_-]{1,32}` (`fullmatch`, because `$` would also match before a trailing newline); the confidence rule (an `int` 0 or 1, or a finite `float` from 0 to 1; `type()` excludes booleans) (`phone/receiver.py:18-25,99-149`). Connect, handshake, write and the wait for SUBSCRIBED each get 5 s. Idle time between results has no deadline; once a frame starts, it must complete within 5 s. A JSON integer with more than 10 digits and a non-finite number are rejected while parsing. Deduplication 4,096. Back-off 0.5 to 5 s, reset when a result arrives. Every error, an invalid result included, reconnects; there is no terminal class. While running, it prints `subscribed session=<session>` and `reconnect reason=<exception type>` to standard error. Each distinct result goes to standard output as compact JSON, its confidence included. At the end it prints `{"received":N,"reconnects":M}` to standard error. Exit codes: Ctrl+C returns 130; configuration errors (`OSError`, `ssl.SSLError`, `ValueError`) print `configuration_error=<type>` to standard error and return 1; with `--count` given and too few results received, it returns 1; otherwise 0 (`phone/receiver.py:41-57,160-210,213-246`). Built: tested in the full suite on the laptop |
| `phone/unity/CommsPhoneCore.cs` | `PhoneReceiver(authorityDer, results, session = "ltc-comms", port = 19999)`. Fixed TLS 1.2. Connect plus handshake 5 s in total, write 5 s, wait for SUBSCRIBED 5 s; idle after subscribing has no deadline; once a frame starts, it must complete within 5 s. SUBSCRIBE and SUBSCRIBED at `v` 1. `PhoneProtocol.ParseResult` accepts only `v` 3 with exactly 10 keys, each of them required; `device_id` 1 or 2; the `request_id` and `result_id` rules; the label rule as the regular expression `\A[A-Za-z0-9_-]{1,32}\z` (`\z`, because .NET `$` also matches before a trailing newline); the confidence rule (not a string or `null`, parsed with `Double.TryParse` in the invariant culture, then NaN, infinity, below 0 and above 1 refused; the explicit infinity check matters because .NET Core 3.0 and later parse `1e999` as infinity). `GestureResult.Confidence` (`double`) carries the received value; `Json` still carries the whole body (`CommsPhoneCore.cs:19-80`). Deduplication 4,096. Back-off 0.5 to 5 s. A certificate validation failure and an invalid result also reconnect. Status texts: `Stopped`, `Connecting to Phone localhost`, `Subscribed`, `Reconnect after <exception type>`. On 2026-10-14 only the changed `GestureResult` and `PhoneProtocol` section was compiled, with the C# 5 compiler of Windows PowerShell 5.1 (`Add-Type`), and it passed 88 contract checks; the whole file needs C# 6 or 7. On 2026-10-15 the whole file compiled: with the self-test under PowerShell 7 (113 checks passed), and on its own at C# 7.0 against the .NET 10 libraries (0 errors, 0 warnings). An automatic reconnect empties its result queue (`CommsPhoneCore.cs:338,387,426`), unlike the iOS queue |
| `phone/unity/CommsPhoneReceiver.cs` | Inspector fields: `authorityDer` (a `.bytes` asset holding the public CA in DER format), `localForwardPort` = 19999, `sessionId` = `ltc-comms`, `showOverlay` = true, `onResultJson`. Queue capacity 32, freshness 2 s. Stops on pause, disable and destroy; restarts on resume. Overlay title `B07 Communications receiver \| <status>` (`CommsPhoneReceiver.cs:90`; it said `dummy receiver` before 2026-10-14). Additional status texts: `Assign the verified public CA .bytes asset`, `Configuration error: <type>`, `Receiver stopped after an unexpected failure`. Needs Unity, so it was checked by reading only, not compiled |
| `laptop/phone_simulator.py` | `--host` default `127.0.0.1`; `--port` default 19999; `--ca` required; `--session-id` default `ltc-comms`; `--count` default 0; `--reconnect` optional. It validates with the board's own `ultra96.protocol.validate_message`, so it accepts exactly the version-3 results the board may send (`laptop/phone_simulator.py:10,24,26`). The read timeout per result is 5 s, so 5 s of idle times out. No deduplication. Certificate validation failures and protocol validation failures are not retried; it exits. Only network errors reconnect, and only with `--reconnect` |
| `phone/ish_control.py` | sshd path `/usr/sbin/sshd`; listens on `127.0.0.1:2222`; reverse forward `127.0.0.1:22222:127.0.0.1:2222`; subcommand timeout 20 s; waits 5 s for the listener. Working directory `~/comms-control/<id>-<random>/` (`ish_control.py:235,241,302`). For remote commands over the master connection, the SSH config file is `~/.ssh/week7-ish-password.conf` and the host alias is `week7-ultra96` (`ish_control.py:192-195`). Both names are already configured in iSH on the phone, so they stay. Nothing in the repository creates new names |

## Workflow

Normal path (using the Week 7 receiver app on the iPhone as the example, rebuilt from the current source; the installed build differs as described in "Current deployment state"):

1. The app starts. `TlsDataReceiver.Start` in the scene runs, enlarges the label, then calls `Week7Start()`.
2. `Week7Start` forwards to `commsStart()`. That clears the memory of delivered text and queues an install action on the main queue.
3. The install action runs on the main thread: the status is set to `Tap Communications Connect to configure this iPhone`; the resign-active and become-active notifications are registered; the `Communications Connect` button is attached at the top right.
4. From then on, `Update` calls `Week7CopyDisplay(display, 2048)` every frame. It updates the label only when the return value is greater than 0.
5. The user taps the button and the form opens. The usernames and the switch are prefilled with the last saved values. The CA is loaded from the data directory and its fingerprint is checked again.
6. On first use, the user taps `Import verified public CA` and picks the file. At most 65,537 bytes of the file are read; more than 65,536 bytes is rejected. After the checks pass, the certificate line shows the fingerprint.
7. The user enters the board username and password and the jump host username and password, and taps `Connect`.
8. The form validates first: the usernames are valid; the CA is imported; the board password is not empty; the jump password is not empty when the jump host is on.
9. `onConnect` runs: it saves the public settings and the CA; stops the old session; calls `begin("Connecting")`, so `Received` resets to 0, the deduplication table empties, and (source only) the per-result queue empties and its two counters reset; builds `SSHRoute` from the hard-coded host names and host keys; creates `CommsClient(session: "ltc-comms")`; changes the button text to `Communications Settings`; calls `start()`. The form clears the passwords and closes.
10. `CommsClient.connect` emits the status `Connecting`, checks the configuration, builds the TLS context from the imported CA, parses the two pinned keys and starts the 10 s overall deadline.
11. TCP connects to port 22 of the jump host. The SSH handshake runs: compare the host key, offer the jump password.
12. A direct-tcpip channel opens over the first SSH layer to port 22 of the board, and a second SSH layer runs inside it: compare the host key, offer the board password.
13. A direct-tcpip channel opens over the second SSH layer to `127.0.0.1:9999`, and a TLS handshake runs inside it: verify the certificate chain, the host name `ultra96.week7.internal` and the validity period.
14. After the TLS handshake completes, the phone sends the SUBSCRIBE frame and starts the 5 s frame timer.
15. The board validates the session ID, displaces the old subscriber (if there is one) and replies SUBSCRIBED (`ultra96/server.py:406-428`).
16. The phone receives and validates SUBSCRIBED, cancels the 10 s overall deadline and the frame timer, and the status becomes `Subscribed`. This shows only that the subscription handshake succeeded. Whether results flow shows only as `Received` rising and line 3 changing.
17. The board pushes one frame for each result it produces, unless the board drops that result first (failure path 11). The phone decodes and validates the frame (version 3, 10 keys, the label and confidence rules), resets the retry wait to 0.5 s, then passes the result to `DisplayState.accept`: deduplicate, `Received` +1, keep only the latest result, and (source only) append it to the per-result queue.
18. On the next Unity poll, the new text arrives and the label shows four lines.
19. If no new result arrives within 2 s, line 3 becomes `No live result`. `Received` does not change, and the status stays `Subscribed`.
20. After that, the connection does not drop when there is no input, because idle after subscribing has no deadline.

A game build that calls `CommsNextResult` takes each queued result out in a loop on its next frame. The Week 7 export never calls it. In a Week 7 export rebuilt from the current source, the queue therefore stays bounded on its own: every `Week7CopyDisplay` poll drops the entries older than 2 s and counts them in `pendingExpired`, which nothing displays.

Failure paths:

1. Form validation fails: no network action starts. The notice line shows the matching text.
2. The imported file is not the enrolled CA: the notice reports a certificate format error or a CA mismatch. The existing CA does not change.
3. Retryable error (for example the phone is not on the VPN, the jump host is unreachable, the connection was closed, no subscription within 10 s, a frame not complete within 5 s): the status becomes `Disconnected: <reason>; retrying`; the displayed result is cleared; the wait starts at 0.5 s, doubles each time and stops growing at 5 s; the whole route reconnects from the start and sends SUBSCRIBE again. `Received`, the deduplication table and (source only) the per-result queue are kept; queued results still expire 2 s after arrival. Results the board produced during the disconnection are not resent.
4. Every retry rebuilds the whole route: a new TCP connection to the jump host, new password logins to the jump host and the board, then both channel layers again. There is no retry limit. As long as the app is in the foreground it keeps trying, and once the wait has reached 5 s it logs in to the jump host and to the board about once every 5 s. The phone ends up on this path when the board service is not running, when the session IDs differ, and when another subscriber displaces it. When the service is not ready, tap Disconnect first instead of leaving the app in `retrying`. The repository cannot confirm whether the jump host limits frequent logins.
5. When the board service is not running, the direct-tcpip channel over the second SSH layer cannot open. Judging from the code path, this error is not a `TransportFailure`, so it shows as `Disconnected: SSH, TLS or protocol verification failed; retrying`. This has not been verified on a device. When the session IDs differ or the phone is displaced, the board closes the connection, and the phone shows `Disconnected: connection closed; retrying`.
6. Terminal error (for example a wrong password, a host key mismatch, an expired server certificate, a result that breaks the rules, such as a result of version 1 or 2): the status becomes `Disconnected: <reason>; correct setup and reconnect`; the client deactivates; the route and passwords are cleared; no retry. The user must open the form again, enter the passwords and tap Connect. The status goes through `DisplayState.clear`, so results already queued for `CommsNextResult` stay until they are taken or expire.
7. The app resigns active (screen lock, switch to another app, system UI covering it): the status becomes `Paused — return and connect again`; the client stops; the passwords are cleared; the per-result queue is emptied; the button text changes back to `Communications Connect`. On return to the foreground, the button is attached only if it is not attached yet. There is no automatic reconnect.
8. The user taps `Disconnect`: the status becomes `Disconnected`; the client stops; the passwords are cleared; the per-result queue is emptied.
9. The Unity object is destroyed: `OnDestroy` calls `Week7Stop()`. The status becomes `Stopped` at once and the per-result queue is emptied. The button, form, notification observers and client are all removed.
10. Another subscriber connects to the same session (for example `laptop.phone_simulator` running at the same time): the board closes the phone's connection. The phone treats this as a closed connection and retries. Once it subscribes again it displaces the other subscriber, and the two keep displacing each other.
11. Results the board produces while there is no subscriber: the board counts them and drops them (`ultra96/server.py:341-344`, `_publish`). The phone cannot get them by connecting later. With a subscriber, the board also drops results from its queue: the oldest when the 32-entry queue is full, and any result that has waited 2 s or more on the board or cannot be written to the phone's connection in what is left of those 2 s (`ultra96/server.py:58-109,463-484`, `ResultQueue.put`, `get_timed` and `_send_results`). A write that does not finish in that time also ends that phone connection on the board, and the phone reconnects as after any retryable error. That rule limits only how long a result waits on the board (queue plus write). It does not promise that the phone receives the result: bytes already handed to TCP/TLS cannot be recalled. It is not an end-to-end latency bound either. The phone's own 2 s display window counts from when the phone received the result (hand-off 7.2 and 9.2).
12. The polling buffer is too small or null: `CommsCopyDisplay` returns 0 and does not write to the buffer. The next poll tries again. For `CommsNextResult` (source only), a null or too small buffer returns −(byte count + 1), writes nothing, and leaves the result at the front of the queue, where it still expires 2 s after arrival.

## Why it is designed this way

1. The phone dials out over SSH itself, and TLS runs inside a direct-tcpip channel. Reason: the campus firewall lets through only SSH on port 22 to the Ultra96; neither the phone nor the laptop can accept incoming connections; 8888 and 9999 bind only to the board loopback. Rejected at the time: the phone as a TLS server listening on 5005 (the approach in Jie Ling's original export; both the direction and the frame format were wrong); the laptop forwarding results to the phone; a separate local listener on 19999 on the phone (an iSH or Termux forward). Sources: `docs/archive/design/architecture-and-interface-draft-v0.1.md:137,230,253`; decisions 7 and 12 in `docs/archive/design/week7-selected-design-2026-09-06.md`; IOS-08, IOS-16 and IOS-17 in `docs/archive/reports/week7-continuation-report-2026-09-14.md`; `docs/archive/design/specs/2026-09-14-ios-visualizer-design.md:23-29`.
2. Link the Swift package into the Unity export, and replace only method bodies in the generated code. Reason: the Unity source project was not available at the time, and editing a loose C# file would not change that app. Rejected at the time: exporting again from the Unity source project; editing only `reference/TlsDataReceiver.cs`. Sources: lines 13-21 of the same design specification; IOS-10, IOS-15. Not used for the next build (the owner's direction of 2026-10-14, final when Jie Ling confirms; hand-off 7.3): Jie Ling calls the functions from C# in the Unity project, pushes it to the team repo, exports it, adds `CommsNative` to the Xcode project, and builds and installs the app; olsonwangyj provides `CommsNative` in the team repo and short steps for adding it.
3. Unity polls a C function, and the native side holds no managed pointer. Reason: network callbacks run on the NIO thread, and Unity APIs can be used only on the main thread. Polling confines the thread boundary to one locked snapshot. Rejected at the time: native callbacks modifying Unity objects directly. Sources: lines 18-19 of the design specification; `docs/archive/reports/week7-system-technical-report.md:371-373`.
4. Keep only the latest result, 2 s freshness, deduplication of 4,096. Reason: memory is bounded; queued old data is not shown; the count represents only the distinct results within this Connect. Rejected at the time: a result queue and replay on the phone. Sources: IOS-21; selected design decision 9 (the board keeps no history). Added for the game on 2026-10-14 (the owner's direction, final when Jie Ling confirms; in the source, compiled and tested on Linux since 2026-10-15, on macOS and built for iOS since 2026-10-16, not installed; limits provisional): the latest-only text stays as a status display, and a bounded per-result queue, `CommsNextResult`, is added because the game's actions are one-shot and need results one at a time, not a display that the next result overwrites. It keeps the same principles: bounded memory, no stale results (2 s after the phone received them), drops counted, still no replay, and no promise that every result is delivered (hand-off 7.3). It lives in `DisplayState`, under the lock that network callbacks and Unity polls already share, so `IntegrationController` and the start and stop functions needed no change: `begin` and `stop` empty it, `clear` keeps it. The two counters record results lost while a session runs (queue full, waited too long); a stop discards the waiting results without counting them as lost. The negative return is −(byte count + 1), the capacity needed including the trailing 0, so a caller can size a buffer from it directly.
5. Both SSH host keys are hard-coded, and only one CA is accepted, identified by its SHA-256 fingerprint. Reason: no trust on first use; importing a valid but unrelated certificate is also rejected. Rejected at the time: trusting the key on first connection; accepting any CA; skipping host name verification; a plaintext fallback. Sources: lines 33-47 of the design specification; IOS-18.
6. Passwords live only in memory, and the session stops when the app leaves the foreground. Reason: the on-site route uses password authentication; this avoids depending on unverified iOS background execution; nothing is written to disk, so there is no credential file to manage. Rejected at the time: saving passwords; enrolling key files; background reception. Sources: lines 35-39 and 63-64 of the design specification; IOS-19, IOS-20.
7. Authentication, trust and protocol errors terminate at once; network errors back off and retry. Reason: do not keep trying an account with a wrong password; do not accept an untrusted peer; network glitches recover on their own. Rejected at the time: retrying every error. Source: IOS-23.
8. Idle after subscribing has no deadline; only a frame that has started but not completed gets 5 s. Reason: the old implementation also applied a 5 s deadline between two results, so a healthy quiet connection closed itself; a test on 2026-09-21 lost 16 results because of it. Rejected at the time: a 5 s idle timeout. This change also replaced the "30 s grace for the first result" in the design records (IOS-22). No heartbeat was added. Sources: `docs/archive/test-evidence/phone-recovery-test-2026-09-21.md:114-153,166-179`; `docs/archive/test-evidence/phone-post-update-test-2026-09-21.md:51-91`.
9. The TLS identity is fixed as `ultra96.week7.internal`, even though TCP connects to `127.0.0.1`. Reason: both ends of the channel are loopback addresses, so an address cannot serve as an identity; the certificate is issued to the service name. Rejected at the time: disabling host name verification; a plaintext mode; mutual TLS (SSH already provides access control). Source: selected design decision 11.
10. The patch script is pinned by hash and refuses unknown exports. Reason: the generated code changes with every export, and blind text substitution would break it. Rejected at the time: fuzzy substitution on any export. Sources: IOS-26; `patch_export.py:1-8`.
11. Clear the inherited symbol upload token and signing team, and do not upload symbols by default. Reason: a local build should not upload to the teammate's Unity account that the export carries. Sources: lines 83-85 of the design specification; IOS-27.
12. Stretch the label's rectangle at run time. Reason: the original label is 200×50 and cannot fit four lines. Rejected at the time: editing the binary scene or metadata files. Source: IOS-25.
13. Keep the Python and Android C# receivers as references. Reason: the phone baseline first chosen for Week 7 was Android with Termux's own SSH forward. After the on-site device became an iPhone, the route changed first to iSH plus Python, then to native Swift. Sources: selected design decisions 15 and 29; `docs/communications-quickstart.md:170`.
14. The phone checks the shape of a result, not its meaning: any label of 1 to 32 safe characters and any confidence from 0 to 1, the same rule on the board and on every receiver (2026-10-14; hand-off 5, item 17, and 6.5, D8). Reason: Communications carries labels without knowing the set, which Wen Ree and Jie Ling agree; the board refuses a result the phone would reject, because a rejected result ends the phone session and clears its passwords. The Swift rule counts Unicode scalars, not `Character`s, so a composed or combining sequence cannot pass as one allowed character. Rejected: a fixed list of labels on the phone; rounding the confidence, which would change the model's output (hand-off 6.5, D17).
15. Version 3 only, with the subscription envelopes left at version 1 (2026-10-14; hand-off 5, item 16, and 6.5, D4 to D6). Reason: the owner's rule that only the newest version is supported, so there is no mixed state; `SUBSCRIBE` and `SUBSCRIBED` never carried the packet version and did not change; `request_id` stays in every result, so the field set stays exact. Cost: the phone app must be rebuilt and reinstalled together with the board redeploy.

## Cautions and known limits

### Caller rules

These constraints come from the C functions themselves. A game that reuses this receiver must follow them. Rules 13 to 16 concern `CommsNextResult`, which is not in the installed app (compiled and tested on Linux and macOS and built for iOS on 2026-10-16; not installed).

1. Only one poller. The memory of "text already delivered" exists once per process (`DisplayMailbox.swift:7,52-53`). Two pollers would each get only part of the changes.
2. The text is UTF-8 and ends with 0. The return value is a byte count, not a character count. Decode the bytes as UTF-8.
3. The buffer capacity must be greater than the text's byte count. Week 7 uses 2,048 bytes. A return of 0 means "no change, does not fit, or null pointer"; keep the previous text in that case.
4. Use `result_id` to decide whether a result is new, not the label text. The same label twice in a row is two different results.
5. The bridge gives only the latest result. If several results arrive between two polls, only the last is visible; `Received` still counts all of them. Poll every frame, and do not assume every result is seen. Measured against "make sure the next module receives it accurately", this is not per-result delivery. The owner's direction (2026-10-14, final when Jie Ling confirms): the text stays a status display, and results one at a time, with the real confidence, come from `CommsNextResult` (see "Per-result function `CommsNextResult`"; hand-off 7.3 and 13). Until a build that calls `CommsNextResult` is installed, the game can show the text and test the connection, but it cannot drive actions reliably from the text.
6. The calling component must survive scene changes. `CommsStop` removes everything and clears the passwords. After it, `CommsStart` must be called again and the user must enter the passwords again. The Week 7 export calls `Week7Stop` when its object is destroyed only because that object lives until the app ends.
7. Call `CommsStop` only when the app truly stops using Communications. Do not call it on a scene change, do not use it as a "reset", and do not call it on entering the background. The native layer handles foreground and background itself.
8. One call to `CommsStart` is enough. It does not connect automatically. Only the user can start a connection, by tapping the button and entering the passwords.
9. Poll on the main thread.
10. The native layer already deduplicates by `result_id`, with a window of 4,096 that is cleared each time the user taps Connect.
11. The button is attached only when a "root controller of the key window of a foreground-active scene" exists (`IntegrationController.swift:36-43`). If none exists when `CommsStart` runs, the button is not attached that time; the next `didBecomeActive` notification tries again (`IntegrationController.swift:30-33`). Once the button exists, it is not attached again (it is attached only when `button == nil`), so it stays on the root view it was attached to. The form is presented as a `formSheet` from the root controller at that moment (`IntegrationController.swift:86-88`). If the game calls `CommsStart` early during start-up, or replaces the root controller while running, check that the button is visible.
12. Keep the top right corner of the screen free for this button (10 pt below the top of the safe area, 12 pt in from the right). It is the only way to connect and reconnect.
13. One consumer for `CommsNextResult`. There is one queue per process, and each result can be taken out only once, so two callers would each get only some of the results. Call it from the same single object that polls `CommsCopyDisplay`, on the main thread.
14. Call `CommsNextResult` in a loop each frame while it returns a positive number. A return of 0 means nothing is waiting. A negative return means the buffer was null or too small; the result is still waiting, and the negated value is the capacity needed. With the proposed 512-byte buffer this does not happen.
15. Each positive return is one compact JSON object of exactly four keys (`result_id`, `gesture`, `confidence`, `device_id`), all ASCII, ending with 0 at the returned byte count. Parse it as JSON. Use `result_id` to tell results apart, as in rule 4.
16. Results not taken out within 2 s of reaching the phone are dropped, and so is the oldest when 32 wait. The counters of these drops exist only inside the native layer; the game cannot read them.

### Extension point: model labels and real confidence (done in source; Swift compiled and tested on Linux and macOS, built for iOS; not installed)

olsonwangyj stated that Communications itself must support model labels and real confidence, and that the owner makes the change (hand-off document section 8, item 5). **It was done on the evening of 2026-10-14**, ahead of the Fri 10-16 and Sat 10-17 plan, together with protocol version 3, on the local branch `comms/protocol-v3`. Only the newest version is supported (the owner's rule, 2026-10-14): the board sets `v` 3 on every result (`ultra96/server.py:333,367`), and every phone-side check accepts only version 3. The board, the iPhone source and the two reference receivers changed together. There is no transition period: the installed Week 7 app still rejects version-3 results, model labels and any confidence other than 1, so the phone app must be rebuilt and reinstalled in the same upgrade as both boards and the board service (hand-off section 8, item 1, and 6.3).

| Location | Before (source at `c42b386`) | Now (version 3, branch `comms/protocol-v3`) | Status |
|---|---|---|---|
| `Protocol.swift:48-87` | Result `v` 1 or 2; label `["REST","FIST","OPEN","POINT"][seq % 4]` (v1) or one of the four (v2); `confidence == 1` | `v` 3 only, 10 keys, `request_id` always present; the label rule over Unicode scalars; confidence finite, 0 to 1 | Compiled and tested on Linux (Swift 6.1) and macOS; compiled for iOS (2026-10-16) |
| `Protocol.swift:7-25` | `GestureResult` had no confidence field | `confidence: Double`; `nextResultJSON` for `CommsNextResult` | Compiled and tested on Linux (Swift 6.1) and macOS; compiled for iOS (2026-10-16) |
| `DisplayState.swift`, `DisplayMailbox.swift:27-47,70-74` | No per-result queue; three `Comms*` functions | The per-result queue and `CommsNextResult` | Compiled and tested on Linux (Swift 6.1) and macOS; compiled for iOS (2026-10-16); limits provisional |
| `DisplayMailbox.swift:16,18` | Literals `confidence 1.0` and `Communications • DUMMY inference` | The received confidence; line 1 `Communications` | Compiled and tested on Linux (Swift 6.1) and macOS; compiled for iOS (2026-10-16) |
| `SetupViewController.swift:51` | `DUMMY gestures · session ltc-comms` | `session ltc-comms` | Compiled for iOS on 2026-10-16 (`#if os(iOS)` file; simulator and device builds); the `NativePreview` UI test drove the form on the simulator |
| `phone/receiver.py:18-25,118-149` | The same whitelist and confidence check | The same version-3 rules | Built (full suite on the laptop) |
| `phone/unity/CommsPhoneCore.cs:19-80` | The same; `GestureResult` without confidence | The same version-3 rules; `GestureResult.Confidence` | Whole file compiled (C# 7.0, .NET 10 libraries); self-test passed 113 checks (PowerShell 7). On 2026-10-14 only this section had been compiled (C# 5, 88 contract checks) |
| `ultra96/protocol.py:8-12,31-40,93-99` | The same check on the board side | The same rules; the board refuses an invalid model result before sending (see [detail chapter 4](04-ultra96-service-and-certificates.md)) | Built |
| Result samples in the test files | All samples used the 4 labels and 1.0 | Version-3 samples with model labels and confidences other than 1; versions 1 and 2 as refused cases | Python ran; Swift ran on Linux (72 tests), on macOS (73 tests, `PythonBoardTests` included; 2026-10-16) and, for `TransportTests` and `TrustTests`, on the iOS Simulator (34 tests; 2026-10-16); `CoreSelfTest.cs` ran (113 checks) |

The installed app's own texts are older still: its button reads `Week 7 Connect`, and by its source line 1 reads `Week 7 • DUMMY inference` (see "Display text"; the screen was not checked). Its validation is the version-2 kind, dummy labels only (hand-off 6.3); it accepted version-2 results on 2026-09-28 (see "How to run and verify").

Checks across the peers (hand-off 6.2): an adversarial review found no defect in the Swift or C# rules, and 11,421 result bodies were validated identically by the board, the Python receiver and a compiled C# harness. At the time of that review the Swift was checked by reading only, plus two indirect checks on the laptop without compiling any Swift: the Python ingest half of `PythonBoardTests` against the real Python service (100 results), and a Python mirror of `FlatJSON` on the `ProtocolTests` vectors. On 2026-10-15 the Swift itself compiled and passed its tests on Linux, `ProtocolTests` included, and on 2026-10-16 on macOS, `PythonBoardTests` included (see "Build status of the Swift and C# code").

For reference: the model's current classes are in `models/class_names.json`. There are six: `PICKUPHOLD`, `PLACEDOWN`, `CHOP`, `WASH`, `THROW`, `FIREEXT`; all six pass the label rule. The final label set, and whether the model outputs anything while idle, are asked of Wen Ree in the message described in hand-off document section 7.2. The label names, how often a label is produced, and whether several identical labels in a row mean one action or several are for Wen Ree and Jie Ling to agree between themselves (hand-off 3.1). Communications forwards each label and confidence as they are, without filtering, renaming or rounding (hand-off 7.2).

Hidden constraint: `GESTURE_RESULT` cannot freely gain fields. All four validators match the field set exactly:

1. The iPhone parser accepts at most 10 fields, and a version-3 result has exactly 10 (`Protocol.swift:32,202`). Values can only be strings, numbers or `null`. Arrays, nested objects and booleans all fail (`Protocol.swift:206-211`), and the failure is a terminal error.
2. The C# reference implementation requires exactly 10 fields and reads each of the ten (`CommsPhoneCore.cs:50-51,75-80`).
3. The board-side validation and the Python receiver both require the key set to be exactly equal (`ultra96/protocol.py:13-21,67-68`; `phone/receiver.py:21-22,99-103`).
4. All four require `result_id` to equal exactly `device_id:boot_id:seq` (with `cmd:` in front for command results), and allow only 1 or 2 for `device_id` (`Protocol.swift:63-67`; `CommsPhoneCore.cs:53-64`; `ultra96/protocol.py:73-74,93-95,107-109`; `phone/receiver.py:134-144`).
5. The board's event log also has a field whitelist (`ultra96/diagnostics.py:25-31,100-101`, see [detail chapter 4](04-ultra96-service-and-certificates.md)).

So the only correlation information a result message can carry is the identity of one sample: the `device_id`, `boot_id` and `seq` of the sample the model names. This matches the output fields in hand-off document section 7.2. Adding any other field means changing all four places together, and the phone app must be rebuilt and reinstalled.

### Known limits

- Host names, both host keys and the CA fingerprint are hard-coded in the source. Changing the board or the CA means editing the source, then rebuilding and reinstalling the app.
- The server certificate is issued by `tools/generate_comms_pki.py` and is valid for 30 days (`generate_comms_pki.py:47`); the CA is valid for 365 days (`generate_comms_pki.py:117`). The phone checks the validity period. An expired certificate is a terminal error, and the status stays at `Disconnected: SSH, TLS or protocol verification failed; correct setup and reconnect`. To renew, use `--renew-server-from <CA directory>` (function `renew_server_identity`). It issues a new server private key and certificate from the existing CA. The CA does not change, so the fingerprint in the phone source does not need to change. Running the tool without this option replaces the CA too; the fingerprint in the phone source must then change, and the app must be reinstalled.
- Works only in the foreground. Screen lock, switching apps, and system UI that makes the app resign active all disconnect and clear the passwords.
- No heartbeat. A silent network black hole is detected only when the system reports an error.
- No replay. Results produced during a disconnection are lost for good.
- The board has only one subscriber slot. A second subscriber running at the same time leads to mutual displacement. Do not run `laptop/phone_simulator.py` or `tools/rehearse_remote_comms.py` during a demo or integration test.
- Retryable errors make the phone log in to both SSH hops with passwords again and again, with no limit (see failure path 4).
- `Received` is an aggregate count. The phone keeps no per-result record and no timestamps. It is evidence level 5 and must be read by a person. `CAPTURE PASSED` from `demo.py` is level 3 (hand-off document section 4.7). Comparing the increase in `Received` with `Phone expected increase` is valid only while the board runs the built-in dummy model, which gives one result per accepted sample or command; a real model's result rate is not known yet (hand-off 8, item 6). Gated firmware does not break this comparison: a skipped idle tick gets no `seq` and is not a generated sample, so `Phone expected increase` counts only the samples that were sent.
- The per-result queue's counters (`pendingCount`, `pendingDropped`, `pendingExpired`) are not shown in the text and not returned by any C function. A result that the queue drops is therefore visible only as a gap between `Received` and the number of results the game took out.
- The 2 s freshness means "recently received locally": the phone's display window counts from when the phone received the result. It is not end-to-end latency. The board has its own, separate 2 s limit on how long a result may wait there (failure path 11). There is no end-to-end timestamp and no end-to-end latency bound (hand-off 9.2).
- Gaps in the `seq` part of `result_id` are normal. The `seq` is a sample sequence number, and samples can be missing: lost over the radio, dropped after waiting more than 2 s on the laptop, discarded from the laptop's queue on a BLE disconnect, or counted as ambiguous drops on a TLS reconnect (not resent). While a glove is disconnected it produces no samples, so that time shows only as a jump in `uptime_ms`, not in `seq` (hand-off 7.2). The same holds while a gated glove is still. A gap on its own does not show that the phone lost a result.
- With gated gloves, long pauses between results are normal. While both gloves are still, no result for a sample arrives; only laptop commands still give `cmd:` results, because commands do not go through the glove module. Without commands, the status stays `Subscribed`, line 3 shows `No live result` 2 s after the last result, `Received` stops rising, and `CommsNextResult` returns 0. Idle after subscribing has no deadline on the phone, so it does not disconnect (design reason 8); the receiver kept its connection through about 129 s without input on 2026-09-21 (see "How to run and verify"). The two gloves gate independently, so results from one glove can continue while the other is still. Stillness is not the only cause of a pause. With the real glove module (a `-glove` build), a glove sends only from its MOVING decision until its IDLE decision. The detector evaluates a 1 s window every 200 ms (`hardware/gloves/integration_files/glove_sensor.cpp:46-50`). MOVING needs two positive evaluations in a row, so it comes about 0.2 to 0.4 s after the window first crosses the threshold. IDLE needs three negative ones in a row, so it comes about 0.4 to 0.6 s after the window falls below it (`glove_sensor.cpp:381-389`). The window keeps motion samples for up to 1 s after the movement ends, so the IDLE decision comes about 0.4 to 1.6 s after the movement itself ends, depending on how long the window stays above the threshold. Samples before the MOVING decision are never sent, so they never give results. After a failed sensor reading, a non-finite sample or more than 100 ms between two `gloveUpdate` calls, the module resets its movement detector (`hardware/gloves/integration_files/glove_sensor.cpp:485-497,533-536`), and the glove then sends nothing for at least about 1.2 s, even in the middle of a gesture. These are properties of Siqiang's module (hand-off 7.1, issues 2 and 3), not faults of the phone. The laptop stand-in `laptop/phone_simulator.py` is different: it times out after 5 s without a result (see "Reference implementation constants"), so with gated gloves it needs `--reconnect`.
- On 2026-09-21, one 60 s run left the phone 109 results short. The cause is still unknown (`docs/archive/test-evidence/dual-esp-iphone-test-2026-09-21.md:41-49`).
- `patch_export.py` accepts only known hashes. After a fresh export from `vis/` it refuses, with `Unknown receiver source; expected the verified sanitized import.`. It is not needed for the next build: Jie Ling exports the Xcode project from a Unity project whose C# already calls the functions, so the new export needs only the link, which Jie Ling makes with the owner's steps (hand-off 7.3 and section 8, item 7).
- `configure_xcode.py` depends on fixed Xcode object IDs. It also has three hard conditions for a new export: `UIRequiredDeviceCapabilities` in `Info.plist` must include `arm64`, `metal` and `arkit`, otherwise it reports `Unknown Unity app Info.plist` (`configure_xcode.py:158-159`); `process_symbols.sh` must start with `#!/bin/sh` (`configure_xcode.py:152-153`); each of the five anchors in the project file must appear exactly once, including the line `00000000008063A1000160D3 /* UnityRuntime.framework in Frameworks */` (`configure_xcode.py:121-148`). Whether these hold for a new export has not been verified. The owner's proposal (hand-off 6.4, not yet confirmed by Jie Ling) is that Jie Ling pushes the Unity changes on Sat 10-17 and, once the owner has pushed `CommsNextResult` (Sun 10-18 at the latest), exports the project, adds `CommsNative`, and builds and installs the app on Jie Ling's iPhone before the session on Tue 10-20.
- `verify-import.py` checks the import baseline and applies only to a freshly imported, unpatched project. In the current working copy, at least 4 files differ from the baseline on purpose: `Assembly-CSharp.cpp`, `project.pbxproj`, `Info.plist`, `process_symbols.sh`. Running it on the current `xcode-export/` therefore reports `Changed or incomplete` and ends with `IMPORT_CHECK_FAILED`. That is expected (`verify-import.py:32-33,41-43`).
- Building for iOS, signing and installing need a Mac with Xcode whose Swift is 6.1 or newer. On the Windows laptop the package compiles and passes its 72 tests only on Linux, in a Docker container. On the owner's Mac on 2026-10-16 (Xcode 26.2) it passed 73 tests on macOS, the `NativePreview` app built and passed its tests on the iOS Simulator, and the Week 7 export built unsigned for a generic iOS device (see "Build status of the Swift and C# code"). The app has not been signed, installed or run on a phone.
- The Week 7 export is a device-only project (`SUPPORTED_PLATFORMS = iphoneos`, `ARCHS = arm64`), so it cannot be built for the iOS Simulator. Only `NativePreview` runs the native code on a simulator.
- Every build of the export rewrites three tracked IL2CPP byproducts with machine-specific content (output path, job count, SDK path; for example the exporter's iPhoneOS26.5.sdk against iPhoneOS26.2.sdk on the owner's Mac): `Il2CppOutputProject/Source/il2cppOutput/compile-data.json`, `il2cpp-compile.traceevents` and `profile.json` in the same folder. Restore them with `git checkout -- <those three files>` after a build and before committing; never commit the rewritten versions. `Il2CppTempDirArtifacts/` is Git-ignored.
- Choosing a team in Xcode's Signing & Capabilities writes the team ID into `project.pbxproj`, and Xcode 26 may also re-save the whole file (for example `objectVersion` 46 to 60; such a re-save from the `Week7Native` era sat uncommitted on the Mac's local `main` and was stashed on 2026-10-16, not discarded). Do not commit either: check `git diff`, then restore `project.pbxproj` with `git checkout --` before committing. Rerunning `configure_xcode.py` empties the `DevelopmentTeam` target attributes but leaves any `DEVELOPMENT_TEAM` build setting Xcode wrote, so it does not fully remove a chosen team. If the bundle identifier `com.CookingCompany.unityTutorial` is already registered to another team, Xcode's automatic signing asks for a different one; that is the owner's choice.
- The C# reference compiled only against the .NET 10 libraries (C# 7.0, and inside the PowerShell 7 self-test), not against .NET Standard 2.1 or in Unity. `CommsPhoneReceiver.cs` was checked by reading only.
- `xcode-export/` has 275 Git LFS files. It cannot be built without pulling them.
- The Python and C# reference receivers have no "terminal error" class. With a wrong CA, or on a result that breaks the version-3 rules, they keep reconnecting.

### Current deployment state (2026-10-15, afternoon; the Mac run of 2026-10-16 added)

The following comes from hand-off document section 6.3. The repository cannot replace a check on the devices. Nothing was installed on the iPhone or deployed to the Ultra96 during the version-3 work, on 2026-10-15, or in the Mac run of 2026-10-16:

- The iPhone has the Week 7 build of the app: button text `Week 7 Connect`, session `week7-demo` (`ios-visualizer/README.md:11,26`, `NATIVE-INTEGRATION.md:87,89`). It predates version 3: it accepts only results of version 1 or 2 with the dummy labels `REST`, `FIST`, `OPEN`, `POINT` and confidence 1, shows `DUMMY inference` on line 1 and the literal `confidence 1.0` on line 3 (see "Display text"), and has no `CommsNextResult` (by its `Week7Native` source it exports only the three `Week7*` functions). **It cannot read version-3 results**: a version-3 result, a model label or any other confidence is a terminal error on it. The current source has the button `Communications Connect`, session `ltc-comms`, version 3 and `CommsNextResult`. It is compiled and tested on Linux (72 tests) and macOS (73 tests). On 2026-10-16 the Week 7 export was rebuilt from it on the owner's Mac, unsigned, for a generic iOS device. That build is not signed or installed, so the iPhone still has the Week 7 build that was used on 2026-09-28. To replace it, the owner chooses their own signing team in Xcode and runs the `Unity-iPhone` scheme on the iPhone, which rebuilds the app signed and installs it; the unsigned app in DerivedData is not installed as it is (hand-off 6.3, step 4; see "How to run and verify").
- The service on the Ultra96 should still be the code snapshot from 28 September (version 2), with session `week7-demo`. Nobody has logged in to check. That process was not started with `demo.py service --start`. The untracked `.week7-local/co_deploy.py` started it in the background (`subprocess.Popen` with `start_new_session=True`), with its output in `BOARD_ROOT/evidence/` and its PID in `BOARD_ROOT/evidence/server.pid`. It does not depend on an SSH session and may still be running. Look for it there when redeploying; the recorded PID is historical and must be verified before use ([detail chapter 4](04-ultra96-service-and-certificates.md)). The phone app and the board service must use the same session ID. If only one side changes, the phone keeps showing `Disconnected: connection closed; retrying`. The redeploy to version 3 with session `ltc-comms` is one command with `tools/deploy_service.py`, run by the owner (hand-off 6.3, step 1; [detail chapter 4](04-ultra96-service-and-certificates.md)).
- Only the laptop's copy of the server certificate was checked. It is the certificate deployed to the board in September, and it expired at 2026-10-06 15:11:29 UTC. Whether the board's certificate was replaced later has not been checked, so the board's certificate is not verified as expired. The CA is valid until 2027-09-06, and its SHA-256 matches `EnrolledTrust.caSHA256` in `Configuration.swift`. A renewed server certificate from the same CA (valid 2026-10-14 14:22:35 to 2026-11-13 14:27:35 UTC) is ready on the owner's laptop, outside the repository, and not yet on the board (hand-off 4.8 and 6.3). Because the CA is unchanged, the phone source does not need to change.
- The existing `xcode-export/` is already patched and linked with `CommsNative`. `patch_export.py` and `configure_xcode.py` can be run again safely; on the owner's Mac on 2026-10-16 both ran and changed nothing. Its `Package.resolved` already held the tested pins but a stale origin hash (that of the old `Week7Native` graph), so Xcode floated two pins when it resolved again; the commit with these documents replaces only that origin hash. The unsigned rebuild of 2026-10-16 picked up the version-3 `CommsNative` from the working copy, but its generated code still calls only the three `Week7*` functions, so it shows the text and never calls `CommsNextResult`.

What must happen next on the phone side, in order (hand-off 6.3, steps 3 to 5, and section 8, item 7; the owner's work; steps 1 to 3 need a Mac with Xcode whose Swift is 6.1 or newer):

1. `swift test --package-path ios-visualizer/CommsNative`, in a checkout of `comms/protocol-v3`. **Done on 2026-10-16** on the owner's Mac, with the branch checked out from the fork at `e555f77`: 73 tests, 0 failures. Beyond the Linux run of 2026-10-15 (72 tests), this compiled the Apple branches of `Configuration.swift` (CryptoKit, Security) and ran `PythonBoardTests`. There was no build or test failure, and no source change was needed.
2. The `NativePreview` simulator build and tests (see "How to run and verify"). **Done on 2026-10-16:** the preview app built for the iOS Simulator, the first compile of the `#if os(iOS)` code (`IntegrationController.swift`, `SetupViewController.swift` and the iOS branches) since the changes of 2026-10-14 (version 3), with 0 errors and 0 warnings in those files; `CommsNativeTransport` passed 34 tests and `CommsNativePreview` passed its 1 UI test.
3. Rebuild the existing Week 7 export from the current source and install it on the owner's iPhone (`patch_export.py`, `configure_xcode.py`, then Xcode). This is the owner's test app; it lets the phone subscribe to the redeployed `ltc-comms` service before Jie Ling's game build exists. **Partly done on 2026-10-16:** both scripts ran and changed nothing, the stale origin hash in the export's `Package.resolved` was replaced so that Xcode keeps the tested pins, and the export built unsigned for a generic iOS device, linking the `CommsNative` C functions. Left for the owner: choose their own signing team in Xcode, build and install on the iPhone (Xcode rebuilds the app signed; the unsigned build is not installed as it is); then restore the three IL2CPP byproducts and do not commit the team ID that Xcode writes (see "How to run and verify", export project).
4. Acceptance against the board once it is redeployed (hand-off 6.3, step 1), with the board running the built-in dummy model (see "How to run and verify").
5. Push `CommsNative` with `CommsNextResult` to the team repo with short steps for adding it to an Xcode project, and tell Jie Ling (hand-off 8, item 7). Since 2026-10-16 `CommsNative` with `CommsNextResult` is in the team pull request #19, open and not merged when this chapter was updated (hand-off 6.2); the short steps are not written yet.

Planned phone-side steps up to the in-person integration session on Tue 2026-10-20 (from the owner's plan in hand-off 6.4; Jie Ling's dates are proposals until Jie Ling confirms them):

| Date | Phone-side step | State (2026-10-15, afternoon; the Sat 10-17 row updated on 2026-10-16) |
|---|---|---|
| Thu 10-15 | Board service redeployed from current source (session `ltc-comms`) with the renewed server certificate; Jie Ling answers whether the timing works | Not done: needs the owner's login. The certificate is renewed locally. The deploy tool is written; its board-side half was verified in WSL (27/27 checks), and its SSH and upload half has not run yet |
| Fri 10-16 | The three Python and C# label and confidence checks accept model labels and real confidence | Done early: Python built; C# whole file compiled and self-test passed (113 checks, PowerShell 7, 10-15) |
| Sat 10-17 | On the Mac: `Protocol.swift` accepts model labels and real confidence; `CommsNextResult` and the `confidence` field in the Swift client; the existing Week 7 export rebuilt from current source and installed, so the phone can subscribe to `ltc-comms`; Jie Ling pushes the Unity project changes to the team repo (`vis/`): the C# that calls the Communications functions, with the 5005 listener removed; the owner pushes `CommsNative` with `CommsNextResult` and the steps for adding it, and tells Jie Ling | Swift written early (10-14); compiled and tested on Linux in a Swift 6.1 container on 10-15 (72 tests). On the Mac on 10-16: tests passed (73 on macOS; 34 transport tests and 1 UI test on the iOS Simulator), and the Week 7 export rebuilt from current source, unsigned. `CommsNative` pushed to the fork and in the team pull request #19 on 10-16 (not merged); the steps for adding it not written. Signing and the install not done |
| Sun 10-18 | Jie Ling exports the project, adds `CommsNative`, builds and installs the app on their iPhone (Sun or Mon), and tells the owner about any problem | Teammate step |
| Mon 10-19 | Full dry run: gloves → laptop → Ultra96 → model → phone → game | Not done |
| Tue 10-20 | In-person integration; Jie Ling has the Unity project on a laptop, to change and push if needed | Not done |

Between the board redeploy and the installation of the rebuilt phone app, the installed Week 7 app (session `week7-demo`) cannot subscribe to a service that uses `ltc-comms`; it keeps showing `Disconnected: connection closed; retrying`. Even with a matching session it could not read the version-3 results. The package now builds and passes its tests on the Mac, and the Week 7 export builds from the current source (2026-10-16, unsigned). Installing the app signed, which Xcode rebuilds when the owner chooses a signing team and runs it on the iPhone (hand-off 6.3, step 4), closes that gap.

### Week 7 names that stay unchanged

| Name | Location | Notes |
|---|---|---|
| TLS host name `ultra96.week7.internal` | `CommsClient.swift:142`, `phone/receiver.py:17`, `CommsPhoneCore.cs:365`, `common/tls.py:4`, `tools/generate_comms_pki.py:24` | Written into the server certificate. Renaming it means reissuing the certificate and reinstalling the app |
| `Week7Start`, `Week7CopyDisplay`, `Week7Stop` | `DisplayMailbox.swift:85-95`, `patch_export.py:26-28` | The generated code in the Week 7 export calls these three names. `CommsNextResult` has no `Week7*` wrapper |
| iOS legacy data directory `Application Support/Week7` and file `week7-ca.pem` | `IntegrationController.swift:18`, `Configuration.swift:79` | Read-only fallback |
| App display name `Week 7 Visualizer` and the local network usage text | `configure_xcode.py:160,162` | The name shown on the home screen |
| Environment variable `WEEK7_ALLOW_SYMBOL_UPLOAD` | `configure_xcode.py:151-156` | Switch for symbol upload |
| Temporary file prefixes `.week7-configure-`, `.week7-receiver-` | `configure_xcode.py:95`, `patch_export.py:190` | Exist only briefly during an atomic replace |
| Comments in the generated code: `Week 7 native client bridge`, `Week 7 display layout declarations`, `End Week 7 display layout declarations` | `patch_export.py:25,31,44` | Changing them changes the patch hash |
| iSH SSH config file name `week7-ish-password.conf` and host alias `week7-ultra96` | `phone/ish_control.py:192-195` | A file and an alias that already exist in iSH on the phone; left over from the historical iSH route |

### Where documents disagree with the code (the code wins)

- `ios-visualizer/README.md:3` says the exported Unity project is outside this repository handoff. This working copy (the fork) has it, patched and linked. Since 2026-10-16 the last sentence of `README.md:3`, and `NATIVE-INTEGRATION.md:3`, name the team repository, which is correct. The "Git layout" section of `AGENTS.md` explains that local `main` carries it and the team repo does not.
- Lines 57-59 of the design specification and IOS-22 say the first result has a 30 s grace period. In the code, idle after subscribing has no deadline at all (`Subscriber.swift:41-43`).
- Selected design decision 31 says the Python receiver waits 30 s for the first result. The code uses `allow_idle=True`, with no deadline (`phone/receiver.py:180`).
- Lines 17-18 of the design specification say three methods are replaced. The code replaces four; the extra one is `ListenLoop`.
- `vis/README.md:39` says the phone runs a TLS server on port 5005. That contradicts the network model, and the Week 7 export has emptied that code.
- The technical report uses the old names `Week7Native`, `Week7Core`, `Week7Transport`, `Week7Bridge`, `Week7Client`. They are now `CommsNative`, `CommsCore`, `CommsTransport`, `CommsBridge`, `CommsClient`.

### History and removed items

- The session ID used to be `week7-demo`. It changed to `ltc-comms` on 2026-10-08. The source now uses `ltc-comms` everywhere, but the installed app and the board service may still use the old value (see "Current deployment state").
- The button text of the app installed for Week 7 is `Week 7 Connect`. The current source has `Communications Connect`, which takes effect only after a rebuild and reinstall.
- On 2026-10-14 the Week 7 compatibility code was removed (commits `28db0b3` and `b414696`, merge commit `5db56ad`; before the history rewrite described in hand-off 6.2 they were `d2fff21`, `5f2c12a` and `4c2b078`). After it only `LC` packets and `LCS1` statistics were accepted (version 3 later that evening moved the statistics marker to `LCS3`), `.week7-local` is no longer read, and the session for `demo.py service --start` comes from `--session-id`, `LTC_COMMS_SESSION` or the default `ltc-comms`. These changes are on the laptop and firmware side (see [detail chapter 2](02-firmware.md) and [detail chapter 3](03-laptop-relay-and-tools.md)); the phone code never dealt with packet magic. Only two things changed on the phone side with it. The wrong host name in the tests and in the test certificate generator changed from `wrong.week7.internal` to `wrong-host.internal` (`LocalPeers.swift`, `TransportTests.swift`, `generate_test_pki.py`, `CoreSelfTest.cs`, `test_receiver.py`). The working directory of the iSH script changed from `week7-control` to `comms-control`, while its SSH config file name and host alias stayed.
- Before 2026-09-21 the Swift client also applied a 5 s deadline between two results, and the design specification had a "30 s grace for the first result". "No deadline for idle after subscribing" replaced both.
- iSH plus Python was the iPhone route chosen on 2026-09-07 and tested on 2026-09-08 (selected design decision 29). The native Swift client replaced it.
- In the technical report period the modules were named `Week7Native` and so on, and the package exported only `Week7Start`, `Week7CopyDisplay` and `Week7Stop`. They were renamed to `Comms*` on 2026-10-08 (`caf330e`), which added the `Comms*` C functions and kept the three `Week7*` names as wrappers. The installed Week 7 app was built before the rename.
- Until the evening of 2026-10-14 (commit `c42b386`), the phone side accepted two result versions. Version 1 had 9 fields and its label had to equal `["REST","FIST","OPEN","POINT"][seq % 4]`, the label rule of the deterministic dummy data. Version 2 added `request_id` (10 fields) and allowed any of the four labels. Both required confidence equal to 1. The Swift `GestureResult` had no confidence field, the display showed `Communications • DUMMY inference` and the literal `confidence 1.0`, the setup form showed `DUMMY gestures · session ltc-comms`, and the C# overlay said `B07 Communications dummy receiver`. Protocol version 3 replaced all of this in commit `57a3fbd` on branch `comms/protocol-v3` (the board-side rules came in `a34c467`; the review fixes in `a4b907b` changed no phone code). The installed Week 7 app still behaves the old way.
- Until the same evening, this chapter described `CommsNextResult` as planned and not built, under the heading "Planned: per-result function `CommsNextResult`". It was implemented as proposed. The rules that the proposal left open were settled in the code: the negative return is −(byte count + 1), a null buffer counts as too small, a stop empties the queue without counting, and the two counters reset on a new Connect (hand-off 6.5, D14). The extension point for model labels and real confidence was likewise retitled from "accept model labels and real confidence" once it was done in the source.
- Until the same evening, `ios-visualizer/README.md` and `NATIVE-INTEGRATION.md` told new integrations to use only `CommsStart`, `CommsCopyDisplay` and `CommsStop`, and the README called the shown result "simulated". This chapter listed that under "Where documents disagree with the code". With version 3 both files were rewritten in the working tree of `comms/protocol-v3`: the rewrites name `CommsNextResult` as the game input, mark the Swift changes as written, not compiled, and describe the labels as whatever the board's model sends. Both branches carry these 2026-10-14 rewrites (`comms/protocol-v3` with the documents; `comms/protocol-v3-team` first in `ab3c7f6`, and since its rebuild on 2026-10-15 in `09dc603`). On 2026-10-15 both files were updated again in the working tree of `comms/protocol-v3` (Swift compiled and tested on Linux, the Swift 6.1 minimum, a Linux test section). At the time of writing that update was not committed and not on the team branch (see "Files only on the fork, not in the team repo").
- Until 2026-10-15 no Swift of version 3 had been compiled: the laptop had no Swift toolchain, and this chapter called all the Swift changes written, not compiled, with `swift test` on a Mac as their first compile. On 2026-10-15 the package compiled and passed 72 tests on Linux in a Swift 6.1 container, after the Linux build fix `6583f9d`. Likewise, until 2026-10-15 only the changed `GestureResult` and `PhoneProtocol` section of `CommsPhoneCore.cs` had been compiled (C# 5, 88 contract checks), and `run_core_tests.ps1` had not run since version 3. With the .NET SDK and PowerShell 7 installed that day, the whole file compiled and the self-test passed 113 checks. See "Build status of the Swift and C# code".
- Until 2026-10-16 the `#if os(iOS)` code, the Apple branches of `Configuration.swift`, `PythonBoardTests` and `NativePreview` had not been compiled since version 3. This chapter called the package not yet built for iOS, and the `#if os(iOS)` code and `NativePreview` written, not compiled. The Mac run of 2026-10-16 compiled all of them and ran their tests (see "Build status of the Swift and C# code"). Until the same run, the Unity export's `Package.resolved` held the tested pins but carried the origin hash of the old `Week7Native` package graph, so Xcode resolved the packages again and moved two of them past the tested pins; the commit with these documents replaces only that origin hash.

## How to run and verify

What has run for version 3 on the Windows laptop:

- The full Python suite, `python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider`, which includes `phone/tests` and the Python receiver: at `3b94990`, 778 passed and 4 skipped, or 779 passed and 3 skipped with `B07_LINUX_DEPLOY_TEST=1` (hand-off 6.2); at `d582ce6` (2026-10-15), 841 passed and 4 skipped.
- The first Windows command below: 62 passed and 1 skipped, at `3b94990` and again at `d582ce6` while this chapter was updated (the skipped iSH test needs local POSIX OpenSSH tools; `g++` was present, so the compiled-method test ran). `phone/tests` alone gives 44 passed and 1 skipped (at `3b94990`).
- The C# self-test (second Windows command): `PASS 113` on 2026-10-15, in four runs and once more while this chapter was updated. Before that, on 2026-10-14, only the changed C# section had been compiled, with the C# 5 compiler of Windows PowerShell 5.1 (`Add-Type`), and run against 88 contract checks.
- `CommsPhoneCore.cs` alone at C# 7.0: 0 errors, 0 warnings (2026-10-15).
- The Swift package on Linux in the `swift:6.1` container (`swift build --build-tests` and `swift test` on a copy of the package with `reference/` beside it, as the Docker command below does): 72 tests, 0 failures, in six runs on 2026-10-15. When this chapter was first updated, only the command's mount and `swift --version` (6.1.3) were checked, not a full rerun, and the command then mounted only the package. A later full run of that command at `d582ce6` gave 72 tests with 2 failures: the two `ConfigurationTests` that read `reference/teammate-localhost-cert.pem` could not find it. The command in this chapter still mounted only the package until a review on 2026-10-16 (+08:00) corrected it. The corrected command below then ran in full at `4c6ab4c` (no phone file changed after `d582ce6`), Swift 6.1.3: 72 tests, 0 failures (`ConfigurationTests` 6, `DisplayMailboxTests` 4, `DisplayStateTests` 15, `ProtocolTests` 13, `TransportTests` 26, `TrustTests` 8).

What has run on the owner's Mac on 2026-10-16 (the Mac and export-project commands below, from the repository root, at `e555f77`; Xcode 26.2, Swift 6.2.3; details under "Build status of the Swift and C# code"):

- `swift test`: 73 tests, 0 failures (the six suites of the Linux run and `PythonBoardTests` 1).
- `generate_test_pki.py`, `xcodegen generate` (XcodeGen 2.46.0) and the `CommsNativePreview` build for the iOS Simulator: `BUILD SUCCEEDED`. The scheme `CommsNativeTransport`: 34 tests, 0 failures (`TransportTests` 26, `TrustTests` 8). The scheme `CommsNativePreview`: 1 UI test, 0 failures.
- `patch_export.py` printed `EXPORT_PATCH_OK: already applied` and `configure_xcode.py` printed its success line; neither changed a file.
- After the stale origin hash in the export's `Package.resolved` was replaced, the unsigned device build of the Week 7 export: `BUILD SUCCEEDED`, and the `nm` link check below.

What has not run: signing the app, installing it on the iPhone, and anything on the iPhone or the Ultra96. The stand-in commands below were not run while this chapter was updated.

Windows, repository root (PowerShell):

```powershell
python -m pytest phone/tests tests/test_ios_export_patch.py -q -p no:cacheprovider
& "$env:USERPROFILE\.dotnet\tools\pwsh.exe" -NoProfile -File phone/tests/run_core_tests.ps1
```

- To run all Communications tests, use `python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider`. Do not run `python -m pytest` without paths from the repository root (`AGENTS.md`, Rules item 4).
- The loopback TLS tests in `test_receiver.py` need `cryptography` (`requirements-dev.txt`).
- `test_ios_export_patch.py` needs the import baseline object in repository history. Without a C++ compiler (`clang++` or `g++`), it skips the test that compiles and runs the methods (`test_ios_export_patch.py:219-222`).
- The C# self-test needs PowerShell 7, because the whole `CommsPhoneCore.cs` uses C# 6 and 7 features; Windows PowerShell 5.1 compiles only C# 5. On this laptop PowerShell 7.6.7 is a .NET global tool at `%USERPROFILE%\.dotnet\tools\pwsh.exe`, and the .NET SDK 10.0.402 is installed per user in `%USERPROFILE%\.dotnet` (with Microsoft's `dotnet-install.ps1`). Neither is on `PATH`, so call them by full path; on a machine where `pwsh` is on `PATH`, `pwsh -NoProfile -File phone/tests/run_core_tests.ps1` is the same. On success the script prints one line, `PASS 113 C# contract/frame/freshness checks` (`CoreSelfTest.cs:160` builds it).
- To repeat the C# 7.0 compile of `CommsPhoneCore.cs` alone, put a project file like this in a scratch folder outside the repository (with the real path of the file), then run `& "$env:USERPROFILE\.dotnet\dotnet.exe" build` in that folder. Expect 0 errors and 0 warnings. `SYSLIB0057` is suppressed for the same reason as in `run_core_tests.ps1`: the certificate constructor that .NET 9 and later deprecate is the one Unity's .NET Standard API offers.

  ```xml
  <Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
      <TargetFramework>net10.0</TargetFramework>
      <OutputType>Library</OutputType>
      <LangVersion>7.0</LangVersion>
      <Nullable>disable</Nullable>
      <ImplicitUsings>disable</ImplicitUsings>
      <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
      <NoWarn>SYSLIB0057</NoWarn>
    </PropertyGroup>
    <ItemGroup>
      <Compile Include="D:/LetThemCook/phone/unity/CommsPhoneCore.cs" Link="CommsPhoneCore.cs" />
    </ItemGroup>
  </Project>
  ```

Swift on Linux (Windows laptop with Docker Desktop, repository root, PowerShell):

```powershell
docker run --rm -v "${PWD}/ios-visualizer/CommsNative:/src/CommsNative:ro" -v "${PWD}/ios-visualizer/reference:/src/reference:ro" swift:6.1 bash -c "cp -r /src /work && cd /work/CommsNative && swift build --build-tests && swift test"
```

- The image `swift:6.1` (Swift 6.1.3) is already on this laptop. Docker Desktop's `docker` is on `PATH` (`C:\Program Files\Docker\Docker\resources\bin`).
- The command mounts the package and `ios-visualizer/reference/` read-only, side by side, and builds a copy of both inside the container, so nothing is written to the working tree. Two `ConfigurationTests` read `reference/teammate-localhost-cert.pem` beside the package (`ConfigurationTests.swift:15-16,74-75`); without it they fail with `The file doesn't exist`. The container is removed afterwards, so every run fetches the pinned dependencies from GitHub again; it needs internet access.
- On success `swift test` reports 72 tests with 0 failures (the six suites listed under "Build status of the Swift and C# code").
- This proves only the platform-independent code. It does not compile the `#if os(iOS)` code or `PythonBoardTests`, and it does not replace the Mac build.
- Use Swift 6.1 or newer: the pinned dependencies need Swift 6.1 tools.
- "Test the source on Linux" in `ios-visualizer/NATIVE-INTEGRATION.md` and the Docker command in hand-off section 11 now mount `ios-visualizer/reference` as well (corrected on 2026-10-16, before the Mac run). Before that they copied only the package, and the same two `ConfigurationTests` failed there. [Detail chapter 6](06-tests-operations-extension.md) (section A, step 8) also keeps `reference/` beside the package.

Mac, repository root (Xcode whose Swift is 6.1 or newer; check with `swift --version`). `swift test` builds for macOS: it compiles the Apple branches and runs `PythonBoardTests`, but not the `#if os(iOS)` code. The `xcodebuild` commands build for the iOS Simulator and compile the `#if os(iOS)` code (see "Build status of the Swift and C# code"):

```sh
swift test --package-path ios-visualizer/CommsNative
python3 ios-visualizer/NativePreview/tools/generate_test_pki.py
xcodegen generate --spec ios-visualizer/NativePreview/project.yml
xcodebuild -project ios-visualizer/NativePreview/CommsNativePreview.xcodeproj -scheme CommsNativePreview -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -jobs 4 build
xcodebuild -project ios-visualizer/NativePreview/CommsNativePreview.xcodeproj -scheme CommsNativeTransport -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -jobs 4 -parallel-testing-enabled NO test
xcodebuild -project ios-visualizer/NativePreview/CommsNativePreview.xcodeproj -scheme CommsNativePreview -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -jobs 4 test
```

- All six commands ran on the owner's Mac on 2026-10-16 (Xcode 26.2, iPhone 17 Pro simulator with iOS 26.3). Expected results, as seen then: `swift test` reports 73 tests with 0 failures; the build ends with `** BUILD SUCCEEDED **`; `CommsNativeTransport` runs 34 tests and `CommsNativePreview` 1 UI test, each ending with `** TEST SUCCEEDED **`. If the Mac's Xcode has no iPhone 17 Pro simulator, use a simulator it has.
- On success, the certificate generator prints `Generated 12 isolated test authorities: 8 valid, 2 wrong-host, 2 expired. Credentials were not printed.`.
- `xcodegen` is XcodeGen; the owner's Mac has 2.46.0 from Homebrew. The generated `CommsNativePreview.xcodeproj` and `.comms-local/CommsFixturePKI` are Git-ignored.
- `PythonBoardTests` (macOS only, inside `swift test`) starts `python3 -m ultra96.server` from the repository, so it needs Python 3 on the Mac and the version-3 `ultra96/` and `common/` of the same checkout. On the owner's Mac `python` is not on `PATH`, and `python3` is `/usr/bin/python3` (Python 3.9.6), which ran the test and the scripts here. Use `python3` on such a Mac wherever another document writes `python`; the `python` commands in the hand-off document are for the Windows laptop (hand-off 9.2).
- These tests verify only the source and loopback peers. They cannot prove that the Unity build, reception on a device or signing work.

Export project (Mac, repository root):

```sh
python3 ios-visualizer/tools/patch_export.py
python3 ios-visualizer/tools/configure_xcode.py
xcodebuild -project ios-visualizer/xcode-export/Unity-iPhone.xcodeproj -resolvePackageDependencies
xcodebuild -project ios-visualizer/xcode-export/Unity-iPhone.xcodeproj -scheme Unity-iPhone -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build
```

- In the current working copy, the hash of `Assembly-CSharp.cpp` equals the "current patch" hash in the script, so the first command should print `EXPORT_PATCH_OK: already applied`. It did on 2026-10-16, and the file's SHA-256 was the same before and after.
- On success the second command prints `Configured local CommsNative package; signing stays operator-owned.`. On failure it prints a line that starts with `XCODE_CONFIGURE_FAILED:`. On 2026-10-16 it succeeded and `project.pbxproj`, `Info.plist` and `process_symbols.sh` stayed byte-identical: the export was already configured (the local package `../CommsNative` linked into `UnityFramework`, `DevelopmentTeam = ""` and `DEVELOPMENT_TEAM = ""`).
- The third command should resolve swift-asn1 1.7.2 and swift-collections 1.6.0, the pins of `CommsNative/Package.resolved`, and leave the export's `Package.resolved` unchanged; it did on 2026-10-16, after the stale origin hash in that file was replaced. If `git status` then shows that `Package.resolved` changed, Xcode moved the pins away from the tested versions; check the change before building or committing.
- The fourth command builds the app for a generic iOS device without signing (`ReleaseForRunning`, arm64). The export is device only, so it cannot be built for the simulator. On 2026-10-16 it ended with `** BUILD SUCCEEDED **` and produced an unsigned `unityTutorial.app` (`CFBundleDisplayName` `Week 7 Visualizer`, bundle identifier `com.CookingCompany.unityTutorial`, minimum iOS 15.0) in `~/Library/Developer/Xcode/DerivedData/Unity-iPhone-*/Build/Products/ReleaseForRunning-iphoneos/`. It ran the IL2CPP step (588 C++ objects into `libGameAssembly.a`; that step alone took about 154 s). It had 21 warnings, none in Communications sources (Unity and ARKit deprecations, ARKit precompiled-module paths from the exporter's machine, run-script phases without outputs, the missing 1024×1024 App Store icon, one `not stripping binary because it is signed`).
- Link check, in that products folder: `nm -u libGameAssembly.a | grep -E 'Week7|Comms'` lists `_Week7Start`, `_Week7CopyDisplay` and `_Week7Stop` (the calls of the patched code); `nm -gU UnityFramework.framework/UnityFramework | grep -E 'Week7|Comms'` lists those three and `_CommsStart`, `_CommsCopyDisplay`, `_CommsStop` and `_CommsNextResult`; and `nm -u` on `UnityFramework` lists no `Week7` or `Comms` symbol. That shows the patched receiver's calls resolve to the `CommsNative` wrappers in the app's `UnityFramework`, and that nothing in the export calls `_CommsNextResult`. It does not show that the app runs.
- After every build, restore the three tracked IL2CPP byproducts that the build rewrites: `git checkout -- ios-visualizer/xcode-export/Il2CppOutputProject/Source/il2cppOutput/compile-data.json ios-visualizer/xcode-export/Il2CppOutputProject/Source/il2cppOutput/il2cpp-compile.traceevents ios-visualizer/xcode-export/Il2CppOutputProject/Source/il2cppOutput/profile.json`. After a build they hold machine-specific paths; never commit those versions.
- Left for the owner (not done on 2026-10-16): open `ios-visualizer/xcode-export/Unity-iPhone.xcodeproj` in Xcode, choose your own signing team under Signing & Capabilities, and run the `Unity-iPhone` scheme on the phone. The unsigned app in DerivedData is not installed as it is: Xcode rebuilds it, signs it and installs it. Xcode also writes the team ID into `project.pbxproj` and may re-save the whole file. Do not commit that: check `git diff`, then restore `project.pbxproj` with `git checkout --` before committing. Rerunning `configure_xcode.py` empties the `DevelopmentTeam` target attributes but leaves any `DEVELOPMENT_TEAM` build setting Xcode wrote, so it does not fully remove a chosen team (see "Known limits"). If the bundle identifier is already registered to another team, automatic signing asks for a different one; that is the owner's choice. Then restore the three byproducts above.

Without an iPhone, the stand-in subscriber on the laptop can show the results:

```powershell
python -m tools.ssh_tunnel --local-port 19999 --remote-port 9999
python -m laptop.phone_simulator --ca <public CA path> --count 0 --reconnect
```

- The first command only prints a two-hop OpenSSH local forward command. The default accounts are in the `--jump` and `--target` arguments of `tools/ssh_tunnel.py`. Run the printed command in a separate terminal. olsonwangyj runs the login.
- The stand-in subscriber displaces the phone's subscription. Close it as soon as you are done, and do not run it during a demo or integration test.
- It allows 5 s per result, so it times out whenever no result arrives for 5 s; `--reconnect` makes it subscribe again. With gated gloves this happens at every still period of 5 s or more without laptop commands, and results produced during the reconnect wait are dropped by the board (no subscriber). The phone has no such timeout.

On-device acceptance steps (preconditions: the board service runs version 3 with session `ltc-comms` and the built-in dummy model, the server certificate is valid, and the phone has the app built from the current source after the package built and passed its tests on the Mac). None of these steps has been run on version 3:

1. The phone connects to the campus VPN itself. The laptop's VPN does not provide a route for the phone.
2. Open the app and tap `Communications Connect`. On first use, import the public CA first.
3. Enter the board and jump host usernames and passwords, and tap `Connect`.
4. Wait until the screen shows `Subscribed` and `Received: 0`. Only then start sending data. Without a subscriber, the board drops results. `Subscribed` shows only that the subscription handshake succeeded; whether results flow is checked in steps 5 and 6.
5. On the laptop, open the tunnel and start the capture (`python demo.py tunnel` and `python demo.py run`; see [detail chapter 3](03-laptop-relay-and-tools.md)). The screen should show changing labels and `result_id` values; with the dummy model the labels are random among `REST`, `FIST`, `OPEN`, `POINT` and line 3 shows `confidence 1.0`. If a board runs gated firmware (a `-glove` build, or the dummy build with `COMMS_DUMMY_IDLE_MS` set; [detail chapter 2](02-firmware.md)), that board's results for samples arrive only while its glove module reports MOVING (the gated dummy alternates fixed moving and idle phases; the `cmd:` results of laptop commands arrive either way), and line 3 shows `No live result` once a pause lasts 2 s.
6. After the capture, compare the increase in `Received` with `Phone expected increase` in the `demo.py` output. Equal values are an aggregate-level pass, which is evidence level 5. The comparison holds only with the built-in dummy model (one result per accepted sample or command), as `demo.py` prints.
7. Lock and unlock the screen. `Paused — return and connect again` should appear. After entering the passwords again and connecting, `Received` starts from 0.

Existing on-device evidence (all from before the rename on 2026-10-08, using the Week 7 app and session `week7-demo`; all of it with version 1 or 2 results, none with version 3):

- 2026-09-21, updated native receiver: four captures. A 60 s baseline with 1,202 results; 1,206 results on resuming after about 129 s without input; 621 results through a manual VPN recovery; 12,003 results in 600 s after a screen lock. 15,032 in total, and the phone's aggregate count matched every capture (`docs/archive/test-evidence/phone-post-update-test-2026-09-21.md:233-239`).
- 2026-09-21, two boards plus the iPhone: a 600 s rerun passed with 12,004 / 12,004. An earlier 60 s baseline received only 1,094 / 1,203, 109 short, cause unknown (`docs/archive/test-evidence/dual-esp-iphone-test-2026-09-21.md:3,41-49`).
- 2026-09-28: v2 results plus 6 commands, 1,320 in total (1,314 sensor samples plus 6 commands). The aggregate count matched (`docs/archive/test-evidence/co-live-deployment-2026-09-28.md:111-123`).
