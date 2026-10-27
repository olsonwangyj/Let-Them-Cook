"""The hand12 runner's adapter: scripted backend, fake clock, both hands (no socket service, no FPGA)."""
import contextlib
import io
import json
from pathlib import Path
import socket
import tempfile
import threading
import time

import numpy as np
import pytest

from common.sensor import CHANNELS as V3_CHANNELS
from src.hand_runtime import CHANNELS, LABELS
from ultra96 import hand_runner
from ultra96.hand_runner import (HandAdapter, IncompatibleService, check_bridge_hello, main,
                                 serve)

HELLO = dict(type="hello", format=1, channels=list(CHANNELS))
LEFT, RIGHT = 1, 2


class ScriptedBackend:
    """Scripts the gesture through the sensor input: the window's newest row picks it.

    The label is LABELS[round(flex3 * 10)] (flex3 is index 11) with confidence 0.94, or
    with flex2 (index 10) as the confidence when flex2 is not zero. delay advances the
    given clock during each inference, as a slow backend would.
    """

    def __init__(self, clock=None, delay=0.0):
        self.clock = clock
        self.delay = delay
        self.calls = []
        self.closed = False

    def probabilities(self, device, window):
        row = np.asarray(window)[-1]
        index = int(round(row[11] * 10))
        confidence = float(row[10]) or 0.94
        self.calls.append((device, LABELS[index]))
        if self.delay:
            self.clock.now += self.delay
        result = np.full(7, (1.0 - confidence) / 6)
        result[index] = confidence
        return result

    def close(self):
        self.closed = True


def values(label, confidence=None):
    row = [0.0] * 12
    row[11] = LABELS.index(label) / 10
    row[10] = confidence or 0.0
    return row


class Glove:
    """One hand's bridge samples at 50 Hz: seq and uptime advance 20 ms per sample."""

    def __init__(self, device, boot):
        self.device = device
        self.boot = boot
        self.seq = 0
        self.sent = []

    def sample(self, label, confidence=None, seq=None):
        if seq is None:
            seq = self.seq
            self.seq += 1
        message = dict(type="sample", device_id=self.device, boot_id=self.boot, seq=seq,
                       uptime_ms=(1000 + seq * 20) % 2 ** 32, values=values(label, confidence))
        self.sent.append(message)
        return message


class Clock:
    def __init__(self, now=100.0):
        self.now = now

    def __call__(self):
        return self.now


class Run:
    """An adapter driven like serve(): every 20 ms the new samples arrive, then one poll."""

    def __init__(self, delay=0.0, connect=True, **settings):
        self.clock = Clock()
        self.backend = ScriptedBackend(self.clock, delay)
        self.records = []
        epochs = ("{:032x}".format(n) for n in range(1, 1000))
        self.adapter = HandAdapter(self.backend, log=self.records.append,
                                   epoch_factory=lambda: next(epochs), **settings)
        self.results = []
        self.left = Glove(LEFT, 11)
        self.right = Glove(RIGHT, 22)
        if connect:
            self.adapter.connected(HELLO, self.clock())

    def step(self, *samples, clock=False):
        self.clock.now += 0.02
        for message in samples:
            self.adapter.on_sample(message, self.clock())
        results = self.adapter.poll(self.clock(), clock=self.clock if clock else None)
        self.results += results
        return results

    def play(self, seconds, left=None, right=None, left_confidence=None, right_confidence=None,
             clock=False):
        """Both hands for seconds; a hand given no label sends nothing (it is silent)."""
        produced = []
        for _ in range(int(round(seconds / 0.02))):
            samples = []
            if left:
                samples.append(self.left.sample(left, left_confidence))
            if right:
                samples.append(self.right.sample(right, right_confidence))
            produced += self.step(*samples, clock=clock)
        return produced

    def events(self, device=None, kind=None, delivery=None):
        return [r for r in self.records if r["type"] == "hand_event"
                and (device is None or r["device_id"] == device)
                and (kind is None or r["kind"] == kind)
                and (delivery is None or r["delivery"] == delivery)]

    def resets(self, device=None):
        return [r for r in self.records if r["type"] == "hand_reset"
                and (device is None or r["device_id"] == device)]

    def hand(self, device):
        return [r for r in self.results if r["device_id"] == device]


