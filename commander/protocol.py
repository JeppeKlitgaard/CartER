from __future__ import annotations
from datetime import time

import struct
from typing import Optional, Dict, Any, ForwardRef, Type, TypeVar
from abc import ABC, abstractmethod
from commander.serial import Connection

T = TypeVar("T")


class PacketHandler:
    def __init__(self) -> None:
        pass


class Packet(ABC):
    id_: bytes
    connection: Connection
    is_constructed: bool = False

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    @abstractmethod
    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        ...

    @classmethod
    @abstractmethod
    def read(cls: Type[Packet]) -> Packet: ...


class PingPacket(Packet):
    id_: bytes = bytes(0x70)

    timestamp: Optional[int] = None

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["timestamp"], int)
        self.timestamp = kwargs.pop("timestamp")

        self.is_constructed = True

    def read(self) -> None:
        timestamp, = struct.unpack("L", self.connection._serial)

        self.construct(timestamp=timestamp)


def __filter_packet_subclasses(cls: Type[T]) -> bool:
    return Packet in getattr(cls, "__bases__", list())


PACKET_ID_MAP: Dict[bytes, Type[Packet]] = {
    cls.id_: cls for (clsname, cls) in globals().items() if __filter_packet_subclasses(cls)
}
