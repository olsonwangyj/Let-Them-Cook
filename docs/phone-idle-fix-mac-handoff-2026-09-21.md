# Install the receiver idle fix on the Mac

The installed app disconnects during quiet input. This update keeps healthy
subscriptions open and retains deadlines for incomplete frames and connection
setup. Native commit `724f3995f41120640b13711637ba8ab58f7b3ffe` contains the
receiver update and its tests. This integration brings the fix and diagnostic
reports into `main`, with no ESP firmware or board-protocol change.

## Update from Git

From the Mac's existing Let-Them-Cook repository:

```sh
git status --short
git switch main && git pull --ff-only origin main
git merge-base --is-ancestor 724f3995f41120640b13711637ba8ab58f7b3ffe HEAD
```

The last command exits successfully without output when the receiver fix is
present. Preserve local signing selections and other uncommitted work. If Git
reports conflicting local changes, a divergent branch, or an error, stop and
keep the message for review; do not reset or force the update.

The earlier `receiver-idle-fix-20260921.zip` remains an offline snapshot of the
native patch. After updating from Git, do not apply that patch again. Its
original instructions predate this integration; use this document instead.

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
