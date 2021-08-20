from serial import Serial
from commander.network.utils import bytes_to_hexstr
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PacketReadError(ConnectionError):
    """
    Raised when an error occurs while reading a packet.
    """

    @staticmethod
    def _buf_str_to_spaced_ascii(buf_str: str) -> str:
        ascii_str = "".join([f" {char} " for char in buf_str])

        return ascii_str

    def __init__(self, message: str, id_: bytes, reason: Optional[str] = None, dump_buf: Optional[Serial] = None) -> None:
        id_ascii = id_.decode("ascii", errors="ignore")
        id_hex = bytes_to_hexstr(id_, prefix=True)

        message = f"Packet with id {id_ascii} ({id_hex}) failed: {message}. {reason or ''}"

        if dump_buf is not None:
            rest_of_data = dump_buf.read_all()

            buf_str = rest_of_data.decode("ascii", errors="ignore")

            hex_str = bytes_to_hexstr(rest_of_data, prefix=False)
            ascii_str = self._buf_str_to_spaced_ascii(buf_str=buf_str)
            logger.warn("Rest of data (HEX)  : " + hex_str)
            logger.warn("Rest of data (ASCII): " + ascii_str)

        super().__init__(message)
