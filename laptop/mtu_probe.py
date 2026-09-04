"""Run the test-only Gate D ATT MTU notification-boundary probe."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

from bleak import BleakClient, BleakScanner


EXPECTED_SERVICE_UUID = "6e1c0001-7a45-4dc4-b678-3f2d5a9c1001"
CONTROL_CHARACTERISTIC_UUID = "6e1c0003-7a45-4dc4-b678-3f2d5a9c1001"
PROBE_CHARACTERISTIC_UUID = "6e1c0004-7a45-4dc4-b678-3f2d5a9c1001"
ATT_VALUE_OVERHEAD_BYTES = 3
SAFE_LENGTH = 20
DEFAULT_SCAN_TIMEOUT_SECONDS = 5.0
DEFAULT_NOTIFICATION_TIMEOUT_SECONDS = 2.0
DEFAULT_QUEUE_SIZE = 8


class RequiredGattMissing(RuntimeError):
    """The connected peripheral is not exposing the test-only Gate D API."""


class NotificationInbox:
    """Bound callback work to copying bytes into an asyncio queue."""

    def __init__(self, maxsize: int) -> None:
        if maxsize < 1:
            raise ValueError("queue size must be positive")
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=maxsize)
        self._drop_count = 0

    def put_from_callback(self, payload: bytes) -> None:
        try:
            self._queue.put_nowait(bytes(payload))
        except asyncio.QueueFull:
            self._drop_count += 1

    async def get(self, timeout_seconds: float) -> bytes:
        return await asyncio.wait_for(self._queue.get(), timeout=timeout_seconds)

    def drain(self) -> list[bytes]:
        messages: list[bytes] = []
        while True:
            try:
                messages.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                return messages

    @property
    def drop_count(self) -> int:
        return self._drop_count


@dataclass(frozen=True)
class TrialResult:
    requested_length: int
    outcome: str
    received_length: Optional[int]
    payload_exact: bool
    payload: Optional[bytes] = None

    def to_public_json(self) -> dict[str, object]:
        return {
            "outcome": self.outcome,
            "payload_exact": self.payload_exact,
            "received_length": self.received_length,
            "requested_length": self.requested_length,
        }


@dataclass(frozen=True)
class MtuProbeSummary:
    windows_att_mtu: int
    value_boundary: int
    trials: tuple[TrialResult, ...]
    queue_drop_count: int
    unexpected_notification_count: int
    cleanup_error_count: int

    def exit_code(self) -> int:
        expected = ("exact", "exact", "laptop_absence")
        trials_ok = len(self.trials) == 3 and tuple(
            trial.outcome for trial in self.trials
        ) == expected
        anomalies = any(
            (
                self.queue_drop_count,
                self.unexpected_notification_count,
                self.cleanup_error_count,
            )
        )
        return 0 if trials_ok and not anomalies else 1

    def to_json(self) -> str:
        return json.dumps(
            {
                "cleanup_error_count": self.cleanup_error_count,
                "queue_drop_count": self.queue_drop_count,
                "trials": [trial.to_public_json() for trial in self.trials],
                "unexpected_notification_count": self.unexpected_notification_count,
                "value_boundary": self.value_boundary,
                "windows_att_mtu": self.windows_att_mtu,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


def advertises_expected_service(service_uuids: Optional[Iterable[str]]) -> bool:
    """Return whether the advertisement contains Gate D's test service UUID."""
    return any(uuid.lower() == EXPECTED_SERVICE_UUID for uuid in service_uuids or ())


def deterministic_payload(length: int) -> bytes:
    """Build Gate D's explicitly test-only byte-i-is-i-mod-256 payload."""
    return bytes(index & 0xFF for index in range(length))


