#ifndef PACKET_SENDER_H
#define PACKET_SENDER_H

#include <CustomArduino.h>

#include <memory>
#include <string>

#include <Packet.h>

// Artificial noise
const bool ADD_ARTIFICIAL_NOISE_TO_SERIAL = false;
const bool SERIAL_ARTIFICIAL_NOISE_FREQUENCY = 1000;

class PacketSender
{
protected:
    Stream &_s;

public:
    explicit PacketSender(Stream &stream);

    size_t write(const byte *buf, size_t size);

    template <class T>
    void send(std::unique_ptr<T> packet) const
    {
        if (ADD_ARTIFICIAL_NOISE_TO_SERIAL && random(0, SERIAL_ARTIFICIAL_NOISE_FREQUENCY) == 0)
        {
            for (uint8_t i = 0; i < random(1, 5); i++)
            {
                byte rand_byte = static_cast<byte>(random(0, 256));
                _s.write(rand_byte);
            }
        }

        RawPacket raw_packet = packet->to_raw_packet();
        _s.write(raw_packet.data(), raw_packet.size());
    }

    void send_debug(std::string msg) const;
    void send_info(std::string msg) const;
    void send_error(std::string msg) const;
};

extern PacketSender packet_sender;

#endif