def identities(results):
    return [(r["device_id"], r["boot_id"], r["seq"]) for r in results]


def test_result_lines_have_exactly_the_bridge_result_fields():
    run = Run()
    run.play(3.0, left="PICKUP")
    assert run.results == [dict(type="result", gesture="PICKUP", confidence=0.94, device_id=LEFT,
                                boot_id=11, seq=120)]
    assert json.loads(json.dumps(run.results[0])) == run.results[0]


def test_both_hands_are_independent_and_each_result_names_its_own_hand():
    run = Run()
    run.play(3.0, left="CHOP", right="PICKUP")
    left, right = run.hand(LEFT), run.hand(RIGHT)
    # A full two-second window first exists at seq 100; three confirmations land at seq 120.
    assert [(r["gesture"], r["seq"]) for r in right] == [("PICKUP", 120)]
    assert [r["gesture"] for r in left] == ["CHOP"] * len(left) and len(left) >= 3
    assert left[0]["seq"] == 120
    assert [r["seq"] for r in left] == list(range(120, 120 + 10 * len(left), 10))
    assert {r["boot_id"] for r in left} == {11} and {r["boot_id"] for r in right} == {22}
    kinds = [r["kind"] for r in run.events(LEFT, delivery="forwarded")]
    assert kinds == ["state_start"] + ["state_refresh"] * (len(left) - 1)
    starts = run.events(LEFT, "state_start")
    assert {r["state_id"] for r in run.events(LEFT, "state_refresh")} == {starts[0]["state_id"]}
    assert [r["kind"] for r in run.events(RIGHT)] == ["pulse"]
    # Every forwarded result names a sample this hand really sent.
    for device, glove in ((LEFT, run.left), (RIGHT, run.right)):
        sent = {(m["boot_id"], m["seq"]) for m in glove.sent}
        assert all((r["boot_id"], r["seq"]) in sent for r in run.hand(device))
    forwarded = run.events(delivery="forwarded")
    assert all(r["inference_ms"] is not None and r["worker_sample_age_ms"] == 0 for r in forwarded)
    summary = run.adapter.summary(run.clock())
    assert summary["hands"]["1"]["forwarded"] == len(left)
    assert summary["hands"]["2"]["events"] == {"pulse": 1}
    assert not run.resets()


def test_repeated_and_out_of_order_samples_are_ignored_and_counted():
    run = Run()
    repeats = 0
    for tick in range(250):
        samples = [run.left.sample("PICKUP")]
        if tick % 10 == 9:
            samples.append(dict(samples[0]))  # the same sample again
            samples.append(run.left.sample("PICKUP", seq=run.left.seq - 6))  # an older seq
            repeats += 2
        run.step(*samples)
    counts = run.adapter.counts[LEFT]
    assert counts["duplicates_ignored"] == repeats and counts["invalid"] == 0
    assert counts["samples"] == 250 + repeats
    assert not run.resets()
    # A held PICKUP is one pulse, not a pulse per confirmation.
    assert [r["gesture"] for r in run.results] == ["PICKUP"]
    assert counts["predictions"] >= 10


def test_a_transition_gives_one_result_at_its_sample_and_the_state_end_is_not_sent():
    run = Run()
    run.play(3.0, left="CHOP")
    chop = len(run.results)
    run.play(2.0, left="POURING")
    after = run.results[chop:]
    assert all(r["gesture"] == "CHOP" for r in run.results[:chop])
    assert after and all(r["gesture"] == "POURING" for r in after)
    start = run.events(LEFT, "state_start", "forwarded")[-1]
    assert start["gesture"] == "POURING"
    # Exactly one result at the transition sample: the POURING state_start.
    transition = start["source"]["seq"]
    assert [r for r in run.results if r["seq"] == transition] == [after[0]]
    ends = run.events(LEFT, "state_end")
    assert [(e["gesture"], e["delivery"]) for e in ends] == [("CHOP", "not_forwarded")]
    assert ends[0]["source"]["seq"] <= transition
    assert len(set(identities(run.results))) == len(run.results)
    assert run.adapter.counts[LEFT]["collisions"] == 0


