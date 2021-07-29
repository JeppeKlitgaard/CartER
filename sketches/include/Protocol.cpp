#include <Protocol.h>

unsigned long RawPacket::pop_unsigned_long() {
    static_assert(sizeof(unsigned long) == 4, "bad datatype size");

    unsigned long l  = static_cast<unsigned long>((*this)[0]) |
                       static_cast<unsigned long>((*this)[1]) << 8 |
                       static_cast<unsigned long>((*this)[2]) << 16 |
                       static_cast<unsigned long>((*this)[3]) << 24;

    this->erase(this->begin(), this->begin() + 4);

    return l;

}

Packet::Packet(const PacketHandler &packetHandler) : _packetHandler(packetHandler)
{
}

void Packet::consume(RawPacket &buf)
{
    // Assert id
    if (buf[0] != id)
    {
        // Error
        return;
    }

    _consume(buf);
}

void Packet::_consume(RawPacket &buf)
{
    return;
}

void Packet::react() {
    react();
}

void Packet::_react() {
    return;
}

// PING
void PingPacket::_consume(RawPacket &buf)
{
    timestamp = buf.pop_unsigned_long();
}

void PingPacket::_react() {
    PongPacket pong(_packetHandler);
    _packetHandler.send(pong);
}

// PONG
PongPacket::PongPacket(const PacketHandler &packetHandler) : Packet(packetHandler) {}

void PongPacket::construct() {
    timestamp = micros();
}

RawPacket PongPacket::toRawPacket()
{
    RawPacket rawPacket(id, timestamp);

    return rawPacket;
}

// PACKETHANDLER
PacketHandler::PacketHandler(Stream &stream) : _s(stream)
{
}

void PacketHandler::send(Packet &packet) const
{
    RawPacket rawPacket = packet.toRawPacket();

    _s.write(rawPacket.data(), rawPacket.size());
    _s.write(PACKET_END);
}