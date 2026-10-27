"""Hand12 runner: Wen Ree's independent-hand engine in the model runner slot (compat delivery).

The service (ultra96.server --sensor-version 4 --model ultra96.model_bridge) sends this
runner the bridge hello and every accepted sample of both gloves over its model socket;
this runner answers with result lines. It runs src.hand_runtime.HandEngine and
src.hand_events.EventEncoder unchanged, one of each per hand, and delivers in COMPAT
mode: one result line (one v3 GESTURE_RESULT at the service) for each pulse,
state_start, state_refresh and idle event, naming the hand and the source sample of
that event. A v3 result has no place for state_end and reset events; they are logged
here and not sent.

    cd <staged folder> && sudo <PYNQ python> -m ultra96.hand_runner --bundle bundle --backend fpga --bit <overlay>.bit

Each bridge connection gets a fresh worker_epoch and fresh engines and encoders. A
hand whose samples stop for --reconnect-gap seconds, or whose boot_id changes, is
reset before its next sample; the other hand is not touched. Stdout carries JSON
lines: the scope, connections, every forwarded result, every state_end and reset,
and a summary every --summary-interval seconds and at exit. --out records every
record, predictions included. All times are this runner's own monotonic clock.

Exit status: 0 after SIGTERM or Ctrl+C; 2 after a backend (model or FPGA) error or
another fatal error; 3 when the service's hello is not the twelve-channel v4 hello.
"""
import argparse
from collections import Counter, OrderedDict
import json
import math
import os
from pathlib import Path
import queue
import secrets
import signal
import socket
import sys
import threading
import time

from common.hand_contract import ProtocolError, make_hello
from src.hand_backend import NumpyHandBackend, PynqHandBackend
from src.hand_events import EventEncoder
from src.hand_runtime import CHANNELS, HandEngine, ModelBundle, digest

# The deployment folder of the board service (tools/demo_service.py BOARD_ROOT).
DEFAULT_SOCKET = "/var/tmp/cg4002-week7-yanjie-20260907/model-runner.sock"
DEFAULT_IP_NAME = "gesture_cnn_hand_u2_cache_0"
DELIVERY = "compat_v3_gesture_result"
FORWARDED_KINDS = ("pulse", "state_start", "state_refresh", "idle")
HANDS = (1, 2)  # LEFT, RIGHT
LEASE_MS = 1000  # the format-2 hello needs one; compat delivery does not carry it
MAX_LINE_BYTES = 4096  # as ultra96.model_bridge
FORWARDED_MEMORY = 4096  # source identities kept against a second result, as the service keeps
POLL_SECONDS = 0.005
RETRY_SECONDS = 1.0
EXIT_BACKEND = 2
EXIT_INCOMPATIBLE = 3
TIMING_SCOPE = ("runner-local monotonic clock only: inference_ms and worker_sample_age_ms are "
                "measured inside this runner from the arrival of a sample line; they exclude the "
                "glove, BLE, laptop, network, service and game, whose clocks are not synchronized")


class IncompatibleService(ValueError):
    """The service's first line is not the twelve-channel v4 bridge hello."""


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:  # an integer beyond the float range
        return False


def _uint32(value):
    return type(value) is int and 0 <= value < 2 ** 32


def sample_error(message):
    """Why a sample's identity or values cannot enter a window; None when they can.

    HandWindow.add refuses these as well, but numpy raises TypeError or OverflowError,
    not ValueError, for some malformed values (an object, a huge integer). Checking here
    first keeps every malformed sample non-fatal, and a refused sample never resets its hand.
    """
    if not all(_uint32(message.get(key)) for key in ("boot_id", "seq", "uptime_ms")):
        return "boot_id, seq and uptime_ms must be unsigned 32-bit integers"
    values = message.get("values")
    if not isinstance(values, list) or len(values) != len(CHANNELS) or not all(map(_number, values)):
        return "values must be a list of twelve finite numbers"
    return None


def check_bridge_hello(message):
    """Accept only the bridge hello format 1 naming exactly the twelve v4 channels, in order."""
    if (not isinstance(message, dict) or message.get("type") != "hello"
            or type(message.get("format")) is not int or message.get("format") != 1):
        raise IncompatibleService("expected the model bridge hello (type hello, format 1) first")
    channels = message.get("channels")
    if channels != list(CHANNELS):
        if isinstance(channels, list) and len(channels) == 11:
            raise IncompatibleService("the service sends the eleven-channel sensor v3 hello; start "
                                      "ultra96.server with --sensor-version 4 for this runner")
        raise IncompatibleService("the service hello must name the twelve v4 channels "
                                  + ",".join(CHANNELS))
    return message


