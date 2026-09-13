# Week 7 native iOS integration design

## Scope and authorization

Implement the actual supplied Unity iOS export, preserving the ESP32 → Windows
BLE bridge → Ultra96 → iPhone path and dummy contract. The user's Mac prompt
explicitly delegates design decisions, implementation, tests, review, commit and
push to a `codex/ios-visualizer-*` branch. Routine skill approval gates are waived.
No merge, credential publication, account bypass or claim of physical acceptance.

## Selected approach

Three approaches were considered: regenerate from original Unity source (best
long-term, but no original project found in this checkout/Documents); edit only
the detached C# receiver (cannot change this app); integrate a native Swift
package into the export (selected). Keep the Unity scene and its serialized
TMP_Text reference. Reproducibly replace only the old receiver's Start, Update
and OnDestroy method bodies with a C ABI bridge. Update polls a bounded snapshot
on Unity's main thread and calls the existing TMP setter. Never open port 5005
or restore the removed server PFX. Re-exporting Unity requires reapplying these
explicit hooks, or porting the adapter to original source.

The Swift package contains protocol validation, lifecycle state and transport.
Apple SwiftNIO SSH provides an app-owned connection to the configured SSH host
on TCP22, optionally through the pinned institutional jump host and then board
TCP22. TLS runs within a direct-tcpip channel to board 127.0.0.1:9999. This is the
same Phone-owned SSH route without opening an unnecessary Phone TCP19999
listener. No Laptop forwarding dependency, externally reachable board app port,
remote shell, or foreground iSH dependency is introduced.

## Security and setup

Use exact enrolled SSH public host keys, never trust-on-first-use. Preserve the
two already documented Ed25519 host keys as public defaults. Use interactive
password authentication in this foreground app for both hops (the existing
physical route used passwords); do not assume inaccessible Windows key files.
Passwords are supplied in secure text fields, kept in memory for reconnect only,
and discarded when disconnected or the app is backgrounded. No password save,
logging, automatic account enrollment or silent host-key replacement.

Import the real public Week 7 CA PEM via the document picker; configuration and
public CA may be stored in the app's private directory with data protection.
No private keys or PFX imports. SwiftNIO TLS uses only that CA, full certificate
and hostname verification for `ultra96.week7.internal`, TLS >=1.2, bounded
handshake timeout, and no insecure fallback. Local tests use separate temporary
PKI. No live CA found locally means live setup remains a human next step.

## Protocol and lifecycle

4-byte big-endian body length, 1..16384 bytes, strict UTF-8 JSON object, duplicate
keys rejected, exact fields, lexical integer uint32 bounds, finite numbers,
configured valid session, deterministic gesture/result_id/confidence checks.
Send one SUBSCRIBE, require SUBSCRIBED, then receive live-only results. Reject
malformed frames/extra schema fields without resynchronizing.

Connection/TLS/subscription/frame deadlines are bounded. The first ever result
gets 30 seconds before its first byte; after any first byte use a single 5-second
prefix/body budget. Established streams use 5 seconds. Reconnect 0.5..5 seconds;
stop closes owned channels, cancels timers and invalidates old generations.
Deduplicate at most 4096 result IDs; keep only the newest display snapshot with
2-second monotonic freshness. Display dummy label, count, trace and status;
clear live label on disconnect, pause or stale data. Backgrounding stops all
network activity and forgets passwords; foreground requests Connect again.

## Verification and evidence boundaries

Use test-first protocol/state behavior and real local SSH/TLS integration tests
of the same Swift package linked into the actual app. Exercise wrong host key,
wrong CA/hostname, framing/schema errors, subscription order, timeout, duplicate,
freshness, reconnect and cancellation. Build the full Unity-iPhone arm64 app
without signing; verify linked bridge symbols and old receiver replacement.
Build/sign/install only when identities/devices are actually available. A host
package test or unsigned build does not prove device UI, BLE path, VPN, camera,
lock/background or full physical acceptance. Record exact remaining actions.

## Initial environment decisions

Work on a new branch in the clean existing checkout: this avoids duplicating
1.47 GB of Unity import inputs and preserves the user's requested Mac location.
Install missing Git LFS locally through Homebrew, hydrate and verify original
manifest before modifying imported sources. Keep that manifest as provenance.
Use an ignored Python environment for the existing tests. Remove inherited
Unity symbol-upload token settings before building and make symbol upload
opt-in: a local build must not publish to the teammate's Unity account.
