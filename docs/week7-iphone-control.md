# Temporary iSH maintenance access

The user requested agent-operated Phone testing to reduce repeated iPhone
copy/paste. The installed `/usr/sbin/sshd` was confirmed on the actual Phone.
This procedure enables a temporary shell inside iSH; it does not grant iOS UI
control. VPN toggles, screen locking, app switching and foreground recovery
still need the operator. Keep iSH foreground during initial commissioning.

**Actual replacement Phone, 2026-09-08:** pinned key authentication, remote
Python 3.9.16, application TLS 1.3, wrong-name/untrusted-certificate rejection
and board loopback management binding have now been verified. Alpine is 3.14.3
with OpenSSH 8.6p1. The locked root prerequisite used the guarded decision-33
backup/remedy; the private backup remains on Phone. An effective-policy check
exposed the OpenSSH 8.6 challenge-response default, fixed by disabling both
interactive directives and reloading only the verified scoped daemon. Fresh
authentication and policy checks passed. See the continuation report for
packet evidence and remaining physical lifecycle actions.

## Selected design and implementation sequence

Use a dedicated, key-only iSH SSH daemon and a maintenance forward through the
Phone's existing SSH master. This uses software already installed on Phone and
the known port-22 route; Windows USB drivers or a new command-execution protocol
would add dependencies without removing iOS's physical actions.

1. Generate a dedicated Ed25519 client key in the Laptop's private directory.
   Transfer only the public key in `control-public.json` with the launcher.
2. Verify the board's effective forwarding policy before publishing the setup.
   `GatewayPorts` must be `no` or `clientspecified`; `yes` forces a wildcard
   reverse listener even when the client requests loopback.
3. The launcher checks the existing master and creates its own Phone directory,
   host key, authorized key file, daemon configuration, PID and log. It refuses
   an occupied port or locked account instead of changing global SSH settings
   or account credentials. Run the platform's `sshd -t` preflight.
4. Start the scoped daemon on Phone `127.0.0.1:2222`; request only the maintenance
   reverse forward, board `127.0.0.1:22222` to Phone `127.0.0.1:2222`.
5. Publish the Phone public host key/status over the existing trusted master.
   On Laptop, pin that exact key and connect through a separate local SSH
   forward, Laptop `127.0.0.1:12222` to board `127.0.0.1:22222`.
6. Independently verify the board listener address, actual key authentication,
   remote Python execution and the existing application TLS connection before
   treating the Phone as controllable. Collect captures only from the device
   that produced them: `phone100.DoakOF` remains on the original Phone and
   cannot be retrieved from this replacement. Proceed with fresh bounded runs.
7. At the end, stop only the owned daemon and cancel only the maintenance
   forward. Verify its board listener disappears and the result tunnel still
   works. Retain evidence and public manifests; remove the temporary client's
   access as part of cleanup. No service is installed for automatic startup.

The maintenance path is separate from the assessed application topology:

```text
Application: Phone receiver -> Phone localhost:19999 -> Phone SSH -L
             -> jump:22 -> Ultra96:22 -> board localhost:9999

Maintenance: Laptop client -> Laptop localhost:12222 -> Laptop SSH -L
             -> jump:22 -> Ultra96:22 -> board localhost:22222
             -> Phone SSH -R -> Phone localhost:2222 (scoped iSH sshd)
```

This is an explicit maintenance-only exception to the historical plan's ban
on reverse forwards. No sensor/result data is rerouted through this path, and
the Phone still owns its independent application `-L`. No additional external
Ultra96 port is used. The two Phone forwards initially share one SSH master;
a VPN outage or termination of that master also interrupts management. Do not
claim independent management survival during those fault tests.

## Isolation and verification

The standalone daemon permits only the dedicated key and the root account
inside iSH, with password and keyboard-interactive authentication disabled.
Its private host key stays on Phone. Forwarding, PTY allocation and user RC
hooks are disabled; file transfer and noninteractive commands remain available.
The SSH server does not change the Phone application's CA or TLS identity.

OpenSSH 8.6 multiplex control commands must use an empty config (`-F /dev/null`)
and the explicit existing socket. Loading the normal config can accidentally
include its other forwardings in `-O forward` or `-O cancel`. Cancellation exit
status alone is insufficient in that version: inspect the actual listener.

The launcher is [phone/ish_control.py](../phone/ish_control.py). Place it with
the matching `control-public.json`; after the Phone has established its own
verified master, invoke `python3 ish_control.py "$week7_ssh_socket"`. Its
`--stop /root/week7-control/RUN/state.json` option requests cleanup only after
checking the saved scope and live daemon's executable, dedicated log descriptor,
process group and session. Use the actual state path returned by startup.

iSH truncates rewritten process titles and reports a zero process-start field.
The helper therefore uses the owned, unreaped subprocess during startup and
failure rollback, and checks the dedicated log descriptor for later shutdown.
It does not use an old PID or a zero timestamp as proof of process ownership.
An existing board listener or readiness file blocks a second setup attempt;
reconcile the previous owned attempt before trying again.

Keep logs distinguishable: local unit/config checks establish launcher behavior;
`PHONE_CONTROL_READY` establishes only the launcher's reported startup and
forward request. The separate actual remote-authentication check establishes
access. A successful SSH probe is not a Phone packet/lifecycle acceptance run.
Do not activate background keepalive workarounds: they would alter the behavior
the screen-lock and background tests are meant to measure.

## Sources

- [iSH's SSH server guide](https://github.com/ish-app/ish/wiki/Running-an-SSH-server)
  documents the server, high localhost port and account-lock limitations.
- [OpenSSH 8.6 daemon configuration](https://raw.githubusercontent.com/openssh/openssh-portable/V_8_6_P1/sshd_config.5)
  defines forwarding and authentication restrictions.
- [OpenSSH 8.6 multiplex implementation](https://raw.githubusercontent.com/openssh/openssh-portable/V_8_6_P1/mux.c)
  explains the forwarding-list and cancellation behavior.
- [iSH process information implementation](https://github.com/ish-app/ish/blob/master/fs/proc/pid.c)
  supplies the process-title, timestamp and descriptor compatibility constraints.

The current concrete bundle paths, hashes, actual outcomes and remaining Phone
actions are recorded in the [continuation report](week7-continuation-report-2026-09-07.md).
