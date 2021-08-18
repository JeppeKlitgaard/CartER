"""
Contains the networking logic for communication with the Controller.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from inspect import isabstract
from typing import Any, Dict, Optional, Type, Union

from serial import Serial
from typing_extensions import TypeGuard

from commander.network.constants import CartID, SetOperation
from commander.network.utils import (
    CRLF,
    Format,
    _stringify_self,
    byte,
    bytes_to_hexstr,
    pack,
    skip_crlf,
    unpack,
)


class Packet(ABC):
    id_: bytes

    @abstractmethod
    def __init__(self) -> None:
        ...

    def _get_local_properties(self) -> dict[str, Any]:
        properties = {}
        for key in dir(self):
            value = getattr(self, key)

            if key.startswith("_"):
                continue

            if callable(value):
                continue

            properties[key] = value

        return properties


class InboundPacket(Packet):
    """
    InboundPackets are packets that the commander will only ever receive.

    Writing the serialisation method could be easily done,
    but wouldn't ever be useful.
    """

    read_time: Optional[dt.datetime] = None

    @classmethod
    def read(cls, serial: Serial) -> InboundPacket:
        read_time = dt.datetime.now()

        packet = cls._read(serial=serial)
        packet.read_time = read_time

        return packet

    @classmethod
    @abstractmethod
    def _read(cls, serial: Serial) -> InboundPacket:
        ...

    def __repr__(self) -> str:
        return _stringify_self(self)


class OutboundPacket(Packet):
    """
    OutboundPackets are packets that the commander will only ever transmit.

    Writing the deserialisation method could be easily done,
    but wouldn't ever be useful.
    """

    @abstractmethod
    def to_bytes(self) -> bytes:
        ...

    def to_hexstr(self) -> str:
        return bytes_to_hexstr(self.to_bytes())

    def __repr__(self) -> str:
        return _stringify_self(self)


class BidirectionalPacket(InboundPacket, OutboundPacket):
    """
    BidirectionalPackets are packets that both the controller and commander
    should be able to send and receive.
    """

    def __repr__(self) -> str:
        return _stringify_self(self)


class OnlyIDPacket(BidirectionalPacket):
    """
    A packet that has no attributes apart from its ID.
    """

    def __repr__(self) -> str:
        return _stringify_self(self)

    def __init__(self) -> None:
        ...

    @classmethod
    def _read(cls, serial: Serial) -> OnlyIDPacket:
        return cls()

    def to_bytes(self) -> bytes:
        return self.id_


class NullPacket(OnlyIDPacket):
    id_ = byte(0x00)  # NUL


class UnknownPacket(BidirectionalPacket):
    id_ = byte(0x3F)  # ?

    def __init__(self, observed_id: bytes) -> None:
        self.observed_id = observed_id

    @classmethod
    def _read(self, serial: Serial) -> UnknownPacket:
        raise NotImplementedError("UnknownPacket does not have a read method.")

    def to_bytes(self) -> bytes:
        raise NotImplementedError("UnknownPacket does not have a to_bytes method.")


class MessagePacketBase(BidirectionalPacket):
    def __repr__(self) -> str:
        return _stringify_self(self)

    def __init__(self, msg: str) -> None:
        self.msg = msg

    @classmethod
    def _read(cls, serial: Serial) -> MessagePacketBase:
        msg = unpack(Format.STRING, serial)
        skip_crlf(serial)

        return cls(msg=msg)

    def to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.STRING, self.msg)
        bytes_ += CRLF

        return bytes_


class DebugPacket(MessagePacketBase):
    id_ = byte(0x23)  # #


class InfoPacket(MessagePacketBase):
    id_ = byte(0x7E)  # ~


class ErrorPacket(MessagePacketBase):
    id_ = byte(0x21)  # !


class PingPongBasePacket(BidirectionalPacket):
    def __repr__(self) -> str:
        return _stringify_self(self)

    def __init__(self, timestamp: int) -> None:
        self.timestamp = timestamp

    @classmethod
    def _read(cls, serial: Serial) -> PingPongBasePacket:
        timestamp = unpack(Format.UINT_32, serial)

        return cls(timestamp=timestamp)

    def to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.UINT_32, self.timestamp)

        return bytes_


class PingPacket(PingPongBasePacket):
    id_ = byte(0x70)  # p


class PongPacket(PingPongBasePacket):
    id_ = byte(0x50)  # P


class RequestDebugInfoPacket(OnlyIDPacket):
    id_ = byte(0x24)  # $


class SetQuantityPacket(OutboundPacket):
    def __repr__(self) -> str:
        return _stringify_self(self)

    def __init__(self, operation: SetOperation, cart_id: CartID, value: int) -> None:
        self.operation = operation
        self.cart_id = cart_id
        self.value = value

    def to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.ASCII_CHAR, self.operation.value)
        bytes_ += pack(Format.UINT_8, self.cart_id.value)
        bytes_ += pack(Format.INT_16, self.value)

        return bytes_


class SetPositionPacket(SetQuantityPacket):
    id_ = byte(0x78)  # x


# ! Currently unused
class GetPositionPacket(InboundPacket):
    id_ = byte(0x58)  # X

    def __init__(self, value_steps: int, value_mm: float) -> None:
        self.value_steps = value_steps
        self.value_mm = value_mm

    @classmethod
    def _read(cls, serial: Serial) -> GetPositionPacket:
        value_steps = unpack(Format.INT_32, serial)
        value_mm = unpack(Format.FLOAT_32, serial)

        return cls(value_steps=value_steps, value_mm=value_mm)


class SetVelocityPacket(SetQuantityPacket):
    id_ = byte(0x76)  # v


# ! Currently unused
class GetVelocityPacket(GetPositionPacket):
    id_ = byte(0x56)  # V


class FindLimitsPacket(OnlyIDPacket):
    """
    Instructs the controller to do a limit finding routine.

    Controller will return a `FindLimitsPacket` when limit finding is done.
    """

    id_ = byte(0x7C)  # | (vertical bar)


class CheckLimitPacket(OnlyIDPacket):
    """
    Instructs the controller to do a limit checking routine.

    Controller will return a `CheckLimitPacket` when the limit checking is done."""

    id_ = byte(0x2F)  # / (forward slash)


class DoJigglePacket(OnlyIDPacket):
    """
    Instructs the controller to do a jiggle in order to get pendulum arm
    to point straight down, at which point an angle offset can be calculated.

    Controller will return a `DoJigglePacket` when the jiggling is done.
    """

    id_ = byte(0xA7)  # § (section)


class ObservationPacket(InboundPacket):
    id_ = byte(0x40)  # @

    def __init__(
        self, timestamp_micros: int, cart_id: CartID, position_steps: int, angle: float
    ) -> None:
        self.timestamp_micros = timestamp_micros
        self.cart_id = cart_id
        self.position_steps = position_steps
        self.angle = angle

    @classmethod
    def _read(cls, serial: Serial) -> ObservationPacket:
        timestamp_micros = unpack(Format.UINT_32, serial)
        cart_id = CartID(unpack(Format.UINT_8, serial))
        position_steps = unpack(Format.INT_32, serial)
        angle = unpack(Format.FLOAT_32, serial)

        return cls(
            timestamp_micros=timestamp_micros,
            cart_id=cart_id,
            position_steps=position_steps,
            angle=angle,
        )


class ExperimentStartPacket(BidirectionalPacket):
    id_ = byte(0x02)  # STX

    def __init__(self, timestamp_micros: int):
        self.timestamp_micros = timestamp_micros

    @classmethod
    def _read(cls, serial: Serial) -> ExperimentStartPacket:
        timestamp_micros = unpack(Format.UINT_32, serial)

        return cls(timestamp_micros=timestamp_micros)

    def to_bytes(self) -> bytes:
        bytes = b""

        bytes += self.id_
        bytes += pack(Format.UINT_32, self.timestamp_micros)

        return bytes


class ExperimentStopPacket(OnlyIDPacket):
    id_ = byte(0x03)  # ETX


class ExperimentDonePacket(BidirectionalPacket):
    ...


class ExperimentInfoPacket(InboundPacket):
    ...


CartSpecificPacket = Union[ObservationPacket]


def is_valid_packet(cls: Type[object]) -> TypeGuard[Type[Packet]]:
    try:
        conditions = (
            issubclass(cls, Packet),
            cls is not Packet,
            hasattr(cls, "id_"),
        )

        return all(conditions)

    except TypeError:
        return False


def is_valid_inbound_packet(cls: Type[object]) -> TypeGuard[Type[InboundPacket]]:
    try:
        conditions = (
            issubclass(cls, InboundPacket),
            cls is not InboundPacket,
            not isabstract(cls),
            hasattr(cls, "id_"),
        )

        return all(conditions)

    except TypeError:
        return False


PACKET_ID_MAP: Dict[bytes, Type[Packet]] = {
    cls.id_: cls for cls in globals().values() if is_valid_packet(cls)
}

INBOUND_PACKET_ID_MAP: Dict[bytes, Type[InboundPacket]] = {
    cls.id_: cls for cls in globals().values() if is_valid_inbound_packet(cls)
}