def check_settings(threshold, confirmations, interval, reconnect_gap, session_id):
    """Raise ValueError for any setting HandEngine, the format-2 hello or this adapter refuses."""
    for name, value in (("threshold", threshold), ("interval", interval),
                        ("reconnect gap", reconnect_gap)):
        if not _number(value):
            raise ValueError(name + " must be a finite number")
    if interval <= 0 or reconnect_gap <= 0:
        raise ValueError("interval and reconnect gap must be positive seconds")
    HandEngine(None, threshold, confirmations, interval)  # its own checks
    make_hello(session_id, "0" * 32, LEASE_MS, threshold, confirmations)  # ProtocolError is a ValueError


def _hand_counts():
    return dict(samples=0, duplicates_ignored=0, invalid=0, predictions=0, stale_suppressed=0,
                events=Counter(), forwarded=0, collisions=0, resets=Counter(), encoder_errors=0,
                event_time_raised=0)


def _discard(record):
    pass


class HandAdapter:
    """Both hands between the model bridge and the result path; no sockets, no clock of its own.

    The caller passes host-monotonic times in seconds. engines[d] and encoders[d] serve
    hand d only and share one backend, so resetting one hand never touches the other.
    The engine and the encoder run unchanged; this class only routes samples to them,
    resets a hand on a reconnect, and turns events into result lines. log(record)
    receives every record. Backend exceptions propagate: the caller stops the runner.
    """

    def __init__(self, backend=None, *, threshold=0.70, confirmations=3, interval=0.2,
                 reconnect_gap=1.0, session_id="ltc-comms", log=None, backend_factory=None,
                 epoch_factory=None):
        check_settings(threshold, confirmations, interval, reconnect_gap, session_id)
        self.backend = backend
        self.backend_factory = backend_factory  # called once, after the first valid hello
        self.threshold = threshold
        self.confirmations = confirmations
        self.interval = interval
        self.reconnect_gap = reconnect_gap
        self.session_id = session_id
        self.log = log if log is not None else _discard
        self.epoch_factory = epoch_factory if epoch_factory is not None else lambda: secrets.token_hex(16)
        self.epoch = None
        self.engines = {}
        self.encoders = {}
        self.counts = {hand: _hand_counts() for hand in HANDS}
        self.totals = Counter()  # connections, bad and unexpected lines, samples naming no hand
        self._arrival = {}  # hand -> arrival time of its last sample that entered a window
        self._boot = {}
        self._event_time = {}  # hand -> latest local time handed to its encoder
        self._prediction = {}  # hand -> its latest prediction record
        self._forwarded = OrderedDict()  # (hand, boot_id, seq) already sent as a result
        self._outbox = []

    def connected(self, hello, now):
        """A bridge connection sent hello at now: check it, then start a fresh worker epoch."""
        check_bridge_hello(hello)
        if self.epoch is not None:
            self.disconnected(now)
        if self.backend is None:
            if self.backend_factory is None:
                raise RuntimeError("the adapter has no backend")
            self.backend = self.backend_factory()
        epoch = self.epoch_factory()
        negotiated = make_hello(self.session_id, epoch, LEASE_MS, self.threshold, self.confirmations)
        self.engines = {hand: HandEngine(self.backend, self.threshold, self.confirmations, self.interval)
                        for hand in HANDS}
        self.encoders = {hand: EventEncoder(negotiated) for hand in HANDS}
        self.epoch = epoch
        for state in (self._arrival, self._boot, self._event_time, self._prediction):
            state.clear()
        self.totals["connections"] += 1
        self.log(dict(type="connection_open", worker_epoch=epoch, channels=list(CHANNELS), at=now))

    def disconnected(self, now):
        """The bridge connection ended: reset both hands; the next connection gets a new epoch."""
        if self.epoch is None:
            return
        for hand in HANDS:
            self._reset_hand(hand, now, "worker_disconnect")
        self.log(dict(type="connection_close", worker_epoch=self.epoch, at=now))
        self.epoch = None
        self.engines = {}
        self.encoders = {}
        self._outbox = []  # nowhere to send them now

    def on_sample(self, message, received):
        """One bridge sample line, stamped with its arrival. True when it entered its hand's window."""
        if self.epoch is None:
            raise RuntimeError("sample before the bridge hello")
        hand = message.get("device_id") if isinstance(message, dict) else None
        if type(hand) is not int or hand not in HANDS:
            self.totals["samples_without_hand"] += 1
            self.log(dict(type="invalid_sample", device_id=None, error="device_id must be 1 or 2"))
            return False
        counts = self.counts[hand]
        counts["samples"] += 1
        error = sample_error(message)
        if error is not None:
            counts["invalid"] += 1
            self.log(dict(type="invalid_sample", device_id=hand, error=error))
            return False
        boot = message.get("boot_id")
        previous = self._arrival.get(hand)
        if previous is not None and _uint32(boot) and _number(received):
            if boot != self._boot[hand]:
                self._reset_hand(hand, received, "source_reset", previous_boot_id=self._boot[hand],
                                 boot_id=boot)
            elif received - previous >= self.reconnect_gap:
                self._reset_hand(hand, received, "connection_reset",
                                 silence_s=round(received - previous, 6))
        try:
            added = self.engines[hand].add(message, received)
        except (TypeError, ValueError) as error:  # the engine's own checks, e.g. time moving back
            counts["invalid"] += 1
            self.log(dict(type="invalid_sample", device_id=hand, error=str(error)))
            return False
        if not added:
            counts["duplicates_ignored"] += 1  # a repeated or older seq of the same boot
            return False
        self._arrival[hand] = received
        self._boot[hand] = boot
        return True

    def poll(self, now, clock=None):
        """Run the inferences that are due; returns the result lines to send, oldest first."""
        if self.epoch is None:
            return []
        for hand in HANDS:
            records = self.engines[hand].process_due(now, clock)
            for record in records:
                self._record(hand, record)
            for index, record in enumerate(records):
                if not self._consume(hand, record):
                    self._reset_hand(hand, clock() if clock else now, "manual_reset",
                                     cause="encoder_error", records_skipped=len(records) - index - 1)
                    break
        results, self._outbox = self._outbox, []
        return results

    def bad_line(self, reason):
        self.totals["bad_lines"] += 1
        self.log(dict(type="bad_line", reason=reason, count=self.totals["bad_lines"]))

    def unexpected_line(self, message):
        self.totals["unexpected_lines"] += 1
        kind = message.get("type") if isinstance(message, dict) else type(message).__name__
        self.log(dict(type="unexpected_line", line_type=str(kind)[:64]))

    def summary(self, now, final=False):
        hands = {}
        for hand in HANDS:
            hands[str(hand)] = {key: dict(value) if isinstance(value, Counter) else value
                                for key, value in self.counts[hand].items()}
        return dict(type="summary", final=final, at=now, worker_epoch=self.epoch,
                    totals=dict(self.totals), hands=hands)

    def _reset_hand(self, hand, now, reason, **detail):
        """Reset one hand's engine and encoder. Neither the state_end nor the reset is forwarded."""
        self.counts[hand]["resets"][reason] += 1
        self.log(dict(type="hand_reset", device_id=hand, reason=reason, at=now, **detail))
        engine = self.engines[hand]
        engine.reset(now)
        # The windows are empty now, so this runs no inference: it returns the state_end
        # of an active state, and any state_end an earlier add() left pending.
        records = engine.process_due(now)
        for record in records:
            self._record(hand, record)
        for record in records:
            self._consume(hand, record)
        for event in self.encoders[hand].reset(reason, device=hand):
            self._event(hand, event)
        self._arrival.pop(hand, None)
        self._boot.pop(hand, None)
        self._prediction.pop(hand, None)

    def _record(self, hand, record):
        kind = record.get("type")
        if kind == "prediction":
            self.counts[hand]["predictions"] += 1
            self._prediction[hand] = record
        elif kind == "stale_suppressed":
            self.counts[hand]["stale_suppressed"] += 1
        self.log(dict(record, origin="engine"))

    def _consume(self, hand, record):
        """Hand one engine record to the hand's encoder; False after an encoder error."""
        floor = self._event_time.get(hand)
        elapsed = record.get("elapsed_s")
        if floor is not None and _number(elapsed) and elapsed < floor:
            # The engine stamps a reset found in add() (and the reset above) with a sample's
            # arrival time, which can precede an inference that finished in an earlier poll.
            # The encoder needs non-decreasing local time, so the record goes over at the
            # later time; a state_end is never forwarded, so no result changes.
            record = dict(record, elapsed_s=floor)
            self.counts[hand]["event_time_raised"] += 1
        try:
            events = self.encoders[hand].consume(record)
        except ProtocolError as error:
            self.counts[hand]["encoder_errors"] += 1
            self.log(dict(type="encoder_error", device_id=hand, record_type=record.get("type"),
                          error=str(error)))
            return False
        if _number(record.get("elapsed_s")):
            self._event_time[hand] = max(record["elapsed_s"], floor if floor is not None else -math.inf)
        for event in events:
            self._event(hand, event)
        return True

    def _event(self, hand, event):
        kind = event["kind"]
        counts = self.counts[hand]
        counts["events"][kind] += 1
        source = event["source"]
        record = dict(type="hand_event", device_id=hand, kind=kind, gesture=event["gesture"],
                      confidence=event["confidence"], event_id=event["event_id"],
                      state_id=event["state_id"], reason=event["reason"], source=source)
        if kind not in FORWARDED_KINDS:
            record["delivery"] = "not_forwarded"  # compat v3 results carry no state end or reset
            self.log(record)
            return
        identity = (hand, source["boot_id"], source["seq"])
        if identity in self._forwarded:
            counts["collisions"] += 1
            record["delivery"] = "collision"  # the service refuses a second result for a sample
            self.log(record)
            return
        self._forwarded[identity] = None
        if len(self._forwarded) > FORWARDED_MEMORY:
            self._forwarded.popitem(last=False)
        prediction = self._prediction.get(hand)
        if prediction is not None and (prediction["boot_id"], prediction["seq"]) == identity[1:]:
            record.update(inference_ms=prediction["inference_ms"],
                          worker_sample_age_ms=prediction["worker_sample_age_ms"])
        else:
            record.update(inference_ms=None, worker_sample_age_ms=None)
        counts["forwarded"] += 1
        record["delivery"] = "forwarded"
        self._outbox.append(dict(type="result", gesture=event["gesture"], confidence=event["confidence"],
                                 device_id=hand, boot_id=source["boot_id"], seq=source["seq"]))
        self.log(record)


