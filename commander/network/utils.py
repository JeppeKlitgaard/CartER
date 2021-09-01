"""
Contains utilities for turning Python datatypes into byte-level networking
datatypes.

Note: All types are little-endian when transferred.
"""
import struct
from enum import Enum, unique
from typing import TYPE_CHECKING, Literal, Union, cast, overload

from serial import Serial

if TYPE_CHECKING:
    from commander.network.protocol import Packet

ENDIANNESS = "<"  # Little endian

CRLF: bytes = "\r\n".encode("ascii")


@unique
class Format(str, Enum):
    NUL = "_"

    CHAR = "c"

    INT_8 = "b"
    UINT_8 = "B"

    INT_16 = ENDIANNESS + "h"
    UINT_16 = ENDIANNESS + "H"

    INT_32 = ENDIANNESS + "i"
    UINT_32 = ENDIANNESS + "I"

    INT_64 = ENDIANNESS + "q"
    UINT_64 = ENDIANNESS + "Q"

    FLOAT_32 = ENDIANNESS + "f"
    FLOAT_64 = ENDIANNESS + "d"

    STRING = "S"  # home-made
    ASCII_CHAR = "A"  # home-made


PackableT = Union[str, int, float, bytes, None]
UnpackableT = PackableT

StringFormats = Literal[Format.STRING, Format.ASCII_CHAR]
IntFormats = Literal[
    Format.INT_8,
    Format.UINT_8,
    Format.INT_16,
    Format.UINT_16,
    Format.INT_32,
    Format.UINT_32,
    Format.INT_64,
    Format.UINT_64,
]
FloatFormats = Literal[Format.FLOAT_32, Format.FLOAT_64]
ByteFormats = Literal[Format.CHAR]
NulFormats = Literal[Format.NUL]

Formats = Union[StringFormats, IntFormats, FloatFormats, ByteFormats, NulFormats, Format]


def _stringify_self(self: "Packet") -> str:
    properties = {}
    for key in dir(self):
        value = getattr(self, key)

        if key.startswith("_"):
            continue

        if callable(value):
            continue

        properties[key] = value

    prop_strs = [f"{k}: {v}" for (k, v) in properties.items()]
    prop_str = ", ".join(prop_strs)

    return f"<{self.__class__.__name__}: {prop_str}>"


@overload
def unpack(fmt: NulFormats, serial: Serial) -> None:
    ...


@overload
def unpack(fmt: StringFormats, serial: Serial) -> str:
    ...


@overload
def unpack(fmt: IntFormats, serial: Serial) -> int:
    ...


@overload
def unpack(fmt: FloatFormats, serial: Serial) -> float:
    ...


@overload
def unpack(fmt: ByteFormats, serial: Serial) -> bytes:
    ...


@overload
def unpack(fmt: Format, serial: Serial) -> UnpackableT:
    ...


def unpack(fmt: Formats, serial: Serial) -> UnpackableT:
    """
    Wraps struct.unpack to make calcsizing easier.

    Note: Only unpacks a single data type at a time
    """
    if fmt is Format.NUL:
        return None

    # Special case: string
    if fmt is Format.STRING:
        # String consists of an size_t (ulong on Due)
        # And then that many characters of ASCII formatted characters
        size_str = unpack(Format.UINT_32, serial)
        fmt_str = str(size_str) + "s"

        size = struct.calcsize(fmt_str)
        buf = serial.read(size)
        msg_bytes = cast(bytes, struct.unpack(fmt_str, buf)[0])

        return msg_bytes.decode("ascii")

    if fmt is Format.ASCII_CHAR:
        obj = unpack(Format.CHAR, serial)

        return obj.decode("ascii")

    fmt_str = fmt.value

    size = struct.calcsize(fmt_str)
    buf = serial.read(size)
    return cast(UnpackableT, struct.unpack(fmt_str, buf)[0])


def pack(fmt: Union[Format, str], obj: PackableT) -> bytes:
    if fmt is Format.NUL:
        return b""

    if fmt is Format.STRING:
        assert isinstance(obj, str)
        size_bytes = pack(Format.UINT_32, len(obj))

        return size_bytes + pack(str(len(obj)) + "s", obj)

    if fmt is Format.ASCII_CHAR:
        assert isinstance(obj, str)
        assert len(obj) == 1

        return obj.encode("ascii")

    if isinstance(fmt, Format):
        fmt = fmt.value

    return struct.pack(fmt, obj)


def byte(num: int) -> bytes:
    return bytes([num])


def bytes_to_hexes(bytes_: bytes, prefix: bool = True) -> list[str]:
    hex_space_str = bytes_.hex(" ")
    hexes = hex_space_str.split(" ")
    hexes = [hex.upper() for hex in hexes]

    if prefix:
        hexes = ["0x" + hex for hex in hexes]

    return hexes


def bytes_to_hexstr(bytes_: bytes, prefix: bool = True) -> str:
    hexes = bytes_to_hexes(bytes_, prefix)

    return " ".join(hexes)


def skip_crlf(serial: Serial) -> None:
    crlf = serial.read(2)

    if crlf != CRLF:
        raise ValueError(f"CRLF misaligned. Was actually: {bytes_to_hexstr(crlf)}")
