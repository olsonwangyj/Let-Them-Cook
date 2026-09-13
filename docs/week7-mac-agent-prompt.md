# Autonomous Mac handoff: Week 7 iOS visualizer

Copy everything below the divider into a new GPT-6/Codex task opened in this
repository on the Mac. This is an execution request, not a request for a plan.

---

Continue my CG4002 Week 7 communications and iOS visualizer integration in this
Mac checkout of `olsonwangyj/Let-Them-Cook`. I am going to sleep. Use Superpowers
if available, and actually implement, build, test, and document everything you
can. Do not stop after a proposal, an initial review, a successful unit test, or
the first unavailable device. Work until every remaining task genuinely needs
my physical action or an unavailable external resource you cannot obtain with
the access already available.

## Authority and working rules

- Make all routine architecture, protocol-adaptation, library, implementation,
  and test decisions yourself. This includes historical TBDs, unresolved issues,
  pending approval, and TLS/security design questions. Choose the most practical
  Week 7 solution and record each material decision and its reasoning. My
  explicit autonomous authorization supersedes routine approval checkpoints in
  local plans and skills. Preserve the constraints below.
- Do not wait for me to press Enter, select a design, approve a plan, or say
  "continue". Run noninteractive commands when possible. If a command genuinely
  requires my password, MFA, Apple account consent, Keychain authorization,
  device trust, unlock, Developer Mode, or other physical action, record the
  exact action and continue independent work. Do not bypass those controls.
- Use already installed tools and existing authorized credentials first. You may
  fetch normal project dependencies and make reversible project-local setup
  changes. Do not purchase services, accept agreements for me, change account
  security, wipe devices, or perform destructive system changes.
- Preserve unrelated edits, existing evidence, keys, pairing state and services.
  Never store passwords, SSH private keys, server/CA private keys, signing
  identities, or provisioning profiles in Git, app resources, prompts or logs.
  Use private local files/Keychain and public trust anchors appropriately.
- Check Git state before edits. Create/use an isolated `codex/ios-visualizer-*`
  branch without discarding local work. Make cohesive local commits and push that
  branch to origin when possible; no force-push or automatic merge to main.
  A push failure must not prevent finishing local work.
- Delegate independent bounded reviews/tests when useful. Keep short progress
  updates, but do not turn them into questions. Maintain a task checklist and a
  current continuation report so another task can resume after compaction or an
  interruption. Do not contact teammates; draft any unavoidable request for me.
- No PDF is needed. Produce Markdown, code, scripts and test evidence.

## Read and inspect first

Locate the actual checkout; do not assume any Windows path exists on this Mac.
Check branch, status, remotes, recent commits, and applicable `AGENTS.md` files.
Read these files before choosing the implementation:

1. `ios-visualizer/README.md` and its import inventory/verification instructions.
2. `docs/week7-continuation-report-2026-09-14.md`, then the relevant sections of
   `docs/week7-continuation-report-2026-09-07.md`.
3. `docs/week7-selected-design-2026-09-06.md`,
   `docs/week7-development-plan.md`, and `docs/week7-visualizer-handoff.md`.
4. `docs/week7-phone-runbook.md`, `phone/unity/Week7PhoneCore.cs`,
   `phone/unity/Week7PhoneReceiver.cs`, and the Phone/core tests.
5. Actual teammate reference source, generated receiver implementation, Xcode
   build settings, Info.plist and dependencies under `ios-visualizer/`.

Historical unchecked gates and obsolete jump-host guesses do not override the
latest selected design and measured evidence. Add a dated Mac continuation
report; link it from the existing report and README.

The export uses Git LFS. Check that LFS objects are hydrated (`git lfs pull`, then
`git lfs fsck`) and run the documented import check before editing it. Do not
attempt to build LFS pointer text as a framework. If an LFS download is blocked,
continue work on the available source/tests and record the exact missing object.

## Scope and known integration facts

My Week 7 task is to demonstrate deterministic dummy packets travelling through
**ESP32 -> protected BLE -> Windows Laptop -> Ultra96 -> real iPhone visualizer**.
A changing gesture label, count and connection status are sufficient for the
minimal UI. Real AI/FPGA inference and a second ESP32 are outside this selected
one-ESP communications demo. Do not claim this establishes an unseen grading
rubric, multi-ESP synchronization, or actual AI accuracy.