def test_a_silence_of_the_reconnect_gap_resets_only_that_hand():
    run = Run()
    run.play(3.0, left="PICKUP", right="CHOP")
    assert [r["gesture"] for r in run.hand(LEFT)] == ["PICKUP"]
    right_start = run.events(RIGHT, "state_start")
    run.play(1.2, right="CHOP")  # the left glove reconnects meanwhile
    during = len(run.hand(RIGHT))
    run.play(3.0, left="PICKUP", right="CHOP")
    resets = run.resets()
    assert [(r["device_id"], r["reason"]) for r in resets] == [(LEFT, "connection_reset")]
    assert resets[0]["silence_s"] >= 1.2
    assert [e["reason"] for e in run.events(LEFT, "reset", "not_forwarded")] == ["connection_reset"]
    # After the reset a held PICKUP is a new pulse, from a sample after the silence.
    left = run.hand(LEFT)
    assert [r["gesture"] for r in left] == ["PICKUP", "PICKUP"]
    assert left[1]["seq"] >= 150 + 100
    # The right hand's state carried on through the left's reconnect: one state, refreshed.
    assert run.events(RIGHT, "state_start") == right_start
    assert len(run.hand(RIGHT)) > during > 1
    assert not run.events(RIGHT, "reset") and not run.events(RIGHT, "state_end")


def test_a_reconnect_ends_an_active_state_and_the_next_state_is_new():
    run = Run(reconnect_gap=0.3)
    run.play(3.0, left="CHOP")
    first = run.events(LEFT, "state_start")[0]["state_id"]
    run.play(0.36)  # silent, shorter than the 0.6 s prediction timeout
    assert run.adapter.encoders[LEFT].active[LEFT] is not None
    run.play(0.02, left="CHOP")
    assert run.adapter.encoders[LEFT].active[LEFT] is None
    ends = run.events(LEFT, "state_end")
    assert [(e["reason"], e["delivery"]) for e in ends] == [("connection_reset", "not_forwarded")]
    assert [r["reason"] for r in run.resets(LEFT)] == ["connection_reset"]
    before = len(run.results)
    run.play(3.0, left="CHOP")
    second = run.events(LEFT, "state_start")[-1]["state_id"]
    assert second != first and run.results[before]["gesture"] == "CHOP"
    assert run.events(LEFT, "state_start", "forwarded")[-1]["source"]["seq"] == run.results[before]["seq"]


def test_a_new_boot_id_is_a_source_reset():
    run = Run()
    run.play(3.0, left="CHOP", right="PICKUP")
    run.left = Glove(LEFT, 12)  # the left glove rebooted: new boot_id, seq from 0
    run.play(3.0, left="CHOP", right="PICKUP")
    assert [(r["device_id"], r["reason"]) for r in run.resets()] == [(LEFT, "source_reset")]
    assert run.resets()[0]["previous_boot_id"] == 11 and run.resets()[0]["boot_id"] == 12
    assert {r["boot_id"] for r in run.hand(LEFT)} == {11, 12}
    assert [r["gesture"] for r in run.hand(RIGHT)] == ["PICKUP"]
    assert len(run.events(LEFT, "state_start")) == 2


def test_a_bridge_reconnect_starts_a_new_epoch_and_resets_both_hands():
    run = Run()
    run.play(3.0, left="CHOP", right="PICKUP")
    first_epoch = run.adapter.epoch
    run.adapter.disconnected(run.clock())
    assert run.adapter.epoch is None and run.adapter.poll(run.clock()) == []
    assert sorted((r["device_id"], r["reason"]) for r in run.resets()) == [
        (LEFT, "worker_disconnect"), (RIGHT, "worker_disconnect")]
    assert [r["type"] for r in run.records if r["type"].startswith("connection_")] == [
        "connection_open", "connection_close"]
    before = len(run.results)
    run.adapter.connected(HELLO, run.clock())
    assert run.adapter.epoch != first_epoch
    run.play(3.0, left="CHOP", right="PICKUP")
    again = run.results[before:]
    assert [r["gesture"] for r in again if r["device_id"] == RIGHT] == ["PICKUP"]
    starts = run.events(LEFT, "state_start")
    assert len(starts) == 2 and starts[1]["event_id"].startswith(run.adapter.epoch + ":1:")
    assert len(set(identities(run.results))) == len(run.results)


