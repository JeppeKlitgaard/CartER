#include <PacketSender.h>
#include <Protocol.h>
#include <string>

PacketSender::PacketSender(Stream &stream) : _s(stream) {}

void PacketSender::send_debug(const std::string msg) const
{
    std::unique_ptr<DebugPacket> packet = std::make_unique<DebugPacket>();

    packet->construct(msg.c_str(), msg.length());

    send(std::move(packet));
}

void PacketSender::send_error(const std::string msg) const
{
    std::unique_ptr<ErrorPacket> packet = std::make_unique<ErrorPacket>();

    packet->construct(msg.c_str(), msg.length());

    send(std::move(packet));
}
