#include <Packet.h>

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
Packet::Packet()
{
}

// Packet::~Packet() {}

void Packet::pre_consume() {}
void Packet::consume(Stream &sbuf) {}
void Packet::post_consume() {}

void Packet::construct() {}

RawPacket Packet::to_raw_packet() {}