def test_the_adapter_connected_twice_closes_the_previous_epoch():
    # Adapter level only: serve() calls connected() once per stream (see the serve test below).
    run = Run()
    run.play(3.0, left="CHOP")
    run.adapter.connected(HELLO, run.clock())
    assert run.adapter.totals["connections"] == 2
    assert [r["type"] for r in run.records if r["type"].startswith("connection_")] == [
        "connection_open", "connection_close", "connection_open"]


def test_when_samples_stop_no_result_and_no_idle_is_invented():
    run = Run()
    run.play(3.0, left="CHOP")
    last = run.left.seq - 1
    run.play(0.2)  # the newest window still gets its inference when it falls due
    assert run.results[-1]["seq"] == last
    before = len(run.results)
    run.play(3.0)  # both hands silent; the runner keeps polling
    assert len(run.results) == before
    ends = run.events(LEFT, "state_end")
    assert [(e["reason"], e["delivery"]) for e in ends] == [("prediction_timeout", "not_forwarded")]
    assert not run.events(kind="idle")


def test_a_backend_slower_than_half_a_second_is_suppressed_as_stale():
    run = Run(delay=0.6)
    run.play(4.0, left="CHOP", clock=True)
    assert run.results == []
    counts = run.adapter.counts[LEFT]
    assert counts["stale_suppressed"] >= 1 and counts["predictions"] == 0


def test_an_old_seq_after_a_pause_is_ignored():
    run = Run()
    run.play(3.0, left="CHOP")
    run.play(0.2)  # the newest window's own inference
    before = len(run.results)
    run.play(0.6)  # with the 0.2 s above, shorter than the reconnect gap
    run.step(run.left.sample("CHOP", seq=run.left.seq - 10))
    run.play(0.2)
    assert len(run.results) == before
    assert run.adapter.counts[LEFT]["duplicates_ignored"] == 1
    assert not run.resets()


def test_confident_idle_is_one_result_and_low_confidence_never_becomes_idle():
    run = Run()
    run.play(3.0, left="IDLE", right="CHOP", right_confidence=0.5)
    assert run.hand(LEFT) == [dict(type="result", gesture="IDLE", confidence=0.94, device_id=LEFT,
                                   boot_id=11, seq=120)]
    assert run.hand(RIGHT) == []
    right = [r for r in run.records if r["type"] == "prediction" and r["device_id"] == RIGHT]
    assert right and not any(r["above_threshold"] for r in right)
    # A confident state followed by uncertainty ends locally; it never turns into IDLE.
    run.play(1.0, right="CHOP")
    run.play(2.0, right="CHOP", right_confidence=0.5)
    assert [r["gesture"] for r in run.hand(RIGHT)] and all(
        r["gesture"] == "CHOP" for r in run.hand(RIGHT))
    assert [e["reason"] for e in run.events(RIGHT, "state_end")] == ["prediction_timeout"]


def test_a_reset_stamped_before_the_last_inference_still_reaches_the_encoder():
    run = Run(delay=0.01)  # each inference takes 10 ms of the clock
    run.play(2.82, left="CHOP", clock=True)  # seq 0..140: the last poll inferred seq 140
    last = [r for r in run.records if r["type"] == "prediction"][-1]
    assert last["seq"] == 140 and last["elapsed_s"] == run.clock()
    assert run.adapter.encoders[LEFT].active[LEFT] is not None
    # A sample that arrived while that inference ran, but is handed to the adapter after
    # it, with a seq gap: the engine resets the hand at the sample's arrival time.
    late = run.clock() - 0.005
    gap = run.left.sample("CHOP", seq=run.left.seq + 1)
    run.adapter.on_sample(gap, late)
    run.step()
    counts = run.adapter.counts[LEFT]
    assert counts["encoder_errors"] == 0 and counts["event_time_raised"] == 1
    assert [e["reason"] for e in run.events(LEFT, "state_end")] == ["source_reset"]
    assert run.adapter.encoders[LEFT].active[LEFT] is None


