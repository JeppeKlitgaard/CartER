#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <CustomArduino.h>

#include <vector>
#include <PString.h>
#include <Packet.h>
#include <Init.h>

/** Protocol is little-endian.
  */


// Null
class NullPacket : public Packet
{

public:
    static const byte id = 0x00; // NUL

    NullPacket();
    using Packet::construct;

    virtual byte get_id() const override;
};

// Unknown
class UnknownPacket : public Packet
{
public:
    static const byte id = 0x3F; // ?

    UnknownPacket();
    using Packet::construct;

    virtual byte get_id() const override;
};

class DebugErrorBasePacket : public Packet
{
public:
    char* _msg;
    size_t _size;

    DebugErrorBasePacket();
    using Packet::construct;

    virtual byte get_id() const override = 0;
    virtual RawPacket to_raw_packet() override;

    void construct(char *message, size_t size);
};

// Debug
class DebugPacket : public DebugErrorBasePacket
{
public:
    static const byte id = 0x7E; // ~

    DebugPacket();
    using DebugErrorBasePacket::construct;

    virtual byte get_id() const override;
};

// Error
class ErrorPacket : public DebugErrorBasePacket
{
public:
    static const byte id = 0x21; // !

    ErrorPacket();
    using DebugErrorBasePacket::construct;

    virtual byte get_id() const override;
};

// PingPongBase
class PingPongBasePacket : public Packet
{
public:
    unsigned long ping_timestamp;

    PingPongBasePacket();
    using Packet::construct;

    virtual byte get_id() const override = 0;

    virtual RawPacket to_raw_packet() override;
    virtual void consume(Stream &sbuf) override;

    virtual void construct(unsigned long timestamp);
};

// Ping
class PingPacket : public PingPongBasePacket
{

public:
    static const byte id = 0x70; // p

    PingPacket();
    using PingPongBasePacket::construct;

    virtual byte get_id() const override;
};

// Pong
class PongPacket : public PingPongBasePacket
{
public:
    static const byte id = 0x50; // P

    PongPacket();
    using PingPongBasePacket::construct;

    virtual byte get_id() const override;
};

#endif
