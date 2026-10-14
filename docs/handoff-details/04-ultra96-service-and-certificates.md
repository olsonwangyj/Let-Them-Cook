# Detail chapter 4: Ultra96 service and certificates

> This is a detail chapter of the hand-off document, [../communications-handoff.md](../communications-handoff.md). It was checked against local `main` on 2026-10-14 (commit `dc582c7`, which was `25fe4e4` before the history rewrite in hand-off 6.2; the code has not changed since, up to `971fc52`), and updated the same day for the owner's rules, the owner's direction on the interfaces and the proposed schedule up to the in-person integration session on Tue 2026-10-20 (hand-off sections 3.1, 6.4, 7, 8 and 13). The interface shapes and the teammate dates are proposals until the teammates confirm them. Everything marked "planned" below does not exist in code yet. The code is the only source of truth. Where this chapter and the code disagree, follow the code.

## Role and boundaries

- The Ultra96 service is a Python asyncio process that uses only the standard library. Its entry point is `python3 -m ultra96.server` (`main` in `ultra96/server.py`).
- It opens only two TLS listeners, both on the board's loopback address: the ingest port `127.0.0.1:8888` and the gateway port `127.0.0.1:9999`.
- The ingest port receives `SENSOR_BATCH` from the laptop and answers each one with an `INGEST_ACK`.
- The gateway port receives `SUBSCRIBE` from the phone and answers `SUBSCRIBED`. After that it only pushes `GESTURE_RESULT` to the phone.
- Both ports are reachable only through SSH. The laptop first logs in over SSH to port 22 of the jump host `stujump`. It then logs in through the jump host to port 22 of the Ultra96. Finally an SSH local forward reaches port 8888 on the board. The iPhone makes the same two hops inside the app and ends at port 9999 on the board. The two routes are independent of each other.
- The service never connects out. The code has only the two listeners and no logic that opens a connection to the phone or the laptop.
- Communications' responsibility here ends at these two interfaces: samples are received accurately (proven by the ACK), and results are written accurately to the subscriber. Once the model interface exists (planned; the owner's proposal of 2026-10-14, final when Wen Ree confirms; hand-off 3.1 and 7.2), the board side of Communications also decodes each newly accepted sample into 11 physical floats, calls the model's `on_sample` once per sample, provides `emit`, and carries each result to the phone unchanged. It never merges, splits, filters or reinterprets results.
- The following belong neither to this service nor to Communications: pairing the left and right gloves, building model windows, deciding gesture or idle, model accuracy, and mapping labels to game actions. They belong to Wen Ree and Jie Ling. Wen Ree and Jie Ling also agree between themselves the label names, how often a label is produced, and whether several identical labels in a row (for example several `CHOP`) mean one action or several (hand-off 3.1).
- The current results are dummy labels. They are generated at `ultra96/server.py:264-267`. This is where Wen Ree's model input and output will connect. The interface requirements are in section 7.2 of the hand-off document. They are planned, not built: none of `start(emit)`, `on_sample(...)` or the thread-safe `emit(...)` exists in code yet. The dates asked of Wen Ree, proposals until Wen Ree confirms them, are a first connectable version pushed to the team repo by Fri 10-16 and the real model by Sun 10-18; what the Friday push must contain for the in-process and the separate-process option is in hand-off 6.4 and 7.2.
- Evidence levels follow the 5 levels in section 4.7 of the hand-off document. `INGEST_ACK` is level 3. It proves only that the board service validated and accepted this input, not that the phone received anything. `result_write_complete` in the event log is level 4. It proves only that the board wrote the result into the connection, not that the phone received it; the event always carries `phone_receipt_confirmed=false`. `Received` on the phone screen is level 5. `CAPTURE PASSED` printed by `demo.py` is level 3. The phone status `Subscribed` is none of these: it means only that the `SUBSCRIBE`/`SUBSCRIBED` handshake with this service succeeded, and it does not prove that results are flowing.
- Certificates: the local tool `tools/generate_comms_pki.py` generates a new CA and server certificate, or renews only the server certificate from the existing CA. The service loads only the server certificate and private key. The laptop and the phone get only the CA certificate.

## Components and files

| File | Responsibility |
|---|---|
| `ultra96/__init__.py` | Package marker with a one-line docstring. |
| `ultra96/protocol.py` | Field sets and all validation rules for the five message types; the label table `GESTURES`; `validate_session`, `validate_message`, `trace_fields`, `result_identity`. |
| `ultra96/server.py` | `CommsServer` (two listeners, connection limit, deduplication, replay protection, dummy results, subscriber, shutdown); `ResultQueue` (the result queue); the command-line entry point and SIGTERM handling. |
| `ultra96/diagnostics.py` | `BoundedEventLog`: an optional bounded event log. A background thread writes it to file. On close it gives an integrity receipt and a SHA-256. |
| `common/__init__.py` | Package entry. It imports `common.sensor`, and `common/sensor.py` reads `common/dummy_fixtures.json` at import time. So importing `common.wire` on the board also needs these two files. |
| `common/wire.py` | Frame encoding and decoding: a 4-byte big-endian length plus a UTF-8 JSON object; length limit; read and write timeouts; `ProtocolError`. |
| `common/tls.py` | TLS contexts: `client_context(ca_file)`, `server_context(cert_file, key_file)`; the constant `TLS_SERVER_NAME`. |
| `tools/generate_comms_pki.py` | Two modes. Without `--renew-server-from` it creates a new CA and server certificate, 4 files in all. With `--renew-server-from <CA folder>` it issues only a new server certificate from the existing CA, 3 files in all (function `renew_server_identity`). Only this tool needs the third-party library `cryptography`. |
| `tools/demo_service.py` | The implementation of `python demo.py service`. Over two SSH hops it inspects the service status on the board read-only, or starts the service in the foreground when both ports are free. `demo.py service --session-id` passes in the session ID. The deployment folder constants `BOARD_ROOT` and `BOARD_SOURCE` are here. |
| `tests/test_transport.py` | Over real local TLS: frames, trust, schema validation, 100 ACK and result pairs, v1 deduplication eviction, queue, connection limit, shutdown, PKI properties, renewal (the new certificate is signed by the original CA, old clients still trust it, a mismatched key is refused, non-empty and Git folders are refused), simulated subscriber. |
| `tests/test_transport_cleanup.py` | Shutdown releases connections that are waiting for TLS close; after shutdown the same ports can restart at once. |
| `tests/test_v2_events.py` | v2 `request_id` rules, random labels, a duplicate produces no second result, fingerprint conflicts, stale identities, namespace and command capacity, correlation fields in the event log. |
| `tests/test_server_diagnostics.py` | Event log: exclusive folder, non-blocking, overflow, file cap, write failure, short write, field allowlist, close timeout, receipt and hash, sequence numbers with several producers. |
| `tests/test_server_observation.py` | Each accepted result has exactly one outcome; accounting for replacement, cancellation, send failure and staleness; observer errors do not affect ACKs or forwarding; the default metric keys are unchanged; the command-line `--event-log-dir`. |
| `tests/test_server_signals.py` | Real SIGTERM and SIGINT on Linux: exit code 0, exactly one `stopped` line, ports reusable at once. These two cases are skipped on non-Linux systems. One more case does not depend on the platform: when the event loop does not support signal handlers, cleanup still follows the cancellation path. |
| `tests/test_accept_recovery.py` | Retry on temporary listener errors (capped at 1.0 s); fatal errors are visible; the command line does not idle after its listener dies. |
| `tests/test_ack_window_transport.py` | Over real TLS with a 0.35 s downstream delay: the ACK windows of two laptop bridges working with `CommsServer`; results match per device, one by one. |
| `tests/test_co_contracts.py` | v2 header bytes (`LC`, `4c43…`), dummy data selection, the firmware dummy data header file matches the JSON, control frame round trip and limits. Least related to the board service. |
| `tests/test_ssh_trust.py` | SSH command: strict host checking on each of the two hops, timeouts, keep-alive, port 22, the `-L` specification; the identity file is used only for the target hop; supervised mode refuses an interactive proxy. |
| `tests/test_demo_service.py` | The start script passes the requested session ID to the service as one argument (including session IDs with spaces and quotes); an invalid session ID is rejected; `service --start` follows the same session rule as capture (environment variable and command-line argument); port guard (a failed query does not start, either port taken does not start, start only when both are free); interactive SSH options; a cancel does not contact SSH; status mode is read-only. |

Used directly but outside this table: `tools/ssh_tunnel.py` (`tunnel_command` builds the two-hop SSH command), `demo.py` (entry point of the `service` subcommand), `common/sensor.py` and `common/dummy_fixtures.json` (needed at import time).

Local files that are not under version control but concern this chapter: `.week7-local/co_deploy.py` (the script used for the 28 September deployment) and `.week7-local/deployment-20260928T122047Z.json` (the record of that deployment). See "Cautions and known limitations".

## Data formats and constants

### Frame format (same on both ports, `common/wire.py`)

| Offset | Length | Type | Content |
|---:|---:|---|---|
| 0 | 4 | uint32, big-endian (`struct` format `!I`) | Body length N in bytes, not counting these 4 bytes |
| 4 | N | UTF-8 | One JSON object, compact separators, `ensure_ascii=False` |

