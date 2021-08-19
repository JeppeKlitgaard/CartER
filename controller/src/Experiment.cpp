#include <Experiment.h>

#include <memory>

#include <Init.h>
#include <Steppers.h>
#include <RotaryEncoder.h>
#include <Protocol.h>
#include <Mode.h>

uint32_t last_observation_us = 0;

void observation_tick()
{
    if (experiment_mode != ExperimentMode::RUNNING) {
        return;
    }

    if (abs(micros() - last_observation_us) >= OBSERVATION_INTERVAL_US)
    {
        // Update last observation
        last_observation_us = micros();

        send_observation(1);

        if (configuration == TWO_CARRIAGES)
        {
            send_observation(2);
        }
    }
}

void send_observation(uint8_t cart_id)
{
    uint32_t timestamp_micros = micros();

    CustomAccelStepper &astepper = get_astepper_by_id(cart_id);
    int32_t position_step = astepper.currentPosition();

    CustomAMS_5600 &rot_encoder = get_rot_encoder_by_id(cart_id);
    float_t angle_deg = rot_encoder.readAngleDeg();

    std::unique_ptr<ObservationPacket> packet = std::make_unique<ObservationPacket>();

    packet->construct(timestamp_micros, cart_id, position_step, angle_deg);

    packet_sender.send(std::move(packet));
}

void experiment_start() {
    packet_sender.send_debug("Starting experiment...");

    experiment_mode = ExperimentMode::RUNNING;

    std::unique_ptr<ExperimentStartPacket> packet = std::make_unique<ExperimentStartPacket>();

    packet->construct(micros());

    packet_sender.send(std::move(packet));
}

void experiment_stop() {
    packet_sender.send_debug("Stopping experiment...");

    std::unique_ptr<ExperimentStopPacket> stop_pkt = std::make_unique<ExperimentStopPacket>();
    packet_sender.send(std::move(stop_pkt));

    experiment_mode = ExperimentMode::DONE;

    std::unique_ptr<ExperimentDonePacket> done_pkt = std::make_unique<ExperimentDonePacket>();
    done_pkt->construct(0, FailureMode::NUL);
    packet_sender.send(std::move(done_pkt));

}
