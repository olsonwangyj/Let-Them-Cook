# iOS visualizer delivery

Jieling's Week 7 delivery, imported on 2026-09-14 from the former root `unity/`
folder. **Native integration is implemented in this branch; physical iPhone acceptance
remains pending. This is an Xcode export, not the original Unity Editor project.**
See [native build, setup and verification](NATIVE-INTEGRATION.md). The original
receiver remains incompatible as reference; the actual export uses native client
hooks. Start the Mac work with the
[autonomous agent prompt](../docs/week7-mac-agent-prompt.md).

| Path | Purpose |
| --- | --- |
| `Week7Native/` | App-linked Swift protocol, Phone-owned SSH/TLS and native settings |
| `tools/patch_export.py`, `tools/configure_xcode.py` | Guarded receiver hooks and local package integration |
| `NativePreview/` | Same native UI module in a simulator test host; not Unity acceptance |
| `xcode-export/Unity-iPhone.xcodeproj` | Native Xcode project; renamed outer directory preserves internal paths |
| `xcode-export/Il2CppOutputProject/` | Generated C++ and supplied IL2CPP compiler inputs |
| `xcode-export/Data/`, `Frameworks/`, `Libraries/` | Required Unity app data and native dependencies |
| `reference/TlsDataReceiver.cs` | Sanitized teammate reference; editing it does not update the export |
| `reference/teammate-localhost-cert.pem` | Public certificate for the old Phone server, for reference only |
| `import-manifest.json` | SHA-256 inventory of the sanitized imported files, plus executable paths |
| `verify-import.py` | Standard-library check of that baseline after downloading LFS objects |

## Get the actual files on the Mac

Use a Git checkout with Git LFS installed. From the repository root, before
modifying the imported files:

```sh
git lfs install --local
git lfs pull
git lfs fsck
python3 ios-visualizer/tools/patch_export.py
python3 ios-visualizer/tools/configure_xcode.py
open ios-visualizer/xcode-export/Unity-iPhone.xcodeproj
```

The original baseline was verified before this integration. On this branch,
`verify-import.py` intentionally reports the documented native edits. For the
original import commit only, it should pass unchanged.

The manifest describes the import baseline. An intentional later edit should
change its hash; retain the original inventory as provenance rather than
regenerating it to hide changes. `verify-import.py` is not a build or app test.
If it reports a Git LFS pointer or missing file, fix the download first. Files
over 5 MiB and native/opaque app binaries use LFS; the 239,610,632-byte UnityRuntime
archive exceeds GitHub's normal Git file limit. See
[GitHub's large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

## What the export can build

Its build settings record Unity **6000.5.10f1**, **iOS 15.0 minimum**, arm64 and
`iphoneos`. It includes UnityRuntime, MediaPipeUnity and ARKit and requires
arm64/Metal/ARKit capabilities. Simulator support is not established. The complete
generating Xcode version was not established; dependency build metadata is not
proof of the export's Xcode version.

No original `Assets/`, `Packages/` or `ProjectSettings/` source project was supplied.
Xcode builds the generated C++ using the included IL2CPP tools. A new C# file
outside that pipeline will not change the app. This branch supplies a guarded
native integration; original Unity source would allow a future source-level
adapter. See
[Unity's Xcode project structure](https://docs.unity3d.com/6000.0/Documentation/Manual/StructureOfXcodeProject.html).

Automatic signing remains configured. The original eight teammate build settings
and two remaining target-level team attributes were cleared. Xcode 26.2 and its
iOS SDK successfully built the actual app in Debug and Release. This Mac has no
valid signing identity or attached physical iPhone, so signing/install/device
trust remain pending. The existing bundle
identifier is `com.CookingCompany.unityTutorial`; select a suitable user-owned
identifier during provisioning. Nineteen script/native-tool executable bits are
stored in Git for macOS checkout.

## Original protocol mismatch and native replacement

| Concern | Delivered reference | Selected Week 7 contract |
| --- | --- | --- |
| Phone role | TLS server on all interfaces, port 5005 | TLS client subscribing to Ultra96 |
| Framing | Newline-delimited strings | 4-byte big-endian length + UTF-8 JSON, max 16,384 bytes |
| Registration | None | SUBSCRIBE / SUBSCRIBED, session `week7-demo` |
| Network route | Would require an inbound Phone connection | Phone-owned SSH route via board TCP22 to loopback9999 |
| Trust | Phone server PFX, self-signed localhost cert | Client verifies Week 7 CA and `ultra96.week7.internal` |
| UI delivery | Main-thread label fed by unbounded queue | Bounded, fresh, validated results with reconnect/cancellation |

The existing reusable C# client remains in `phone/unity/`. This branch supplies
the iOS build/UI/SSH integration through the app-linked native package. The
supplied reference additionally lacks bounded
lines/queues, schema/session validation, handshake/read deadlines, and robust
active-client shutdown. Port 5005 alone does not establish compatibility. Keep
board application ports private; only SSH TCP22 is externally reachable.

## Sanitization and provenance

The full original delivery was copied and all 7,250 original files verified
byte-for-byte before modification. The private Windows preservation location is
`D:\LetThemCook-builds\ios-visualizer-import-20260914\original-unity`; it is not
available automatically on the Mac and is not required for the intended client.

- Removed `Data/Raw/server.pfx`, which contains a private key. The old server
  receiver therefore cannot start unchanged; do not restore that key into the
  app to get a green test.
- Replaced the old password with the equal-length placeholder `REMOVED` in the
  reference C#, serialized `Data/level0`, and
  `Data/Managed/Metadata/global-metadata.dat`. File lengths are preserved;
  Mac builds now pass; serialized scene/app runtime validity still requires
  physical-device validation.
- Excluded Apple archive metadata, Xcode user state and the personal signing
  screenshot. Retained third-party libraries/licenses and generated source paths.
- Cleared eight nonempty teammate signing-team settings. No board service,
  existing TLS trust, firmware or tested communications code was changed.

The reference public certificate has SHA-256 fingerprint
`a923727ca7c065ed884080fe47efffdfccc4b0d5673aec84b3d97da00851179e`, subject/issuer
`CN=localhost`, valid 2026-09-13 through 2027-09-13. It is **not** the Week 7 CA.
For live integration obtain the actual public CA through the existing private
setup; generate separate temporary PKI for local tests. No private key is needed
in a Phone TLS client.

Read the [current continuation report](../docs/week7-continuation-report-2026-09-14.md)
for import verification and the distinction between historical iSH results and
unverified Unity app acceptance.
