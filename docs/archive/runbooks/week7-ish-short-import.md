# iSH setup import using separate short commands

Use this delivery path after a long heredoc was interpreted by the shell.
The replacement Phone operator has confirmed `PHONE_OK` from a manually typed
Python command and reported that both final `~/.ssh/week7-*` files are missing.
Keep the same foreground iSH shell and its VPN connected. Copy each command
separately, without shell prompt text; stop at any error. Do not feed later
commands into an SSH password prompt. No heredocs are needed.

This only changes delivery of the already tested setup. Keep temporary import
files separate from the final configuration: the setup checks existing final
files against their exact expected bytes and refuses conflicting contents.
The script applies the [guarded root-lock remedy](week7-ish-root-lock.md) only
when its checks require it. The account backup remains private on the Phone.

Current downloads use v3, which explicitly disables the older OpenSSH 8.6
challenge-response default. The successfully installed v2 Phone was separately
corrected and verified; retain its original download and evidence.

## 1. Prepare and check the two public host keys

Copy these four commands separately. The fresh directory is private by
`mktemp -d`; `${w7f:?}` refuses further file access if its shell variable was
lost. The first command prints its directory path.

```sh
w7f=$(mktemp -d "$HOME/w7-fetch.XXXXXX") && printf '%s\n' "$w7f"
```

```sh
printf '%s\n' 'stujump.comp.nus.edu.sg ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILfypXFWxIhmHZ1nZZKsNKIYRZvnXrra4sqWpnBRy66i' > "${w7f:?}/k"
```

```sh
printf '%s\n' 'makerslab-fpga-35.ddns.comp.nus.edu.sg ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC7by9bvClMnRjk3KKoR+QpRdhuUXhIhVPC1+F2FnV39' >> "${w7f:?}/k"
```

```sh
ssh-keygen -lf "${w7f:?}/k" -E sha256
```

Require both established fingerprints before proceeding:

- Jump: `SHA256:UZRh6MN1S3Q9DI2OEH4POiJQ4fEaxrpI83ZSTTZtMYw`
- Ultra96: `SHA256:vrFwqkqWIfyDZ1S66aJb1gLy59wx3LakOqhnyQJEOhg`

## 2. Write a temporary SSH configuration

Each command below is one shell line. The shared configuration applies strict
host verification to both the jump client and destination client. Keep the
connection timeouts in their specific host sections: an earlier wildcard value
would take precedence over later values in OpenSSH.

```sh
printf 'Host *\n UserKnownHostsFile "%s/k"\n' "${w7f:?}" > "${w7f:?}/c"
```

```sh
printf '%s\n' ' GlobalKnownHostsFile /dev/null' ' StrictHostKeyChecking yes' ' HostKeyAlgorithms ssh-ed25519' ' Port 22' >> "${w7f:?}/c"
```

```sh
printf '%s\n' ' ServerAliveInterval 15' ' ServerAliveCountMax 3' ' ExitOnForwardFailure yes' >> "${w7f:?}/c"
```

```sh
printf '%s\n' 'Host j' ' HostName stujump.comp.nus.edu.sg' ' User yanjie' ' ConnectTimeout 20' >> "${w7f:?}/c"
```

```sh
printf '%s\n' 'Host b' ' HostName makerslab-fpga-35.ddns.comp.nus.edu.sg' ' User xilinx' ' ProxyJump j' ' ConnectTimeout 60' >> "${w7f:?}/c"
```

```sh
chmod 600 "${w7f:?}/k" "${w7f:?}/c"
```

The operator may inspect each effective configuration without connecting:

```sh
ssh -F "${w7f:?}/c" -G j
```

```sh
ssh -F "${w7f:?}/c" -G b
```

Require the intended hostname/user, port 22, strict checking, Ed25519-only
host keys, this temporary known-hosts file, and timeouts 20/60 respectively.
The destination must show `proxyjump j`.

## 3. Download the whole setup file

```sh
w7remote=/var/tmp/cg4002-week7-yanjie-20260907/phone-control-w7-fd3c60de
```

```sh
scp -F "${w7f:?}/c" "b:${w7remote:?}/replacement-key-setup-v3.py" "${w7f:?}/setup.py"
```

Enter the existing authorized passwords privately at their prompts. Wait for
the transfer and the normal shell prompt before entering anything else. A
host-key question or mismatch requires inspection; do not weaken verification.
The known `/home/xilinx` permission warning is not itself proof of transfer
failure or success. Require the file transfer and verification below.

## 4. Verify and execute

```sh
w7sha=41503a72b25f5a14c6287ed274f37b4813361c49ec4d5eace450f8a061c7c472
```

```sh
printf '%s  %s\n' "${w7sha:?}" "${w7f:?}/setup.py" | sha256sum -c - && python3 "${w7f:?}/setup.py"
```

The `&&` gates execution on a matching file hash. The setup can ask for both
SSH passwords again when it starts its independent application tunnel.
Retain any private account backup and follow the restore guide after temporary
maintenance access ends. `PHONE_CONTROL_READY` still requires independent
verification of loopback binding, pinned Phone-host authentication, remote
Python and Phone TLS before claiming management or application success.
