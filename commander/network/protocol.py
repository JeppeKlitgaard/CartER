"""
Contains the networking logic for communication with the Controller.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from serial import Serial

from commander.network.constants import CartID, SetOperation
from commander.network.utils import Format, byte, pack, unpack


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

    def __repr__(self) -> str:
        props = [f"{k}| {v}" for (k, v) in self._get_local_properties().items()]
        prop_str = ", ".join(props)

        return f"<{__name__}: {prop_str}>"

    @classmethod
    @abstractmethod
    def read(cls, serial: Serial) -> Packet:
        ...

    @abstractmethod
    def to_bytes(self) -> bytes:
        ...


class InboundOnlyPacket(Packet):
    """
    InboundOnlyPackets are packets that the commander will only ever receive.

    Writing the serialisation method could be easily done,
    but wouldn't ever be useful.
    """

    def to_bytes(self) -> bytes:
        raise NotImplementedError(
            f"{self.__class__.__name__} is an inbound only packet. "
            "It does not have a serialisation method."
        )


class OutboundOnlyPacket(Packet):
    """
    OutboundOnlyPackets are packets that the commander will only ever transmit.

    Writing the deserialisation method could be easily done,
    but wouldn't ever be useful.
    """

    @classmethod
    def read(cls, serial: Serial) -> OutboundOnlyPacket:
        raise NotImplementedError(
            f"{cls.__name__} is an outbound only packet. "
            "It does not have a deserialisation method."
        )


class OnlyIDPacket(Packet):
    """
    A packet that has no attributes apart from its ID.
    """

    def __init__(self) -> None:
        ...

    @classmethod
    def read(cls, serial: Serial) -> OnlyIDPacket:
        return cls()

    def _to_bytes(self) -> bytes:
        return self.id_


class NullPacket(OnlyIDPacket):
    id_ = byte(0x00)  # NUL


class UnknownPacket(Packet):
    id_ = byte(0x3F)  # ?

    def __init__(self, observed_id: bytes) -> None:
        self.observed_id = observed_id

    @classmethod
    def read(self, serial: Serial) -> UnknownPacket:
        raise NotImplementedError("UnknownPacket does not have a read method.")

    def _to_bytes(self) -> bytes:
        raise NotImplementedError("UnknownPacket does not have a to_bytes method.")


class DebugPacket(Packet):
    id_ = byte(0x7E)  # ~

    def __init__(self, msg: str) -> None:
        self.msg = msg

    @classmethod
    def read(cls, serial: Serial) -> DebugPacket:
        msg = unpack(Format.STRING, serial)

        return cls(msg=msg)

    def _to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.STRING, self.msg)

        return bytes_


class ErrorPacket(DebugPacket):
    id_ = byte(0x21)  # !


class PingPacket(Packet):
    id_ = byte(0x70)  # p

    def __init__(self, timestamp: int) -> None:
        self.timestamp = timestamp

    @classmethod
    def read(cls, serial: Serial) -> PingPacket:
        timestamp = unpack(Format.UINT_32, serial)

        return cls(timestamp=timestamp)

    def _to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.UINT_32, self.timestamp)

        return bytes_


class PongPacket(PingPacket):
    id_ = byte(0x50)  # P


class SetPositionPacket(OutboundOnlyPacket):
    id_ = byte(0x78)  # x

    def __init__(self, operation: SetOperation, cart_id: CartID, value: int) -> None:
        self.operation = operation
        self.cart_id = cart_id
        self.value = value

    def _to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.ASCII_CHAR, self.operation.value)
        bytes_ += pack(Format.UINT_8, self.cart_id.value)
        bytes_ += pack(Format.INT_16, self.value)

        return bytes_


#! Currently unused
class GetPositionPacket(InboundOnlyPacket):
    id_ = byte(0x58)  # X

    def __init__(self, value_steps: int, value_mm: float) -> None:
        self.value_steps = value_steps
        self.value_mm = value_mm

    @classmethod
    def read(cls, serial: Serial) -> GetPositionPacket:
        value_steps = unpack(Format.INT_32, serial)
        value_mm = unpack(Format.FLOAT_32, serial)

        return cls(value_steps=value_steps, value_mm=value_mm)


class SetVelocityPacket(SetPositionPacket):
    id_ = byte(0x76)  # v


#! Currently unused
class GetVelocityPacket(GetPositionPacket):
    id_ = byte(0x76)  # V


class FindLimitsPacket(OnlyIDPacket):
    id_ = byte(0x7C)  # | (vertical bar)


class CheckLimitPacket(OnlyIDPacket):
    id_ = byte(0x2F)  # / (forward slash)


class ObservationPacket(InboundOnlyPacket):
    id_ = byte(0x40)  # @

    def __init__(
        self, timestamp_micros: int, cart_id: CartID, position_steps: int, angle: float
    ) -> None:
        self.timestamp_micros = timestamp_micros
        self.cart_id = cart_id
        self.position_steps = position_steps
        self.angle = angle

    @classmethod
    def read(cls, serial: Serial) -> ObservationPacket:
        timestamp_micros = unpack(Format.UINT_32, serial)
        cart_id = CartID(unpack(Format.UINT_32, serial))
        position_steps = unpack(Format.INT_32, serial)
        angle = unpack(Format.FLOAT_32, serial)

        return cls(
            timestamp_micros=timestamp_micros,
            cart_id=cart_id,
            position_steps=position_steps,
            angle=angle,
        )


# Construct PACKET_ID_MAP
def __is_packet_subclass(cls: Any) -> bool:
    try:
        conditions = (
            issubclass(cls, Packet),
            cls is not Packet,
            hasattr(cls, "id_"),
        )

        return all(conditions)

    except TypeError:
        return False


PACKET_ID_MAP: Dict[bytes, Type[Packet]] = {
    cls.id_: cls for (clsname, cls) in globals().items() if __is_packet_subclass(cls)
}