"""
Contains utilities for turning Python datatypes into byte-level networking
datatypes.

Note: All types are little-endian when transferred.
"""
import struct
from enum import Enum
from typing import Union, cast

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


PackableT = Union[str, int]
UnpackableT = PackableT


def unpack(fmt: Union[Format, str], serial: Serial) -> UnpackableT:
    """
    Wraps struct.unpack to make calcsizing easier.

    Note: Only unpacks a single data type at a time
    """
    # Special case: string
    if fmt is Format.STRING:
        # String consists of an size_t (ulong on Due)
        # And then that many characters of ASCII formatted characters
        size_str = unpack(Format.UINT_32, serial)
        fmt = str(size_str) + "s"

        msg_bytes = cast(bytes, unpack(fmt, serial))

        return msg_bytes.decode("ascii")

    if fmt is Format.ASCII_CHAR:
        obj = cast(bytes, unpack(Format.CHAR, serial))

        return obj.decode("ascii")

    if isinstance(fmt, Format):
        fmt = fmt.value

    size = struct.calcsize(fmt)
    buf = serial.read(size)
    return cast(UnpackableT, struct.unpack(fmt, buf)[0])


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
