import datetime as dt
import logging
from pathlib import Path
from typing import Type

from commander.network.protocol import InboundPacket, ObservationPacket


class ReadPacketFilter(logging.Filter):
    def __init__(self, excludes: tuple[Type[InboundPacket]]) -> None:
        self.excludes = excludes

    def filter(self, record: logging.LogRecord) -> bool:
        # Ignore non-packet type records
        if not hasattr(record, "packet"):
            return True

        if isinstance(record.packet, self.excludes):  # type: ignore[attr-defined]
            return False

        return True


def setup_logging(console: bool = True, file: bool = True) -> None:
    now = dt.datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

    if console:
        console_formatter = logging.Formatter("%(name)-30s: %(levelname)-8s %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)

        logging.root.addHandler(console_handler)

    if file:
        file_formatter = logging.Formatter("%(asctime)s %(name)-30s %(levelname)-8s %(message)s")
        file_path = Path("logs") / f"commander_{now_str}.log"
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        logging.root.addHandler(file_handler)

    logging.root.setLevel(logging.DEBUG)

    logging.getLogger("numba").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    packet_excludes = (ObservationPacket,)
    pkt_filter = ReadPacketFilter(packet_excludes)

    for handler in logging.root.handlers:
        handler.addFilter(pkt_filter)

    logging.debug("Sat up logging...")
