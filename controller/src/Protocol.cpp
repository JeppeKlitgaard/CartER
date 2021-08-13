#include <Protocol.h>

#include <array>

#include <BufferUtils.h>
#include <Packet.h>
#include <DebugUtils.h>

// Unknown
UnknownPacket::UnknownPacket() {}
byte UnknownPacket::get_id() const { return UnknownPacket::id; }
void UnknownPacket::read(Stream &sbuf) {};

// DebugErrorBase
DebugErrorBasePacket::DebugErrorBasePacket()
{
    _msg = nullptr;
    _size = 0;
}

void DebugErrorBasePacket::construct(char *msg, size_t size)
{
    _msg = msg;
    _size = size;
}

RawPacket DebugErrorBasePacket::to_raw_packet() const
{
    RawPacket raw_packet;
    raw_packet.add(this->get_id());
    raw_packet.add(this->_msg, this->_size);
    raw_packet.add_newline();

    return raw_packet;
}

// Debug
DebugPacket::DebugPacket() {}
byte DebugPacket::get_id() const { return DebugPacket::id; }

// Error
ErrorPacket::ErrorPacket() {}
byte ErrorPacket::get_id() const { return ErrorPacket::id; }

// PingPongBase
PingPongBasePacket::PingPongBasePacket()
{
    ping_timestamp = 0;
}
// byte PingPongBasePacket::get_id() const { return 0x70; }

void PingPongBasePacket::read(Stream &buf)
{
    ping_timestamp = read_uint32(buf);
}

void PingPongBasePacket::construct(unsigned long timestamp)
{
    ping_timestamp = timestamp;
}

RawPacket PingPongBasePacket::to_raw_packet() const
{
    RawPacket raw_packet;

    raw_packet.add(this->get_id());

    std::array<byte, 4> timestamp = ulong_to_bytes(this->ping_timestamp);
    raw_packet.add(timestamp);

    return raw_packet;
}

// Ping
PingPacket::PingPacket() {}
byte PingPacket::get_id() const { return PingPacket::id; }

// Pong
PongPacket::PongPacket() {}
byte PongPacket::get_id() const { return PongPacket::id; }