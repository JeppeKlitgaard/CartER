"""
Contains the networking logic for communication with the Controller.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, cast

from serial import Serial

from commander.network.constants import CartID, SetOperation
from commander.network.utils import Format, byte, pack, unpack


class Packet(ABC):
    id_: bytes
    is_constructed: bool = False

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


class InboundOnlyPacket(Packet):
    """
    InboundOnlyPackets are packets that the commander will only ever receive.

    Writing the serialisation method could be easily done,
    but wouldn't ever be useful.
    """

    def _to_bytes(self) -> bytes:
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

    def read(self, serial: Serial) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} is an outbound only packet. "
            "It does not have a deserialisation method."
        )


class OnlyIDPacket(Packet):
    """
    A packet that has no attributes apart from its ID.
    """

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        self.is_constructed = True

    def read(self, serial: Serial) -> None:
        self.construct()

    def _to_bytes(self) -> bytes:
        return self.id_


class NullPacket(OnlyIDPacket):
    id_ = byte(0x00)  # NUL


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
        timestamp = unpack(Format.UINT_32, serial)

        self.construct(timestamp=timestamp)

    def _to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.UINT_32, self.timestamp)

        return bytes_


class PongPacket(PingPacket):
    id_ = byte(0x50)  # P


class SetPositionPacket(OutboundOnlyPacket):
    id_ = byte(0x78)  # x

    operation: Optional[SetOperation] = None
    cart_id: Optional[CartID] = None
    value: Optional[int] = None  # In steps

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["operation"], SetOperation)
        assert isinstance(kwargs["cart_id"], int)
        assert isinstance(kwargs["value"], int)

        self.operation = kwargs.pop("operation")
        self.cart_id = kwargs.pop("cart_id")
        self.value = kwargs.pop("value")

        self.is_constructed = True

    def _to_bytes(self) -> bytes:
        bytes_ = b""

        bytes_ += self.id_
        bytes_ += pack(Format.ASCII_CHAR, cast(str, self.operation.value))
        bytes_ += pack(Format.UINT_8, cast(int, self.cart_id.value))
        bytes_ += pack(Format.INT_16, cast(int, self.value))

        return bytes_


class GetPositionPacket(InboundOnlyPacket):
    id_ = byte(0x58)  # X

    position_steps: Optional[int] = None
    position_mm: Optional[float] = None

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["position_steps"], int)
        assert isinstance(kwargs["position_mm"], float)

        self.position_steps = kwargs.pop("position_steps")
        self.position_mm = kwargs.pop("position_mm")

        self.is_constructed = True

    def read(self, serial: Serial) -> None:
        position_steps = unpack(Format.INT_32, serial)
        position_mm = unpack(Format.FLOAT_32, serial)

        self.construct(position_steps=position_steps, position_mm=position_mm)


class SetVelocityPacket:
    id_ = byte(0x76)  # v


class GetVelocityPacket(Packet):
    id_ = byte(0x76)  # V


class FindLimitsPacket(OnlyIDPacket):
    id_ = byte(0x7C)  # | (vertical bar)


class CheckLimitPacket(OnlyIDPacket):
    id_ = byte(0x2F)  # / (forward slash)


class ObservationPacket(InboundOnlyPacket):
    id_ = byte(0x40)  # @

    timestamp_micros: Optional[int] = None
    cart_id: Optional[CartID] = None
    position_steps: Optional[int] = None
    angle: Optional[float] = None

    def construct(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        assert isinstance(kwargs["timestamp_micros"], int)
        assert isinstance(kwargs["cart_id"], int)
        assert isinstance(kwargs["position_steps"], int)
        assert isinstance(kwargs["angle"], float)

        self.timestamp_micros = kwargs.pop("timestamp_micros")
        self.cart_id = kwargs.pop("cart_id")
        self.position_steps = kwargs.pop("position_steps")
        self.angle = kwargs.pop("angle")

        self.is_constructed = True

    def read(self, serial: Serial) -> None:
        timestamp_micros = unpack(Format.UINT_32, serial)
        cart_id = unpack(Format.UINT_32, serial)
        position_steps = unpack(Format.INT_32, serial)
        angle = unpack(Format.FLOAT_32, serial)

        self.construct(
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
