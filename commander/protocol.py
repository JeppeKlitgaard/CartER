from __future__ import annotations

import struct
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Type

if TYPE_CHECKING:
    from commander.serial import Connection


class Packet(ABC):
    id_: bytes
    connection: "Connection"
    is_constructed: bool = False

    def __init__(self, connection: "Connection") -> None:
        self.connection = connection

    @abstractmethod
    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def read(self) -> None:
        ...


class PingPacket(Packet):
    id_: bytes = bytes([0x70])

    timestamp: Optional[int] = None

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["timestamp"], int)
        self.timestamp = kwargs.pop("timestamp")

        self.is_constructed = True

    def read(self) -> None:
        (timestamp,) = struct.unpack("L", self.connection._serial)

        self.construct(timestamp=timestamp)


class PongPacket(PingPacket):
    id_: bytes = bytes([0x50])


def __is_packet_subclass(cls: Any) -> bool:
    try:
        return issubclass(cls, Packet) and cls is not Packet
    except TypeError:
        return False


PACKET_ID_MAP: Dict[bytes, Type[Packet]] = {
    cls.id_: cls for (clsname, cls) in globals().items() if __is_packet_subclass(cls)
}