The teammate delivery was renamed from `unity/` to `ios-visualizer/`. It contains
an **exported native Xcode/IL2CPP project**, not the original editable Unity
Editor project. The reference script is separate. Runtime metadata says Unity
6000.5.10f1; target is iOS 15+, arm64, `iphoneos`. ARKit and MediaPipe dependencies
are included. Simulator support for this export is not established.

The supplied `TlsDataReceiver.cs` is a **TLS server listening on all interfaces,
port 5005**, reading newline-delimited strings. The generated app implements the
same logic. It does not implement our framed JSON subscription client. A port
change alone cannot fix this. Its private `server.pfx` was intentionally removed;
its password was replaced with `REMOVED`, including serialized/generated copies.
The original receiver cannot run unchanged. The included reference public
certificate is self-signed for `localhost`, not our Ultra96 trust anchor.

Editing the standalone C# reference does **not** update the already generated
Xcode app. Determine what actually builds into the app before claiming an
integration. Prefer the original Unity `Assets/`, `Packages/`, `ProjectSettings/`
and scenes if they are already available on this Mac. If absent, do not stop:
finish the reusable Unity client/adapter and tests, and investigate an explicit
native iOS adapter in the exported project. Use a documented minimal native
diagnostic app only as a clearly labelled fallback, not as proof that the
teammate's Unity scene is integrated. Keep any generated-code workaround small,
reproducible, and documented for replacement on the next Unity export.

## Required networking and security contract

- Ultra96 exposes **only TCP port 22 externally, as SSH**. Working route:
  `ssh -J yanjie@stujump.comp.nus.edu.sg xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg`.
  Do not use the old unverified `stfjump` spelling.
- Board application listeners stay on `127.0.0.1`: ingestion 8888, results 9999.
  Windows owns its SSH forward, typically localhost18888 -> board8888. The Phone
  owns a separate SSH path, typically localhost19999 -> board9999. TLS runs
  inside those paths. The Laptop is not the application result relay.
- Preserve that application topology. Do not solve iOS by opening board5005,
  using UDP/plaintext, silently relaying results through the Laptop, or relying
  on the temporary reverse SSH maintenance route used for iSH administration.
- Solve iOS SSH ownership and app lifecycle explicitly. An embedded/in-process
  maintained SSH implementation is a candidate; investigate available buildable
  options, licensing, host-key verification, jump routing, credential storage,
  cancellation and reconnect before choosing. Do not assume an external iSH
  tunnel survives switching to Unity. If the exact route is blocked by missing
  credentials or device consent, implement/test everything independent of that
  access and write the remaining provisioning steps.
- TLS >=1.2; verify server certificate and identity
  `ultra96.week7.internal`. Reject wrong trust, wrong identity, expired certificates
  and plaintext. Never introduce accept-all callbacks or ship a private server
  key in the Phone. Provision the actual public Week 7 CA when available; use
  separate generated test PKI for local tests and label it clearly.
- Frames are a 4-byte unsigned big-endian **UTF-8 byte count**, followed by one
  JSON object, maximum 16,384 bytes. Handle partial/coalesced reads, bounds,
  deadlines, EOF, cancellation, strict schema and invalid UTF-8/JSON. Inspect
  existing code for the complete validation rules instead of approximating them.
- Phone sends `{"v":1,"type":"SUBSCRIBE","session_id":"week7-demo"}`;
  validate `SUBSCRIBED`, then consume `GESTURE_RESULT` for that session.
  Results include `device_id`, `boot_id`, `seq`, `result_id`, `gesture` and
  `confidence`. The ID is `<device_id>:<boot_id>:<seq>` and the deterministic
  cycle is REST, FIST, OPEN, POINT (`seq % 4`), confidence 1.0.
- Preserve bounded queues, background network processing, main-thread Unity UI,
  freshness and duplicate handling, a single writer, and explicit lifecycle
  cancellation/reconnect. Board behavior is one active subscriber per session,
  new subscriber replaces old, bounded fresh results and no offline replay.
  Do not launch diagnostic subscribers that evict the app under test.

## Execution and validation