- N ranges from 1 to 16384 (`MAX_FRAME_SIZE`, `common/wire.py:7`). The stream buffer limit is 16388 (`STREAM_LIMIT`, `common/wire.py:8`).
- There is no newline delimiter, no BOM and no error frame.
- On read, these are rejected: length 0 or above 16384, an incomplete header, an incomplete body, invalid UTF-8, invalid JSON, duplicate keys at any level, `NaN` and `Infinity`, floats that overflow to infinity (such as `1e999`), and a top level that is not an object.
- On write, `encode_frame` rejects the same things: a non-object, values that cannot be encoded, non-finite numbers, and a body over 16384 bytes (`common/wire.py:35-46`).
- A clean disconnect (EOF) between frames is a normal end and is not counted in `rejected`. A disconnect halfway through a header is an error (`common/wire.py:53-57`).
- The header and the body of one frame share one deadline, 5.0 s by default (`common/wire.py:49`, `:73`). Writing one frame also has a 5.0 s default deadline (`common/wire.py:76-79`).
- `write_frame` assumes that only one task writes on each connection (the docstring at `common/wire.py:77`). On the service, the only task that writes results to the phone is the send task `_send_results`.

### Rules common to all messages (`ultra96/protocol.py`)

- `type` must be one of the five types. The field set must match the tables below exactly. One extra or one missing field is rejected (`ultra96/protocol.py:46-48`).
- Integers must be real integers. The booleans `true` and `false` do not count as integers.
- `v` can only be 1 or 2 (`ultra96/protocol.py:42-43`). Planned: version 3 replaces both, with no interoperability between versions (see "Communications' own extension points").
- `session_id`: a string of 1 to 128 characters, with no control characters below code point 32 and nothing in U+D800 to U+DFFF (`ultra96/protocol.py:20-25`). It must also equal the session ID configured when the service started. Otherwise the code raises `wrong configured session` internally (`ultra96/protocol.py:50-51`).
- Every validation failure is handled the same way: the connection is closed, `rejected` goes up by 1, and no message is sent back. The exception texts (for example `wrong configured session`, `unexpected message type`, `values must contain exactly eight int16 integers`, `inconsistent dummy result`) are used only inside the process. They are not logged and not sent to the peer. The peer only sees the connection close (`ultra96/server.py:224-227`).

### `SENSOR_BATCH` (laptop to 8888)

| Field | Type | Values and rules |
|---|---|---|
| `v` | int | 1 or 2 |
| `type` | string | `"SENSOR_BATCH"` |
| `session_id` | string | See the common rules; the current default is `ltc-comms` |
| `device_id` | int | 1 or 2 (1 = left hand, 2 = right hand) |
| `boot_id` | int | 0 to 4294967295 |
| `seq` | int | 0 to 4294967295 |
| `uptime_ms` | int | 0 to 4294967295 |
| `values` | list | Exactly 8 integers, each −32768 to 32767 (`ultra96/protocol.py:67-69`). v1 must also equal `seq % 2000 − 1000 + 10*i`, for i from 0 to 7 (`ultra96/protocol.py:70-72`) |
| `request_id` | null or int | v2 only, and then required. Rules below |

### `INGEST_ACK` (8888 back to the laptop on the same connection)

| Field | Type | Values and rules |
|---|---|---|
| `v` | int | Same as the matching input |
| `type` | string | `"INGEST_ACK"` |
| `session_id`, `device_id`, `boot_id`, `seq` | As above | Echoed unchanged |
| `status` | string | `"accepted"` or `"duplicate"` |
| `request_id` | null or int | v2 only, echoed unchanged |

### `SUBSCRIBE` (phone to 9999) and `SUBSCRIBED` (9999 back to the phone)

| Field | Type | Values and rules |
|---|---|---|
| `v` | int | Only 1. A v2 subscription message is rejected (`ultra96/protocol.py:44-45`) |
| `type` | string | `"SUBSCRIBE"` or `"SUBSCRIBED"` |
| `session_id` | string | Must equal the session ID configured on the service |

The `SUBSCRIBED` that the service sends is always `{"v":1,"type":"SUBSCRIBED","session_id":<configured session ID>}` (`ultra96/server.py:331`).

### `GESTURE_RESULT` (9999 pushes to the phone)

| Field | Type | Values and rules |
|---|---|---|
| `v` | int | Same as the input that triggered it |
| `type` | string | `"GESTURE_RESULT"` |
| `session_id`, `device_id`, `boot_id`, `seq` | As above | Taken from the input that triggered it |
| `result_id` | string | Telemetry: `"device_id:boot_id:seq"`; command: `"cmd:device_id:boot_id:seq"` (`ultra96/protocol.py:94-96`) |
| `gesture` | string | Currently only `REST`, `FIST`, `OPEN`, `POINT` (`ultra96/protocol.py:4`). v1 must equal `GESTURES[seq % 4]`; v2 is a random one of the four |
| `confidence` | number | Currently fixed at 1.0. Validation accepts only the numeric value 1.0; the integer 1 also passes (`ultra96/protocol.py:82-83`) |
| `request_id` | null or int | v2 only, echoed unchanged |

### v1 versus v2, and the `request_id` rules

| Item | v1 | v2 |
|---|---|---|
| `request_id` field | Not allowed | Required |
| `values` | Must be the deterministic sentinel values | Any 8 int16 values |
| Dummy label | `GESTURES[seq % 4]` | `random.SystemRandom().choice(GESTURES)` |
| Deduplication | Looks only at `(device_id, boot_id, seq)`; content is not compared | Also compares the fingerprint `(uptime_ms, values)`, with replay protection |
| Subscription messages | Use v1 | Not allowed |

- `request_id = null`: ordinary telemetry.
- `request_id` is an integer: a command. The range is 1 to 4294967295, and `seq == request_id` is required (`ultra96/protocol.py:58-62`). 0, negative numbers, 2^32 and booleans are rejected.
- The ACK and the result echo `request_id` unchanged. A command's `result_id` has the `cmd:` prefix.

### Deduplication and replay protection

| Category | Storage | Limit | When full | Counts as a duplicate when | Connection is closed when |
|---|---|---|---|---|---|
| v1 | `_recent` (ordered dictionary) | 4096 | Evicts the oldest entry; an evicted identity is accepted again later | The key exists | Never |
| v2 telemetry | `_v2_recent` (fingerprints) and `_v2_high_water` (the highest `seq` per `(device_id, boot_id)`) | 4096 fingerprints; 128 namespaces | Fingerprints evict the oldest entry; high-water marks are never evicted | The key is in the fingerprint table with the same fingerprint | Different fingerprint; `seq` not above the high-water mark and not in the fingerprint table; the 129th namespace |
| v2 command | `_v2_commands` | 4096, never evicted | No eviction | The key exists with the same fingerprint | Different fingerprint; the 4097th new command |

- The implementation is at `ultra96/server.py:250-259` (v1) and in `_v2_duplicate` (`ultra96/server.py:277-307`).
- A duplicate input gets `status: "duplicate"` and produces no second result.
- When the connection is closed, no ACK is sent and `rejected` goes up by 1. The internal exception texts for the three kinds of close are `conflicting payload for existing v2 identity`, `stale v2 stream identity outside replay window`, and `v2 stream identity capacity exhausted; start a new session` or `v2 command identity capacity exhausted; start a new session` (`ultra96/server.py:291`, `:300`, `:302`, `:295`). These texts are never output.
- After capacity runs out, existing namespaces and existing commands still work normally. A new glove reboot (a new `boot_id`) or a new command is rejected every time until the service restarts.
- All deduplication state lives only in memory and belongs to this one process. A service restart clears all of it.
- v2 telemetry `seq` must increase within one power-up. Wrap-around is not supported. An earlier sample that arrives out of order makes the service close the connection.
- State is recorded before the next input is processed (`_v2_duplicate` finishes before any `await`). So even if the ACK was never written, the same identity arriving again is treated as a duplicate or a conflict.

### Limits and timeouts

| Item | Value | Location |
|---|---|---|
| Listen address | `127.0.0.1`, IPv4 | `ultra96/server.py:149` |
| Default ports | Ingest 8888, gateway 9999 | `ultra96/server.py:87` |
| Listen backlog | 8 | `ultra96/server.py:150` |
| Concurrent connection limit | 8, both ports together, including connections still in the handshake | `ultra96/server.py:181` |
| TLS handshake timeout | 5.0 s | `ultra96/server.py:216` |
| Timeout to read one frame | 5.0 s | `common/wire.py:49` |
| Write timeout for an ACK or `SUBSCRIBED` | 5.0 s | `common/wire.py:76` |
| Result queue length | 32, shared by both gloves | `ultra96/server.py:35` |
| Result freshness (waiting on the board only) | 2.0 s, counted from enqueue time; checked once at dequeue and once before the write | `ultra96/server.py:73`, `:369-370` |
| Result write timeout | The remaining freshness: 2.0 s minus the time already waited | `ultra96/server.py:378` |
| Wait when closing one connection | 1.0 s, then a forced abort | `ultra96/server.py:27` |
| Retry after a temporary listener error | Starts at 0.1 s, doubles each time, capped at 1.0 s | `ultra96/server.py:162-179` |
| Write buffer water marks | High 32768, low 16384 | `ultra96/server.py:218` |
| Minimum TLS version | 1.2 on both ends. If the server context does not meet it, construction fails with `server requires TLS >=1.2` | `common/tls.py:9`, `:18`; `ultra96/server.py:89-91` |
| v2 namespace and command capacity | 128 and 4096 (constructor arguments `max_v2_namespaces`, `max_v2_commands`) | `ultra96/server.py:88` |
| Event log queue | 2048 entries | `ultra96/diagnostics.py:56` |
| Event log file cap | 50 × 1024 × 1024 bytes | `ultra96/diagnostics.py:56` |
| Event log close wait | 2.0 s | `ultra96/server.py:416` |