class Log:
    """JSON lines: the operator's records on stdout (flushed), every record in out."""

    CONSOLE = frozenset(("scope", "hardware_artifacts", "waiting_for_service", "connection_open",
                         "connection_close", "connection_lost", "hand_event", "hand_reset",
                         "invalid_sample", "bad_line", "unexpected_line", "encoder_error",
                         "summary", "error"))

    def __init__(self, out=None, stream=None):
        self.out = out
        self.stream = stream if stream is not None else sys.stdout
        self._lock = threading.Lock()

    def __call__(self, record):
        line = json.dumps(record, separators=(",", ":"), default=str) + "\n"
        with self._lock:
            if self.out is not None:
                self.out.write(line)
                self.out.flush()
            if record.get("type") in self.CONSOLE:
                self.stream.write(line)
                self.stream.flush()


class _BadLine:
    def __init__(self, reason):
        self.reason = reason


_CLOSED = object()


def _receive(sock, lines, clock):
    """Receiver thread: put (arrival time, message) for each line; (time, _CLOSED) at the end."""
    pending = b""
    skipping = False  # inside a line already refused as too long
    try:
        while True:
            try:
                data = sock.recv(65536)
            except OSError:
                break
            if not data:
                break
            arrived = clock()
            pending += data
            while True:
                end = pending.find(b"\n")
                if end < 0:
                    break
                line, pending = pending[:end], pending[end + 1:]
                if skipping:
                    skipping = False
                    continue
                if len(line) > MAX_LINE_BYTES:
                    lines.put((arrived, _BadLine("line longer than {} bytes".format(MAX_LINE_BYTES))))
                    continue
                if not line.strip():
                    continue
                try:
                    message = json.loads(line.decode("utf-8"))
                except (ValueError, RecursionError):  # UnicodeDecodeError is a ValueError
                    lines.put((arrived, _BadLine("not a JSON line")))
                    continue
                lines.put((arrived, message))
            if len(pending) > MAX_LINE_BYTES:
                if not skipping:
                    lines.put((arrived, _BadLine("line longer than {} bytes".format(MAX_LINE_BYTES))))
                pending = b""
                skipping = True
    finally:
        lines.put((clock(), _CLOSED))


