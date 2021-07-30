#ifndef PACKET_SENDER_H
#define PACKET_SENDER_H

#include <Arduino.h>

#include <Packet.h>

class PacketSender {
    protected:
        Stream &_s;

    public:
        PacketSender(Stream &stream);

        void send(Packet &packet);
};

extern PacketSender packet_sender;

#endif