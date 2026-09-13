# Week 7 continuation: native iOS integration — 2026-09-14

## Current Mac outcome

The actual Unity Xcode export now contains a compatible native Phone subscriber.
It owns its SSH connection through Ultra96 TCP22, verifies the Week 7 TLS CA and
service hostname, subscribes using the existing framed protocol, and updates the
scene's existing TextMeshPro label. The old inbound TLS receiver is disabled.
The reusable implementation, tests and reproducible export scripts are in
[the native integration guide](../ios-visualizer/NATIVE-INTEGRATION.md).

**Verified:** full unsigned arm64 Unity Debug and Release builds; 54 Swift tests; 246 Python
tests (4 platform-dependent skips, 49 subtests); 26 transport/trust tests executed
inside the iOS simulator in addition to the shared native UI test; 100-result
interoperability with the actual Python board server over
two real local SSH hops. **Not verified:** signed install or execution of the
Unity app on a physical iPhone, campus VPN/account access from this app, actual
Windows BLE/ESP32 chain, or physical lock/background recovery. Historical iSH
acceptance below remains separate.

Work began on a clean `main` at `bf38f83`, equal to fetched `origin/main`, and
continues on **`codex/ios-visualizer-week7-native`**. No merge to main or PDF was
made. The original Unity source was not found in this checkout or the bounded
Documents search; its absence does not prevent this native-export build.

**Publication:** implementation commit `33f8c7e127e810b9c5071feac9aee8ba7a16c34b`
was pushed to [the feature branch](https://github.com/olsonwangyj/Let-Them-Cook/tree/codex/ios-visualizer-week7-native).
An independent `git ls-remote` check confirmed that exact remote commit and
unchanged `main` at `bf38f83d9ca3d621258ac32b8de9f3d789042651`. Staged whitespace
and credential checks passed; the working tree was clean after the implementation
commit. This publication record is a documentation-only follow-up. All available
Mac implementation, build, testing and review work is complete; the remaining
physical/account steps are listed below.

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
unchanged. The remaining actions still require a physical device, accounts or
the existing live hardware/private setup.

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
server processes are cleaned up; no institutional accounts were contacted.

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
| Device/signing discovery | `xcrun devicectl list devices`: **No devices found**. `security find-identity -v -p codesigning`: **0 valid identities**. |

Full logs and Unity builds remain in the ignored `.week7-local` directory on this
Mac; follow-up simulator products/results are under the Library path above.
They are local evidence, not a claim of remote hardware acceptance. Imported
Unity/native dependencies emit deprecation and unavailable original debug-path
warnings; the original vendor files were not broadly refactored.

## Exact next human actions

1. Open `ios-visualizer/xcode-export/Unity-iPhone.xcodeproj`. Select your Apple
   development team and an available app bundle ID; connect/unlock/trust the
   iPhone and enable Developer Mode. Run the Unity-iPhone scheme. Expected:
   Unity scene plus **Week 7 Connect**, with no attempt to load `server.pfx`.
2. Transfer the existing **public** Week 7 CA to Files. Its SHA-256 must be
   `4dfba4905c171e68c3623dbc952154149076ed89004b85d475e858cc550760ec`.
   Import it in the app, enable the required Phone VPN, enter board/jump
   usernames and passwords, and Connect. Expected: **Subscribed**.
3. Stop competing subscribers. Start the existing board service and Windows BLE
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
coding approval is pending. App-owned campus authentication, real Phone TLS,
camera/ARKit behavior and complete ESP32→BLE→Windows→Ultra96→iPhone acceptance
cannot be established from host tests or unsigned builds.

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
