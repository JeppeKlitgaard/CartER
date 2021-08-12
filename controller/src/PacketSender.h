#ifndef PACKET_SENDER_H
#define PACKET_SENDER_H

#include <CustomArduino.h>

#include <memory>

#include <Packet.h>

class PacketSender {
    protected:
        Stream &_s;

    public:
        explicit PacketSender(Stream &stream);

        void send(Packet &packet);
        void send(std::unique_ptr<Packet> packet);
};

extern PacketSender packet_sender;

#endif