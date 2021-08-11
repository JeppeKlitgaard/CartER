"""
Contains the abstraction layer around the network communication.
"""

from typing import cast

from serial import Serial

from commander.protocol import PACKET_ID_MAP, Packet


class Connection:
    _serial: Serial

    def __init__(self, port: str = PORT, baudrate: int = BAUDRATE):
        self.port = port
        self.baudrate = baudrate

        self._serial = Serial()

    @property
    def port(self) -> str:
        return cast(str, self._serial.port)

    @port.setter
    def port(self, val: str) -> None:
        self._serial.port = val

    @property
    def baudrate(self) -> int:
        return cast(int, self._serial.baudrate)

    @baudrate.setter
    def baudrate(self, val: int) -> None:
        self._serial.baudrate = val

    def open(self) -> None:
        self._serial.open()

    def close(self) -> None:
        self._serial.close()

    def read_packet(self) -> Packet:
        """
        Warning: Blocks
        """
        id_ = self._serial.read(1)

        packet: Packet
        try:
            packet = PACKET_ID_MAP[id_](self)
        except KeyError:
            raise ConnectionError(f"Invalid packet ID: {id_}")

        packet.read()

        return packet
