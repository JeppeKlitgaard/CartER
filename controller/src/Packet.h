#ifndef PACKET_H
#define PACKET_H

#include <CustomArduino.h>

#include <vector>
#include <string>
#include <array>

class RawPacket : private std::vector<byte>
{
private:
    // in case I changed to boost or something later, I don't have to update everything below
    typedef std::vector<byte> base_vector;

public:
    typedef typename base_vector::size_type size_type;
    typedef typename base_vector::iterator iterator;
    typedef typename base_vector::const_iterator const_iterator;
    typedef typename base_vector::value_type value_type;

    using base_vector::vector; // constructor

    using base_vector::operator[];

    using base_vector::begin;
    using base_vector::clear;
    using base_vector::data;
    using base_vector::end;
    using base_vector::erase;
    using base_vector::insert;
    using base_vector::push_back;
    using base_vector::reserve;
    using base_vector::resize;
    using base_vector::size;

    unsigned long pop_unsigned_long();

    void add(const char *msg, size_t size);
    void add_newline();

    template <class T>
    void add(T value)
    {
        std::copy((byte *)&value, ((byte *)&value) + sizeof(T), std::back_inserter(*this));
    }
    template <size_t SIZE>
    void add(std::array<byte, SIZE> &b_array)
    {
        this->insert(this->end(), b_array.begin(), b_array.end());
    }
};

/**
 * Command packets (PC -> Arduino) don't necessarily have all methods implemented
 */
class Packet
{
public:
    byte observed_id = 0x0F; // For UnknownPacket case

    explicit Packet() = default;
    virtual ~Packet() = default;
    Packet(const Packet &) = delete;
    Packet &operator=(const Packet &) = delete;

    virtual byte get_id() const = 0;

    virtual void construct();
    virtual void construct(byte id); // For UnknownPacket case
};

class InboundPacket : virtual public Packet
{
public:
    explicit InboundPacket() = default;
    virtual ~InboundPacket() = default;
    using Packet::construct;

    virtual void read(Stream &sbuf) = 0;
};

class OutboundPacket : virtual public Packet
{
public:
    explicit OutboundPacket() = default;
    virtual ~OutboundPacket() = default;
    using Packet::construct;

    virtual RawPacket to_raw_packet() const = 0;
};

class OnlyIDPacket : public OutboundPacket, public InboundPacket {
public:
    explicit OnlyIDPacket() = default;
    virtual ~OnlyIDPacket() = default;
    using Packet::construct;

    virtual void read(Stream &sbuf) override;
    virtual RawPacket to_raw_packet() const override;
};

class NullInboundPacket : public InboundPacket
{
public:
    NullInboundPacket();
    using InboundPacket::construct;

    virtual byte get_id() const override;

    virtual void read(Stream &sbuf) override;
};

class NullOutboundPacket : public OutboundPacket
{
public:
    NullOutboundPacket();
    using OutboundPacket::construct;

    virtual byte get_id() const override;

    virtual RawPacket to_raw_packet() const override;
};

class NullPacket : public NullOutboundPacket, public NullInboundPacket
{
public:
    static const byte id = 0x00; // NUL

    NullPacket();
    using OutboundPacket::construct;

    virtual byte get_id() const override;
};

#endif