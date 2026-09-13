# Week 7 continuation: iOS delivery and Mac handoff — 2026-09-14

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

No new design approval is pending. These decisions supplement the 35 existing
communications/security decisions without rewriting physical acceptance.

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
  correctness. Remote publication is checked after committing below.

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
