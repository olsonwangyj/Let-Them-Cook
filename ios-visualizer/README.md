# iOS communications source

This directory provides the native Communications Swift package and a separate preview/test host. It is a **source handoff**. The team's exported Unity Xcode project, generated IL2CPP files, app data, signing configuration and prebuilt iPhone app are outside this repository handoff. This checkout alone cannot rebuild or reinstall the deployed Unity visualizer.

| Path | Purpose |
| --- | --- |
| [`CommsNative/`](CommsNative/) | Swift package with `CommsCore` (framing, schemas and display state), `CommsTransport` (phone-owned SSH/TLS subscriber) and `CommsBridge` (native UI/C bridge) |
| [`NativePreview/`](NativePreview/) | Optional iOS preview, UI tests and loopback transport tests against the same source modules |
| [`NATIVE-INTEGRATION.md`](NATIVE-INTEGRATION.md) | macOS source tests, preview steps, and requirements for integrating the package into the team's Unity export |

The deployed phone app opens its **own** SSH route to Ultra96 and subscribes through verified TLS to the board's result service. It does not receive results from the Windows laptop. The screen shows `Subscribed`, the newest simulated gesture/result identity, and a `Received` count when the connection is active. The already deployed Unity app labels its setup button **Week 7 Connect**; the source-only package labels a future integration **Communications Connect**. The operational sequence and the limits of ACK versus phone evidence are in the [communications quickstart](../docs/communications-quickstart.md).

The source package uses `Comms*` names. New integrations use `CommsStart`, `CommsCopyDisplay` and `CommsStop`. The existing deployed export still calls `Week7*` C bridge symbols; wrapper symbols remain a deliberate ABI compatibility surface until that export is updated. The packet magic `W7`, session `week7-demo`, and TLS identity `ultra96.week7.internal` likewise remain deployed protocol/trust identifiers. Their spelling does not mean the old Week 7 operating guides apply to the current v2 demo.
