"""
Contains utilities for turning Python datatypes into byte-level networking
datatypes.

Note: All types are little-endian when transferred.
"""
import struct
from enum import Enum
from typing import Literal, Union, cast, overload

from serial import Serial

ENDIANNESS = "<"  # Little endian


class Format(str, Enum):
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


PackableT = Union[str, int, float, bytes]
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


def unpack(
    fmt: Union[StringFormats, IntFormats, FloatFormats, ByteFormats], serial: Serial
) -> UnpackableT:
    """
    Wraps struct.unpack to make calcsizing easier.

    Note: Only unpacks a single data type at a time
    """
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