- What the 2 s rule covers. It limits how long a result may wait on the board: in the queue (`ResultQueue.get_timed`, `ultra96/server.py:69-77`) plus the write into the phone's connection (`_send_results`, `ultra96/server.py:366-387`, where the write gets only the time that is left). It is not an end-to-end latency bound, and it is not a promise that the phone receives the result: once `write_frame` returns, the bytes are with TCP and TLS and cannot be recalled (the comment at `ultra96/server.py:374-375`). Time spent before the board (the glove, BLE, the laptop's own 2 s freshness, the tunnel) and after it (SSH, the phone) is not counted here. The phone keeps its own 2 s display window, counted from when it received a result (`ios-visualizer/CommsNative/Sources/CommsCore/DisplayState.swift:79`, `:109`). The planned phone result queue for `CommsNextResult` would also drop a result 2 s after the phone received it (a provisional V1 limit, revisited once Wen Ree says how often results come; hand-off 7.3, detail chapter 5). See also hand-off 9.2.
- Every accepted connection gets `TCP_NODELAY` (`ultra96/server.py:185`).
- `SO_REUSEADDR` is set only on POSIX (`ultra96/server.py:144-148`). It lets the same ports restart at once after the service stops.
- With port 0, the system assigns a port. The actual port is read from the `listening` line (`ultra96/server.py:154-155`, `:439-440`). The tests use it this way.
- Temporary listener errors are: a connection aborted by the peer while it was queued, file descriptors exhausted, buffers or memory exhausted (`errno` `ECONNABORTED`, `EMFILE`, `ENFILE`, `ENOBUFS`, `ENOMEM`, or Windows 10024, 10053, 10055). See `ultra96/server.py:170-174`.

### Command-line arguments (`python3 -m ultra96.server`)

| Argument | Default | Meaning |
|---|---|---|
| `--cert` | Required | Server certificate PEM |
| `--key` | Required | Server private key PEM |
| `--session-id` | `ltc-comms` | The only session ID this process accepts |
| `--ingest-port` | 8888 | Ingest port |
| `--gateway-port` | 9999 | Gateway port |
| `--event-log-dir` | Off | Event log folder; must be a new folder that does not exist yet |

Defined at `ultra96/server.py:459-466`. The log format is `%(asctime)s %(levelname)s %(message)s`, at level INFO (`ultra96/server.py:468`).

### Command-line arguments (`python demo.py service`)

| Argument | Default | Meaning |
|---|---|---|
| No arguments | — | Read-only inspection: `ss -ltnp` on the board, this user's processes, and the PID and working directory of each `ultra96.server` process (`tools/demo_service.py:64-71`) |
| `--start` | Off | Starts the service in the foreground when both ports are free |
| `--session-id` | The environment variable `LTC_COMMS_SESSION`, otherwise `ltc-comms` | Used only with `--start`. Same default rule as `demo.py run` and `live` (`demo.py:54-55`, `:70-71`). It is first checked with `validate_session`, then written into the start command through `shlex.quote` (`tools/demo_service.py:29-30`, `:50`) |

The account, jump host, board and deployment folders cannot be changed with arguments (see "Deployment constants" below).

### Standard output, logs and metrics

- After start, the service prints one line on standard output: `{"event": "listening", "host": "127.0.0.1", "tls": true, "ingest_port": 8888, "gateway_port": 9999}` (`ultra96/server.py:439-440`).
- On stop it prints one line: `{"event": "stopped", "metrics": {...}}` (`ultra96/server.py:453`). This is the only place the metrics are visible. There is no way to query metrics while the process runs.
- With the event log on, one more line comes last: `{"event": "observation_stopped", "state": {...}}` (`ultra96/server.py:419`).
- For each new input accepted, one INFO line goes to standard error: `accepted session=… device=… boot=… seq=…` (`ultra96/server.py:262-263`). `values` is not printed.
- When a listener task dies, one ERROR line goes to standard error: `listener task failed: <exception type name>` (`ultra96/server.py:202`).
- These two are the only routine log lines. Duplicates, rejections and drops are not logged.
- Metric keys: `accepted`, `duplicates`, `rejected`, `subscribers`, `replaced`, `disconnected_results`, `result_drops`, `result_stale`, `client_limit`, `accept_retries`, `accept_failures`. With an observer there is one more: `observer_errors` (`ultra96/server.py:121-126`).
- `result_drops` and `result_stale` are added to the metrics only when a subscriber ends (`ultra96/server.py:361-362`).
- `rejected` counts more than bad frames on the ingest port. All of the following land in the same `except _EXPECTED_ERRORS` in `_client` (`ultra96/server.py:20-21`, `:226-227`), and each adds 1:
  - a failed handshake, or a handshake longer than 5.0 s (`ultra96/server.py:215-216`);
  - on the ingest port: a bad frame, mismatched fields, a wrong session, a v2 identity conflict, exhausted capacity, a read timeout;
  - on the gateway port: a bad frame or a timeout before `SUBSCRIBE`;
  - on the gateway port: a failed or timed-out result write. The exception travels from `_send_results` (`ultra96/server.py:377-385`) through `task.result()` and `except Exception: raise` in `_gateway` (`ultra96/server.py:337-339`, `:345-348`) up to `_client`.

  So `rejected` above 0 does not necessarily mean that the laptop sent bad data.

### Event log (`--event-log-dir`)

- Files: while the service runs, `events.partial.jsonl` and `status.json`. After a normal end, `events.partial.jsonl` is renamed to `events.jsonl`, and `status.json` receives `events_sha256` and the counts.
- The folder is created with `mkdir(parents=True, exist_ok=False)` (`ultra96/diagnostics.py:62`). If the folder already exists, this raises `FileExistsError` and the service does not start.
- Each line is one JSON object with these fixed fields: `schema` (`ultra96-observer-event-v1`), `run_id`, `event_seq`, `utc`, `monotonic`, `event`.
- The `schema` of `status.json` is `ultra96-bounded-event-log-status-v1` (`ultra96/diagnostics.py:32`). Its keys include `complete`, `incomplete`, `lost_event_count`, `overflow_count`, `callback_error_count`, `file_cap_reached`, `file_cap_drop_count`, `writer_error_count`, `writer_error_type`, `close_timed_out` and `finalized` (`ultra96/diagnostics.py:241-269`).
- There are 15 event names (`ultra96/diagnostics.py:17-23`): `result_accepted`, `result_duplicate`, `result_no_subscriber`, `result_enqueued`, `result_drop_oldest`, `result_drop_stale`, `result_send_started`, `result_write_complete`, `result_send_failed`, `result_send_cancelled`, `result_abandoned`, `subscriber_claimed`, `subscriber_replaced`, `subscribed_write_complete`, `subscriber_ended`.
- There are 14 allowed extra fields (`ultra96/diagnostics.py:24-30`): `device_id`, `boot_id`, `seq`, `subscriber_id`, `previous_subscriber_id`, `queue_size`, `queued_count`, `session_id`, `reason`, `error_type`, `phone_receipt_confirmed`, `ambiguous`, `age_seconds`, `request_id`. The allowlist includes `queued_count`, but the current service code does not emit it.
- The log does not record `values`, `gesture`, the peer address or any credential.
- Result-queue events carry `subscriber_id` and `queue_size` automatically, and `age_seconds` when the enqueue time is known (`ultra96/server.py:43-54`).
- `result_drop_stale` carries `reason`: `dequeue` when the result is found stale at dequeue, `before_write` when the re-check before the write finds it stale (`ultra96/server.py:75`, `:372`).
- The `reason` of `result_abandoned` equals the reason that subscriber ended (`ultra96/server.py:83`, `:359-360`).
- `result_send_failed` and `result_send_cancelled` carry `ambiguous=true`. The first also carries `error_type` (`ultra96/server.py:380`, `:383-384`).
- `subscribed_write_complete` and `result_write_complete` carry `phone_receipt_confirmed=false`. The log object allows only `false` for this field (`ultra96/diagnostics.py:126-128`).
- `reason` and `error_type` must match `^[A-Za-z][A-Za-z0-9_.-]{0,63}$` (`ultra96/diagnostics.py:31`, `:118-120`).
- Values of `reason` in `subscriber_ended`: `peer_eof`, `unexpected_input`, `sender_stopped`, `replaced`, `server_shutdown`, `cancelled`, `error`, `disconnected` (`ultra96/server.py:319`, `:340-347`, `:359`).
- An invalid event name or field is not raised into the service. That event is dropped and `callback_error_count` goes up by 1 (`ultra96/diagnostics.py:160-165`).
- A full queue, exceeding the file cap, a write failure, a rejected field or a close timeout all make the receipt's `complete` `false` (`ultra96/diagnostics.py:304-312`). After the file cap is exceeded, later events are only dropped, never written (`ultra96/diagnostics.py:205-212`).

### Certificates (`tools/generate_comms_pki.py`)

New-PKI mode (without `--renew-server-from`, function `generate_pki`):

| Output | Content | Where it goes |
|---|---|---|
| `ca-key.pem` | CA private key, RSA 2048, public exponent 65537, PKCS#8, no passphrase, file mode 0600 | Stays only on the machine that generated it |
| `ca-cert.pem` | CA certificate, CN `B07 Communications Development CA`, valid 365 days, `CA=true`, path length 0, KeyUsage only `keyCertSign` and `cRLSign` | Laptop `--ca`; imported on the phone |
| `server-key.pem` | Server private key, RSA 2048, public exponent 65537, PKCS#8, no passphrase, mode 0600 | Board `BOARD_ROOT/tls/` |
| `server-cert.pem` | Server certificate, CN and SAN both `ultra96.week7.internal`, valid 30 days, `CA=false`, KeyUsage `digitalSignature` and `keyEncipherment`, extended key usage `serverAuth` | Board `BOARD_ROOT/tls/` |

Renewal mode (`--renew-server-from <CA folder>`, function `renew_server_identity`, `tools/generate_comms_pki.py:75-100`):

