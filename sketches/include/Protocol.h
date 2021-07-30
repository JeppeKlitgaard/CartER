#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>

#include <vector>

#include <Packet.h>

// Null
class NullPacket : public Packet
{
public:
    static const byte id = 0x00; // NUL

    NullPacket();

    virtual byte get_id() const override;
};

// Unknown
class UnknownPacket : public Packet
{
public:
    static const byte id = 0x3F; // ?
    byte observed_id = 0x0F;

    UnknownPacket();

    virtual byte get_id() const override;

    virtual void construct(byte id);
};

// Debug
class DebugPacket : public Packet
{
public:
    static const byte id = 0x7E; // ~

    virtual byte get_id() const override;

    DebugPacket();
};

// Error
class ErrorPacket : public Packet
{
public:
    static const byte id = 0x21; // !

    virtual byte get_id() const override;

    ErrorPacket();
};

// Ping
class PingPacket : public Packet
{

public:
    static const byte id = 0x70; // p

    unsigned long ping_timestamp;

    PingPacket();

    virtual byte get_id() const override;

    virtual RawPacket to_raw_packet() override;
    virtual void consume(Stream &sbuf) override;

    virtual void construct(unsigned long timestamp);
};

// Pong
class PongPacket : public PingPacket
{
public:
    static const byte id = 0x50; // P

    PongPacket();

    virtual byte get_id() const override;
};

#endif