def test_an_encoder_error_is_counted_and_resets_only_that_hand(monkeypatch):
    run = Run()
    run.play(2.5, left="CHOP", right="CHOP")
    encoder = run.adapter.encoders[LEFT]
    original = encoder.consume
    failures = []

    def consume(record):
        if not failures and record["type"] == "prediction":
            failures.append(record)
            raise hand_runner.ProtocolError("scripted encoder failure")
        return original(record)

    monkeypatch.setattr(encoder, "consume", consume)
    run.play(1.0, left="CHOP", right="CHOP")
    assert run.adapter.counts[LEFT]["encoder_errors"] == 1
    assert [(r["device_id"], r["reason"], r["cause"]) for r in run.resets()] == [
        (LEFT, "manual_reset", "encoder_error")]
    assert any(r["type"] == "encoder_error" for r in run.records)
    assert not run.events(RIGHT, "reset")


def test_a_second_result_for_one_sample_is_never_forwarded():
    run = Run()
    run.play(3.0, left="PICKUP")
    adapter = run.adapter
    event = dict(kind="idle", gesture="IDLE", confidence=0.94, event_id="x", state_id=None,
                 reason="confirmed", source=dict(boot_id=11, seq=120, uptime_ms=3400))
    adapter._event(LEFT, event)
    assert adapter.poll(run.clock()) == []
    assert adapter.counts[LEFT]["collisions"] == 1
    assert run.events(LEFT, "idle")[-1]["delivery"] == "collision"


def test_invalid_samples_are_counted_not_fatal():
    run = Run()
    bad = run.left.sample("CHOP")
    bad["values"] = bad["values"][:11]
    run.adapter.on_sample(bad, run.clock())
    run.adapter.on_sample(dict(type="sample", device_id=3), run.clock())
    run.adapter.on_sample(dict(bad, values=values("CHOP"), boot_id=-1), run.clock())
    # numpy raises TypeError or OverflowError, not ValueError, for some of these.
    malformed = ({}, {"ax": 1}, [{}] * 12, "abc", None, [None] * 12, [True] * 12, [10 ** 400] * 12,
                 [[1.0]] * 12, values("CHOP")[:-1] + [float("nan")])
    for item in malformed:
        assert run.adapter.on_sample(dict(bad, values=item), run.clock()) is False
    assert run.adapter.counts[LEFT]["invalid"] == 2 + len(malformed)
    assert run.adapter.totals["samples_without_hand"] == 1
    run.play(3.0, left="CHOP")
    assert run.results and run.results[0]["gesture"] == "CHOP"
    # A malformed sample naming a new boot_id is refused before it can reset the hand.
    run.adapter.on_sample(dict(run.left.sample("CHOP"), boot_id=99, values={}), run.clock())
    assert not run.resets() and run.adapter.encoders[LEFT].active[LEFT] is not None
    assert run.adapter.counts[LEFT]["invalid"] == 3 + len(malformed)


def test_only_the_twelve_channel_hello_is_accepted():
    made = []
    adapter = HandAdapter(backend_factory=lambda: made.append(1) or ScriptedBackend())
    with pytest.raises(IncompatibleService, match="--sensor-version 4"):
        adapter.connected(dict(type="hello", format=1, channels=list(V3_CHANNELS)), 0.0)
    for hello in (dict(HELLO, format=2), dict(HELLO, format=True), dict(HELLO, channels=list(CHANNELS)[::-1]),
                  dict(type="sample"), [HELLO]):
        with pytest.raises(IncompatibleService):
            adapter.connected(hello, 0.0)
    assert adapter.epoch is None and made == []  # no backend (no overlay) for a refused service
    adapter.connected(HELLO, 0.0)
    assert made == [1] and len(adapter.epoch) == 32
    assert check_bridge_hello(HELLO) is HELLO


