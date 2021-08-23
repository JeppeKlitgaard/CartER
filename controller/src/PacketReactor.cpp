#include <PacketReactor.h>

#include <memory>

#include <Protocol.h>
#include <Init.h>
#include <PacketSender.h>
#include <BufferUtils.h>
#include <DebugUtils.h>
#include <PString.h>
#include <Steppers.h>
#include <CustomAccelStepper.h>
#include <Limits.h>
#include <Experiment.h>

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

        packet_sender.send_debug("NUL");
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

    case RequestDebugInfoPacket::id:
    {
        send_debug_information();
        break;
    }

    case SetPositionPacket::id:
    {

        std::unique_ptr<SetPositionPacket> packet = _read_and_construct_packet<SetPositionPacket>();

        CustomAccelStepper &astepper = get_astepper_by_id(packet->cart_id);

        switch (packet->operation)
        {
        case SetOperation::ADD:
            astepper.move(packet->value);
            break;
        case SetOperation::EQUAL:
            astepper.moveTo(packet->value);
            break;
        case SetOperation::SUBTRACT:
            astepper.move(-packet->value);
            break;
        case SetOperation::NUL:
            break;
        }

        break;
    }

    case SetVelocityPacket::id:
    {
        std::unique_ptr<SetVelocityPacket> packet = _read_and_construct_packet<SetVelocityPacket>();

        CustomAccelStepper &astepper = get_astepper_by_id(packet->cart_id);

        switch (packet->operation)
        {
        case SetOperation::ADD:
            astepper.setSpeed(astepper.speed() + static_cast<float_t>(packet->value));
            break;
        case SetOperation::EQUAL:
            astepper.setSpeed(static_cast<float_t>(packet->value));
            break;
        case SetOperation::SUBTRACT:
            astepper.setSpeed(astepper.speed() - static_cast<float_t>(packet->value));
            break;
        case SetOperation::NUL:
            break;
        }

        break;
    }

    case SetMaxVelocityPacket::id:
    {
        std::unique_ptr<SetVelocityPacket> packet = _read_and_construct_packet<SetVelocityPacket>();

        CustomAccelStepper &astepper = get_astepper_by_id(packet->cart_id);

        switch (packet->operation)
        {
        case SetOperation::ADD:
            astepper.setMaxSpeed(std::max(astepper.maxSpeed() + static_cast<float_t>(packet->value), MAX_SETTABLE_SPEED));
            break;
        case SetOperation::EQUAL:
            astepper.setMaxSpeed(static_cast<float_t>(packet->value));
            break;
        case SetOperation::SUBTRACT:
            astepper.setMaxSpeed(std::max(astepper.maxSpeed() - static_cast<float_t>(packet->value), (float_t)0.0));
            break;
        case SetOperation::NUL:
            break;
        }

        break;
    }

    case FindLimitsPacket::id:
    {
        do_limit_finding();
        break;
    }

    case CheckLimitPacket::id:
    {
        do_limit_check();
        break;
    }

    case DoJigglePacket::id:
    {
        do_jiggle();
        break;
    }

    case ExperimentStartPacket::id:
    {
        experiment_start();
        break;
    }

    case ExperimentStopPacket::id:
    {
        experiment_stop();
        break;
    }

    default:
        std::unique_ptr<UnknownPacket> packet = std::make_unique<UnknownPacket>();
        packet->construct(id);

        // Reaction
        packet_sender.send_debug("Received unknown packet with ID: " + std::to_string(packet->observed_id));

        break;
    }
}

void experiment_done_trigger()
{
    experiment_done = true;
    asteppers_stop();

    std::unique_ptr<ExperimentDonePacket> packet = std::make_unique<ExperimentDonePacket>();
    packet_sender.send(std::move(packet));
};