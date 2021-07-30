#include <Protocol.h>

#include <BufferUtils.h>
#include <Packet.h>

// Null
NullPacket::NullPacket() {}

// Unknown
UnknownPacket::UnknownPacket() {}

void UnknownPacket::construct(byte id)
{
    observed_id = id;
}

// Debug
DebugPacket::DebugPacket() {}

// Error
ErrorPacket::ErrorPacket() {}

// Ping
PingPacket::PingPacket() {}

void PingPacket::consume(Stream &buf)
{
    ping_timestamp = read_unsigned_long(buf);
}

void PingPacket::construct(unsigned long timestamp)
{
    ping_timestamp = timestamp;
}

RawPacket PingPacket::to_raw_packet()
{
    RawPacket raw_packet(id, ping_timestamp);

    return raw_packet;
}

// Pong
PongPacket::PongPacket() {}