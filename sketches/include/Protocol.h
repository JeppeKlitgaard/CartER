#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>
#include <Utils.h>
#include <array>
#include <vector>

/**
 * Command packets (PC -> Arduino) don't necessarily have all methods implemented
 */

// Packet buffer
const unsigned int MAX_PACKET_SIZE = 25;

constexpr byte PACKET_END = 0x0A; // \n

// using RawPacket = std::vector<byte>;

class RawPacket : private std::vector<byte> {
private:
    // in case I changed to boost or something later, I don't have to update everything below
    typedef std::vector<byte> base_vector;

public:
    typedef typename base_vector::size_type       size_type;
    typedef typename base_vector::iterator        iterator;
    typedef typename base_vector::const_iterator  const_iterator;

    using base_vector::vector; // constructor

    using base_vector::operator[];

    using base_vector::begin;
    using base_vector::clear;
    using base_vector::end;
    using base_vector::erase;
    using base_vector::push_back;
    using base_vector::reserve;
    using base_vector::resize;
    using base_vector::size;
    using base_vector::data;

    unsigned long pop_unsigned_long();
};

class PacketHandler; // forward reference

class Packet
{
protected:
    const PacketHandler &_packetHandler;
    virtual void _consume(RawPacket &buf);
    virtual void _react();

public:
    static const byte id = 0x00; // NUL

    Packet(const PacketHandler &packetHandler);

    void consume(RawPacket &buf);
    void react();
    virtual void construct();
    virtual RawPacket toRawPacket();
};

class PacketHandler
{
protected:
    Stream &_s;

public:
    PacketHandler(Stream &stream);

    const void receive();
    void send(Packet &packet) const;
};

class UnknownPacket : public Packet
{
public:
    static const byte id = 0x3F; // ?
};

class DebugPacket : public Packet
{
public:
    static const byte id = 0x7E; // ~

    DebugPacket(const PacketHandler &packetHandler);

    virtual void construct();
    virtual RawPacket toRawPacket();
};

class ErrorPacket : public Packet
{
public:
    static const byte id = 0x21; // !

    ErrorPacket(const PacketHandler &packetHandler);

    virtual RawPacket toRawPacket();
};

class PingPacket : public Packet
{

public:
    static const byte id = 0x70; // p

    unsigned long timestamp;

    PingPacket(const PacketHandler &packetHandler);

    virtual void _consume(RawPacket &buf);
    virtual void _react();
};

class PongPacket : public Packet
{
public:
    static const byte id = 0x50; // P

    unsigned long timestamp;

    PongPacket(const PacketHandler &packetHandler);

    virtual RawPacket toRawPacket();
    virtual void construct();
};

#endif
