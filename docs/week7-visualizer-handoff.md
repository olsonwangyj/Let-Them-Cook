# Week 7 visualizer teammate handoff

Request the target phone OS and Unity version; the Unity project/repository
(including the scene or UI controller to integrate); the desired display for
`REST`, `FIST`, `OPEN`, `POINT`; and an installable test build/device session.
A changing text label is sufficient for the Week 7 dummy connection demo.

The existing [Unity adapter](../phone/unity/Week7PhoneReceiver.cs) exposes
`On Result Json`, a main-thread `UnityEvent<string>`. The communications side
provides the receiver/core, framed `GESTURE_RESULT` contract, verified public
CA and SSH setup. The app uses Phone localhost port 19999 through its own SSH
tunnel to Ultra96; the board exposes SSH port 22 only. See the
[Phone runbook](week7-phone-runbook.md#unity-sample) for setup.

The supplied Unity sample targets native Android and still requires compilation
in her project and a device integration test. Actual iPhone results so far are
Python/iSH reception. An iPhone Unity target needs its own SSH/lifecycle
integration and install/signing route; switching from iSH to Unity is not an
established working transport. Confirm the target before promising that build.

Copyable message:

> Hi, our Week 7 dummy-packet communications are working. Could you send me your
> Unity project, Unity version and target phone (Android/iPhone), and tell me how
> REST/FIST/OPEN/POINT should appear in the UI? I have a C# receiver ready for
> integration; a changing label is enough for the demo. Then we can test a build
> together. Please flag an iPhone target because its Unity connection still
> needs integration.
