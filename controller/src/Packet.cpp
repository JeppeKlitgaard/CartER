#include <Packet.h>
#include <BufferUtils.h>

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

void RawPacket::add(const char *msg, size_t size)
{
    add(size);
    for (size_t i = 0; i < size; ++i)
        add(msg[i]);
}

void RawPacket::add(std::string const &str)
{
    uint32_t bytes_len = static_cast<uint32_t>(str.size());
    this->add(bytes_len);

    auto bytes = reinterpret_cast<byte const *>(str.data());
    this->insert(this->end(), bytes, bytes + str.size());
}

void RawPacket::add_newline()
{
    add((byte)0x0D);
    add((byte)0x0A);
}

// Packet
void Packet::construct() {}
void Packet::construct(byte id)
{
    observed_id = id;
}

void OnlyIDPacket::read(Stream &sbuf) {}
RawPacket OnlyIDPacket::to_raw_packet() const
{
    RawPacket raw_packet;
    raw_packet.add(this->get_id());

    return raw_packet;
}

// NullInbound
NullInboundPacket::NullInboundPacket() {}
byte NullInboundPacket::get_id() const { return NullPacket::id; }
void NullInboundPacket::read(Stream &sbuf) {}

// NullOutbound
NullOutboundPacket::NullOutboundPacket() {}
byte NullOutboundPacket::get_id() const { return NullPacket::id; }

RawPacket NullOutboundPacket::to_raw_packet() const
{
    RawPacket raw_packet;
    raw_packet.add(this->get_id());

    return raw_packet;
}

NullPacket::NullPacket() : NullInboundPacket() {}
byte NullPacket::get_id() const { return NullPacket::id; }
