#include <PacketReactor.h>

#include <memory>

#include <Protocol.h>
#include <Init.h>
#include <PacketSender.h>
#include <BufferUtils.h>
#include <DebugUtils.h>
#include <PString.h>

// PacketReactor
PacketReactor::PacketReactor(Stream &stream) : _s(stream) {}

void PacketReactor::tick()
{
    // Read
    int id_raw = _s.read();

    if (id_raw == -1)
    {
        id_raw = 0; // NullPacket::id as int
    }

    byte id = static_cast<byte>(id_raw);

    //
    switch (id)
    {
    case NullPacket::id:
    {
        std::unique_ptr<NullInboundPacket> packet = _read_and_construct_packet<NullInboundPacket>();
        break;

        // Reaction
        DPL("NUL");
    }
    case UnknownPacket::id:
    {
        std::unique_ptr<UnknownPacket> packet = _read_and_construct_packet<UnknownPacket>();
        break;
    }
    case PingPacket::id:
    {
        std::unique_ptr<PingPacket> packet = _read_and_construct_packet<PingPacket>();

        // Reaction
        std::unique_ptr<PongPacket> pong_pkt = std::make_unique<PongPacket>();

        pong_pkt->construct(packet->ping_timestamp);

        packet_sender.send(std::move(pong_pkt));
        break;

    }
    case PongPacket::id:
    {
        std::unique_ptr<PongPacket> packet = _read_and_construct_packet<PongPacket>();
        break;
    }
    default:
        std::unique_ptr<UnknownPacket> packet = std::make_unique<UnknownPacket>();
        packet->construct(id);

        // Reaction
        std::unique_ptr<DebugPacket> debug_pkg = std::make_unique<DebugPacket>();

        char s_buf[STRING_BUF_SIZE];
        PString debug_msg(s_buf, sizeof(s_buf));
        debug_msg.print("Received unknown packet with ID: ");
        debug_msg.print(packet->observed_id);

        debug_pkg->construct(s_buf, debug_msg.length());

        packet_sender.send(std::move(debug_pkg));

        break;
    }
}
