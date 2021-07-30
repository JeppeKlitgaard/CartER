#include <Networking.h>
#include <Protocol.h>

// RawPacket
unsigned long RawPacket::pop_unsigned_long()
{
    static_assert(sizeof(unsigned long) == 4, "bad datatype size");

    unsigned long l = static_cast<unsigned long>((*this)[0]) |
                      static_cast<unsigned long>((*this)[1]) << 8 |
                      static_cast<unsigned long>((*this)[2]) << 16 |
                      static_cast<unsigned long>((*this)[3]) << 24;

    this->erase(this->begin(), this->begin() + 4);

    return l;
}

// Packet
Packet::Packet(const PacketHandler &packet_handler) : _packet_handler(packet_handler)
{
}

void Packet::consume(Stream &sbuf)
{
}

void Packet::react()
{
}

// PacketHandler
PacketHandler::PacketHandler(Stream &stream) : _s(stream)
{
}

void PacketHandler::send(Packet &packet) const
{
    RawPacket raw_packet = packet.to_raw_packet();

    _s.write(raw_packet.data(), raw_packet.size());
    _s.write(PACKET_END);
}

Packet PacketHandler::read_packet() const
{
    int id = _s.read();

    if (id == -1)
    {
        return NullPacket(*this);
    }

    switch (id)
    {
    case NullPacket::id:
        return _read_and_construct_packet<NullPacket>();
    case UnknownPacket::id:
        return UnknownPacket(*this);
    case DebugPacket::id:
        return DebugPacket(*this);
    case ErrorPacket::id:
        return ErrorPacket(*this);
    case PingPacket::id:
        return PingPacket(*this);
    case PongPacket::id:
        return PongPacket(*this);
    default:
        UnknownPacket p(*this);
        p.construct(id);

        return p;
    }
}
