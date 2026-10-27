"""Software loopback of the hand12 runner: TLS service (v4) -> model bridge -> runner -> subscriber.

Real CommsServer(sensor_version=4) on random local ports with throwaway certificates,
a real ultra96.model_bridge.Bridge attached to one end of a socket pair, the runner's
serve() loop on the other end with the scripted backend, two 50 Hz v4 glove streams
in real time and a phone subscriber. No BLE, FPGA, SSH or phone.
"""
import asyncio
import socket
import threading
import time

import pytest

pytest.importorskip("cryptography")

from common.sensor_v4 import CHANNELS as V4_CHANNELS, SensorPacket
from common.tls import TLS_SERVER_NAME, client_context, server_context
from common.wire import read_frame, write_frame
from src.hand_runtime import LABELS
from tests.test_comms_hand_runner import ScriptedBackend
from tools.generate_comms_pki import generate_pki
from ultra96.hand_runner import HandAdapter, serve
from ultra96.model_bridge import Bridge
from ultra96.server import CommsServer

SESSION = "ltc-comms"
LEFT, RIGHT = 1, 2
TICK = 0.02  # 50 Hz
TICKS = 380  # 7.6 s
DUPLICATE_TICK = 150  # the left sample re-sent unchanged
RESULT_FIELDS = {"v", "type", "session_id", "device_id", "boot_id", "seq", "request_id",
                 "result_id", "gesture", "confidence"}


class BridgeModel:
    """The service's model: a model_bridge.Bridge served over a socket pair, not a Unix listener."""
    name = "hand-runner-loopback"

    def __init__(self):
        self.bridge = Bridge()

    def configure_sensor_version(self, version):
        assert version == 4
        self.bridge.channels = tuple(V4_CHANNELS)

    def start(self, emit):
        self.bridge.start(emit)

    def on_sample(self, device_id, boot_id, seq, uptime_ms, values):
        self.bridge.on_sample(device_id, boot_id, seq, uptime_ms, values)


def left_label(tick):
    return "CHOP" if tick < 200 else "POURING"


def right_label(tick):
    # PICKUP, then 1.3 s of silence (a glove reconnect), then PICKUP again.
    return None if 150 <= tick < 215 else "PICKUP"


async def glove(server, context, device, boot, label_at, acks, start):
    """One hand's laptop relay: a v4 SENSOR_BATCH every 20 ms, each waiting for its ACK.

    seq and uptime follow the tick, so the silent ticks are samples lost in the reconnect.
    """
    reader, writer = await asyncio.open_connection("127.0.0.1", server.ingest_port, ssl=context,
                                                   server_hostname=TLS_SERVER_NAME)
    loop = asyncio.get_running_loop()
    try:
        for tick in range(TICKS):
            await asyncio.sleep(max(0.0, start + tick * TICK - loop.time()))
            label = label_at(tick)
            if label is None:
                continue
            values = [0] * 12
            values[11] = LABELS.index(label) * 1000  # flex3 x10000: physical label index / 10
            message = SensorPacket(device, boot, tick, 1000 + tick * 20, tuple(values)).to_message(SESSION)
            sends = 2 if device == LEFT and tick == DUPLICATE_TICK else 1
            for _ in range(sends):
                await write_frame(writer, message)
                ack = await read_frame(reader)
                acks.append((device, tick, ack["status"]))
    finally:
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), 1)
        except (OSError, ConnectionError, asyncio.TimeoutError):
            writer.transport.abort()


async def scenario(pki):
    model = BridgeModel()
    server = CommsServer(server_context(pki / "server-cert.pem", pki / "server-key.pem"),
                         ingest_port=0, gateway_port=0, model=model, sensor_version=4)
    await server.start()
    service_end, runner_end = socket.socketpair()
    model.bridge.attach(service_end)  # after start(): the bridge has its emit
    records = []
    adapter = HandAdapter(ScriptedBackend(), log=records.append)
    stop = threading.Event()
    failures = []

    def run_runner():
        try:
            serve(runner_end, adapter, stop, records.append)
        except Exception as error:  # reported by the test
            failures.append(error)

    runner = threading.Thread(target=run_runner, name="hand-runner", daemon=True)
    runner.start()
    phone_writer = None
    consumer = None
    results, acks = [], []
    try:
        context = client_context(pki / "ca-cert.pem")
        phone, phone_writer = await asyncio.open_connection(
            "127.0.0.1", server.gateway_port, ssl=context, server_hostname=TLS_SERVER_NAME)
        await write_frame(phone_writer, dict(v=1, type="SUBSCRIBE", session_id=SESSION))
        assert await read_frame(phone) == dict(v=1, type="SUBSCRIBED", session_id=SESSION)

        async def receive():
            while True:
                results.append(await read_frame(phone, timeout=30))

        consumer = asyncio.create_task(receive())
        deadline = time.monotonic() + 5
        while adapter.epoch is None:  # the runner has the hello
            assert time.monotonic() < deadline, "runner never received the bridge hello"
            await asyncio.sleep(0.01)
        start = asyncio.get_running_loop().time() + 0.05
        await asyncio.gather(glove(server, context, LEFT, 11, left_label, acks, start),
                             glove(server, context, RIGHT, 22, right_label, acks, start))
        # Let the last inferences finish, then wait until the subscriber has every result.
        settled, deadline = time.monotonic() + 0.5, time.monotonic() + 3
        while time.monotonic() < settled or len(results) < server.metrics.get("model_results", 0):
            assert time.monotonic() < deadline, "results did not reach the subscriber"
            await asyncio.sleep(0.02)
    finally:
        stop.set()
        runner.join(5)
        if consumer is not None:
            consumer.cancel()
            await asyncio.gather(consumer, return_exceptions=True)
        if phone_writer is not None:
            phone_writer.close()
            try:
                await asyncio.wait_for(phone_writer.wait_closed(), 1)
            except (OSError, ConnectionError, asyncio.TimeoutError):
                phone_writer.transport.abort()
        await server.close()
        model.bridge.close()
        runner_end.close()
    return dict(server=server, bridge=model.bridge, adapter=adapter, records=records,
                results=results, acks=acks, failures=failures, runner_alive=runner.is_alive())


