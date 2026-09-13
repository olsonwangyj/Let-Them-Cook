# Week 7 visualizer teammate handoff

Jieling's iPhone delivery is now in [ios-visualizer](../ios-visualizer/README.md).
Start with the [autonomous Mac prompt](week7-mac-agent-prompt.md) and
[current decisions and findings](week7-continuation-report-2026-09-14.md).
It is a Unity 6000.5.10f1 Xcode/IL2CPP export; original Unity Editor source was
not included. Her receiver is a TLS server on port 5005 using newline strings,
while the selected Phone protocol requires a framed-JSON TLS client. A port
change alone cannot integrate them. A changing REST/FIST/OPEN/POINT label, count
and connection status suffice for the selected Week 7 dummy demo.

The existing [Unity adapter](../phone/unity/Week7PhoneReceiver.cs) exposes
`On Result Json`, a main-thread `UnityEvent<string>`. The communications side
provides the receiver/core, framed `GESTURE_RESULT` contract, verified public
CA and SSH setup. The app uses Phone localhost port 19999 through its own SSH
tunnel to Ultra96; the board exposes SSH port 22 only. See the
[Phone runbook](week7-phone-runbook.md#unity-sample) for setup.

The supplied reusable Unity sample targeted native Android and still requires
actual iOS compilation, scene integration and a device test. Existing iPhone
results are Python/iSH reception. The iPhone Unity app needs its own SSH/lifecycle
integration and install/signing route; switching from iSH to Unity is not an
established working transport. Editing the detached teammate C# reference does
not update the generated Xcode app. Use original source if available; otherwise
complete independent work and investigate a documented native export adapter.

If original Unity source cannot be found on the Mac, request it later:

> Hi Jieling, thanks! Could you also send the original Unity project, including
> Assets, Packages and ProjectSettings? I received the Xcode export. Our Phone
> needs a TLS client with length-prefixed JSON, while the supplied receiver is a
> TLS server on 5005, so I'm adapting it and need the scene/UI source too.
