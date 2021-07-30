#include <PacketReactor.h>

#include <Protocol.h>
#include <Init.h>
#include <PacketSender.h>
#include <memory>

// PacketReactor
PacketReactor::PacketReactor(Stream &stream) : _s(stream) {}

// void PacketReactor::send(Packet &packet) const
// {
//     RawPacket raw_packet = packet.to_raw_packet();

//     _s.write(raw_packet.data(), raw_packet.size());
//     _s.write(PACKET_END);
// }

std::unique_ptr<Packet> PacketReactor::read_packet()
{
    int id = _s.read();

    S.print("ID: ");
    S.println(id);

    if (id == -1)
    {
        return std::make_unique<NullPacket>();
    }

    std::unique_ptr<Packet> packet = std::make_unique<Packet>();

    // This could definitely be templated
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
        // packet = std::make_unique<UnknownPacket>();
        // packet->construct(id);
        break;

    return packet;
    }
}

void PacketReactor::react_packet(std::unique_ptr<Packet> packet)
{
    S.print("ID2: ");
    S.println(packet->id);

    if (packet->id == NullPacket::id) {
        S.println("NULL");
    } else if (packet->id == PingPacket::id) {
        S.println("PONG");
        PongPacket pong;
        pong.construct(micros());

        packet_sender.send(pong);
    }
}

void PacketReactor::tick()
{
    std::unique_ptr<Packet> packet = read_packet();

    react_packet(std::move(packet));
}
