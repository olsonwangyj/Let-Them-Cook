# Let-Them-Cook

A cooking AR game inspired by Overcooked.

This repository handoff contains the Communications subsystem: protected dummy-data streams from two FireBeetle32 boards through a Windows relay and Ultra96 to the installed Unity iPhone visualizer. Start with the [communications quickstart](docs/communications-quickstart.md) for setup, `flash.py`, `demo.py`, evidence and the source-only iOS boundary.

## Communications guides

- [Live demonstration, English](docs/B07-CO-live-demo-guide.en.md) · [中文](docs/B07-CO-live-demo-guide.zh-CN.md): the instructor's item order, actions, observations and pass conditions.
- [Protocol version 2](docs/co-protocol-v2.md) · [中文入门讲解](docs/B07-CO-protocol-explained.zh-CN.md): sensor, control, file and result formats.
- [Video operator script, 中文](docs/B07-CO-video-operator-script.zh-CN.md) · [English presentation](docs/B07-CO-video-presentation.en.md): physical recording and on-screen explanation.
- [28 September physical deployment evidence](docs/co-live-deployment-2026-09-28.md): measured results under the recorded conditions.
- [iOS source and integration boundary](ios-visualizer/README.md) · [native build and preview](ios-visualizer/NATIVE-INTEGRATION.md).
- [Team integration handoff](docs/integration-handoff.md): how Communications connects to the other game subsystems.

New source defaults use `LC` sensor packets, `LCS1` source statistics and the `ltc-comms` session. The original deployment still uses `W7`, `W7S1` and `week7-demo`; the laptop decoders accept either packet marker, and the original server/app require an explicit legacy session setting when used with the updated launcher. The TLS name `ultra96.week7.internal` and the deployed iPhone bridge's `Week7*` symbols remain compatibility identifiers until certificates and the Unity export are replaced. See the [migration instructions](docs/communications-quickstart.md#source-and-deployment-identifiers). The Unity Xcode export and a prebuilt iPhone app are not part of this repository handoff.