def serve(sock, adapter, stop_event, log, *, clock=time.monotonic, summary_interval=None):
    """Serve one connected bridge stream until it closes or stop_event is set.

    A receiver thread reads the lines and stamps their arrival; this thread feeds the
    adapter, polls it about every 5 ms and writes each result as one compact JSON line.
    When the stream ends the hands are reset. IncompatibleService and backend errors
    propagate (after that reset).
    """
    sock.settimeout(None)
    lines = queue.Queue()
    receiver = threading.Thread(target=_receive, args=(sock, lines, clock),
                                name="hand-runner-receive", daemon=True)
    receiver.start()
    opened = False
    next_summary = clock() + summary_interval if summary_interval else None
    try:
        while not stop_event.is_set():
            try:
                item = lines.get(timeout=POLL_SECONDS)
            except queue.Empty:
                item = None
            ended = False
            while item is not None:
                received, message = item
                if message is _CLOSED:
                    ended = True
                    break
                if isinstance(message, _BadLine):
                    adapter.bad_line(message.reason)
                elif not opened:
                    adapter.connected(message, received)
                    opened = True
                elif isinstance(message, dict) and message.get("type") == "sample":
                    adapter.on_sample(message, received)
                else:
                    adapter.unexpected_line(message)
                try:
                    item = lines.get_nowait()
                except queue.Empty:
                    item = None
            if opened:
                results = adapter.poll(clock(), clock=clock)
                try:
                    for result in results:
                        sock.sendall((json.dumps(result, separators=(",", ":")) + "\n").encode("utf-8"))
                except OSError as error:
                    log(dict(type="connection_lost", error_type=type(error).__name__,
                             results_unsent=len(results)))
                    break
            if ended:
                break
            if next_summary is not None and clock() >= next_summary:
                log(adapter.summary(clock()))
                next_summary = clock() + summary_interval
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)  # wakes the receiver
        except OSError:
            pass
        receiver.join(2)
        if opened:
            adapter.disconnected(clock())