def test_each_connection_negotiates_a_fresh_format_2_hello_with_the_engine_threshold():
    adapter = HandAdapter(ScriptedBackend(), threshold=0.8, confirmations=2)
    adapter.connected(HELLO, 0.0)
    hello = adapter.encoders[LEFT].hello
    assert hello["format"] == 2 and hello["confidence_threshold"] == 0.8 == adapter.engines[LEFT].filters[LEFT].threshold
    assert hello["confirmations"] == 2 and hello["lease_ms"] == 1000 and hello["session_id"] == "ltc-comms"
    epoch = adapter.epoch
    assert adapter.encoders[RIGHT].hello["worker_epoch"] == epoch
    assert adapter.engines[LEFT] is not adapter.engines[RIGHT]
    assert adapter.encoders[LEFT] is not adapter.encoders[RIGHT]
    adapter.disconnected(1.0)
    adapter.connected(HELLO, 2.0)
    assert adapter.epoch != epoch


@pytest.mark.parametrize("settings", [dict(threshold=1.5), dict(threshold=float("nan")),
                                      dict(confirmations=0), dict(confirmations=11),
                                      dict(interval=0), dict(interval=float("nan")),
                                      dict(reconnect_gap=0), dict(session_id="")])
def test_invalid_settings_are_refused(settings):
    with pytest.raises(ValueError):
        HandAdapter(ScriptedBackend(), **settings)


@pytest.fixture(scope="module")
def synthetic_bundle():
    from tools.hand_hls_prepare import prepare
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / "bundle"
        with contextlib.redirect_stdout(io.StringIO()):
            prepare(folder, synthetic=True)
        yield folder


def cli_error(capsys, *argv):
    with pytest.raises(SystemExit) as stopped:
        main(list(argv))
    assert stopped.value.code == 2
    return capsys.readouterr().err


def test_cli_refuses_inconsistent_options_before_reading_the_bundle(capsys, tmp_path):
    missing = str(tmp_path / "no-bundle")
    assert "needs --bit" in cli_error(capsys, "--bundle", missing, "--backend", "fpga")
    assert "only meaningful with --backend fpga" in cli_error(capsys, "--bundle", missing, "--bit", "x.bit")
    bit = tmp_path / "overlay.bit"
    bit.write_bytes(b"")
    assert ".hwh" in cli_error(capsys, "--bundle", missing, "--backend", "fpga", "--bit", str(bit))
    assert "invalid setting" in cli_error(capsys, "--bundle", missing, "--threshold", "1.5")
    assert "invalid setting" in cli_error(capsys, "--bundle", missing, "--reconnect-gap", "0")
    assert "summary-interval" in cli_error(capsys, "--bundle", missing, "--summary-interval", "0")
    assert "bundle refused" in cli_error(capsys, "--bundle", missing)


def test_cli_refuses_a_synthetic_bundle_without_allow_synthetic(capsys, synthetic_bundle):
    assert "allow-synthetic" in cli_error(capsys, "--bundle", str(synthetic_bundle))


@pytest.mark.skipif(hasattr(socket, "AF_UNIX"), reason="this Python has Unix sockets")
def test_cli_explains_a_python_without_unix_sockets(capsys, synthetic_bundle):
    assert "Unix sockets" in cli_error(capsys, "--bundle", str(synthetic_bundle), "--allow-synthetic")


def test_scope_record_names_the_delivery_bundle_and_timing(synthetic_bundle):
    from src.hand_runtime import ModelBundle
    bundle = ModelBundle(synthetic_bundle, allow_synthetic=True)
    args = hand_runner._parser().parse_args(["--bundle", str(synthetic_bundle)])
    scope = hand_runner.scope_record(args, bundle, "/tmp/x.sock")
    assert scope["delivery"] == "compat_v3_gesture_result" and scope["synthetic"] is True
    assert scope["logged_only_kinds"] == ["state_end", "reset"]
    assert len(scope["manifest_sha256"]) == 64 and set(scope["model_parameter_sha256"]) == {"1", "2"}
    assert "runner-local" in scope["timing_scope"]
    assert scope["settings"]["reconnect_gap_s"] == 1.0 and scope["settings"]["threshold"] == 0.7


def test_log_writes_every_record_to_out_and_the_operator_records_to_stdout():
    out, stream = io.StringIO(), io.StringIO()
    log = hand_runner.Log(out, stream)
    log(dict(type="prediction", device_id=1))
    log(dict(type="hand_event", device_id=1, delivery="forwarded"))
    assert [json.loads(line)["type"] for line in out.getvalue().splitlines()] == ["prediction", "hand_event"]
    assert [json.loads(line)["type"] for line in stream.getvalue().splitlines()] == ["hand_event"]


