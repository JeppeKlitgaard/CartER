#include <PacketSender.h>
#include <Protocol.h>
#include <string>
#include <Init.h>

PacketSender::PacketSender(Stream &stream) : _s(stream) {}

size_t PacketSender::write(const byte *buf, size_t size)
{
    return _s.write(buf, size);
}

// Not entirely sure how to code-dedup this in c++
// Could do templating, but I prefer having separate methods over overloading
// in this case.
void PacketSender::send_debug(std::string msg) const
{
    std::unique_ptr<DebugPacket> packet = std::make_unique<DebugPacket>();

    packet->construct(msg);

    send(std::move(packet));
}

void PacketSender::send_info(std::string msg) const
{
    std::unique_ptr<InfoPacket> packet = std::make_unique<InfoPacket>();

    packet->construct(msg);

    send(std::move(packet));
}

void PacketSender::send_error(std::string msg) const
{
    std::unique_ptr<ErrorPacket> packet = std::make_unique<ErrorPacket>();

    packet->construct(msg);

    send(std::move(packet));
}