| Output | Content |
|---|---|
| `server-key.pem` | A new server private key, same specification as above |
| `server-cert.pem` | A new server certificate signed by the existing CA, same specification as above |
| `ca-cert.pem` | An unchanged copy of the existing CA certificate |

- Renewal mode neither outputs nor changes the CA private key or the CA certificate. Clients keep trusting the same `ca-cert.pem`, and the CA fingerprint registered in the phone source stays valid.
- Before renewal, the tool checks that `ca-key.pem` and `ca-cert.pem` are the same key pair. If not, it reports `ca-key.pem does not belong to ca-cert.pem` (`tools/generate_comms_pki.py:88-89`). The CA private key must have no passphrase.
- Renewal requires the CA to outlive the new server certificate. If now plus 30 days is past the CA's expiry, the tool reports `the CA expires before a new server certificate would; generate a new PKI` (`tools/generate_comms_pki.py:91-92`).
- Both certificates become valid 5 minutes before the issue time. The signature algorithm is SHA-256. The server certificate is built in `_server_certificate` (`tools/generate_comms_pki.py:38-56`), with the 30 days on line 47. The CA's 365 days and path length 0 are on lines 117 and 118.
- The host name constant is `SERVER_NAME = "ultra96.week7.internal"` (`tools/generate_comms_pki.py:24`), the same as `TLS_SERVER_NAME` at `common/tls.py:4`.
- The output folder must be outside every Git repository (neither the folder nor any parent folder may contain `.git`) and must be empty. It may not exist yet; the tool then creates it. Otherwise the tool reports `PKI output must be outside Git repositories and worktrees` or `PKI output directory must be empty; refusing to overwrite keys` and overwrites nothing (`tools/generate_comms_pki.py:27-35`). Both modes apply these rules.
- Before writing keys, the tool restricts the output folder's permissions. On Windows it gets the current user with `whoami`, then runs `icacls /reset` and `icacls /inheritance:r /grant:r <user>:(OI)(CI)F`, so only the current user has access. On other systems it runs `chmod 700` (`tools/generate_comms_pki.py:12-21`).
- Private keys are created with `O_EXCL` and mode 0600 (`tools/generate_comms_pki.py:64`). Certificates are written in exclusive mode. Existing files are never overwritten.
- Output on success: new-PKI mode prints `Created B07 Communications development PKI in <folder>` and `Copy only ca-cert.pem to clients; copy server-cert.pem/server-key.pem to Ultra96.` (`tools/generate_comms_pki.py:145-146`). Renewal mode prints `Issued a new server certificate from the existing CA in <folder>` and `Clients keep their ca-cert.pem; copy server-cert.pem/server-key.pem to Ultra96.` (`tools/generate_comms_pki.py:141-142`).
- On connect, clients verify the certificate chain and the host name `ultra96.week7.internal` (`TLS_SERVER_NAME`), even though they actually connect to the forwarded port on `127.0.0.1`.
- Server authentication only. There are no client certificates.
- The current CA is valid until 2027-09-06. Its SHA-256 matches the fingerprint registered in the phone source (`ios-visualizer/CommsNative/Sources/CommsBridge/Configuration.swift:12`). Under the rule above, it can no longer be used for renewal after about 2027-08-07. From then on, only a new PKI works.

### Deployment constants (`tools/demo_service.py`)

| Constant | Value |
|---|---|
| `BOARD_ROOT` | `/var/tmp/cg4002-week7-<account>-20260907`; the exact value is at `tools/demo_service.py:11` |
| `BOARD_SOURCE` | `BOARD_ROOT + "/source-co-v2-20260928T122047Z"` (`tools/demo_service.py:12`) |
| Certificate paths | `BOARD_ROOT/tls/server-cert.pem`, `BOARD_ROOT/tls/server-key.pem` (`tools/demo_service.py:50`) |
| Interpreter | `/usr/bin/python3 -u` (`tools/demo_service.py:50`) |
| Ports | `--ingest-port 8888 --gateway-port 9999`, hard-coded in the start command |
| SSH endpoints of the jump host and the board | See `tools/demo_service.py:17-18` |
| Session ID | Passed in by `demo.py service --session-id`; the default is `LTC_COMMS_SESSION`, otherwise `ltc-comms` |

`ssh_command` (`tools/demo_service.py:15-26`) reuses the two-hop command that `tunnel_command` builds. It removes `-L` with its argument, removes `-N` and `-T`, and adds `-tt`. So it keeps the settings of both hops: `StrictHostKeyChecking=yes`, `ServerAliveInterval=15`, `ServerAliveCountMax=3`, `BatchMode=no`, `Port=22`, the explicit `ProxyCommand`, and the connect deadlines of 20 s for the jump host and 60 s for the target (`tools/ssh_tunnel.py:26-38`).

## Workflow

### Normal path

1. Prepare the certificates. On first deployment, run `python -m tools.generate_comms_pki --output-dir <empty folder outside Git>` on the laptop to get 4 files. When a CA already exists (as it does now), use `--renew-server-from` to issue only a new server certificate. The steps are under "Renewing the server certificate" below.
2. Distribute the certificates. Put `server-cert.pem` and `server-key.pem` in `BOARD_ROOT/tls/` on the board, with the private key at mode 600. `demo.py service --start` uses only these two paths. Give `ca-cert.pem` to the laptop and the phone. `ca-key.pem` never leaves the machine that generated it.
3. Upload the code. The repository has no tracked upload script. Two methods are recorded. The first is the manual method in `docs/week7-runbook.md:112-135`: pack with `git archive`, upload with `scp`, extract into a new folder under `BOARD_ROOT`, check with `compileall`. The second is `.week7-local/co_deploy.py`, which was used on 28 September but is not committed (see "Cautions and known limitations"). The snapshot needs at least the whole of `ultra96/`, plus `__init__.py`, `sensor.py`, `dummy_fixtures.json`, `wire.py` and `tls.py` under `common/`. The smoke check on line 134 of the runbook imports the old class name `Week7Server`; the current class name is `CommsServer`. Do not extract over the running folder. After the upload, change `BOARD_SOURCE` in `tools/demo_service.py` to the new folder.
4. Inspect read-only first: `python demo.py service`. It prints, from the board, the listener list, this user's processes, and the PID and working directory of each `ultra96.server` process. If a healthy service already runs, reuse it. Do not start another one.
5. Start: `python demo.py service --start`, adding `--session-id <name>` when needed. The session ID is first checked with `validate_session`. If it is invalid, `demo.py` prints `Demo could not complete: …` and returns 2 without contacting SSH (`demo.py:294-296`).
6. After the check passes, it prints three lines (`tools/demo_service.py:57-59`): `Run 'python demo.py service' first. Reuse an existing healthy service.`, `Confirm ESP, board and iPhone versions match this deployment: <BOARD_SOURCE>`, `Session: <session ID> (the capture and the phone must use the same one)`. Then it prompts `Press Enter to start only if absent, or type q to cancel: `. Only pressing Enter alone continues. Any non-empty input cancels, returns 130 and does not contact SSH.
7. The script runs a piece of `sh` on the board over two SSH hops (`tools/demo_service.py:29-51`). It uses `ssh -tt`, strict host key checking on both hops, and the operator types the passwords interactively in the terminal. The `sh` script first runs `set -eu`, enters `BOARD_SOURCE`, confirms with `command -v ss` that the `ss` command exists, then lists listeners with `ss -ltnH`. When 8888 and 9999 are both free, it runs `exec /usr/bin/python3 -u -m ultra96.server --cert BOARD_ROOT/tls/server-cert.pem --key BOARD_ROOT/tls/server-key.pem --session-id <session ID> --ingest-port 8888 --gateway-port 9999`. The service runs as the logged-in user and becomes the foreground process of this SSH session. The exit code of `demo.py` is the exit code of `ssh` (`tools/demo_service.py:73`).
8. The service starts. It loads the certificate and private key (`ultra96/server.py:423`), opens the two listeners, registers a SIGTERM handler on platforms that support it, and prints the `listening` line.
9. The phone subscribes. The phone connects to 9999. The TLS handshake must finish within 5.0 s, and `SUBSCRIBE` must arrive within 5.0 s. After validation, the service creates a new empty result queue, registers this connection as the current subscriber, and then sends `SUBSCRIBED`. Registration comes before writing `SUBSCRIBED`, so every result produced from that moment goes into this queue. The phone shows `Subscribed` when `SUBSCRIBED` arrives. That proves only this handshake; whether results flow depends on input arriving on 8888 while this connection is still the subscriber.
10. After subscribing, the connection only receives. The service sets no idle timeout, so the phone can stay connected indefinitely.
11. The laptop sends samples. Each `SENSOR_BATCH` goes through three steps in order: read the frame, validate the fields and session, check for a duplicate.
12. A new sample: `accepted` goes up by 1, one INFO line is logged, and a result is produced. The code that produces the result is `ultra96/server.py:264-267`: v2 picks one of `GESTURES` at random, v1 takes `GESTURES[seq % 4]`, and `confidence` is hard-coded to 1.0.
13. If there is a subscriber, the result goes into the queue. If there is none, the result is dropped and counted (`ultra96/server.py:268-272`). Then `INGEST_ACK` (`accepted`) goes back to the laptop. The order is enqueue first, ACK write second (`ultra96/server.py:273-275`).
14. The send task takes results from the queue, checks freshness and writes them to the phone. The write timeout equals the remaining freshness (`ultra96/server.py:366-387`). This bounds only the waiting on the board, not end-to-end latency (see "Limits and timeouts").
15. Stop. Press Ctrl+C in the foreground terminal, or send SIGTERM to a verified PID. The service cancels the listener tasks, closes the listeners, cancels all connection tasks, and prints `stopped` with the metrics (`ultra96/server.py:389-403`, `:447-453`). In the Linux tests, both signals give exit code 0.

