#include <PacketSender.h>

PacketSender::PacketSender(Stream &stream)  : _s(stream) {}

void PacketSender::send(Packet &packet) {
    RawPacket raw_packet = packet.to_raw_packet();

    _s.write(raw_packet.data(), raw_packet.size());
}
