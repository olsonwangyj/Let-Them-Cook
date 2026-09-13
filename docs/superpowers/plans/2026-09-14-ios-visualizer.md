# Week 7 iOS Visualizer Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development. The user authorizes independent decisions and continuing past routine checkpoints.

**Goal:** Integrate and verify the Week 7 framed TLS subscriber in the actual Unity iOS export.
**Architecture:** Native Swift package with strict protocol core, app-owned two-hop SSH/TLS, and a small C ABI bridge polled by the delivered TMP label. UIKit configuration is in the same package and compiled only on iOS.
**Tech Stack:** Swift 6.2 compiler in Swift 5 mode, SwiftPM, Apple SwiftNIO/SSH/SSL, UIKit, generated IL2CPP C++.
**Spec:** `docs/superpowers/specs/2026-09-14-ios-visualizer-design.md`

## Global Constraints

- iOS 15+, arm64 device app; macOS 13+ package tests. Strict TLS >=1.2, CA-only roots and `ultra96.week7.internal` hostname.
- Board and jump SSH TCP22 only; SSH direct-tcpip to board 127.0.0.1:9999, no external application ports.
- Framing 1..16384, exact Week7 schemas, session `week7-demo`, bounded 4096 dedup and newest-only 2s UI freshness.
- Preserve imported scene/metadata layout and provenance. No passwords/private keys in Git, build output, persistent settings or reports.
- Foreground only, stop and forget passwords on background. No reliance on iSH. No merge to main.

## Task 1: Protocol core and display state

Files: `ios-visualizer/Week7Native/Sources/Week7Core/{Protocol,DisplayState}.swift`, `Tests/Week7CoreTests/ProtocolTests.swift`.
Interfaces: `Week7Protocol.subscribe(session: String) throws -> [UInt8]`; `FrameDecoder.feed(_ bytes: [UInt8]) throws -> [[UInt8]]`; `Week7Protocol.subscribed(_ body: [UInt8], session: String) throws`; `Week7Protocol.result(_ body: [UInt8], session: String) throws -> GestureResult`; GestureResult immutable public `json`, `resultID`, `gesture`, `seq` properties. Display state is thread-safe, exposes monotonically fresh snapshots and generation-aware accept/clear.

- [ ] Add failing tests with literal SUBSCRIBED/result bodies, fragmented/coalesced frames, exact uint32 limits, duplicate decoded keys, wrong types/fields/session/dummy values, UTF-8 failures, overflow and frame boundaries.
- [ ] Implement bounded lexical JSON validation and framing. Example expectation: result ID `1:7:42` maps to `OPEN`; `seq:42.0` and duplicate `seq` reject.
- [ ] Test first-byte deadline policy, generation discard, reconnect dedup and 2s display expiry at controlled monotonic times; implement state without timers in core.
- [ ] Run `swift test --package-path ios-visualizer/Week7Native --filter Week7CoreTests` and report actual red/green evidence.

## Task 2: Native SSH/TLS transport

Files: `Sources/Week7Transport/*.swift`, `Tests/Week7TransportTests/*.swift` in the same package.
Interfaces: `SSHRoute` with board host/user/password/hostKey, optional jump host/user/password/hostKey and `caPEM`; `Week7Client(route:session:onStatus:onResult:)`, `start()`, `stop()`; callbacks can occur off main thread. Result callback returns Task1 GestureResult; stop invalidates callbacks and closes the entire owned root channel. Fixed production ports22/9999; test-only fixture constructors may inject ephemeral local ports internally.

- [ ] Build failing tests of exact host-key matching and CA/hostname rejection against local SSH/TLS peers; actual app uses this same transport.
- [ ] Implement NIOSSH password delegate, exact NIOSSHPublicKey comparison and direct-tcpip byte wrapper. Nest board SSH inside jump channel. TLS handler uses imported CA, `.fullVerification`, minimum `.tlsv12`, serverHostname constant.
- [ ] Send exactly one SUBSCRIBE after TLS, require SUBSCRIBED; frame deadlines5s, first ever result first-byte grace30s, reconnect0.5..5s, bounded cancellation.
- [ ] Test local two-hop success, trust/auth rejection, partial-frame deadlines, cancellation during connect/live stream, connection recovery and no retired callbacks.

## Task 3: Actual Unity bridge, private setup and reproducible build

Files: `Sources/Week7Bridge/*.swift`, `ios-visualizer/native/*`, `ios-visualizer/tools/*`, targeted exported receiver bodies/Xcode configuration.
Interfaces: C ABI `Week7Start()`, `Week7CopyDisplay(char*, int32_t)->int32_t`, `Week7Stop()`. Main-thread Unity Update calls CopyDisplay into fixed buffer, creates Il2CppString, invokes the existing TMP_Text virtual setter.

- [ ] Run import baseline check after LFS hydration; store evidence locally. Build initially with upload disabled to expose real compiler issues.
- [ ] Write reproducible guarded export patch; fail on unknown input rather than guessing. Preserve method signatures, structs, registration tables, scene and metadata.
- [ ] Add UIKit setup panel with board/jump usernames, secure password fields and CA document import. Persist only public config. Show CA SHA256 for comparison. User starts/stops session explicitly.
- [ ] Store latest result/status only; old generation cannot update text. Register background observer to close and forget credentials. Foreground shows reconnect instructions.
- [ ] Add local SwiftPM product to UnityFramework, C ABI references to generated GameAssembly, camera/local-network descriptions and export-compliance metadata as appropriate to actual included crypto.
- [ ] Build full arm64 app with `CODE_SIGNING_ALLOWED=NO`; inspect linked symbols and assets. Signing/install require real identity/device; document absent inputs.

## Task 4: Verification, review and publication

- [ ] Run existing Python suite in isolated venv plus Swift suite and local actual-package SSH/TLS rehearsals. Save bounded logs, no secrets.
- [ ] Independently review protocol/security/lifecycle and generated export integration; fix findings and rerun affected checks.
- [ ] Update README, continuation report and exact human device steps with decisions, evidence and limitations.
- [ ] Verify staged secret/whitespace checks; commit on `codex/ios-visualizer-week7-native`, push and verify remote commit. No merge or PDF.

## Rulings and progress

- Work in clean existing checkout on feature branch, avoiding duplicate large import. Agents own disjoint source directories and never commit concurrently.
- Internal SSH direct stream replaces an unnecessary local TCP19999 listener; board route and Phone ownership remain unchanged.
- Passwords remain memory-only and are discarded on pause; foreground requires explicit reconnect to avoid hidden authentication loops after sleep.
- Native first-result grace follows the current Python client decision, not the older5s C# behavior.
- Read-only context/scene audits complete; original Unity source, real Week7 CA, signing identity and attached iPhone absent initially.
- Task ownership: protocol agent owns Week7Core; transport agent owns Week7Transport; root owns package manifest, bridge/Xcode/scripts, documentation and integration.
