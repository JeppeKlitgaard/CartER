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
};

// Unknown
class UnknownPacket : public Packet
{
public:
    static const byte id = 0x3F; // ?
    byte observed_id = 0x0F;

    UnknownPacket();

    void construct(byte id);
};

// Debug
class DebugPacket : public Packet
{
public:
    static const byte id = 0x7E; // ~

    DebugPacket();
};

// Error
class ErrorPacket : public Packet
{
public:
    static const byte id = 0x21; // !

    ErrorPacket();
};

// Ping
class PingPacket : public Packet
{

public:
    static const byte id = 0x70; // p

    unsigned long ping_timestamp;

    PingPacket();

    virtual RawPacket to_raw_packet();
    virtual void consume(Stream &sbuf);

    void construct(unsigned long timestamp);
};

// Pong
class PongPacket : public PingPacket
{
public:
    static const byte id = 0x50; // P

    PongPacket();
};

#endif
