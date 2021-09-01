import logging
from time import sleep
from typing import Optional

from serial import Serial

from commander.network.utils import bytes_to_hex_ascii_str, bytes_to_hexstr

logger = logging.getLogger(__name__)


class PacketReadError(ConnectionError):
    """
    Raised when an error occurs while reading a packet.
    """

    def __init__(
        self,
        message: str,
        id_: bytes,
        reason: Optional[str] = None,
        dump_buf: Optional[Serial] = None,
        wait_buf: float = 0.100,
    ) -> None:
        id_ascii = id_.decode("ascii", errors="ignore")
        id_hex = bytes_to_hexstr(id_, prefix=True)

        message = f"Packet with id {id_ascii} ({id_hex}) failed: {message}. {reason or ''}"

        if dump_buf is not None:
            sleep(wait_buf)

            rest_of_data = dump_buf.read_all()

            hex_str, ascii_str = bytes_to_hex_ascii_str(rest_of_data)

            logger.warn("Rest of data (HEX)  : " + hex_str)
            logger.warn("Rest of data (ASCII): " + ascii_str)

        super().__init__(message)
