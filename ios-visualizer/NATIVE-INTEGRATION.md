# Native Week 7 iOS integration

The actual exported app links `Week7Native` into `UnityFramework`. The generated
`TlsDataReceiver` calls a native C bridge from its existing Start/Update/OnDestroy
methods. Update applies the latest bounded display to the scene's existing
TextMeshPro label; the old inbound TLS server is disabled. The detached
`reference/TlsDataReceiver.cs` remains reference material.

## Build on this Mac

Requirements: Xcode with iOS support installed, Git LFS, SwiftPM network access.
The tested toolchain and final results are recorded in the continuation report.
From the repository root:

```sh
git lfs pull
git lfs fsck
python3 ios-visualizer/tools/patch_export.py
python3 ios-visualizer/tools/configure_xcode.py
swift test --package-path ios-visualizer/Week7Native
xcodebuild -project ios-visualizer/xcode-export/Unity-iPhone.xcodeproj \
  -scheme Unity-iPhone -configuration Debug -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -derivedDataPath .week7-local/DerivedData \
  -clonedSourcePackagesDirPath .week7-local/SourcePackages \
  -jobs 6 CODE_SIGNING_ALLOWED=NO
```

This builds the actual arm64 Unity app without signing. The output is
`.week7-local/DerivedData/Build/Products/Debug-iphoneos/unityTutorial.app`.
Release is also verified; replace Debug with Release to build the optimized app.
Use scheme-based builds with an explicit DerivedData directory; overriding only
`CONFIGURATION_BUILD_DIR` in a target-based build broke SwiftPM module-map paths.

The original `import-manifest.json` remains unchanged. `verify-import.py` checks
that original import, so it intentionally reports modified files after applying
this integration. The guarded patch validates the exact receiver source before
editing, or recognizes the reviewed patched version on reapplication. Do not
replace the baseline manifest to make intentional edits appear original.
Unity's compiler also rewrites tracked `compile-data.json`, `profile.json` and
`il2cpp-compile.traceevents`; these are build diagnostics, not application edits.
Restore only these generated diagnostics after a build if preparing a commit.

Dependencies are exact-version SwiftPM pins with checked-in resolved revisions.
The native package uses [Apple SwiftNIO SSH](https://github.com/apple/swift-nio-ssh)
and [SwiftNIO SSL](https://github.com/apple/swift-nio-ssl); their licenses remain
in the fetched package sources. Symbol upload is disabled by default, and the
inherited Unity upload-token settings were cleared. Builds need no Unity account.

## Sign and install the actual app

Open `ios-visualizer/xcode-export/Unity-iPhone.xcodeproj` in Xcode. Select the
Unity-iPhone scheme and your connected, unlocked iPhone. In Signing & Capabilities
select your own team and an available bundle identifier for Unity-iPhone; select
the same team for UnityFramework when Xcode requires it. The teammate's signing
team is not reused. Complete Apple account/Keychain prompts, device trust and
Developer Mode yourself, then Run. No provisioning or signing-control bypass is
provided. The supplied Unity/MediaPipe/ARKit binaries are arm64 device inputs;
this export does not establish Unity simulator support.

## Configure the Phone

1. Obtain the **public** Week 7 `ca-cert.pem` from the existing private setup.
   No CA/server private key, Phone PFX or password file belongs in this app.
   The enrolled CA SHA-256 is
   `4dfba4905c171e68c3623dbc952154149076ed89004b85d475e858cc550760ec`.
   CA rotation requires independent verification and an explicit update to
   `EnrolledTrust`; a different certificate is rejected at import.
2. Enable the institutional VPN on the Phone if needed for the existing campus
   route. Tap **Week 7 Connect**, import the CA, then enter board and jump-host
   usernames/passwords. The app displays the assigned board and jump hosts.
   Keep **Use campus jump host** enabled for the documented route; direct mode
   still uses the same pinned board SSH endpoint on port 22.
3. Tap **Connect**. The Unity label should show `Subscribed`, then fresh dummy
   gestures, result IDs and a received count. The app stores only public setup
   and usernames. Passwords are memory-only, cleared from the form immediately
   after connecting and discarded by the session when disconnected/paused.
4. Keep the app foregrounded. Leaving it, opening system UI that deactivates it,
   or locking the Phone stops reception. On returning, tap Connect and enter
   passwords again. No background-session survival is claimed.

Both documented Ed25519 SSH host keys are pinned. The iPhone owns jump SSH,
board SSH and a `direct-tcpip` stream to board **127.0.0.1:9999**. Both SSH
endpoints use **TCP22**. TLS >=1.2 inside that stream trusts only the supplied
Week 7 CA and verifies `ultra96.week7.internal`. The internal stream replaces
an unnecessary Phone TCP19999 listening socket; the board's app ports remain
private. There is no iSH dependency or Laptop result relay.

## Protocol and display behavior

The client sends one length-prefixed SUBSCRIBE for `week7-demo`, requires
SUBSCRIBED, then validates every result against the existing exact schema and
dummy mapping. It rejects malformed UTF-8/JSON, duplicate keys, extra/missing
fields, invalid numeric types/ranges, wrong session and wrong dummy values.
Frames are bounded to 16,384 bytes. Partial frames get one five-second budget;
initial first-result silence gets 30 seconds before the first byte. After any
result has been received, established streams and subsequent reconnects retain
five seconds. Before that first result, reconnects retain the initial grace.
Network recovery uses capped backoff.
Authentication and trust failures require corrected setup and an explicit retry.

The main-thread mailbox holds only the newest validated result, drops retired
callback generations, deduplicates the most recent 4,096 IDs across reconnects,
and clears results after two seconds of local inactivity. Counts represent
accepted unique results in the current explicit Connect session. No replay or
persistent exactly-once delivery is promised. Local freshness cannot measure
source-to-display latency because the selected result schema has no timestamp.

## Simulator UI check

`NativePreview` is an optional test host for the **same** Swift bridge/settings
module. It does not include Unity/ARKit or synthesize gesture success. Its test
checks setup validation and that backgrounding clears passwords. With XcodeGen
installed:

```sh
xcodegen generate --spec ios-visualizer/NativePreview/project.yml
xcodebuild -project ios-visualizer/NativePreview/Week7NativePreview.xcodeproj \
  -scheme Week7NativePreview -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -derivedDataPath .week7-local/PreviewDerivedData test
```

A successful simulator test proves the native UI behavior, not the delivered
Unity scene on a physical Phone. Full-app build, shared-client tests and actual
physical acceptance remain separate evidence categories.

## Physical acceptance still required

Stop competing Phone simulators/subscribers (the newest subscriber replaces the
old owner). Start the existing board service and Windows BLE bridge using their
runbooks; power the protected ESP32 dummy firmware and complete physical pairing
when needed. After the app says Subscribed, send 100 unique dummy inputs. Compare
app count/result IDs with board/Windows ACK evidence and observe all four labels.
No malformed/stale data should appear. Then interrupt/recover the network and
perform an observed lock/foreground/reconnect test. Verify the old stream cannot
update the resumed label. Record separate pass/fail evidence; historical iSH
results are not Unity acceptance.
