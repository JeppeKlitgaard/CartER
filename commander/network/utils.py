"""
Contains utilities for turning Python datatypes into byte-level networking
datatypes.

Note: All types are little-endian when transferred.
"""
import struct
from enum import Enum
from typing import Union

from serial import Serial

ENDIANNESS = "<"  # Little endian


class Format(str, Enum):
    ULONG = ENDIANNESS + "L"
    LONG = ENDIANNESS + "l"
    STRING = ENDIANNESS + "S"


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
        size_str = unpack(Format.ULONG, serial)
        fmt = str(size_str) + "s"

        msg_bytes = unpack(fmt, serial)

        return msg_bytes.decode("ascii")

    if isinstance(fmt, Format):
        fmt = fmt.value

    size = struct.calcsize(fmt)
    buf = serial.read(size)
    return struct.unpack(fmt, buf)[0]


def pack(fmt: Union[Format, str], obj: PackableT) -> bytes:
    if fmt is Format.STRING:
        size_bytes = pack(Format.ULONG, len(obj))

        return size_bytes + pack(str(len(obj)) + "s")

    if isinstance(fmt, Format):
        fmt = fmt.value

    return struct.pack(fmt, obj)


def byte(num: int) -> bytes:
    return bytes([num])
