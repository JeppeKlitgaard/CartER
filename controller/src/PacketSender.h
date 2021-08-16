#ifndef PACKET_SENDER_H
#define PACKET_SENDER_H

#include <CustomArduino.h>

#include <memory>
#include <string>

#include <Packet.h>

class PacketSender
{
protected:
    Stream &_s;

public:
    explicit PacketSender(Stream &stream);

    void send(const OutboundPacket &packet);

    template <class T>
    void send(std::unique_ptr<T> packet) const
    {
        RawPacket raw_packet = packet->to_raw_packet();
        _s.write(raw_packet.data(), raw_packet.size());
    }

    void send_debug(std::string msg) const;
    void send_info(std::string msg) const;
    void send_error(std::string msg) const;
};

extern PacketSender packet_sender;

#endif