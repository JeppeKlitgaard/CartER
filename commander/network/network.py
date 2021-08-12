from typing import cast

from serial import Serial

from commander.network.protocol import PACKET_ID_MAP, Packet

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
        raw = self.serial.read_until(self.INITIAL_OUTPUT_STOP_MARKER)
        output = raw.decode("ascii")

        return cast(str, output)

    def _cpp_initial_output_decl(self) -> str:
        hex_space_str = self.INITIAL_OUTPUT_STOP_MARKER.hex(" ")
        hexes = hex_space_str.split(" ")
        hexes = [hex.upper() for hex in hexes]
        hexes = ["0x" + hex for hex in hexes]

        hex_str = ", ".join(hexes)
        hex_len_str = str(len(hexes))

        output = ""
        output += "const size_t INITIAL_OUTPUT_STOP_MARKER_LENGTH = " + hex_len_str + ";"
        output += "\n"
        output += "const byte INITIAL_OUTPUT_STOP_MARKER[" + hex_len_str + "] = {" + hex_str + "};"

        return output

    def read_packet(self) -> Packet:
        id_ = self.serial.read(1)

        try:
            packet_cls = PACKET_ID_MAP[id_]
        except KeyError:
            raise ConnectionError(f"Invalid packet ID: {id_}")

        packet = packet_cls.read(self.serial)
        return packet

    def send_packet(self, packet: Packet) -> None:
        bytes_to_transfer = packet.to_bytes()

        self.serial.write(bytes_to_transfer)
