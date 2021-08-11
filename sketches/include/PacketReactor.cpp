#include <PacketReactor.h>

#include <memory>

#include <Protocol.h>
#include <Init.h>
#include <PacketSender.h>
#include <BufferUtils.h>
#include <PString.h>

// PacketReactor
PacketReactor::PacketReactor(Stream &stream) : _s(stream) {}


std::unique_ptr<Packet> PacketReactor::read_packet()
{
    int id_raw = _s.read();

    if (id_raw == -1)
    {
        return std::make_unique<NullPacket>();
    }

    byte id = static_cast<byte>(id_raw);

    std::unique_ptr<Packet> packet = std::make_unique<Packet>();

    // // This could definitely be templated
    switch (id)
    {
    case NullPacket::id:
        packet = _read_and_construct_packet<NullPacket>();
        break;
    case UnknownPacket::id:
        packet = _read_and_construct_packet<UnknownPacket>();
        break;
    case DebugPacket::id:
        packet = _read_and_construct_packet<DebugPacket>();
        break;
    case ErrorPacket::id:
        packet = _read_and_construct_packet<ErrorPacket>();
        break;
    case PingPacket::id:
        packet = _read_and_construct_packet<PingPacket>();
        break;
    case PongPacket::id:
        packet = _read_and_construct_packet<PongPacket>();
        break;
    default:
        packet = std::make_unique<UnknownPacket>();
        packet->construct(id);
        break;
    }

    return packet;
}

void PacketReactor::react_packet(std::unique_ptr<Packet> packet)
{
    byte id = packet->get_id();

    switch (id)
    {
    case UnknownPacket::id:
    {
        std::unique_ptr<DebugPacket> debug_pkg = std::make_unique<DebugPacket>();

        char s_buf[STRING_BUF_SIZE];
        PString debug_msg(s_buf, sizeof(s_buf));
        debug_msg.print("Received unknown packet with ID: ");
        debug_msg.print(packet->observed_id);

        debug_pkg->construct(s_buf, debug_msg.length());

        packet_sender.send(std::move(debug_pkg));

        // S.print(debug_pkg->to_raw_packet().data());
        break;
    }
    case NullPacket::id:
        S.println("NULL");
        break;

    case PingPacket::id:
    {

        std::unique_ptr<PingPacket>
        ping_pkt(static_cast<PingPacket*>(packet.release()));
        std::unique_ptr<PongPacket> pong_pkt = std::make_unique<PongPacket>();

        pong_pkt->construct(ping_pkt->ping_timestamp);

        packet_sender.send(std::move(pong_pkt));
        break;
    }
    }
}

void PacketReactor::tick()
{
    auto packet = read_packet();
    react_packet(std::move(packet));
}