### Renewing the server certificate

1. On the laptop, run `python -m tools.generate_comms_pki --renew-server-from <existing CA folder> --output-dir <new empty folder outside Git>`. The existing CA folder must hold both `ca-cert.pem` and `ca-key.pem`. The location of the current CA and the full command are in section 6.3 of the hand-off document.
2. The tool checks the key pair and the CA's remaining validity, checks the output folder, generates 3 files, and prints the two success lines (see "Certificates" above).
3. Put the new `server-cert.pem` and `server-key.pem` in `BOARD_ROOT/tls/` on the board, with the private key at mode 600. The new certificate is still valid for only 30 days.
4. The service loads the certificate only at start (`ultra96/server.py:423`). After replacing the files, restart the service to use the new certificate.
5. Neither the laptop's `--ca` nor the CA fingerprint in the phone source needs to change.

### Failure paths

1. Invalid session ID: `demo.py` prints `Demo could not complete: session_id must be a nonempty string of at most 128 characters`, returns 2 and does not contact SSH.
2. The board cannot enter `BOARD_SOURCE` (the folder is missing or there is no permission): `cd` fails, the script exits at once because of `set -eu`, and nothing starts.
3. The board has no `ss` command: the script exits at `command -v ss` because of `set -eu`. Nothing starts and no explanation is printed (`tools/demo_service.py:34`).
4. The `ss` query fails: the script prints `Could not inspect service ports. Nothing was started.`, exits with code 2, and starts nothing (`tools/demo_service.py:35-38`).
5. Either 8888 or 9999 is taken: the script prints `Service ports are already in use. Nothing was stopped or started.` and the output of `ss -ltnp`, and exits with code 2 (`tools/demo_service.py:39-46`). The guard matches a listener on any local address that ends in `:8888` or `:9999` (`*:8888|*:9999`), not only `127.0.0.1`. The script never stops or kills an existing process.
6. The certificate or private key fails to load: the service raises an exception during start-up, prints a traceback and exits non-zero. There is no `listening` line.
7. The certificate has expired: the service loads it and starts as usual, because the service code does not check its own certificate's validity. Clients enforce validity, so the handshake fails. On the board this shows as `rejected` growing. The laptop gets no ACK. The phone stops, does not retry, and needs the passwords typed again before it can reconnect (hand-off document sections 4.6 and 9.2).
8. `--event-log-dir` points to an existing folder: constructing the log object raises `FileExistsError` and the service does not start.
9. A plaintext connection, a failed handshake, or a handshake over 5.0 s: the connection is closed and `rejected` goes up by 1.
10. The 9th concurrent connection: closed at once, and `client_limit` goes up by 1. Connections accepted while the service is shutting down are handled the same way.
11. An invalid frame, mismatched fields, or a wrong session ID: the connection is closed, `rejected` goes up by 1, no error frame is sent and nothing is logged. The peer must reconnect.
12. An ingest connection receives no complete frame within 5.0 s: the read times out, the connection is closed, and `rejected` goes up by 1.
13. A duplicate sample: the service answers `duplicate`, `duplicates` goes up by 1, and no result is produced.
14. A v2 fingerprint conflict, a stale identity, or exhausted capacity: see the "Deduplication and replay protection" table. The connection is closed.
15. No subscriber: the result is dropped at once, `disconnected_results` goes up by 1, and the event is `result_no_subscriber`. The laptop still gets `accepted`. A later phone subscription does not get the result resent.
16. The queue already holds 32 results: the oldest is dropped, with the event `result_drop_oldest`.
17. A result has waited 2.0 s or longer on the board (in the queue, or found stale just before the write): it is dropped, with the event `result_drop_stale`.
18. A result write fails or times out: the event is `result_send_failed` (`ambiguous=true`). This subscriber ends (`reason=error`). What remains in the queue is recorded as `result_abandoned`. `rejected` goes up by 1. The phone must subscribe again.
19. A new `SUBSCRIBE` arrives: the new connection becomes the subscriber. The service closes the old connection. Unsent results in the old queue are recorded as `result_abandoned`, `replaced` goes up by 1, and the event is `subscriber_replaced`.
20. The phone sends any byte after subscribing: the subscription ends with `reason=unexpected_input` and the connection is closed.
21. A temporary listener error: `accept_retries` goes up by 1 and the listener retries after a delay.
22. A listener task exits on any other error: `accept_failures` goes up by 1 and standard error shows `listener task failed: <exception type name>`. The service shuts down as usual and prints `stopped`, then exits non-zero with a `RuntimeError: B07 Communications listener failed` traceback (`ultra96/server.py:204-207`, `:445-446`). It never leaves an idle process behind with a dead listener.
23. The observer (event log) raises an exception: only `observer_errors` counts it. ACKs and result forwarding are not affected.
24. During renewal, the CA private key and certificate do not match, the CA has less than 30 days left, or the output folder breaks the rules: the tool exits with an error and writes no file.

## Why it is designed this way

| Design point | Reason | Alternatives rejected in the past | Design record |
|---|---|---|---|
| Both ports bind only to loopback and are reached only through SSH | The campus firewall lets through only TCP 22 of the Ultra96. The laptop and the phone are not on the allowlist and cannot accept incoming connections | Opening 8888 and 9999 to the outside; the phone connecting directly to the laptop; SSH reverse forwarding `-R` | `docs/archive/design/architecture-and-interface-draft-v0.1.md` sections 3 and 6; `docs/archive/design/week7-selected-design-2026-09-06.md` decisions 7 and 12 |
| Separate ingest and gateway ports; the laptop does not forward results | The board hands results directly to the phone's own connection, independent of whether the laptop is online | Having the laptop relay `GESTURE_RESULT` | Architecture draft sections 3 and 4.2; selected design decision 7 |
| A 4-byte big-endian length plus strict JSON; disconnect on any error | TCP and TLS are byte streams and need explicit boundaries. Strict validation keeps the two ends from reading the data differently | Resynchronising after an error; a plaintext mode | Selected design decision 5 |
| No error frame for a wrong schema or session | Keeps the protocol minimal. The closed connection is itself the signal | Adding an ERROR message | Selected design, end of the `Wire reference` section (line 192) |
| TLS inside SSH, a dedicated CA, a fixed host name | Even when the client connects to a local forwarded port, it verifies that the peer really is this service | Skipping the host name check; plaintext fallback | Selected design decision 11 |
| No client certificates | SSH already authenticates whoever gets in | mTLS | Selected design decision 11 |
| Short certificate lifetimes (server 30 days, CA 365 days); private keys stay out of Git | This is a development PKI | Long-lived certificates; keys in the repository | Selected design decision 11 |
| Renewal replaces only the server certificate; the CA stays | The phone source hard-codes the CA fingerprint, and the laptop trusts only this CA. Keeping the CA means no app rebuild and no `--ca` change | Creating a new CA every time | The docstring at `tools/generate_comms_pki.py:75-79`; commit `aa18643` |
| One process, standard library only, an ordinary user, an own folder under `/var/tmp` | The home folder on the board belongs to another user and is not accessible. No sudo, and no changes to the shared board | sudo; a system service; start on boot | Selected design decisions 7, 26 and 28; `docs/week7-runbook.md:104` |
| An own accept loop instead of `asyncio.start_server` | Connections still in the handshake must count toward the limit of 8, and shutdown must be bounded | A high-level TLS listener (it cannot see connections before the handshake, and under Python 3.12 its shutdown waits for live clients) | Selected design decision 21; `RED/GREEN and fixes` in `docs/archive/test-evidence/week7-transport-evidence.md` |
| `SO_REUSEADDR` on POSIX | The same ports must restart at once after a stop | Waiting for TIME_WAIT to end | Selected design decision 21 |
| One subscriber; a new one replaces the old one | The V1 scope is one phone, and the result stream always has exactly one owner | Broadcasting to several subscribers | Selected design decision 9 |
| Live results only: queue of 32, drop oldest, 2 s freshness, nothing resent when no one subscribes | A stale gesture must not be taken as a new game action. The 2 s limits only the board's own waiting (queue plus write); each segment has its own limit and there is no end-to-end bound (see "Limits and timeouts") | Keeping history and resending it after a reconnect | Selected design decision 9; architecture draft section 11 |
| v1 deduplication keeps only the latest 4096 entries, nothing on disk | Only best-effort deduplication within the process is promised | Persistent "exactly once" | Selected design decision 8; `docs/week7-runbook.md:302` |
| v2 high-water marks and the command ledger are never evicted | After an old identity is pushed out of the fingerprint table, it must not draw another random event | Evicting replay protection state along with the cache | `docs/co-protocol-v2.md:15`; `docs/archive/design/plans/2026-09-28-co-features.md:19`; the comment at `ultra96/server.py:105-108` |
| Dummy labels: v1 by `seq % 4`, v2 random | Validates Communications only and does not pretend to be inference | None | Selected design decision 8; `docs/co-protocol-v2.md:15` |
| Graceful exit on SIGTERM with printed metrics | Stopping the service needs a final record that can be checked | Killing the process outright | Selected design decision 28 |
| The event log is optional, bounded and written on a background thread | Added after the phone missed 109 results on 2026-09-21, to find which segment results were lost in. The existing log had only the INFO line for each accepted input | Synchronous disk writes in the event loop; an unbounded log | `Optional server diagnostics` in `docs/archive/test-evidence/phone-recovery-test-2026-09-21.md` |
| A completed write is not a phone receipt | Bytes handed to TCP and TLS cannot be recalled, and the peer's handling of them cannot be confirmed | Treating write completion as delivery evidence | As above; `docs/week7-runbook.md:176-181`; the comment at `ultra96/server.py:374-375` |
| The start script starts only when the ports are free and never stops an old process | A failed query must not count as "ports free". On a shared board, nobody else's process may be killed by mistake | `pkill`; killing by port | The comment at `tools/demo_service.py:31`; `docs/week7-runbook.md:256` |
| `demo.py service` passes in the session ID at start, follows the same rule as capture, and prints it before confirmation | The board service, the capture and the phone must use the same session. Before 2026-10-14 the start script hard-coded `week7-demo` | A start script that hard-codes the session ID | Commit `28db0b3`; `test_service_start_uses_the_same_session_rule_as_capture` in `tests/test_demo_service.py` |

