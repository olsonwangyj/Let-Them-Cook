# Remaining replacement iPhone physical tests

The automated checks on 2026-09-08 are recorded in the
[continuation report](week7-continuation-report-2026-09-07.md): actual Phone
TLS positive/negative checks, 6,100 exact results, controlled local-forward
loss/restoration and a final 100-result receiver restart. The latter had zero
Phone reconnects and all sender error/drop counters zero. The longer run had
one explicitly retained callback-generation discard. Do not reopen protocol
or security decisions to proceed with these physical observations.

## Before another timed run

**Paused at the operator's request on 2026-09-09.** The first screen-lock
attempt lost the maintenance route and awaits manual recovery and collection
of its Phone originals. The operator reported `unlocked`; automatic route
recovery was not observed. Read the latest continuation report before resuming.
Inspect `/root/week7-evidence/phone-lifecycle.NIIdKC` and detached job
`/root/week7-evidence/screen-lock-job.xvmep7mt` after restoring access. Preserve
that attempt and verify the receiver's final state before a new subscription.

1. Obtain the operator's whole-run foreground observation for the completed
   6,100-result run. Ask whether this replacement iPhone stayed unlocked with
   iSH visible and its own VPN connected throughout. Remote process/log
   evidence cannot answer that question or substitute for the observation.
2. Record the iPhone model, iOS version and iSH app version. Check Settings
   while no test is running, then return iSH to foreground. The measured iSH
   environment is Alpine 3.14.3, Python 3.9.16 and OpenSSH 8.6p1.
3. Confirm the operator is ready before starting a bounded fault capture.
   There is no active sender or subscriber left from the completed tests.
   Laptop ingestion still uses its independent local port 18888; Phone results
   still use Phone local port 19999. Keep the Laptop VPN and ingestion tunnel up.

## Prepared capture and recovery files

These exact files are already on the replacement Phone under
`/root/week7-phone/`, and are retained locally under
`D:\LetThemCook-builds\iphone-control-20260908\w7-fd3c60de`:

| File | SHA-256 | Purpose |
|---|---|---|
| `capture-lifecycle.sh` | `fb51e6670bfee55ce5557cf28df8b1175b48c88c6dc61a9af53d8de2220c7b3b` | Capture the unchanged receiver with count 0 and a 240-second overall bound, preserving combined log, context and separate receiver/capture/wrapper exits |
| `resume-week7-control.py` | `8f0bae4b99a18380d41d2be42dae8dc9e4e2b0a7fa5e8a65a2d6a31eb72a8f45` | Manually restore this scoped Phone's routes after its SSH master dies, preserving the verified daemon/key/account |
| `restart-week7-control.py` | `41503a72b25f5a14c6287ed274f37b4813361c49ec4d5eace450f8a061c7c472` | The v3 full setup, reserved for loss of the daemon/iSH kernel after reconciling the old owned readiness record |

The capture is adapted from the verified 6,100-result wrapper; the exact staged
file passed `sh -n` on Phone. Completion of a count-zero fault capture means
process/log completion, not successful delivery. Audit before/after activity
and fault milestones separately.

The resume helper passed 15 offline Windows cases with one POSIX skip and all
16 WSL cases. Actual Phone `--check-only` returned `PHONE_RESUME_ALREADY_READY`,
TLS 1.3, matching maintenance host key and loopback binding. This checks the
healthy path; actual full-master-loss restoration is still a physical test.
The helper may create a private `resume.lock`; it changes no account or routes
in check-only mode. It rejects unknown scope, changed trust files, daemon
identity/configuration, occupied ports or an uncertain live master. Before a
new reverse forward it checks the board's current effective SSH forwarding
policy using its own disposable host key, without sudo or system edits.

## Capture method for each physical fault

Use separate evidence for each row below. The agent should start the capture
as an owned detached Phone process, with `start_new_session=True`, stdin from
`DEVNULL`, and stdout/stderr saved in its fresh private job directory. It must
survive loss of the management SSH connection; attaching the receiver's output
only to that SSH pipe would confound the VPN test with a broken output pipe.
Run `sh /root/week7-phone/capture-lifecycle.sh` as that child. Preserve its PID,
start time, job path and printed `Phone evidence:` path. Do not use an iOS
location/background keepalive workaround.