def connect(path, stop_event, log, retry=RETRY_SECONDS):
    """Connect to the service's model socket, waiting while it is absent; None once stopped."""
    waiting = False
    while not stop_event.is_set():
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(path)
        except (FileNotFoundError, ConnectionRefusedError) as error:
            sock.close()
            if not waiting:
                log(dict(type="waiting_for_service", socket=path, error_type=type(error).__name__))
                waiting = True
            stop_event.wait(retry)
            continue
        except BaseException:
            sock.close()
            raise
        return sock
    return None


def scope_record(args, bundle, path):
    return dict(type="scope", delivery=DELIVERY, forwarded_kinds=list(FORWARDED_KINDS),
                logged_only_kinds=["state_end", "reset"], backend=args.backend,
                synthetic=bundle.synthetic, bundle=str(bundle.folder),
                manifest_sha256=digest(bundle.folder / "manifest.json"),
                model_parameter_sha256={str(hand): bundle.models[hand]["hash"] for hand in HANDS},
                settings=dict(threshold=args.threshold, confirmations=args.confirmations,
                              interval_s=args.interval, reconnect_gap_s=args.reconnect_gap,
                              lease_ms=LEASE_MS, session_id=args.session_id, socket=path,
                              ip_name=args.ip_name if args.backend == "fpga" else None,
                              summary_interval_s=args.summary_interval, out=args.out),
                timing_scope=TIMING_SCOPE, final_gesture_accuracy_validated=False,
                pid=os.getpid(), python=sys.version.split()[0])


def _stop_on_signals(stop_event):
    def handler(signum, frame):
        stop_event.set()
    for name in ("SIGTERM", "SIGINT"):
        number = getattr(signal, name, None)
        if number is not None:
            try:
                signal.signal(number, handler)
            except ValueError:  # not the main thread
                pass


