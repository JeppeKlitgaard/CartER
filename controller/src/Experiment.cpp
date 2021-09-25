#include <Experiment.h>

#include <memory>

#include <Init.h>
#include <Steppers.h>
#include <RotaryEncoder.h>
#include <Protocol.h>
#include <Mode.h>
#include <Limits.h>
#include <TimerInterrupt.h>
#include <Utils.h>

uint32_t last_observation_us = 0;
uint32_t last_memory_us = 0;

void observation_tick()
{
    if (!is_observing)
    {
        return;
    }

    if (static_cast<uint32_t>(micros() - last_observation_us) >= OBSERVATION_INTERVAL_US)
    {
        // Update last observation
        last_observation_us = micros();

        send_observation(1);

        if (configuration == TWO_CARRIAGES)
        {
            send_observation(2);
        }
    }

    if (static_cast<uint32_t>(micros()) - last_memory_us >= MEMORY_INTERVAL_US)
    {
        // Update last memory
        last_memory_us = micros();

        std::unique_ptr<ExperimentInfoPacket> packet = std::make_unique<ExperimentInfoPacket>();
        packet->construct(ExperimentInfoSpecifier::AVAILABLE_MEMORY, 0, free_memory());

        packet_sender.send(std::move(packet));
    }
}

void send_observation(uint8_t cart_id)
{
    uint32_t timestamp_micros = micros();

    CustomAccelStepper &astepper = get_astepper_by_id(cart_id);
    int32_t position_step = astepper.currentPosition();

    CustomAMS_5600 *rot_encoder = get_rot_encoder_by_id(cart_id);
    float_t angle_deg = rot_encoder->readAngleDeg();

    std::unique_ptr<ObservationPacket> packet = std::make_unique<ObservationPacket>();

    packet->construct(timestamp_micros, cart_id, position_step, angle_deg);

    packet_sender.send(std::move(packet));
}

void experiment_start()
{
    packet_sender.send_debug("Starting experiment...");

    asteppers_stop();

    experiment_mode = ExperimentMode::RUNNING;
    limit_finding_mode = LimitFindingMode::DONE;
    limit_check_mode = LimitCheckMode::DONE;

    is_observing = true;

    std::unique_ptr<ExperimentStartPacket> packet = std::make_unique<ExperimentStartPacket>();

    packet->construct(micros());

    packet_sender.send(std::move(packet));
}

void experiment_stop()
{
    packet_sender.send_debug("Stopping experiment...");

    asteppers_stop();

    std::unique_ptr<ExperimentStopPacket> stop_pkt = std::make_unique<ExperimentStopPacket>();
    packet_sender.send(std::move(stop_pkt));

    experiment_mode = ExperimentMode::DONE;
    is_observing = false;

    std::unique_ptr<ExperimentDonePacket> done_pkt = std::make_unique<ExperimentDonePacket>();
    done_pkt->construct(0, FailureMode::NUL);
    packet_sender.send(std::move(done_pkt));
}

/**
 * Called shortly after an unsafe move has been made.
 *
 * We don't mark experiment_done since we wish to keep sending observations.
 * It is up to commander to handle behaviour after
 */
void unsafe_run_trigger()
{
    asteppers_stop();

    packet_sender.send_info("Stopped steppers.");

    experiment_mode = ExperimentMode::FAILED;

    std::unique_ptr<SoftLimitReachedPacket> limit_reached_pkt = std::make_unique<SoftLimitReachedPacket>();
    packet_sender.send(std::move(limit_reached_pkt));

    std::unique_ptr<ExperimentInfoPacket> failure_mode_pkt = std::make_unique<ExperimentInfoPacket>();
    failure_mode_pkt->construct(ExperimentInfoSpecifier::FAILURE_MODE, failure_cart_id, failure_mode);
    packet_sender.send(std::move(failure_mode_pkt));
}