Where documents disagree with the code (follow the code):

- Selected design decision 6 gives the session ID as `week7-demo`. The `Interfaces` section gives `Week7Server(ssl_context, session_id="week7-demo", …)` (`docs/archive/design/week7-selected-design-2026-09-06.md:14`, `:165`). Decision 7 mentions neither. The code uses `ltc-comms` and `CommsServer` (`ultra96/server.py:86-87`).
- Selected design decision 8 mentions only `seq % 4`. In the code, v2 uses random labels.
- `docs/week7-runbook.md` has not been updated. The `tools.generate_week7_pki`, `tools.rehearse_week7` and `Week7Server` in it have been renamed `tools.generate_comms_pki`, `tools.rehearse_comms` and `CommsServer`.
- `docs/week7-runbook.md:302` says the same identity may be accepted again after cache eviction. This holds only for v1. v2 rejects it as a stale identity and closes the connection.
- `docs/week7-runbook.md:137` suggests putting the certificates in a new `tls-redeploy-01` folder when the identity is replaced. `demo.py service --start` hard-codes the certificate path as `BOARD_ROOT/tls/` (`tools/demo_service.py:50`) and does not use files placed anywhere else.
- The technical report says "Version is integer 1" (`docs/archive/reports/week7-system-technical-report.md:198`). The code accepts 1 and 2 (`ultra96/protocol.py:42`).

## Cautions and known limitations

### Certificates

- The server certificate is valid for only 30 days. The owner plans to renew it and redeploy on Thu 10-15, first in the priority order, because nothing on the board works without it (hand-off 6.4). A certificate issued that day expires about 30 days later (around 11-14): it covers the 10-20 session, but must be renewed again before later sessions.
- The laptop keeps a copy of the server certificate that was deployed to the board in September. That laptop copy has been checked: it expired at 2026-10-06 15:11:29 UTC (the expiry is also recorded at `docs/archive/reports/week7-continuation-report-2026-09-07.md:733-734`). The 28 September redeploy kept the existing TLS files (`docs/archive/test-evidence/co-live-deployment-2026-09-28.md:12`). The repository has no record of a later certificate change. The certificate actually on the board has not been checked.
- The service code does not check whether its own certificate has expired. With an expired certificate the service starts as usual, and clients fail the handshake because they enforce validity.
- `--renew-server-from` can now renew from the existing CA. Running the tool without it creates a new CA, and then the fingerprint in the phone source and the laptop's `--ca` must both change.
- The phone app hard-codes the CA's SHA-256 in its source (`ios-visualizer/CommsNative/Sources/CommsBridge/Configuration.swift:12`) and compares against it when the CA is imported (`Configuration.swift:52-53`). Changing the CA means changing this value, rebuilding and reinstalling the app, and updating the laptop's `--ca`.
- The current CA expires on 2027-09-06. From about 2027-08-07, the tool refuses renewal.

### Week 7 names that stay unchanged

- The TLS host name `ultra96.week7.internal`. It is in the CN and SAN of the server certificate. It is also hard-coded in `common/tls.py:4`, `tools/generate_comms_pki.py:24`, `phone/receiver.py:16`, `phone/unity/CommsPhoneCore.cs:357` and `ios-visualizer/CommsNative/Sources/CommsTransport/CommsClient.swift:142`. Changing it needs a new certificate and a rebuild of the phone app.
- The board deployment folder `BOARD_ROOT` and the code snapshot folder `BOARD_SOURCE` have `week7` and a date in their names (`tools/demo_service.py:11-12`). They are real folders on the board.
- The laptop's default CA path `~/.codex/private/cg4002-week7-20260906/ca-cert.pem` (`demo.py:49-50`). Other machines must pass `--ca` explicitly.

### Board state (repository records)

- The last recorded deployment is from 2026-09-28. It was done with `.week7-local/co_deploy.py` (`docs/archive/test-evidence/co-live-deployment-2026-09-28.md:12`; local record `.week7-local/deployment-20260928T122047Z.json`). The code snapshot folder is `BOARD_ROOT/source-co-v2-20260928T122047Z`, which is the current `BOARD_SOURCE`. The start arguments include `--session-id week7-demo` and `--event-log-dir BOARD_ROOT/evidence/observer-co-live-20260928T122047Z`.
- That process was not started by `demo.py service --start`. `co_deploy.py` put it in the background with `start_new_session=True`, wrote its standard output and standard error to a log file under `BOARD_ROOT/evidence/`, and wrote its PID to `BOARD_ROOT/evidence/server.pid`. So it does not depend on any SSH session, and it may still be running if the board has not rebooted. The recorded PID is only a historical value. Before using it, verify it again as described in "How to run and verify".
- The event log of that run was already close to its 50 MiB cap on 2026-09-28 (`docs/archive/test-evidence/co-live-deployment-2026-09-28.md:109`). Later events are only dropped, never written.
- If this old process is still running, it accepts only the session `week7-demo`, while the laptop and the phone in the current code default to `ltc-comms`. It also serves the certificate it loaded when it started on 2026-09-28. That deployment kept the existing TLS files, so this is the September certificate, whose laptop copy expired on 2026-10-06. The redeploy order is in section 6.3 of the hand-off document; the owner plans it for Thu 10-15 (6.4).

### Deployment and operation

- `python demo.py service` hard-codes the account, jump host, board and code folders in `tools/demo_service.py:11-12` and `:17-18`. Arguments cannot change them. The session ID can be changed with `--session-id`.
- `BOARD_SOURCE` points to the 28 September snapshot. After uploading new code to a new folder, change this constant as well. Otherwise the old snapshot still starts.
- `--start` makes the service the foreground process of an `ssh -tt` session (`exec`, `tools/demo_service.py:50`, `:72-73`). There is no `nohup`, no system service and no automatic restart. If that terminal closes, the laptop sleeps, or the VPN drops, the service exits with it (hand-off document section 9.2). The service code handles only SIGTERM and Ctrl+C (`ultra96/server.py:433`, `:469-472`), not SIGHUP, so such an exit does not print the `stopped` line with the metrics. This is inferred from the code and was not tested. Keep the terminal that started the service open, just like the tunnel terminal. Every per-sample INFO log line also goes through this session.
- The previous point applies only to a service started with `--start`. The 2026-09-28 process was started detached by `co_deploy.py` and does not exit with any terminal (see "Board state" above). When looking for an old process before a redeploy, do not assume it ended with an SSH session; check for it with `python demo.py service` and the PID record in `BOARD_ROOT/evidence/server.pid`.
- `--start` does not pass `--event-log-dir`, so by default there is no event log. To record one, start the service by hand on the board.
- If the board snapshot lacks `common/sensor.py` or `common/dummy_fixtures.json`, the service fails at import.
- The board runtime (Python 3.10.4, OpenSSL 3.0.2, an ordinary user with uid 1000) comes from the records in `docs/week7-runbook.md:20` and `:104`. The code has no version check.
- A leftover `LTC_COMMS_SESSION` in the terminal. Transition-period documents taught setting `LTC_COMMS_SESSION=week7-demo`. This variable affects `demo.py run`, `live` and `service --start` together. If it is left set, the newly started service and the capture both use `week7-demo`, and `CAPTURE PASSED` appears as usual. The phone source hard-codes `ltc-comms` (`ios-visualizer/CommsNative/Sources/CommsBridge/IntegrationController.swift:74`), so the phone cannot subscribe. Before starting, confirm that this variable is not set, and look at the `Session:` line in the confirmation prompt.
- What `.week7-local/co_deploy.py` (not committed, ignored by Git) does: it logs in to the board through the jump host with `paramiko`, with strict `known_hosts` checking on both hops. It uploads the `.py` and `.json` files under `common/` and `ultra96/` to `BOARD_ROOT/source-co-v2-<timestamp>` and writes a manifest. It compiles the new code on the board. It requires exactly one of the user's own `ultra96.server` processes to be running under `BOARD_ROOT` and holding 8888 and 9999. It copies the old code to `rollback-co-<timestamp>`. It sends SIGTERM to the old process and waits for the ports to be released. It starts the new process in the background and counts the deployment as successful only if both ports are ready within 10 s; otherwise it stops the new process and restarts the old command from the rollback folder. It cannot be reused as it is: the session ID is hard-coded as `week7-demo`; it refuses to run when no old service is running on the board; `paramiko` is in no dependency file; and it reads the login passwords for both hops from environment variables. Under section 9 of the hand-off document, only olsonwangyj, the Communications owner, performs login steps. Agents do not run this script.

### Behaviour limits

