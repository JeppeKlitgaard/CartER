"""
Contains the networking logic for communication with the Controller.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from serial import Serial

from commander.network.utils import Format, unpack, pack, byte


class Packet(ABC):
    id_: bytes
    is_constructed: bool = False

    def __init__(self) -> None:
        ...

    @abstractmethod
    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def read(self, serial: Serial) -> None:
        ...

    def to_bytes(self) -> bytes:
        if not self.is_constructed:
            raise RuntimeError(
                "Packet was not yet fully constructed. Call construct() or read() first"
            )
        return self._to_bytes()

    @abstractmethod
    def _to_bytes(self) -> bytes:
        ...


class NullPacket(Packet):
    id_ = byte(0x00)  # NUL

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        self.is_constructed = True

    def read(self, serial: Serial) -> None:
        self.construct()

    def _to_bytes(self) -> bytes:
        return self.id_


class UnknownPacket(Packet):
    id_ = byte(0x3F)  # ?

    observed_id: Optional[bytes] = None

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["observed_id"], bytes)
        self.observed_id = kwargs.pop("observed_id")

        self.is_constructed = True

    def read(self, serial: Serial) -> None:
        raise NotImplementedError("UnknownPacket does not have a read method.")

    def _to_bytes(self) -> bytes:
        raise NotImplementedError("UnknownPacket does not have a to_bytes method.")


class DebugPacket(Packet):
    id_ = byte(0x7E)  # ~

    msg: Optional[str] = None

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["msg"], str)
        self.msg = kwargs.pop("msg")

        self.is_constructed = True

    def read(self, serial: Serial) -> None:
        msg = unpack(Format.STRING, serial)

        self.construct(msg=msg)

    def _to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.STRING, self.msg)

        return bytes_

class ErrorPacket(DebugPacket):
    id_ = byte(0x21)  # !

class PingPacket(Packet):
    id_ = byte(0x70)  # p

    timestamp: Optional[int] = None

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["timestamp"], int)
        self.timestamp = kwargs.pop("timestamp")

        self.is_constructed = True

    def read(self, serial: Serial) -> None:
        timestamp = unpack(Format.ULONG, serial)

        self.construct(timestamp=timestamp)

    def _to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.ULONG, self.timestamp)

        return bytes_


class PongPacket(PingPacket):
    id_ = bytes([0x50])  # P


def __is_packet_subclass(cls: Any) -> bool:
    try:
        return issubclass(cls, Packet) and cls is not Packet
    except TypeError:
        return False


PACKET_ID_MAP: Dict[bytes, Type[Packet]] = {
    cls.id_: cls for (clsname, cls) in globals().items() if __is_packet_subclass(cls)
}