Observe a fresh `subscribed session=week7-demo` in the original Phone log, then
start only the real protected BLE sender with `--target 0 --duration 180` and
the established CA/address/session/ingestion port. Save complete sender logs,
exit and UTC context. After at least 30 live results, record an agent UTC
milestone and issue the physical action. Record the operator's actual action
and return times as observations; an instruction timestamp is not the physical
event's timestamp. The Phone's 240-second capture gives recovery margin.
The extra minute also produces a quiet tail after the sender ends, where the
receiver's five-second idle timeout can cause expected reconnects. The final
aggregate reconnect count cannot identify their cause. Record a conservative
last-ACK boundary after the operator's return and require at least 30 matching
Phone IDs produced after it; buffered older results alone are insufficient.

| Separate test | Operator action | Required evidence after return |
|---|---|---|
| Screen lock | Lock for about 30 seconds; unlock and open iSH | Describe whether output paused; recover valid TLS/subscription if needed; observe new live results and retain any lost interval/reconnects |
| Background/app switch | Open another app for about 30 seconds; return to iSH | Record actual suspension/continuation behavior and subsequent live results; do not label this as a Unity app test |
| Phone VPN interruption | Disconnect only the Phone VPN for about 60 seconds, reconnect it and return to iSH | Observe loss/restoration independently on board/Phone; run the resume helper below if the shared master died; record both password prompts privately and restored TLS/results |

While the operator is away from iSH, the agent can monitor the board's scoped
maintenance listener and continuing Laptop ingestion, with UTC observations.
Loss of management alone does not establish whether the Phone receiver paused,
exited or lost data: collect its original log after return. A listener can
linger until keepalive expiry; do not infer an outage solely from VPN button
timing. The selected keepalive is 15 seconds/count 3, not a guaranteed exact
disconnect deadline.

For restoration in the same iSH kernel, the operator runs one short command:

```sh
python3 /root/week7-phone/resume-week7-control.py
```

If routes survived it reports already ready. If the master is genuinely dead,
it creates only a fresh scoped master and prompts for the two existing SSH
passwords in the terminal. It verifies application TLS, the board's loopback
reverse listener and the pinned Phone host key before atomically updating
the existing `state.json` socket path. It backs up the old state first, and
failure cleanup addresses only the new attempt. Never put passwords in logs.
Wait for the VPN route to return before retrying a connectivity failure.

After return, require at least 30 new live results correlated with Laptop ACKs
and board acceptances. Results published while unsubscribed are not replayed;
report expected missing IDs explicitly. The receiver suppresses duplicates
before printing, so its output alone cannot prove no duplicates arrived on the
wire. Collect raw logs, all available exit files, milestones and actual user
observations. A timeout, insufficient post-return activity, or failed recovery
is retained as a failed attempt rather than trimmed or relabelled.

## Force-quit and cleanup boundaries

Force-quitting iSH can end the daemon/kernel as well as the master. Test that
only after the previous evidence is collected. The scoped resume helper will
refuse a missing or changed daemon; do not bypass its identity checks. The
agent must verify the old board listener is absent, preserve and reconcile
only this attempt's stale `phone-ready.json`, then have the operator run the
already staged v3 full setup:

```sh
python3 /root/week7-phone/restart-week7-control.py
```

Verify the new readiness record/host key through the trusted board route before
updating the dedicated Laptop pin. A new daemon/scope needs a newly prepared
resume helper; the old helper intentionally refuses it. Preserve the original
private root-account backup across this process. This is a restart procedure,
not an observed force-quit pass.

After all physical tests, use the verified scoped helper/state to stop only
the temporary daemon and cancel its maintenance forward. The state socket may
have changed after resume, so do not reuse the original socket blindly. Verify
the board maintenance listener disappears, close all owned authenticated
management sessions, and verify the application route separately. Then the
operator uses the saved local-console restoration helper from the
[root-lock guide](week7-ish-root-lock.md) to restore and verify the original
password field. It refuses restoration while known SSH server/session
processes remain. Keep the private backup until restoration is verified and
exclude it from every evidence transfer.

The original iPhone's `phone100.DoakOF` still needs retrieval from that device.
Teammate Unity build/integration remains separate from the working iSH receiver.