- Any process that can reach `127.0.0.1:9999` on the board and knows the session ID can take over the phone's subscription. During a demo, do not run `laptop.phone_simulator`, `tools.rehearse_remote_comms` or any other subscriber against the board in use.
- The limit of 8 connections covers both ports together.
- The service closes an ingest connection that is idle for more than 5.0 s. After a glove drops and reconnects, the first sample may get no ACK. The laptop records it as one ambiguous drop.
- Reconnects can leave gaps in `seq` that the service, and later the model, sees. On a BLE disconnect the laptop discards that glove's queued samples (`inbox.deactivate` in `laptop/bridge.py`; reported as `callback_generation_dropped`). On a TLS reconnect, samples already written but not acknowledged count as ambiguous drops and are not resent (`ambiguous_dropped`). While a glove is disconnected it produces no samples and `seq` does not advance, so that time shows only as a jump in `uptime_ms`. None of these is resent, and nothing on the board fills or reports the gap (hand-off 7.2).
- v2 telemetry must arrive in increasing `seq` order. Gaps are allowed: a `seq` above the high-water mark is accepted however far above it is (`ultra96/server.py:298-303`).
- One process lifetime allows at most 128 `(device_id, boot_id)` pairs and at most 4096 commands. When they are used up, restart the service. Every glove power-up uses one pair.
- A service restart clears the deduplication state. After a restart, an old input that is sent again is accepted again.
- One INFO line is printed per accepted input. With two gloves at about 50 Hz each, that is about 100 lines per second.
- The event log is capped at 50 MiB. Once full, it only drops events. Use a new folder each time.

### Blind spots when troubleshooting

