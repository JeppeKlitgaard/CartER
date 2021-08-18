import random
from collections.abc import Callable
from logging import getLogger
from time import sleep
from typing import Literal, Optional, Sequence, Type, Union, cast, overload

from serial import Serial

from commander.network.protocol import (
    INBOUND_PACKET_ID_MAP,
    InboundPacket,
    OutboundPacket,
    Packet,
    PingPacket,
    PongPacket,
)
from commander.network.types import PacketSelector, PacketT
from commander.network.utils import bytes_to_hexes, bytes_to_hexstr
from commander.utils import noop

logger = getLogger(__name__)

PORT: str = "COM3"
BAUDRATE: int = 74880

DigestCallback = Callable[[], None]


class NetworkManager:
    INITIAL_OUTPUT_STOP_MARKER: bytes = "END OF INITIALISATION\n".encode("ascii")

    def __init__(self, port: str = "COM3", baudrate: int = 74880):
        self.serial = Serial()
        self.serial.port = port
        self.serial.baudrate = baudrate

        self.packet_buffer: list[Packet] = []

    def open(self) -> None:
        self.serial.open()

    def close(self) -> None:
        self.serial.close()

    def tick(self) -> None:
        pass

    @property
    def in_queue(self) -> int:
        return cast(int, self.serial.in_waiting)

    def read_initial_output(self) -> str:
        self.serial.timeout = 0.1

        read_bytes = b""

        while not read_bytes.endswith(self.INITIAL_OUTPUT_STOP_MARKER):
            new_bytes = self.serial.read_until(self.INITIAL_OUTPUT_STOP_MARKER)
            read_bytes += new_bytes

            print(new_bytes.decode("ascii", errors="ignore"), end="")

        self.serial.timeout = None

        # sleep 25ms and then flush buffers
        sleep(0.025)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        return read_bytes.decode("ascii", errors="ignore")

    def _cpp_initial_output_decl(self) -> str:
        hexes = bytes_to_hexes(self.INITIAL_OUTPUT_STOP_MARKER)

        hex_str = ", ".join(hexes)
        hex_len_str = str(len(hexes))

        output = ""
        output += "const size_t INITIAL_OUTPUT_STOP_MARKER_LENGTH = " + hex_len_str + ";"
        output += "\n"
        output += "const byte INITIAL_OUTPUT_STOP_MARKER[" + hex_len_str + "] = {" + hex_str + "};"

        return output

    def assert_ping_pong(self) -> None:
        """
        Does a Ping ⟷ Pong connection check.

        Raises assertion error if something is wrong.
        """
        # Send ping to ensure we have good connection
        checksum = random.randint(0, 2 ** 32 - 1)
        ping_pkt = PingPacket(timestamp=checksum)
        self.send_packet(ping_pkt)

        # Verify pong
        pong_pkt = self.get_packet(PongPacket, block=True)
        assert pong_pkt.timestamp == checksum

    def read_packet(self) -> InboundPacket:
        id_ = self.serial.read(1)

        try:
            packet_cls = INBOUND_PACKET_ID_MAP[id_]
        except KeyError:
            rest_of_data = self.serial.read_all()
            rest_of_data_str = rest_of_data.decode("ascii", "replace")

            hex_str = bytes_to_hexstr(rest_of_data, prefix=False)
            ascii_str = "".join([f" {char} " for char in rest_of_data_str])

            logger.warn("Rest of data (HEX)  : " + hex_str)
            logger.warn("Rest of data (ASCII): " + ascii_str)

            err = f"Invalid packet ID: {id_}."

            raise ConnectionError(err)

        packet = packet_cls.read(self.serial)
        return packet

    def read_packets(self, block: bool = False) -> list[Packet]:
        packets: list[Packet] = []

        while self.serial.in_waiting or (block and not packets):
            packets.append(self.read_packet())

        return packets

    def dump_packets(self, *, digest: bool = True, continuous: bool = False) -> None:
        if continuous and not digest:
            raise ValueError("Invalid combination of arguments. Must digest to be continuous")

        while True:
            packets = self.get_packets(digest=digest)

            for packet in packets:
                print(packet)

            if not continuous:
                break

    def digest(self, block: bool = False) -> None:
        """
        Digests all the packets currently waiting to be read and stores them
        in the internal packet buffer.
        """
        packets = self.read_packets(block=block)

        self.packet_buffer.extend(packets)

    def printer_callback(
        self, *, pop: bool = True, excepts: Union[Type[Packet], tuple[Type[Packet]]]
    ) -> DigestCallback:
        """
        Can be used as a callback to pop and print all digested packets.
        """

        def inner() -> None:
            for packet in self.get_packets(digest=False):
                if isinstance(packet, excepts):
                    self.packet_buffer.append(packet)
                    continue

                print(packet)

        return inner

    @overload
    def get_packet(
        self,
        packet_type: Optional[Type[PacketT]] = None,
        selector: Optional[PacketSelector[PacketT]] = None,
        *,
        pop: bool = True,
        digest: Literal[True] = True,
        block: Literal[True] = True,
        callback: Callable[..., None] = noop,
        _excludes: Optional[Sequence[PacketT]] = None,
    ) -> PacketT:
        ...

    @overload
    def get_packet(
        self,
        packet_type: Optional[Type[PacketT]] = None,
        selector: Optional[PacketSelector[PacketT]] = None,
        *,
        pop: bool = True,
        digest: bool = True,
        block: Literal[False] = False,
        callback: Callable[..., None] = noop,
        _excludes: Optional[Sequence[PacketT]] = None,
    ) -> Optional[PacketT]:
        ...

    @overload
    def get_packet(
        self,
        packet_type: Optional[Type[PacketT]] = None,
        selector: Optional[PacketSelector[PacketT]] = None,
        *,
        pop: bool = True,
        digest: bool = True,
        block: bool = False,
        callback: Callable[..., None] = noop,
        _excludes: Optional[Sequence[PacketT]] = None,
    ) -> Optional[PacketT]:
        ...

    def get_packet(
        self,
        packet_type: Optional[Type[PacketT]] = None,
        selector: Optional[PacketSelector[PacketT]] = None,
        *,
        pop: bool = True,
        digest: bool = True,
        block: bool = False,
        callback: DigestCallback = noop,
        _excludes: Optional[Sequence[PacketT]] = None,
    ) -> Optional[PacketT]:
        """
        Pops a packet from the internel buffer.

        Can be selective in which packet to pop, and block until the packet arrives.

        If defined, `callback` is called after every digest.
        """

        if block and not digest:
            raise ValueError("Invalid combination of arguments. If blocking, must digest")

        if _excludes is None:
            _excludes = []

        if digest:
            self.digest()
            callback()

        # Try to look for packet in buffer
        packet: Optional[PacketT] = None
        while True:
            for trial in self.packet_buffer:

                # Skip if not right type
                if packet_type is not None and not isinstance(trial, packet_type):
                    continue

                trial = cast(PacketT, trial)

                # Skip if not right attributes
                if selector is not None and not selector(trial):
                    continue

                if packet in _excludes:
                    continue

                # We have a match
                packet = trial

                if pop:
                    self.packet_buffer.remove(packet)

                break

            # Wait for packet if blocking
            if packet is None and block:
                self.digest()
                callback()
            else:
                break

        return packet

    @overload
    def get_packets(
        self,
        packet_type: Literal[None] = None,
        selector: Optional[PacketSelector[PacketT]] = None,
        *,
        pop: bool = True,
        digest: bool = True,
        block: bool = False,
        callback: DigestCallback = noop,
    ) -> list[Packet]:
        ...

    @overload
    def get_packets(
        self,
        packet_type: Type[PacketT],
        selector: Optional[PacketSelector[PacketT]] = None,
        *,
        pop: bool = True,
        digest: bool = True,
        block: bool = False,
        callback: DigestCallback = noop,
    ) -> list[PacketT]:
        ...

    def get_packets(
        self,
        packet_type: Optional[Type[PacketT]] = None,
        selector: Optional[PacketSelector[PacketT]] = None,
        *,
        pop: bool = True,
        digest: bool = True,
        block: bool = False,
        callback: DigestCallback = noop,
    ) -> Union[list[PacketT], list[Packet]]:

        packets: list[PacketT] = []

        while True:
            packet = self.get_packet(
                packet_type=packet_type,
                selector=selector,
                pop=pop,
                digest=digest,
                block=block,
                callback=callback,
                _excludes=packets,
            )

            if packet is None:
                return packets

            packets.append(packet)

    def send_packet(self, packet: OutboundPacket) -> None:
        bytes_to_transfer = packet.to_bytes()

        self.serial.write(bytes_to_transfer)
