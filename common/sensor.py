"""W7 v1 fixed 32-byte sensor codec; values are uncalibrated int16 channels.

The codec validates representation. The dummy-inference consumer separately
checks that values equal ``dummy_values(seq)``; real int16 samples still decode.
"""

from dataclasses import dataclass
import struct
from typing import Tuple


_PACKET = struct.Struct("<2sBBIII8h")
PACKET_SIZE = _PACKET.size
SENSOR_CHARACTERISTIC_UUID = "6e1c0005-7a45-4dc4-b678-3f2d5a9c1001"


def _integer(value, minimum: int, maximum: int, name: str) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("{} must be an integer in [{}, {}]".format(name, minimum, maximum))


@dataclass(frozen=True)
class SensorPacket:
    device_id: int
    boot_id: int
    seq: int
    uptime_ms: int
    values: Tuple[int, ...]

    def __post_init__(self) -> None:
        _integer(self.device_id, 1, 2, "device_id")
        for name in ("boot_id", "seq", "uptime_ms"):
            _integer(getattr(self, name), 0, 0xFFFFFFFF, name)
        if not isinstance(self.values, (list, tuple)) or len(self.values) != 8:
            raise ValueError("values must contain exactly eight int16 integers")
        for value in self.values:
            _integer(value, -32768, 32767, "channel")
        object.__setattr__(self, "values", tuple(self.values))

    def to_message(self, session_id: str) -> dict:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a nonempty string")
        return {
            "v": 1,
            "type": "SENSOR_BATCH",
            "session_id": session_id,
            "device_id": self.device_id,
            "boot_id": self.boot_id,
            "seq": self.seq,
            "uptime_ms": self.uptime_ms,
            "values": list(self.values),
        }


def encode_packet(packet: SensorPacket) -> bytes:
    if not isinstance(packet, SensorPacket):
        raise ValueError("packet must be a SensorPacket")
    return _PACKET.pack(
        b"W7", 1, packet.device_id, packet.boot_id, packet.seq, packet.uptime_ms,
        *packet.values
    )


def decode_packet(data: bytes) -> SensorPacket:
    if not isinstance(data, (bytes, bytearray, memoryview)) or len(data) != PACKET_SIZE:
        raise ValueError("W7 packet must contain exactly 32 bytes")
    magic, version, device_id, boot_id, seq, uptime_ms, *values = _PACKET.unpack(data)
    if magic != b"W7":
        raise ValueError("invalid W7 packet magic")
    if version != 1:
        raise ValueError("unsupported W7 packet version")
    return SensorPacket(device_id, boot_id, seq, uptime_ms, tuple(values))


def dummy_values(seq: int) -> Tuple[int, ...]:
    _integer(seq, 0, 0xFFFFFFFF, "seq")
    base = (seq % 2000) - 1000
    return tuple(base + 10 * index for index in range(8))