def read_lines(sock, count, timeout=5.0):
    sock.settimeout(timeout)
    data = b""
    while data.count(b"\n") < count:
        chunk = sock.recv(65536)
        if not chunk:
            break
        data += chunk
    return [json.loads(line) for line in data.splitlines()]


def test_serve_reads_lines_writes_results_and_resets_when_the_stream_ends():
    service, runner = socket.socketpair()
    records = []
    adapter = HandAdapter(ScriptedBackend(), confirmations=1, log=records.append)
    stop = threading.Event()
    failures = []

    def run():
        try:
            serve(runner, adapter, stop, records.append)
        except Exception as error:  # reported by the assertion below
            failures.append(error)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    glove = Glove(LEFT, 11)
    lines = [json.dumps(HELLO), "not json", "x" * 5000, "", json.dumps(dict(type="other"))]
    lines += [json.dumps(glove.sample("PICKUP")) for _ in range(101)]
    service.sendall(("\n".join(lines) + "\n").encode("utf-8"))
    results = read_lines(service, 1)
    assert results == [dict(type="result", gesture="PICKUP", confidence=0.94, device_id=LEFT,
                            boot_id=11, seq=100)]
    assert adapter.totals["bad_lines"] == 2 and adapter.totals["unexpected_lines"] == 1
    service.close()
    thread.join(5)
    assert not thread.is_alive() and not failures
    assert [r["type"] for r in records if r["type"].startswith("connection_")] == [
        "connection_open", "connection_close"]
    assert adapter.epoch is None and adapter.counts[LEFT]["resets"] == {"worker_disconnect": 1}
    runner.close()


def test_serve_counts_a_second_hello_as_an_unexpected_line_not_a_new_connection():
    service, runner = socket.socketpair()
    epochs = []
    adapter = HandAdapter(ScriptedBackend(), confirmations=1,
                          epoch_factory=lambda: epochs.append(1) or "{:032x}".format(len(epochs)))
    stop = threading.Event()
    thread = threading.Thread(target=serve, args=(runner, adapter, stop, lambda record: None), daemon=True)
    thread.start()
    glove = Glove(LEFT, 11)
    lines = [json.dumps(HELLO)] + [json.dumps(glove.sample("PICKUP")) for _ in range(50)]
    lines += [json.dumps(HELLO)] + [json.dumps(glove.sample("PICKUP")) for _ in range(51)]
    service.sendall(("\n".join(lines) + "\n").encode("utf-8"))
    # The window spans both halves: the second hello neither reset the hand nor began an epoch.
    assert read_lines(service, 1) == [dict(type="result", gesture="PICKUP", confidence=0.94,
                                           device_id=LEFT, boot_id=11, seq=100)]
    assert adapter.totals["connections"] == 1 and adapter.totals["unexpected_lines"] == 1
    assert epochs == [1] and adapter.epoch == "{:032x}".format(1)
    assert sum(adapter.counts[LEFT]["resets"].values()) == 0
    stop.set()
    thread.join(5)
    assert not thread.is_alive()
    service.close()
    runner.close()


def test_serve_refuses_the_v3_hello_and_stops_on_request():
    service, runner = socket.socketpair()
    adapter = HandAdapter(backend_factory=lambda: pytest.fail("no backend for a refused service"))
    service.sendall((json.dumps(dict(type="hello", format=1, channels=list(V3_CHANNELS))) + "\n").encode())
    with pytest.raises(IncompatibleService):
        serve(runner, adapter, threading.Event(), lambda record: None)
    service.close()
    runner.close()
    # A stop request ends serve() promptly even while the stream stays open.
    service, runner = socket.socketpair()
    adapter = HandAdapter(ScriptedBackend())
    stop = threading.Event()
    thread = threading.Thread(target=serve, args=(runner, adapter, stop, lambda record: None), daemon=True)
    thread.start()
    service.sendall((json.dumps(HELLO) + "\n").encode())
    deadline = time.monotonic() + 5
    while adapter.epoch is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert adapter.epoch is not None
    stop.set()
    thread.join(5)
    assert not thread.is_alive() and adapter.epoch is None
    service.close()
    runner.close()