1. Inventory macOS/architecture, Xcode/SDK, Unity installations, Python/C# tools,
   signing availability, already trusted devices, VPN and authorized routes with
   bounded read-only checks. Existing Windows BLE pairing uses WinRT; this Mac
   cannot simply run that module. Keep the verified Windows bridge unless a Mac
   port is actually necessary and separately verified. No assumed Windows remote
   control: inspect an already authorized route or use synthetic inputs.
2. Write a concrete implementation plan and decision log, then implement it.
   Compare the actual receiver, generated export and existing client. Resolve
   port/role/framing/trust/UI/lifecycle questions yourself within the constraints.
3. Build meaningful portable tests and a local TLS/framed-JSON fixture harness.
   Cover split headers/payloads, coalesced messages, invalid/oversized frames,
   wrong TLS identity/CA, malformed schema, duplicates, EOF, timeouts, cancellation,
   reconnect, stale/backlogged data and UI-thread handoff. Make failures visible;
   do not write tests that only repeat the implementation.
4. Implement and build the iOS path using actual available tools. Try appropriate
   unsigned physical-device builds without waiting for signing. Use simulator
   tests where the target supports them; a separate portable/native harness does
   not establish that the ARKit/MediaPipe Unity export runs in a simulator. Fix
   build/dependency/executable-mode errors and inspect warnings. Record exact
   commands, tool versions, configurations, exits and logs.
5. If an iPhone is already trusted, provisioned, reachable and suitable for the
   test, use existing signing to build, install, launch and collect logs without
   waiting for me. Otherwise finish unsigned builds, local/simulator tests,
   packaging and precise signing/install instructions. Never claim an unbuilt
   binary is installable, and never bypass device/account prompts.
6. If real ESP/Windows/Ultra96/Phone routes are already available, perform bounded
   dummy-data integration tests. Correlate at least 100 ordered unique packet,
   accepted ACK, board result and **actual app receipt/display** IDs, then a
   ten-minute soak with coverage and counters. Prepare app logs/export and a
   repeatable auditor so receipt can be distinguished from rendered UI. If any
   link is unavailable, test every reachable segment and explicitly mark the
   full physical chain pending.
7. Automate owned-process/socket interruption and reconnect cases where available.
   Screen lock/unlock, foreground/background observation, VPN MFA/toggling, ESP
   reset/power cycling, pairing consent and unavailable device access remain
   physical procedures if they cannot be performed through authorized controls.
   Do not pause all work waiting for those actions; prepare exact short steps,
   expected evidence and pass criteria for the morning.
8. Independently review changes, fix material findings, rerun appropriate tests,
   scan the staged diff for secrets/large files, commit and push the feature
   branch. Update setup/runbook/demo instructions for the actual final design.
   Keep LFS for imported large artifacts and avoid committing caches/build output.

## Evidence, blockers and completion

Earlier real iPhone **Python/iSH** evidence includes a clean 100-result run and a
6,100-result soak with exact ordered IDs. The soak had one callback-generation
discard; do not rewrite it as every counter zero. A controlled local-forward
interruption recovered. These are historical results, not Unity app acceptance.
The screen-lock attempt lost the management route, its final Phone capture is
uncollected, and recovery is **pending, not passed**. Preserve that distinction;
the old Windows-only evidence paths may not exist on this Mac.

Maintain a dated decision log with issue, options considered, choice, reason,
files changed, validation, and remaining limitation. Maintain a test matrix that
separates static review, portable protocol tests, simulator tests, unsigned build,
signed build, actual app test and full real-ESP chain. Record failures and skipped
tests honestly, including why they were skipped; never count them as passes.

If blocked, identify the smallest unavailable dependency and continue all other
tasks. Search available local files/tools and make bounded reasonable recovery
attempts, but do not poll an offline device indefinitely or repeatedly prompt me.
Finish the relevant architecture, interfaces, scripts, fixtures, packaging,
manual procedures and exact pass/fail criteria before stopping.

Only finish when all useful authorized work is exhausted and the remaining list
consists of concrete physical/account actions or unavailable external inputs.
Do not stop merely because a stage is complete or I have not replied. End with:
what changed; what actually passed; branch and commits; unresolved limitations;
and a short ordered list of exactly what I must do when I wake up. Include the
one command or file that resumes the next test. Do not claim the complete Week 7
iPhone visualizer works until the real app and full data path prove it.
