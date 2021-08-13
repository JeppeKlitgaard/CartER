#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <CustomArduino.h>

#include <vector>
#include <PString.h>
#include <Packet.h>
#include <Init.h>

/** Protocol is little-endian.
  */

// Enums
// Mode
enum class SetOperation : char
{
    SUBTRACT = '-',
    EQUAL = '=',
    ADD = '+',
    NUL = '0',
};

// Unknown
class UnknownPacket : public InboundPacket
{
public:
    static const byte id = 0x3F; // ?

    UnknownPacket();
    using Packet::construct;

    virtual byte get_id() const override;

    virtual void read(Stream &sbuf) override;
};

class DebugErrorBasePacket : public OutboundPacket
{
public:
    char* _msg;
    size_t _size;

    DebugErrorBasePacket();
    using OutboundPacket::construct;
    void construct(char *message, size_t size);

    virtual byte get_id() const override = 0;
    virtual RawPacket to_raw_packet() const override;
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
class PingPongBasePacket : public InboundPacket, public OutboundPacket
{
public:
    unsigned long ping_timestamp;

    PingPongBasePacket();
    using Packet::construct;
    virtual void construct(unsigned long timestamp);

    virtual byte get_id() const override = 0;

    virtual RawPacket to_raw_packet() const override;
    virtual void read(Stream &sbuf) override;
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

// SetPosition
class SetQuantityBasePacket : public InboundPacket {
public:
    SetOperation operation;
    uint8_t cart_id;
    int16_t value;

    SetQuantityBasePacket();
    using Packet::construct;
    virtual void construct(SetOperation operation, uint8_t cart_id, int16_t value);

    virtual byte get_id() const override = 0;

    virtual void read(Stream &sbuf) override;
};

#endif