class MtuProbe:
    """Single-connection Gate D probe with an intentionally small BLE callback."""

    def __init__(
        self,
        *,
        scan_timeout_seconds: float = DEFAULT_SCAN_TIMEOUT_SECONDS,
        notification_timeout_seconds: float = DEFAULT_NOTIFICATION_TIMEOUT_SECONDS,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        scanner: type[BleakScanner] = BleakScanner,
        client_factory: Callable[..., BleakClient] = BleakClient,
    ) -> None:
        if scan_timeout_seconds <= 0 or notification_timeout_seconds <= 0:
            raise ValueError("timeouts must be positive")
        self._scan_timeout_seconds = scan_timeout_seconds
        self._notification_timeout_seconds = notification_timeout_seconds
        self._queue_size = queue_size
        self._scanner = scanner
        self._client_factory = client_factory

    async def run(self) -> MtuProbeSummary:
        """Run safe, negotiated-boundary, and boundary-plus-one trials in order."""
        device = await self._scanner.find_device_by_filter(
            lambda _device, advertisement: advertises_expected_service(
                advertisement.service_uuids
            ),
            timeout=self._scan_timeout_seconds,
        )
        if device is None:
            raise TimeoutError("no peripheral advertising the Gate D test service")

        client = self._client_factory(device)
        inbox = NotificationInbox(self._queue_size)
        trials: list[TrialResult] = []
        cleanup_error_count = 0
        unexpected_notification_count = 0
        windows_att_mtu = 0
        value_boundary = 0
        subscribed = False
        try:
            await client.connect()
            self._verify_required_gatt(client)
            windows_att_mtu = client.mtu_size
            value_boundary = windows_att_mtu - ATT_VALUE_OVERHEAD_BYTES
            if value_boundary < SAFE_LENGTH:
                raise RequiredGattMissing(
                    "public client.mtu_size is too small for the required 20-byte safe trial"
                )
            await client.start_notify(
                PROBE_CHARACTERISTIC_UUID, self._make_notification_callback(inbox)
            )
            subscribed = True
            for requested_length, expect_notification in (
                (SAFE_LENGTH, True),
                (value_boundary, True),
                (value_boundary + 1, False),
            ):
                trial, unexpected_count = await self._run_trial(
                    client, inbox, requested_length, expect_notification
                )
                trials.append(trial)
                unexpected_notification_count += unexpected_count
        finally:
            if subscribed:
                try:
                    await client.stop_notify(PROBE_CHARACTERISTIC_UUID)
                except Exception:
                    cleanup_error_count += 1
            if client.is_connected:
                try:
                    await client.disconnect()
                except Exception:
                    cleanup_error_count += 1

        return MtuProbeSummary(
            windows_att_mtu=windows_att_mtu,
            value_boundary=value_boundary,
            trials=tuple(trials),
            queue_drop_count=inbox.drop_count,
            unexpected_notification_count=unexpected_notification_count,
            cleanup_error_count=cleanup_error_count,
        )

    def _verify_required_gatt(self, client: BleakClient) -> None:
        service = client.services.get_service(EXPECTED_SERVICE_UUID)
        if service is None:
            raise RequiredGattMissing("required Gate D test service is missing")
        control = service.get_characteristic(CONTROL_CHARACTERISTIC_UUID)
        if control is None or "write" not in {item.lower() for item in control.properties}:
            raise RequiredGattMissing("required Gate D write control characteristic is missing")
        probe = service.get_characteristic(PROBE_CHARACTERISTIC_UUID)
        if probe is None or "notify" not in {item.lower() for item in probe.properties}:
            raise RequiredGattMissing("required Gate D notify characteristic is missing")

    def _make_notification_callback(
        self, inbox: NotificationInbox
    ) -> Callable[[Any, bytearray], None]:
        def callback(_sender: Any, payload: bytearray) -> None:
            inbox.put_from_callback(payload)

        return callback

    async def _run_trial(
        self,
        client: BleakClient,
        inbox: NotificationInbox,
        requested_length: int,
        expect_notification: bool,
    ) -> tuple[TrialResult, int]:
        request = requested_length.to_bytes(2, byteorder="little", signed=False)
        await client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, request, response=True)
        try:
            payload = await inbox.get(self._notification_timeout_seconds)
        except asyncio.TimeoutError:
            if expect_notification:
                return TrialResult(requested_length, "timeout", None, False), 0
            return TrialResult(requested_length, "laptop_absence", None, False), 0

        if not expect_notification:
            return (
                TrialResult(
                    requested_length,
                    "unexpected_notification",
                    len(payload),
                    False,
                    payload,
                ),
                1,
            )

        expected = deterministic_payload(requested_length)
        exact = payload == expected
        trailing = inbox.drain()
        if trailing:
            return (
                TrialResult(
                    requested_length,
                    "unexpected_notification",
                    len(payload),
                    exact,
                    payload,
                ),
                len(trailing),
            )
        return TrialResult(
            requested_length,
            "exact" if exact else "payload_mismatch",
            len(payload),
            exact,
            payload,
        ), 0


async def _run_from_args(args: argparse.Namespace) -> MtuProbeSummary:
    return await MtuProbe(
        scan_timeout_seconds=args.scan_timeout_seconds,
        notification_timeout_seconds=args.notification_timeout_seconds,
    ).run()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-timeout-seconds", type=float, default=DEFAULT_SCAN_TIMEOUT_SECONDS)
    parser.add_argument(
        "--notification-timeout-seconds",
        type=float,
        default=DEFAULT_NOTIFICATION_TIMEOUT_SECONDS,
    )
    args = parser.parse_args()
    try:
        summary = asyncio.run(_run_from_args(args))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 1
    print(summary.to_json())
    return summary.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
