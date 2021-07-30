import struct

class PacketHandler:
    def __init__(self):
        pass


class Packet:
    id_: bytes

    def __init__(self, packet_handler: PacketHandler):
        self.packet_handler = packet_handler




