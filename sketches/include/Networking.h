#ifndef NETWORKING_H
#define NETWORKING_H

#include <Arduino.h>

#include <vector>

// Packet buffer
constexpr byte PACKET_END = 0x0A; // \n

// using RawPacket = std::vector<byte>;

class RawPacket : private std::vector<byte>
{
private:
    // in case I changed to boost or something later, I don't have to update everything below
    typedef std::vector<byte> base_vector;

public:
    typedef typename base_vector::size_type size_type;
    typedef typename base_vector::iterator iterator;
    typedef typename base_vector::const_iterator const_iterator;

    using base_vector::vector; // constructor

    using base_vector::operator[];

    using base_vector::begin;
    using base_vector::clear;
    using base_vector::data;
    using base_vector::end;
    using base_vector::erase;
    using base_vector::push_back;
    using base_vector::reserve;
    using base_vector::resize;
    using base_vector::size;

    unsigned long pop_unsigned_long();
};

class PacketHandler; // forward reference

class Packet
{
protected:
    const PacketHandler &_packet_handler;

public:
    static const byte id = 0x00; // NUL

    Packet(const PacketHandler &packet_handler);

    virtual RawPacket to_raw_packet();

    void pre_consume();
    void consume(Stream &sbuf);
    void post_consume();

    void react();

    void construct();
};

class PacketHandler
{
protected:
    Stream &_s;

    template <class T>
    Packet _read_and_construct_packet() const
    {
        T packet(*this);

        packet.pre_consume();
        packet.consume(_s);
        packet.post_consume();

        packet.react();

        return packet;
    }

public:
    PacketHandler(Stream &stream);

    const void receive();
    void send(Packet &packet) const;
    Packet read_packet() const;
};

extern const PacketHandler packet_handler;

#endif