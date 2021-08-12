#include <PacketSender.h>

PacketSender::PacketSender(Stream &stream)  : _s(stream) {}

void PacketSender::send(Packet &packet) {
    RawPacket raw_packet = packet.to_raw_packet();

    _s.print("Size: ");
    _s.println(raw_packet.size());
    _s.write(raw_packet.data(), raw_packet.size());
}
void PacketSender::send(std::unique_ptr<Packet> packet) {
    RawPacket raw_packet = packet->to_raw_packet();

    // _s.print("Size: ");
    // _s.println(raw_packet.size());
    _s.write(raw_packet.data(), raw_packet.size());
}
