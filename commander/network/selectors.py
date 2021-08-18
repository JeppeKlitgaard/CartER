from commander.network.protocol import InfoPacket, MessagePacketBase
from commander.network.types import PacketSelector


def limit_finding_done() -> PacketSelector[InfoPacket]:
    def inner(packet: InfoPacket) -> bool:
        return packet.msg == "LimitFinder: NOW DONE"

    return inner


def message_startswith(start_str: str) -> PacketSelector[MessagePacketBase]:
    def inner(packet: MessagePacketBase) -> bool:
        return packet.msg.startswith(start_str)

    return inner
