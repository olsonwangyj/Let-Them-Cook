# Install the receiver idle fix on the Mac

The installed app disconnects during quiet input. This update keeps healthy
subscriptions open and retains deadlines for incomplete frames and connection
setup. It is native commit `724f3995f41120640b13711637ba8ab58f7b3ffe` on the local
`codex/phone-reliability` branch. It has **not been pushed**; pulling the remote
alone will not obtain it. The supplied patch contains the receiver update and
its tests, with no ESP firmware or board-protocol change.

## Transfer and apply

Copy `receiver-idle-fix-20260921.zip` from Windows to the Mac and extract it into
Downloads. The Windows artifact is under
`D:\LetThemCook-builds\phone-recovery-20260921`.

From the Mac's existing Let-Them-Cook repository, check the patch first, then
apply it only if the check succeeds:

```sh
git status --short
git apply --check "$HOME/Downloads/receiver-idle-fix-20260921/receiver-idle-fix.patch" &&
git apply "$HOME/Downloads/receiver-idle-fix-20260921/receiver-idle-fix.patch"
```

This preserves existing Xcode signing selections. Do not force the patch if
Git reports a conflict or an already-applied change; keep the error for review.
The patch was checked successfully against Windows main `cf1ad08`.
Its SHA-256 is
`eb91ff0d10cc208dc9c30b65420712ba4b67fbc8c6d03e15969901578806e7cc`.
On the Mac it can be checked with:

```sh
shasum -a 256 "$HOME/Downloads/receiver-idle-fix-20260921/receiver-idle-fix.patch"
```

## Build and install

Run the full native tests on macOS, then prepare the existing export:

```sh
swift test --package-path ios-visualizer/Week7Native &&
python3 ios-visualizer/tools/patch_export.py &&
python3 ios-visualizer/tools/configure_xcode.py
```

When those finish successfully, open
`ios-visualizer/xcode-export/Unity-iPhone.xcodeproj` in Xcode. Select the
Unity-iPhone scheme and the connected, unlocked iPhone, use your existing
development team, and press Run to rebuild and install. Reopening the old app
without rebuilding does not install this change. Follow
[Native integration](../ios-visualizer/NATIVE-INTEGRATION.md) for signing details
if needed. Preserve any build or test error rather than skipping it.

Then enable the iPhone VPN, open Unity, tap Week 7 Settings/Connect, enter the
passwords, and connect. Leave Unity foregrounded. Report when the updated app
shows **Subscribed, Received: 0** so the coordinated two-ESP capture can start.
There is no need to reflash either ESP for this update.

## Verification already completed and what remains

The original code reproduced the idle defect in three test cases (57 tests,
eight expected assertions). The updated portable Core/Transport suite passed
54/54 tests on Swift 6.2.3 with all eight locked dependency revisions. Independent
review passed. Windows cannot validate the Apple Bridge/UI/Xcode build here;
the macOS suite and installed iPhone remain separate checks.

The next physical tests are a fresh baseline, foreground idle/resume without
manual Connect, VPN recovery, lock/unlock followed by explicit Connect, and a
final continuous two-ESP run. Counts and board identities must be recorded
separately for each run. This update does not add replay during outages or
background reception. A silent network failure still depends on operating-system
transport failure detection.

See the [recovery report](phone-recovery-test-2026-09-21.md) for the current
1,204-result baseline pass and the diagnosed 16-result idle failure. The report
preserves the earlier 12,004-result soak and the separate unexplained
109-result shortfall; it does not claim universal zero loss.
