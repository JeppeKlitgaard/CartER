#include <Protocol.h>

#include <BufferUtils.h>

// Unknown
void UnknownPacket::construct(byte id) {
    observed_id = id;
}

// PING
PingPacket::PingPacket(const PacketHandler &packet_handler) : Packet(packet_handler) {}

void PingPacket::consume(Stream &buf)
{
    ping_timestamp = read_unsigned_long(buf);
}

void PingPacket::react() {
    PongPacket pong(_packet_handler);
    pong.construct(micros());

    _packet_handler.send(pong);
}

void PingPacket::construct(unsigned long timestamp) {
    ping_timestamp = timestamp;
}

RawPacket PingPacket::to_raw_packet()
{
    RawPacket raw_packet(id, ping_timestamp);

    return raw_packet;
}