def _parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", required=True, help="the hand12 export folder (verified on start)")
    parser.add_argument("--allow-synthetic", action="store_true",
                        help="accept a synthetic contract-test bundle; it is not a trained model")
    parser.add_argument("--backend", choices=("numpy", "fpga"), default="numpy")
    parser.add_argument("--bit", help="the hand12 overlay .bit, its .hwh beside it (fpga only)")
    parser.add_argument("--ip-name", default=DEFAULT_IP_NAME)
    parser.add_argument("--socket", help="the service's model socket (default: COMMS_MODEL_SOCKET, "
                                         "else " + DEFAULT_SOCKET + ")")
    parser.add_argument("--threshold", type=float, default=0.70)
    parser.add_argument("--confirmations", type=int, default=3)
    parser.add_argument("--interval", type=float, default=0.2, help="seconds between a hand's inferences")
    parser.add_argument("--reconnect-gap", type=float, default=1.0,
                        help="seconds of silence after which a hand is reset before its next sample")
    parser.add_argument("--session-id", default="ltc-comms")
    parser.add_argument("--out", help="also record every record, predictions included, in this new file")
    parser.add_argument("--summary-interval", type=float, default=10.0)
    return parser


def main(argv=None, *, stream=None):
    parser = _parser()
    args = parser.parse_args(argv)
    if args.backend == "fpga" and not args.bit:
        parser.error("--backend fpga needs --bit (the hand12 overlay .bit with its .hwh beside it)")
    if args.backend == "numpy" and args.bit:
        parser.error("--bit is only meaningful with --backend fpga")
    if args.bit and not (Path(args.bit).is_file() and Path(args.bit).with_suffix(".hwh").is_file()):
        parser.error("--bit must name an existing .bit with the same-name .hwh beside it")
    if not _number(args.summary_interval) or args.summary_interval <= 0:
        parser.error("--summary-interval must be positive seconds")
    try:
        check_settings(args.threshold, args.confirmations, args.interval, args.reconnect_gap,
                       args.session_id)
    except ValueError as error:
        parser.error("invalid setting: " + str(error))
    try:
        bundle = ModelBundle(args.bundle, args.allow_synthetic)
    except Exception as error:
        parser.error("bundle refused ({}): {}".format(type(error).__name__, error))
    if not hasattr(socket, "AF_UNIX"):
        parser.error("this Python has no Unix sockets; run the runner on the Ultra96")
    path = args.socket or os.environ.get("COMMS_MODEL_SOCKET") or DEFAULT_SOCKET
    out = None
    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            out = Path(args.out).open("x", encoding="utf-8", newline="\n")
        except OSError as error:
            parser.error("cannot create --out: " + str(error))
    log = Log(out, stream)
    log(scope_record(args, bundle, path))

    def make_backend():
        # Created only once the service is connected: the FPGA backend downloads the overlay.
        if args.backend == "numpy":
            return NumpyHandBackend(bundle)
        backend = PynqHandBackend(bundle, args.bit, args.ip_name)
        log(dict(type="hardware_artifacts", ip_name=args.ip_name, **backend.artifacts))
        return backend

    adapter = HandAdapter(threshold=args.threshold, confirmations=args.confirmations,
                          interval=args.interval, reconnect_gap=args.reconnect_gap,
                          session_id=args.session_id, log=log, backend_factory=make_backend)
    stop = threading.Event()
    _stop_on_signals(stop)
    status = 0
    try:
        while not stop.is_set():
            sock = connect(path, stop, log)
            if sock is None:
                break
            try:
                serve(sock, adapter, stop, log, summary_interval=args.summary_interval)
            finally:
                sock.close()
            if not stop.is_set():
                # A second runner on the socket replaces this one; waiting keeps the two from
                # taking the connection from each other many times a second.
                log(dict(type="connection_lost", reconnect_in_s=RETRY_SECONDS))
                stop.wait(RETRY_SECONDS)
    except KeyboardInterrupt:
        pass
    except IncompatibleService as error:
        log(dict(type="error", error_type=type(error).__name__, message=str(error)))
        status = EXIT_INCOMPATIBLE
    except Exception as error:
        log(dict(type="error", error_type=type(error).__name__, message=str(error)))
        status = EXIT_BACKEND
    finally:
        try:
            if adapter.backend is not None:
                adapter.backend.close()
        except Exception as error:
            log(dict(type="error", error_type=type(error).__name__, message="backend close: " + str(error)))
            status = status or EXIT_BACKEND
        log(adapter.summary(time.monotonic(), final=True))
        if out is not None:
            out.close()
    return status


if __name__ == "__main__":
    sys.exit(main())
