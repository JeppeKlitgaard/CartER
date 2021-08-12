#ifndef PACKET_REACTOR_H
#define PACKET_REACTOR_H

// #include <CustomArduino.h>
#include <CustomArduino.h>

#include <memory>

#include <Packet.h>
#include <Utils.h>

// Packet buffer
constexpr byte PACKET_END = 0x0A; // \n

class PacketReactor
{
protected:
    Stream &_s;

    template <class T>
    std::unique_ptr<T> _read_and_construct_packet()
    {
        // std::make_unique<T> packet;
        std::unique_ptr<T> packet = std::make_unique<T>();

        packet->pre_consume();
        packet->consume(_s);
        packet->post_consume();

        packet->construct();

        return packet;
    }

public:
    PacketReactor(Stream &stream);

    std::unique_ptr<Packet> read_packet();
    void react_packet(std::unique_ptr<Packet> packet);
    void tick();
};

extern PacketReactor packet_reactor;

#endif