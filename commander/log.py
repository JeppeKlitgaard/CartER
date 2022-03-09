import datetime as dt
import logging
from typing import Sequence, Type

from commander.network.protocol import (
    DebugPacket,
    ErrorPacket,
    InfoPacket,
    ObservationPacket,
    Packet,
    SetVelocityPacket,
)
from commander.utils import get_project_root

EXCLUDE_PACKETS: list[Type[Packet]] = [
    DebugPacket,
    InfoPacket,
    ErrorPacket,
]


class PacketFilter(logging.Filter):
    def __init__(self, excludes: Sequence[Type[Packet]]) -> None:
        self.excludes = tuple(excludes)

    def filter(self, record: logging.LogRecord) -> bool:
        # Ignore non-packet type records
        if not hasattr(record, "packet"):
            return True

        if isinstance(record.packet, self.excludes):  # type: ignore[attr-defined]
            return False

        return True


def setup_logging(
    command: str = "", console: bool = True, file: bool = True, debug: bool = False
) -> None:
    now = dt.datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

    command_str = "_" + command if command else ""

    if console:
        console_formatter = logging.Formatter("%(name)-30s: %(levelname)-8s %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)

        logging.root.addHandler(console_handler)

    if file:
        project_root_path = get_project_root()

        file_formatter = logging.Formatter("%(asctime)s %(name)-30s %(levelname)-8s %(message)s")
        file_path = project_root_path / "logs" / f"commander_{now_str}{command_str}.log"
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        logging.root.addHandler(file_handler)

    logging.root.setLevel(logging.DEBUG)

    logging.getLogger("numba").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    exclude_packets = EXCLUDE_PACKETS.copy()
    if not debug:
        exclude_packets.extend(
            [
                SetVelocityPacket,
                ObservationPacket,
            ]
        )

    pkt_filter = PacketFilter(exclude_packets)

    for handler in logging.root.handlers:
        handler.addFilter(pkt_filter)

    logging.debug("Sat up logging...")
