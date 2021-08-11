#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>

#include <vector>
#include <PString.h>
#include <Packet.h>
#include <Init.h>

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

    virtual byte get_id() const override;

    UnknownPacket();
};

// Debug
class DebugPacket : public Packet
{
public:
    char* _msg;
    size_t _size;

    static const byte id = 0x7E; // ~

    virtual byte get_id() const override;
    virtual RawPacket to_raw_packet() override;

    void construct(char *message, size_t size);

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
