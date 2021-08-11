#include <Protocol.h>

#include <array>


#include <BufferUtils.h>
#include <Packet.h>
#include <DebugUtils.h>
#include <Fixes.h>

// Null
NullPacket::NullPacket() {}
byte NullPacket::get_id() const { return NullPacket::id;}

// Unknown
UnknownPacket::UnknownPacket() {}
byte UnknownPacket::get_id() const { return UnknownPacket::id;}

// Debug
DebugPacket::DebugPacket() {}
byte DebugPacket::get_id() const { return DebugPacket::id;}
void DebugPacket::construct(char *msg, size_t size) {
    _msg = msg;
    _size = size;
}

RawPacket DebugPacket::to_raw_packet() {
    RawPacket raw_packet;
    raw_packet.add(id);
    raw_packet.add(_msg, _size);
    raw_packet.add_newline();

    return raw_packet;
}

// Error
ErrorPacket::ErrorPacket() {}
byte ErrorPacket::get_id() const { return ErrorPacket::id;}

// Ping
PingPacket::PingPacket() {}
byte PingPacket::get_id() const { return 0x70;}

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
    // RawPacket raw_packet (get_id());
    RawPacket raw_packet;

    raw_packet.push_back(get_id());

    std::array<byte, 4> timestamp = ulong_to_bytes(ping_timestamp);
    raw_packet.insert(raw_packet.end(), timestamp.begin(), timestamp.end());

    return raw_packet;
}

// Pong
PongPacket::PongPacket() {}
byte PongPacket::get_id() const { return PongPacket::id;}