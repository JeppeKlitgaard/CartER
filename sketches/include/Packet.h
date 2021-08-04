#ifndef PACKET_H
#define PACKET_H

#include <Arduino.h>

#include <vector>

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
    using base_vector::insert;

    unsigned long pop_unsigned_long();
};

/**
 * Command packets (PC -> Arduino) don't necessarily have all methods implemented
 */
class Packet
{
public:
    static const byte id = 0x00; // NUL

    explicit Packet();
    virtual ~Packet() = default;
    Packet(const Packet&) = delete;
    Packet& operator=(const Packet&) = delete;

    virtual RawPacket to_raw_packet();

    virtual byte get_id() const;

    virtual void pre_consume();
    virtual void consume(Stream &sbuf);
    virtual void post_consume();

    virtual void construct();
};

#endif