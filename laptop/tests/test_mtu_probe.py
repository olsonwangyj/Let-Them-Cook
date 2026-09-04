"""Tests for the test-only Gate D ATT MTU diagnostic probe.

Each test names the production break it catches.  Bleak itself is the only
external boundary replaced with fakes; payload assertions use hand-derived
literal byte sequences.
"""

from __future__ import annotations

import asyncio
import unittest

from laptop.mtu_probe import (
    CONTROL_CHARACTERISTIC_UUID,
    EXPECTED_SERVICE_UUID,
    PROBE_CHARACTERISTIC_UUID,
    MtuProbe,
    RequiredGattMissing,
)


class _Characteristic:
    def __init__(self, properties: list[str]) -> None:
        self.properties = properties


class _Service:
    def __init__(self, control_properties: list[str], probe_properties: list[str]) -> None:
        self._control_properties = control_properties
        self._probe_properties = probe_properties

    def get_characteristic(self, uuid: str) -> _Characteristic | None:
        if uuid == CONTROL_CHARACTERISTIC_UUID:
            return _Characteristic(self._control_properties)
        if uuid == PROBE_CHARACTERISTIC_UUID:
            return _Characteristic(self._probe_properties)
        return None


class _Services:
    def __init__(self, control_properties: list[str], probe_properties: list[str]) -> None:
        self._service = _Service(control_properties, probe_properties)

    def get_service(self, uuid: str) -> _Service | None:
        return self._service if uuid == EXPECTED_SERVICE_UUID else None


class _Scanner:
    def __init__(self, device: object) -> None:
        self.device = device
        self.filter = None

    async def find_device_by_filter(self, predicate: object, timeout: float) -> object:
        del timeout
        self.filter = predicate
        return self.device


class _Client:
    def __init__(
        self,
        device: object,
        *,
        mtu_size: int = 25,
        control_properties: list[str] | None = None,
        probe_properties: list[str] | None = None,
        oversize_notification: bool = False,
        disconnect_error: Exception | None = None,
    ) -> None:
        self.device = device
        self.mtu_size = mtu_size
        self.is_connected = False
        self.services = _Services(
            control_properties or ["write"], probe_properties or ["notify"]
        )
        self.oversize_notification = oversize_notification
        self.disconnect_error = disconnect_error
        self.callback = None
        self.write_lengths: list[int] = []
        self.started_before_write = True

    async def connect(self) -> None:
        self.is_connected = True

    async def start_notify(self, _uuid: str, callback: object) -> None:
        self.callback = callback

    async def write_gatt_char(self, _uuid: str, request: bytes, response: bool) -> None:
        assert response is True
        self.started_before_write = self.callback is not None
        requested_length = int.from_bytes(request, "little")
        self.write_lengths.append(requested_length)
        if requested_length <= self.mtu_size - 3 or self.oversize_notification:
            assert self.callback is not None
            payload = bytes(range(requested_length))
            asyncio.get_running_loop().call_soon(self.callback, None, bytearray(payload))

    async def stop_notify(self, _uuid: str) -> None:
        return None

    async def disconnect(self) -> None:
        self.is_connected = False
        if self.disconnect_error is not None:
            raise self.disconnect_error


class _ClientFactory:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.client: _Client | None = None

    def __call__(self, device: object) -> _Client:
        self.client = _Client(device, **self.kwargs)
        return self.client


class MtuProbeTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_uses_scanned_device_and_delivers_exact_safe_and_boundary_payloads(self) -> None:
        """Catches changing the scan/device handoff or accepting truncated/corrupt payloads."""
        device = object()
        scanner = _Scanner(device)
        factory = _ClientFactory(mtu_size=25)

        summary = await MtuProbe(scanner=scanner, client_factory=factory).run()

        self.assertIsNotNone(scanner.filter)
        self.assertIs(factory.client.device, device)
        self.assertTrue(factory.client.started_before_write)
        self.assertEqual(factory.client.write_lengths, [20, 22, 23])
        self.assertEqual(summary.windows_att_mtu, 25)
        self.assertEqual(summary.value_boundary, 22)
        self.assertEqual(summary.trials[0].payload, b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13")
        self.assertEqual(summary.trials[1].payload, b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15")
        self.assertEqual(summary.trials[2].outcome, "laptop_absence")
        self.assertEqual(summary.exit_code(), 0)

    async def test_missing_control_write_property_is_rejected_before_trial(self) -> None:
        """Catches accepting a connected peripheral without Gate D's writable control API."""
        factory = _ClientFactory(control_properties=["read"])

        with self.assertRaises(RequiredGattMissing):
            await MtuProbe(scanner=_Scanner(object()), client_factory=factory).run()

    async def test_oversize_notification_is_an_anomaly_not_evidence_of_rejection(self) -> None:
        """Catches treating a boundary-plus-one notification as a successful rejection."""
        factory = _ClientFactory(mtu_size=25, oversize_notification=True)

        summary = await MtuProbe(scanner=_Scanner(object()), client_factory=factory).run()

        self.assertEqual(summary.trials[2].outcome, "unexpected_notification")
        self.assertEqual(summary.exit_code(), 1)

    async def test_cleanup_failure_is_exposed_in_summary_and_exit_status(self) -> None:
        """Catches silently hiding stop-notify or disconnect cleanup failures."""
        factory = _ClientFactory(disconnect_error=RuntimeError("disconnect failed"))

        summary = await MtuProbe(scanner=_Scanner(object()), client_factory=factory).run()

        self.assertEqual(summary.cleanup_error_count, 1)
        self.assertEqual(summary.exit_code(), 1)


if __name__ == "__main__":
    unittest.main()