- The service records no rejection reasons. Expected errors are caught and only increment `rejected` (`ultra96/server.py:224-227`). A wrong session ID, mismatched fields, a stale v2 identity, exhausted capacity, and a handshake failure caused by an expired certificate all look the same on the board: the connection closes and `rejected` grows.
- The metrics become visible only when the service stops and prints `stopped`. When troubleshooting, do not expect to find texts such as `wrong configured session` or `v2 stream identity capacity exhausted; start a new session` in the board logs. They are never output. When capacity is exhausted, the operator sees a newly powered glove that never connects, and the laptop's `transport_errors` growing.
- The laptop side does not record reasons either (see [detail chapter 3](03-laptop-relay-and-tools.md)). A TLS connect or handshake failure increments only `transport_errors`. An ACK timeout or a mismatched ACK increments both `ack_errors` and `transport_errors`. So no log on either side records the reason. On the laptop, an expired certificate and an unreachable port show only `transport_errors`; a session mismatch and a protocol version mismatch between the two ends show `ack_errors` as well, because the Ultra96 closes the connection after reading the frame. When version 3 arrives, upgrading only one end shows up as a "silent disconnect". Only the newest version is supported (the owner's rule), so both boards, the laptop, the Ultra96 service and the phone app are upgraded together (hand-off 8, step 1).
- The only way to find which segment results are lost in is to start the service by hand with `--event-log-dir`, then read `status.json` and `events.jsonl` after a graceful stop.

### Communications' own extension points

These are all places that Communications itself must change. None is done yet. The order and scope are in section 8 of the hand-off document, and the dates in 6.4 (the owner's own plan; the teammate dates in it are proposals until the teammates confirm them): work on the version-3 packet (firmware, laptop and Ultra96) starting Thu 10-15, Wen Ree's first version connected on Fri 10-16, model labels and real confidence accepted in the three Python and C# checks on Fri 10-16 and in `Protocol.swift` on Sat 10-17, the real model on Sun 10-18. If time runs short, the order in 6.4 applies, and a hop whose teammate part is late is still tested with Communications' own dummy data (in the 11-value format once version 3 lands) and dummy labels.

| Goal | What blocks it now | Planned (the owner's direction of 2026-10-14, final when the teammates confirm, unless marked otherwise) | Code location |
|---|---|---|---|
| Real data with 11 values | `values` must be exactly 8 int16 values; the v1 sentinel formula is also written for 8 values. The service handles only `v` 1 and 2: `ultra96/protocol.py:42-43` rejects any other version, and the request-id field rule, de-duplication, the dummy label and `trace_fields` branch on `v == 1` or `v == 2` (`ultra96/protocol.py:46`, `:89-90`; `ultra96/server.py:250-251`, `:256-259`, `:266-267`). Today `common/sensor.py:50` copies the packet version into the message's `v`, and the service copies the sample's `v` into the result (`ultra96/server.py:264`), so the result path changes too | Protocol version 3, a new format. With the 11 values only it is 38 bytes (16-byte header + 11 × int16); the final layout is frozen only after the IDLE/MOVING answer, because an extra field changes the length and `on_sample`. Only the newest version is supported (the owner's rule): version 3 replaces versions 1 and 2 everywhere, including the dummy test data, which moves to the 11-value format, and there is no transition period. Firmware, laptop, Ultra96 and phone change together, with golden vectors and tests first (hand-off 8, step 1). The int16 scales are checked against Siqiang's real sample log before they are fixed. Out-of-range values are handled in the firmware when scaling: clamp to the int16 limit or drop that one sample, to be agreed with Wen Ree; counted either way, never by dropping a connection or a whole gesture. Normal values are expected to fit, but that is not guaranteed, and a clamped value cannot be told apart from a real value at the limit (the reasons, and the per-sample flag the model would need to know, are in hand-off 8, step 1) | `ultra96/protocol.py:42-46`, `:67-72`; `ultra96/server.py:250-259`, `:264` |
| Give the model physical floats | Nothing decodes `values` today; the service uses them only for validation and the v2 fingerprint (`ultra96/server.py:286`) | Transport stays int16. On the board, Communications decodes each newly accepted sample and divides each value by its scale (hand-off 4.2: ×10000 for acceleration and flex, ×100 for angular rate and angles) before calling `on_sample`. Normalisation is Wen Ree's (7.2) | `ultra96/server.py:264-267` |
| Carry the model's labels | The label table is hard-coded to four labels; result validation accepts only these four | Forward each label as it is. The label set is agreed between Wen Ree and Jie Ling (3.1); by default it is the six in `models/class_names.json` | `ultra96/protocol.py:4`, `:76-81` |
| Carry the model's confidence | Validation accepts only 1.0 | Forward the model's confidence (0 to 1) as it is | `ultra96/protocol.py:82-83` |
| Replace the dummy labels with model results | The result is produced synchronously in the same coroutine that receives the sample, and the ACK comes after it | `start(emit)` once at start-up; `on_sample(device_id, boot_id, seq, uptime_ms, values)` once per newly accepted sample, returning at once; the result comes back later through `emit` (7.2). Proposed dates, until Wen Ree confirms: a first connectable version pushed to the team repo by Fri 10-16, the real model by Sun 10-18 (6.4) | `ultra96/server.py:264-275` |
| A thread-safe result hand-over function | None exists now. The result queue and the subscriber state can only be used on the event loop thread | `emit(gesture, confidence, device_id, boot_id, seq)`, written by the owner, callable from any thread, moving each result onto the event loop (7.2) | `ultra96/server.py:35`, `:56-63`, `:268-272` |
| Result numbering | Now one input maps to one result, and `result_id` is built from that input's identity | Each `emit` names one sample's identity, and each result must name a different sample, because the phone de-duplicates by `result_id`. How often the model emits is Wen Ree's; Communications passes every result through and never merges, splits or filters (3.1) | `ultra96/protocol.py:94-96`, `ultra96/server.py:264-265` |
| Labels in the event log | The field allowlist has no `gesture`. Passing a field outside the allowlist drops that event and makes the receipt incomplete | Not decided | `ultra96/diagnostics.py:24-30`, `:99-100` |

Each receiver also holds its own copy of the same label and confidence allowlist: `phone/receiver.py:17`, `ios-visualizer/CommsNative/Sources/CommsCore/Protocol.swift:54-62`, `phone/unity/CommsPhoneCore.cs:32`. These three and `ultra96/protocol.py` must change together. The details are in [detail chapter 5](05-phone-and-week7-receiver.md). In the same step the phone gains a `confidence` field and the planned per-result function `CommsNextResult` (hand-off 7.3 and 8, step 5; the owner plans it ready by Sun 10-18). It promises only that results wait in arrival order, de-duplicated by `result_id`, and that each result that is not dropped can be taken out at most once; it does not promise that every result is delivered. Its provisional V1 limits (32 waiting results, oldest dropped when full, a result dropped 2 s after it reached the phone, drops counted) belong to the phone and are separate from this service's queue; they are revisited once Wen Ree says how often results come (hand-off 7.3, 13).

### Technical constraints related to teammate interfaces

The content of the three interfaces (fields, how calls are made, questions for teammates) is maintained only in section 7 of the hand-off document: Siqiang in 7.1, Wen Ree in 7.2, Jie Ling in 7.3. This chapter records only the constraints that come from its own code. Every interface in section 7 is planned, not built; the division of work is the table in hand-off 3.1. The interface shapes are the owner's proposals of 2026-10-14, final when the teammates confirm them, and teammates deliver code by pushing it to the team repo on GitHub, not over Telegram (hand-off 7, 13).

- The owner's direction of 2026-10-14 (planned; final when Wen Ree confirms): the model receives each sample's 11 values as physical floats in the agreed order and units. They travel as int16, and Communications decodes them and divides by the scale on the board before calling `on_sample`. Restoring cannot recover precision dropped when packing (acceleration and flex keep 4 decimal places, angular rate and angles 2). Any normalisation is Wen Ree's.
- `on_sample` would be called once per newly accepted sample, from the ingest path at `ultra96/server.py:255-267`: a duplicate (`status: "duplicate"`) produces no call, just as it produces no result today. Samples from the two gloves arrive on two independent connections, with no pairing and no alignment, and can have `seq` gaps (see "Behaviour limits").
- The model input must return immediately. The reason is that the board service has only one asyncio event loop, and the ingest connections of both gloves share it. Today the result is produced synchronously in the `_ingest` coroutine, and the ACK is written only after it (`ultra96/server.py:264-275`). If the model input sits in the same place and blocks, its time adds directly to the ACKs of both gloves, and it also holds up result sending and new connections. The laptop waits up to 5 s for each frame's ACK (`laptop/bridge.py:605-613`; `io_timeout` defaults to 5.0 at `laptop/bridge.py:41`). Sample freshness is 2 s (`laptop/bridge.py:40`). The ACK window is 32 frames (`laptop/dual_bridge.py:414`), and at 50 Hz 32 frames are only 0.64 s.
- The model output must be called on the service's event loop thread. The result queue is an `asyncio.Queue` (`ultra96/server.py:35`). `ResultQueue.put` is synchronous and has no lock (`ultra96/server.py:56-63`). The current subscriber `_subscriber` has no lock either. If the model produces results on another thread or in another process, they must be handed over through the event loop (for example with `loop.call_soon_threadsafe`), not by calling the enqueue function directly. Communications provides this thread-safe hand-over function (the planned `emit`, written by the owner). It is an extension point in the table above.
- Communications passes every result through unchanged: it does not merge, split, filter, rename or reinterpret results. Several identical labels in a row (for example several `CHOP`) reach the phone as several results (subject to the board queue of 32 and the 2 s limit); whether they mean one action or several is for Wen Ree and Jie Ling to agree (hand-off 3.1).
- Only the existing send task may write results to the phone. The frame-writing contract is one writing task per connection (`common/wire.py:77`).
- `GESTURE_RESULT` cannot gain fields freely. All four validators match fields exactly. On the board, `ultra96/protocol.py`, and the Python receiver `phone/receiver.py` (`:111-115`) require the key sets to be exactly equal. The C# reference implementation compares the field count: 9 for v1, 10 for v2 (`phone/unity/CommsPhoneCore.cs:46`, `:70`). The iPhone parser accepts at most 10 fields; a v2 result already has exactly 10, and the values may only be strings, numbers or `null` (`ios-visualizer/CommsNative/Sources/CommsCore/Protocol.swift:179`). All four require `result_id` to equal `device_id:boot_id:seq` exactly (with `cmd:` for commands), and `device_id` to be 1 or 2. So the correlation that the model hands back can only be the identity of one sample, which matches the output fields in section 7.2 of the hand-off document. On the iPhone, a validation failure is a terminal error. All four also accept only `v` 1 and 2 on a result (`ultra96/protocol.py:42-43`, `phone/receiver.py:115`, `phone/unity/CommsPhoneCore.cs:70`, `Protocol.swift:40`), and the service copies the sample's version into the result (`ultra96/server.py:264`), so these checks change together with the version-3 packet (hand-off 8, step 1).
- The service currently runs as an ordinary user, with `/usr/bin/python3 -u` and the standard library only (`tools/demo_service.py:50`).

### History and removed items

- Commit hashes in this chapter are those of local `main` after the history rewrite of 2026-10-14, which changed commit messages only, not file contents (hand-off 6.2): `25fe4e4` became `dc582c7`, `4c2b078` became `5db56ad`, `d2fff21` became `28db0b3`, `5f2c12a` became `b414696`, and `8dc536c` became `aa18643`. The pull request branch `comms/remove-week7-legacy` was rebased onto the team main `880abba` (`1bf8371`, `0fda8d5`, `23bdee6`, then `0b9ed2e` for a README line) and merged into the team main by PR #18 (merge commit `5a004c6`) at the owner's request; further pushes need the owner's go-ahead.
- On 2026-10-14, merge `5db56ad` (branch `comms/remove-week7-legacy`, commits `28db0b3` and `b414696`) removed the Week 7 compatibility. Only one change concerns this chapter. The start command in `tools/demo_service.py` used to hard-code `--session-id week7-demo`. Now `demo.py service --session-id` passes the session ID in, with `LTC_COMMS_SESSION` or `ltc-comms` as the default, and prints it before confirmation. `ultra96/`, `common/wire.py` and `common/tls.py` did not change in this merge.
- The session ID `week7-demo`: the September deployment and the old app installed on the phone use it. The current code defaults to `ltc-comms` everywhere.
- The class name `Week7Server` and the tool names `generate_week7_pki.py` and `rehearse_week7.py` have been renamed `CommsServer`, `generate_comms_pki.py` and `rehearse_comms.py`. The old names appear only in archived documents and in `docs/week7-runbook.md`, which has not been updated.
- The packet magic `W7` and the statistics magic `W7S1`: the board service receives only JSON and never touches them. The laptop side now accepts only `LC` and `LCS1` (see [detail chapter 3](03-laptop-relay-and-tools.md)).
- The code no longer reads `.week7-local/`. It keeps the historical captures, the September deployment script and the deployment record. Do not delete it.

## How to run and verify

This section comes from reading the code and documents. No test, script or build was run while this chapter was written.

### Locally (without the board)

1. Install the dependencies: `python -m pip install -r requirements-dev.txt`.
2. Generate a temporary set of certificates: `python -m tools.generate_comms_pki --output-dir <empty folder outside Git>`.
3. Start the service: `python -m ultra96.server --cert <folder>/server-cert.pem --key <folder>/server-key.pem`. The `listening` line means it started.
4. Open a second terminal as the subscriber: `python -m laptop.phone_simulator --host 127.0.0.1 --port 9999 --ca <folder>/ca-cert.pem --count 3 --reconnect`. It waits only 5.0 s for each result (`laptop/phone_simulator.py:13-14`, `:26`). Without `--reconnect`, if no input arrives, it exits with `TimeoutError` about 5 s after subscribing (`laptop/phone_simulator.py:57-59`).
5. Open a third terminal to send synthetic input: `python -m laptop.dual_bridge --ca <folder>/ca-cert.pem --port 8888 --mock --duration 10`. `--mock` is explicit two-device synthetic input and does not touch BLE (`laptop/dual_bridge.py:430-431`). `--port 8888` connects it directly to the local service; the default 18888 is the tunnel port (`laptop/dual_bridge.py:410`; the host defaults to `127.0.0.1`, see `laptop/bridge.py:36-38`). The subscriber should receive 3 results and exit.
6. Press Ctrl+C to stop the service. The `stopped` line with the metrics should appear.
7. A simpler one-shot rehearsal: `python -m tools.rehearse_comms --pki-dir <same folder> --duration 30 --target 100`. It starts the service, the bridge and the subscriber locally and prints one JSON line. `passed` should be `true`.

To run the tests for this chapter:

```
python -m pytest tests/test_transport.py tests/test_transport_cleanup.py tests/test_v2_events.py tests/test_server_diagnostics.py tests/test_server_observation.py tests/test_server_signals.py tests/test_accept_recovery.py tests/test_ack_window_transport.py tests/test_co_contracts.py tests/test_ssh_trust.py tests/test_demo_service.py -q
```

- Do not run `python -m pytest` without paths from the repository root (rule 4 in `AGENTS.md`). For the full suite, use `python -m pytest tests laptop/tests phone/tests -q -p no:cacheprovider`.
- The two real-signal cases in `test_server_signals.py` run only on Linux. The script cases in `test_demo_service.py` need `sh` on the local machine. Two cases in `test_ssh_trust.py` need `ssh` on the local machine. When a tool is missing, those cases are skipped.

### On the board

Every step below that logs in to the jump host or the Ultra96 is done only by olsonwangyj, the Communications owner, in their own terminal (hand-off document section 9).

1. Turn on the VPN first.
2. Check the status: `python demo.py service`. It prints the board's listener list, this user's processes, and the PID and working directory of each `ultra96.server` process. This step is read-only. A detached process, such as the one `co_deploy.py` started on 2026-09-28, also appears here. Its recorded PID is in `BOARD_ROOT/evidence/server.pid`.
3. Start: first confirm that `LTC_COMMS_SESSION` is not set in the terminal. Then run `python demo.py service --start`, check the `Session:` line, press Enter to confirm, and complete the two-hop login as prompted.
4. Check: the `listening` line appears, and in `ss -ltnp` only `127.0.0.1:8888` and `127.0.0.1:9999` belong to this process.
5. Check the certificate's validity. On the board, run `openssl x509 -noout -dates` on `BOARD_ROOT/tls/server-cert.pem` (whether the board has the `openssl` command-line tool is not recorded). Or, on the laptop with the tunnel open, run `openssl s_client -connect 127.0.0.1:18889 -servername ultra96.week7.internal` (hand-off document section 6.3).
6. End-to-end check: on the laptop side, every sample gets `accepted` (level 3). On the phone side, the increase in `Received` equals the `Phone expected increase` that `demo.py` prints (level 5). These are evidence at different levels. The phone showing `Subscribed` is not evidence that results flow; only the `Received` increase is. `Phone expected increase` is the number of generated samples plus completed commands (`demo.py:209-211`), so it holds only while one input makes one dummy result. Once the model produces results per window, this criterion must be redefined (hand-off 8, step 6).
7. To find which segment results are lost in, enter `BOARD_SOURCE` on the board and run by hand `/usr/bin/python3 -u -m ultra96.server --cert BOARD_ROOT/tls/server-cert.pem --key BOARD_ROOT/tls/server-key.pem --session-id ltc-comms --event-log-dir <new folder that does not exist>`. After a graceful stop, look at `status.json`. Only `complete` equal to `true` and `lost_event_count` equal to 0 make it usable as complete evidence.
8. Stop: press Ctrl+C in the foreground terminal that started it. Or first verify with `ps -p <PID> -o pid=,uid=,args=` and `readlink -f /proc/<PID>/cwd` that it is the user's own `ultra96.server`, then run `kill -TERM <PID>`. Do not use `pkill` or kill by port. A service started in the foreground prints the `stopped` line in that terminal. A service that `co_deploy.py` started in the background writes this line to its log file under `BOARD_ROOT/evidence/`.
