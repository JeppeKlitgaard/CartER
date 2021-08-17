from logging import getLogger
from typing import cast

from serial import Serial

from commander.network.protocol import INBOUND_PACKET_ID_MAP, InboundPacket, OutboundPacket, Packet
from commander.network.utils import bytes_to_hexes, bytes_to_hexstr

logger = getLogger(__name__)

PORT: str = "COM3"
BAUDRATE: int = 74880


class NetworkManager:
    INITIAL_OUTPUT_STOP_MARKER: bytes = "END OF INITIALISATION\n".encode("ascii")

    def __init__(self, port: str = "COM3", baudrate: int = 74880):
        self.serial = Serial()
        self.serial.port = port
        self.serial.baudrate = baudrate

    def open(self) -> None:
        self.serial.open()

    def close(self) -> None:
        self.serial.close()

    def tick(self) -> None:
        pass

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

        return cast(str, read_bytes.decode("ascii", errors="ignore"))

    def _cpp_initial_output_decl(self) -> str:
        hexes = bytes_to_hexes(self.INITIAL_OUTPUT_STOP_MARKER)

        hex_str = ", ".join(hexes)
        hex_len_str = str(len(hexes))

        output = ""
        output += "const size_t INITIAL_OUTPUT_STOP_MARKER_LENGTH = " + hex_len_str + ";"
        output += "\n"
        output += "const byte INITIAL_OUTPUT_STOP_MARKER[" + hex_len_str + "] = {" + hex_str + "};"

        return output

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

    def read_packets(self) -> list[Packet]:
        packets: list[Packet] = []

        while self.serial.in_waiting:
            packets.append(self.read_packet())

        return packets

    def dump_packets(self, continuous: bool = False) -> None:
        while True:
            packets = self.read_packets()

            for packet in packets:
                print(packet)

            if not continuous:
                break

    def send_packet(self, packet: OutboundPacket) -> None:
        bytes_to_transfer = packet.to_bytes()

        self.serial.write(bytes_to_transfer)