@pytest.fixture(scope="module")
def loopback(tmp_path_factory):
    pki = generate_pki(tmp_path_factory.mktemp("hand-loopback") / "pki")
    return asyncio.run(scenario(pki))


def events(run, device, kind=None, delivery=None):
    return [r for r in run["records"] if r["type"] == "hand_event" and r["device_id"] == device
            and (kind is None or r["kind"] == kind) and (delivery is None or r["delivery"] == delivery)]


def hand(run, device):
    return [r for r in run["results"] if r["device_id"] == device]


def test_the_runner_and_the_service_ran_cleanly(loopback):
    assert not loopback["failures"] and not loopback["runner_alive"]
    metrics = loopback["server"].metrics
    assert metrics["model_results_duplicate"] == 0 and metrics["model_results_rejected"] == 0
    assert metrics["model_errors"] == 0 and metrics["rejected"] == 0
    assert loopback["bridge"].counts["results_refused"] == 0 and loopback["bridge"].counts["bad_lines"] == 0
    for device in (LEFT, RIGHT):
        counts = loopback["adapter"].counts[device]
        assert counts["collisions"] == 0 and counts["encoder_errors"] == 0 and counts["invalid"] == 0


def test_every_forwarded_event_is_one_gesture_result_naming_its_own_sample(loopback):
    results = loopback["results"]
    forwarded = sum(loopback["adapter"].counts[d]["forwarded"] for d in (LEFT, RIGHT))
    assert results and len(results) == forwarded == loopback["server"].metrics["model_results"]
    assert loopback["bridge"].counts["results"] == forwarded
    for result in results:
        assert set(result) == RESULT_FIELDS and result["type"] == "GESTURE_RESULT"
        assert result["session_id"] == SESSION and result["request_id"] is None
        assert result["result_id"] == "{}:{}:{}".format(result["device_id"], result["boot_id"], result["seq"])
    assert len({r["result_id"] for r in results}) == len(results)


def test_each_hand_gets_its_own_gestures(loopback):
    left, right = hand(loopback, LEFT), hand(loopback, RIGHT)
    assert {r["boot_id"] for r in left} == {11} and {r["boot_id"] for r in right} == {22}
    gestures = [r["gesture"] for r in left]
    assert gestures[0] == "CHOP" and gestures[-1] == "POURING"
    assert gestures == sorted(gestures, key=["CHOP", "POURING"].index)  # CHOP..., then POURING...
    assert [r["gesture"] for r in right] == ["PICKUP", "PICKUP"]
    assert right[0]["seq"] < 150 <= 215 <= right[1]["seq"]


def test_a_transition_gives_one_result_at_the_transition_sample(loopback):
    start = [e for e in events(loopback, LEFT, "state_start") if e["gesture"] == "POURING"]
    assert len(start) == 1 and start[0]["delivery"] == "forwarded"
    transition = start[0]["source"]["seq"]
    at_transition = [r for r in hand(loopback, LEFT) if r["seq"] == transition]
    assert [r["gesture"] for r in at_transition] == ["POURING"]
    first_pouring = next(r for r in hand(loopback, LEFT) if r["gesture"] == "POURING")
    assert first_pouring["seq"] == transition >= 200
    ends = events(loopback, LEFT, "state_end")
    assert ends and ends[0]["gesture"] == "CHOP" and ends[0]["delivery"] == "not_forwarded"


def test_a_resent_batch_is_a_duplicate_ack_and_no_extra_result(loopback):
    resent = [status for device, tick, status in loopback["acks"] if (device, tick) == (LEFT, DUPLICATE_TICK)]
    assert resent == ["accepted", "duplicate"]
    assert loopback["server"].metrics["duplicates"] == 1
    assert all(status == "accepted" for device, tick, status in loopback["acks"]
               if (device, tick) != (LEFT, DUPLICATE_TICK))
    assert loopback["adapter"].counts[LEFT]["duplicates_ignored"] == 0  # the service kept it out


def test_a_glove_reconnect_resets_only_that_hand(loopback):
    resets = [r for r in loopback["records"] if r["type"] == "hand_reset" and r["reason"] != "worker_disconnect"]
    assert [(r["device_id"], r["reason"]) for r in resets] == [(RIGHT, "connection_reset")]
    assert resets[0]["silence_s"] >= 1.0
    assert [e["reason"] for e in events(loopback, RIGHT, "reset")[:1]] == ["connection_reset"]
    # The left hand's CHOP state ran on through the right glove's reconnect.
    chop = [e for e in events(loopback, LEFT, "state_start") if e["gesture"] == "CHOP"]
    assert len(chop) == 1
    refreshes = [e for e in events(loopback, LEFT, "state_refresh") if e["state_id"] == chop[0]["state_id"]]
    assert any(150 <= e["source"]["seq"] < 200 for e in refreshes)


def test_results_stay_v3_gesture_results_in_v4_mode(loopback):
    # The owner's decision: in v4 mode GESTURE_RESULT stays v=3, since both phone apps reject v=4.
    assert {r["v"] for r in loopback["results"]} == {3}
