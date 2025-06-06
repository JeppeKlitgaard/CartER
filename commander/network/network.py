import random
from collections.abc import Callable
from logging import getLogger
from time import sleep
from typing import Literal, Optional, Sequence, Type, Union, cast, overload

from serial import Serial

from commander.log import EXCLUDE_PACKETS
from commander.network.constants import DEFAULT_BAUDRATE, DEFAULT_PORT
from commander.network.exceptions import PacketReadError
from commander.network.protocol import (
    INBOUND_PACKET_ID_MAP,
    InboundPacket,
    InfoPacket,
    NullPacket,
    OutboundPacket,
    Packet,
    PingPacket,
    PongPacket,
    RequestPacketRealignmentPacket,
)
from commander.network.types import PacketSelector, PacketT
from commander.network.utils import bytes_to_hex_ascii_str, bytes_to_hexes
from commander.utils import noop

logger = getLogger(__name__)

DigestCallback = Callable[[], None]


class NetworkManager:
    INITIAL_OUTPUT_STOP_MARKER: bytes = InfoPacket("END OF INITIALISATION\n").to_bytes()
    PACKET_REALIGNMENT_SEQUENCE: bytes = InfoPacket(
        "=*= Please realign packets here =*=\n"
    ).to_bytes()

    def __init__(self, port: str = DEFAULT_PORT, baudrate: int = DEFAULT_BAUDRATE):
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

    def read_initial_output(self, print_: bool = True) -> str:
        self.serial.timeout = 0.1

        read_bytes = b""

        while not read_bytes.endswith(self.INITIAL_OUTPUT_STOP_MARKER):
            new_bytes = self.serial.read_until(self.INITIAL_OUTPUT_STOP_MARKER)
            read_bytes += new_bytes

            if print_:
                print(new_bytes.decode("ascii", errors="ignore"), end="")

        self.serial.timeout = None

        self.reset_buffers()

        return read_bytes.decode("ascii", errors="ignore")

    def realign_packets(self, print_: bool = True) -> None:
        request_realignment_pkt = RequestPacketRealignmentPacket()
        self.send_packet(request_realignment_pkt)

        flushed_bytes = self.serial.read_until(self.PACKET_REALIGNMENT_SEQUENCE)

        if print_:
            hex_str, ascii_str = bytes_to_hex_ascii_str(flushed_bytes)

            logger.warn("Rest of data (HEX)  : " + hex_str)
            logger.warn("Rest of data (ASCII): " + ascii_str)

    @staticmethod
    def __cpp_decl(var_name: str, seq: bytes) -> str:
        hexes = bytes_to_hexes(seq)

        hex_str = ", ".join(hexes)
        hex_len_str = str(len(hexes))

        decl = ""
        decl += f"const size_t {var_name}_LENGTH = " + hex_len_str + ";"
        decl += "\n"
        decl += f"const byte {var_name}[" + hex_len_str + "] = {" + hex_str + "};"

        return decl

    @classmethod
    def _cpp_initial_output_decl(cls) -> str:
        return cls.__cpp_decl("INITIAL_OUTPUT_STOP_MARKER", cls.INITIAL_OUTPUT_STOP_MARKER)

    @classmethod
    def _cpp_realignment_sequence_decl(cls) -> str:
        return cls.__cpp_decl("PACKET_REALIGNMENT_SEQUENCE", cls.PACKET_REALIGNMENT_SEQUENCE)

    def reset_buffers(self, wait: float = 0.025) -> None:
        # sleep 25ms and then flush buffers
        sleep(wait)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        sleep(wait)

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

    def read_packet(self, auto_realign: bool = True) -> InboundPacket:
        id_ = self.serial.read(1)

        try:
            packet_cls = INBOUND_PACKET_ID_MAP[id_]
        except KeyError as id_exc:
            logger.warn("Received packet with invalid ID: %s", id_)

            if auto_realign:
                logger.info("Attempting packet realignment")

                self.realign_packets()

                return NullPacket()

            else:
                raise PacketReadError("Invalid packet ID", id_, dump_buf=self.serial) from id_exc

        try:
            packet = packet_cls.read(self.serial)
            if not type(packet) in EXCLUDE_PACKETS:
                logger.debug("Read packet: %s", packet, extra={"packet": packet})

        except (PacketReadError, ValueError) as read_exc:
            logger.warn("Failed to read packet. Got exception: %s", read_exc)

            if auto_realign:
                logger.info("Attempting packet realignment")

                self.realign_packets()

                return NullPacket()

            else:
                raise read_exc

        return packet

    def read_packets(self, block: bool = False, auto_realign: bool = True) -> list[Packet]:
        packets: list[Packet] = []

        while self.serial.in_waiting or (block and not packets):
            packets.append(self.read_packet(auto_realign=auto_realign))

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

    def digest(self, block: bool = False, auto_realign: bool = True) -> None:
        """
        Digests all the packets currently waiting to be read and stores them
        in the internal packet buffer.
        """
        packets = self.read_packets(block=block, auto_realign=auto_realign)

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
        auto_realign: bool = True,
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
        auto_realign: bool = True,
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
        auto_realign: bool = True,
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
        auto_realign: bool = True,
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
            self.digest(auto_realign=auto_realign)
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
        auto_realign: bool = True,
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
        auto_realign: bool = True,
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
        auto_realign: bool = True,
    ) -> Union[list[PacketT], list[Packet]]:

        packets: list[PacketT] = []

        while True:
            still_block = block and not bool(packets)

            packet = self.get_packet(
                packet_type=packet_type,
                selector=selector,
                pop=pop,
                digest=digest,
                block=still_block,
                callback=callback,
                auto_realign=auto_realign,
                _excludes=packets,
            )

            if packet is None:
                return packets

            packets.append(packet)

    def send_packet(self, packet: OutboundPacket) -> None:
        logger.debug("Sent packet: %s", packet, extra={"packet": packet})

        bytes_to_transfer = packet.to_bytes()

        self.serial.write(bytes_to_transfer)
