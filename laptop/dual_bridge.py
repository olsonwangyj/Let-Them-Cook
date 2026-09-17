"""Run two independently owned Week 7 ESP32 reception paths."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
from typing import Optional

from laptop.bridge import Bridge, BridgeConfig


LOG = logging.getLogger(__name__)


class DualBridge:
    """Coordinate a common observation without coupling either device path."""

    def __init__(self, left: Bridge, right: Bridge, *, expected_rate=10.0,
                 startup_timeout=30.0, drain_timeout=10.0,
                 shutdown_timeout=25.0):
        self.bridges = {1: left, 2: right}
        for value, name in ((expected_rate, "expected rate"),
                            (startup_timeout, "startup timeout"),
                            (drain_timeout, "drain timeout"),
                            (shutdown_timeout, "shutdown timeout")):
            if not isinstance(value, (int, float)) or isinstance(value, bool) \
                    or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive finite seconds")
        self.expected_rate = float(expected_rate)
        self.startup_timeout = float(startup_timeout)
        self.drain_timeout = float(drain_timeout)
        self.shutdown_timeout = float(shutdown_timeout)
        for device_id, bridge in self.bridges.items():
            if bridge.config.expected_device_id != device_id:
                raise ValueError(f"device {device_id} bridge has the wrong expected identity")
            if bridge.source_audit is None:
                raise ValueError("dual reception requires source auditing")
        if left.config.session_id != right.config.session_id:
            raise ValueError("both bridges must use the same session ID")
        if (left.config.address and right.config.address
                and left.config.address.lower() == right.config.address.lower()):
            raise ValueError("physical devices require distinct BLE addresses")

    async def _wait_for_start(self, active, input_tasks):
        async def both_active():
            while not all(event.is_set() for event in active.values()):
                for task in input_tasks.values():
                    if task.done():
                        task.result()
                        raise RuntimeError("input worker exited before both streams became active")
                await asyncio.sleep(0.01)

        await asyncio.wait_for(both_active(), self.startup_timeout)

    async def run(self, duration=600.0, *, mock=False, mock_rate: Optional[float] = None,
                  ble_options=None):
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) \
                or not math.isfinite(duration) or duration <= 0:
            raise ValueError("duration must be positive finite seconds")
        if not mock:
            addresses = [bridge.config.address for bridge in self.bridges.values()]
            if not all(addresses):
                raise ValueError("physical dual reception requires both BLE addresses")
            if addresses[0].lower() == addresses[1].lower():
                raise ValueError("physical devices require distinct BLE addresses")
        rate = self.expected_rate if mock_rate is None else mock_rate
        if not isinstance(rate, (int, float)) or isinstance(rate, bool) \
                or not math.isfinite(rate) or rate <= 0:
            raise ValueError("mock rate must be positive finite")
        ble_options = ble_options or {}
        stop = {device: asyncio.Event() for device in self.bridges}
        active = {device: asyncio.Event() for device in self.bridges}
        writers = {
            device: asyncio.create_task(bridge.writer_loop(), name=f"writer-{device}")
            for device, bridge in self.bridges.items()
        }
        inputs = {}
        for device, bridge in self.bridges.items():
            if mock:
                coroutine = bridge.dummy_loop(
                    rate, stop_event=stop[device], active_event=active[device])
            else:
                options = dict(ble_options.get(device, {}))
                coroutine = bridge.ble_loop(
                    stop_event=stop[device], active_event=active[device], **options)
            inputs[device] = asyncio.create_task(coroutine, name=f"input-{device}")

        failures = {1: [], 2: []}
        startup_ok = False
        observation_start = observation_end = None
        try:
            try:
                await self._wait_for_start(active, inputs)
                startup_ok = True
            except (Exception, asyncio.TimeoutError) as exc:
                for device in self.bridges:
                    if not active[device].is_set():
                        failures[device].append(f"startup:{type(exc).__name__}")

            if startup_ok:
                observation_start = asyncio.get_running_loop().time()
                for bridge in self.bridges.values():
                    bridge.begin_observation()
                deadline = observation_start + duration
                while True:
                    now = asyncio.get_running_loop().time()
                    if now >= deadline:
                        break
                    for device, task in inputs.items():
                        if task.done() and not stop[device].is_set():
                            try:
                                task.result()
                                marker = "input:stopped"
                            except BaseException as exc:
                                marker = f"input:{type(exc).__name__}"
                            if marker not in failures[device]:
                                failures[device].append(marker)
                    for device, task in writers.items():
                        if task.done():
                            try:
                                task.result()
                                marker = "writer:stopped"
                            except BaseException as exc:
                                marker = f"writer:{type(exc).__name__}"
                            if marker not in failures[device]:
                                failures[device].append(marker)
                    await asyncio.sleep(min(0.02, max(0.0, deadline - now)))
                observation_end = asyncio.get_running_loop().time()
                for bridge in self.bridges.values():
                    bridge.finish_observation()
        finally:
            # Both producers are asked to quiesce together. Each path performs
            # stop-notify and its final source read independently.
            for event in stop.values():
                event.set()
            done, pending = await asyncio.wait(inputs.values(), timeout=self.shutdown_timeout)
            for task in done:
                device = int(task.get_name().rsplit("-", 1)[1])
                if not task.cancelled():
                    try:
                        task.result()
                    except BaseException as exc:
                        failures[device].append(f"shutdown:{type(exc).__name__}")
            for task in pending:
                device = int(task.get_name().rsplit("-", 1)[1])
                failures[device].append("shutdown:timeout")
                task.cancel()
            if pending:
                _, still_pending = await asyncio.wait(pending, timeout=0.5)
                for task in still_pending:
                    device = int(task.get_name().rsplit("-", 1)[1])
                    bridge = self.bridges[device]
                    bridge._retained.add(task)

                    def consume(child, *, bridge=bridge):
                        bridge._retained.discard(child)
                        if not child.cancelled():
                            child.exception()

                    task.add_done_callback(consume)

            drain_deadline = asyncio.get_running_loop().time() + self.drain_timeout
            while (any(bridge.inbox.size or bridge._inflight
                       for bridge in self.bridges.values())
                   and asyncio.get_running_loop().time() < drain_deadline):
                await asyncio.sleep(0.01)
            for device, bridge in self.bridges.items():
                if bridge.inbox.size or bridge._inflight:
                    failures[device].append("drain:timeout")

            for task in writers.values():
                task.cancel()
            _, writer_pending = await asyncio.wait(
                writers.values(), timeout=self.shutdown_timeout)
            for device, task in writers.items():
                if task in writer_pending:
                    failures[device].append("writer:timeout")
                    bridge = self.bridges[device]
                    bridge._retained.add(task)

                    def consume_writer(child, *, bridge=bridge):
                        bridge._retained.discard(child)
                        if not child.cancelled():
                            child.exception()

                    task.add_done_callback(consume_writer)
                elif not task.cancelled():
                    result = task.exception()
                    if result is not None:
                        failures[device].append(f"writer:{type(result).__name__}")
            for bridge in self.bridges.values():
                bridge.inbox.activate(0)
            close_results = await asyncio.gather(
                *(bridge.close_transport() for bridge in self.bridges.values()),
                return_exceptions=True)
            for device, result in zip(self.bridges, close_results):
                if isinstance(result, BaseException):
                    failures[device].append(f"transport_close:{type(result).__name__}")

        observed_duration = (observation_end - observation_start
                             if observation_start is not None and observation_end is not None
                             else 0.0)
        expected_samples = observed_duration * self.expected_rate
        devices = {}
        clean = startup_ok
        anomaly_fields = (
            "malformed", "stale_dropped", "generation_dropped", "duplicate_acks",
            "ack_errors", "ambiguous_dropped", "transport_errors", "ble_errors",
            "cleanup_errors", "identity_mismatches", "source_stats_errors",
            "disconnects", "queue_dropped", "callback_generation_dropped",
            "gaps", "duplicates", "out_of_order", "new_boots",
        )
        for device, bridge in self.bridges.items():
            item = bridge.summary()
            coverage_ok = (item["observation_received"] > 0
                           and item["observation_received"] >= 0.9 * expected_samples)
            silence_ok = item["observation_max_silence"] <= bridge.config.freshness
            protected_ble = mock or not bridge.config.diagnostic_unprotected
            item.update({
                "runtime_failures": failures[device],
                "expected_samples": expected_samples,
                "coverage_ratio": (item["observation_received"] / expected_samples
                                   if expected_samples else 0.0),
                "sustained_coverage": coverage_ok,
                "silence_ok": silence_ok,
                "protected_ble": protected_ble,
                "input": "synthetic" if mock else "physical",
            })
            item_clean = bool(
                not failures[device] and item["source"] and item["source"]["clean"]
                and coverage_ok and silence_ok and protected_ble and not item["unfinished"]
                and not any(item[field] for field in anomaly_fields)
            )
            item["clean"] = item_clean
            clean = clean and item_clean
            devices[str(device)] = item
        return {
            "clean": bool(clean),
            "mock_input": mock,
            "session_id": self.bridges[1].config.session_id,
            "common_observation_seconds": observed_duration,
            "expected_rate_hz": self.expected_rate,
            "devices": devices,
        }


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left-address")
    parser.add_argument("--right-address")
    parser.add_argument("--ca", required=True)
    parser.add_argument("--port", type=int, default=18888)
    parser.add_argument("--session-id", default="week7-demo")
    parser.add_argument("--duration", type=float, default=600.0)
    parser.add_argument("--queue-capacity", type=int, default=64)
    parser.add_argument("--freshness", type=float, default=2.0)
    parser.add_argument("--expected-rate", type=float, default=10.0)
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    parser.add_argument("--drain-timeout", type=float, default=10.0)
    parser.add_argument("--mock", action="store_true",
                        help="explicit two-device synthetic input, not BLE evidence")
    parser.add_argument("--diagnostic-unprotected", action="store_true")
    return parser


def main():
    parser = _parser()
    args = parser.parse_args()
    if not args.mock and (not args.left_address or not args.right_address):
        parser.error("physical mode requires --left-address and --right-address")
    if (args.left_address and args.right_address
            and args.left_address.lower() == args.right_address.lower()):
        parser.error("left and right BLE addresses must be distinct")
    logging.basicConfig(level=logging.INFO)

    def bridge(device_id, address):
        return Bridge(BridgeConfig(
            ca_file=args.ca, port=args.port, session_id=args.session_id,
            queue_capacity=args.queue_capacity, freshness=args.freshness,
            address=address, diagnostic_unprotected=args.diagnostic_unprotected,
            expected_device_id=device_id, source_audit=True))

    async def run():
        dual = DualBridge(
            bridge(1, args.left_address), bridge(2, args.right_address),
            expected_rate=args.expected_rate, startup_timeout=args.startup_timeout,
            drain_timeout=args.drain_timeout)
        return await dual.run(
            duration=args.duration, mock=args.mock, mock_rate=args.expected_rate)

    report = _run_with_bounded_loop(run())
    print(json.dumps(report, sort_keys=True))
    return 0 if report["clean"] else 1


def _run_with_bounded_loop(coroutine, *, retirement_timeout=0.1):
    """Run the CLI owner without asyncio.run's unbounded final task gather."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        pending = {task for task in asyncio.all_tasks(loop) if not task.done()}
        for task in pending:
            task.cancel()
        if pending:
            _, pending = loop.run_until_complete(
                asyncio.wait(pending, timeout=retirement_timeout))
        # These owned tasks have exceeded both coordinator and loop retirement
        # bounds. Closing the private CLI loop prevents further callbacks; the
        # failure is already latched in the returned report.
        for task in pending:
            task._log_destroy_pending = False
        asyncio.set_event_loop(None)
        loop.close()


if __name__ == "__main__":
    raise SystemExit(main())
