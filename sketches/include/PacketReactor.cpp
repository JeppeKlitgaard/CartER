#include <PacketReactor.h>

#include <memory>

#include <Protocol.h>
#include <Init.h>
#include <PacketSender.h>
#include <BufferUtils.h>

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

    if (id == -1)
    {
        return std::make_unique<NullPacket>();
    }

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
        std::unique_ptr<UnknownPacket> packet = std::make_unique<UnknownPacket>();
        packet->construct(id);
        break;
    }

    return packet;
}

void PacketReactor::react_packet(std::unique_ptr<Packet> packet)
{
    byte id = packet->get_id();

    S.print("ID4: ");
    S.println(id);


    switch (id)
    {
    case NullPacket::id:
        S.println("NULL");
        break;
    case PingPacket::id:
        S.println("PONG");
        PongPacket pong;
        unsigned long ts = read_unsigned_long(S);
        pong.construct(ts);
        S.println(ts);

        packet_sender.send(pong);
    }
}

void PacketReactor::tick()
{
    auto packet = read_packet();
    S.print("ID3: ");
    S.println(packet->id);
    S.print("GetID3: ");
    S.println(packet->get_id());
    react_packet(std::move(packet));
}
