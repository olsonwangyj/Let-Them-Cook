# Week 7 transport implementation evidence — 2026-09-06

This evidence is local software/TLS integration only. It does not establish Ultra96 deployment, real BLE delivery, Phone hardware operation, gate K, or gate M.

## Implemented contract

- `common.wire` implements uint32 big-endian length + strict UTF-8 JSON object, length 1..16384, one 5-second frame deadline, duplicate-key/non-finite/non-object rejection, and partial-frame closure. Clean EOF between frames remains distinguishable from malformed partial EOF.
- `common.tls` uses dedicated-CA verification, hostname checking and TLS >=1.2. Clients always use `ultra96.week7.internal` as the verified identity, including through localhost forwards. No plaintext or verification bypass option exists.
- `ultra96.protocol` validates exact fields, integer types/ranges (rejecting bool), one configured session, eight deterministic dummy values, and result correlation/gesture/confidence. Session identifiers are bounded to 128 characters and exclude controls and unpaired surrogates.
- `ultra96.server.Week7Server` binds only IPv4 loopback on configurable ingestion/gateway ports, exposes assigned ephemeral ports, ACKs ingestion, and sends results independently to the latest Phone subscriber. Accepted trace INFO logs contain session/device/boot/sequence and omit raw values, certificates and secrets.
- Deduplication retains the most recent 4096 accepted trace tuples within the process/session. A duplicate does not emit another result. Old evicted traces and service restarts can be accepted again; this is not durable exactly-once delivery.
- Gateway queues hold at most 32 results, drop oldest, and expire at age 2 seconds. Each write receives only the remaining freshness budget. Already handed-off TCP/TLS bytes cannot be retracted; end-to-end rendering latency is not certified by this queue policy. Disconnected results are dropped without replay.
- A total eight accepted sockets includes unfinished TLS handshakes. The server owns accept tasks, handshake tasks, client sockets and subscriber workers and cancels them on close. Reader limits, write watermarks, frame length, queue length, handshake/read/write deadlines and socket backlog are bounded.
- `laptop.phone_simulator` supports a standalone verified TLS subscription, exact response validation, JSON result lines and optional capped reconnection (`--reconnect`, 0.5..5 seconds). `--count 100` stops after 100 results. Trust/protocol failures do not weaken verification.
- `tools/generate_week7_pki.py --output-dir <outside-Git>` creates RSA/SHA-256 CA and service certificates with CA BasicConstraints, serverAuth EKU and exact DNS SAN. Service lifetime is 30 days; CA lifetime is 365 days, with 5 minutes of clock-skew allowance. Private keys use owner-only POSIX modes or Windows directory ACLs; output must be an empty directory outside any Git worktree. Only provisioning requires `cryptography`; deployed transport/server/simulator use Python stdlib.

## Executed verification

Runtime: Windows, Python 3.12.7 from `D:\Anaconda\python.exe`, OpenSSL 3.0.15, cryptography 43.0.0. All test keys were generated beneath pytest's OS temporary directory outside the repository.

Command:

```powershell
& 'D:\Anaconda\python.exe' -m pytest tests/test_transport.py -q --log-cli-level=ERROR
```

Final observed result: **15 passed in 9.11s**, with no ERROR log output.

The suite exercised:

1. Split/coalesced frames; zero/oversize/non-object/duplicate-key/NaN/Infinity/overflowed-float/invalid-UTF-8/malformed JSON; partial header/body and frame deadline.
2. Real localhost TLS ingestion and independent gateway, 100 exact correlated ACK/result pairs, then duplicate suppression with no extra result.
3. Wrong DNS identity, unrelated CA and plaintext rejection.
4. Exact schema, wrong session, invalid scalar types/ranges and wrong dummy values.
5. Subscriber replacement, disconnect, fresh subscription without retained results and live-client shutdown.
6. Deduplication eviction after 4097 accepted traces.
7. Deterministic queue drop-oldest and expiry checks.
8. Real TLS split/coalesced traffic, partial-frame timeouts and connection limits.
9. Eight unfinished TLS handshakes, rejection of a ninth connection and cancellation of all pending handshakes within a one-second test deadline.
10. Normal ingestion EOF versus a declared body abandoned before any body bytes.
11. A real TLS Phone socket with reading paused and a small server socket send buffer: 6000 unique batches still received accepted ACKs; the Phone queue dropped old entries and stayed within 32.
12. PKI overwrite/Git-directory refusal and certificate BasicConstraints/SAN/serverAuth/lifetime checks.
13. Independent simulator delivery and rejection of inconsistent result IDs and an unrelated CA.

All seven transport/server/simulator/provisioning Python files also passed `ast.parse(..., feature_version=(3, 8))`. This is a Python 3.8 syntax check, not execution on a Python 3.8 or ARM runtime.

## RED/GREEN and fixes

The first observed RED was an explicit assertion that the missing framed transport module existed. The simulator test subsequently failed because its module was missing before implementation.

The connected-client shutdown test then exposed Python 3.12 listener closure waiting for still-live clients. A two-second regression failed at `Server.wait_closed`; cancelling owned clients first fixed that case. A separate one-second pending-handshake regression still failed, because the high-level TLS listener hid pre-handshake sockets. Moving acceptance under service ownership let the eight-client limit include handshakes and made shutdown bounded. Windows accept operations are cancelled before listening sockets are closed to avoid invalid overlapped handles.

The controller's first 100-result rehearsal reported one rejection during clean disconnect. A dedicated regression reproduced `rejected == 1` where zero was expected. Framing now distinguishes clean EOF from partial EOF, and both normal-close and partial-body counter assertions pass. Earlier rehearsal evidence should retain its original counter rather than be rewritten.

No SSH session, hardware connection, deployment or Git commit was performed by this transport worker. The controller coordinates final review and commits.
