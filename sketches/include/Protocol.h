#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Networking.h>

/**
 * Command packets (PC -> Arduino) don't necessarily have all methods implemented
 */

// Null
class NullPacket : public Packet
{
public:
    static const byte id = 0x00; // NUL

    NullPacket(const PacketHandler &packet_handler);
};

// Unknown
class UnknownPacket : public Packet
{
public:
    static const byte id = 0x3F; // ?
    byte observed_id = 0x0F;

    UnknownPacket(const PacketHandler &packet_handler);

    void construct(byte id);
};

// Debug
class DebugPacket : public Packet
{
public:
    static const byte id = 0x7E; // ~

    DebugPacket(const PacketHandler &packet_handler);
};

// Error
class ErrorPacket : public Packet
{
public:
    static const byte id = 0x21; // !

    ErrorPacket(const PacketHandler &packet_handler);
};

// Ping
class PingPacket : public Packet
{

public:
    static const byte id = 0x70; // p

    unsigned long ping_timestamp;

    PingPacket(const PacketHandler &packet_handler);

    virtual RawPacket to_raw_packet();
    virtual void consume(Stream &sbuf);
    virtual void react();

    void construct(unsigned long timestamp);
};

// Pong
class PongPacket : public PingPacket
{
public:
    static const byte id = 0x50; // P

    PongPacket(const PacketHandler &packet_handler);
};

#endif
