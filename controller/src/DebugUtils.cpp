#include <DebugUtils.h>

#include <Init.h>
#include <Limits.h>
#include <Steppers.h>
#include <Utils.h>
#include <TimerInterrupt.h>

void send_debug_information()
{
    packet_sender.send_debug("Free memory: " + std::to_string(free_memory()));

    packet_sender.send_debug("STEPPER_CURRENT: " + std::to_string(STEPPER_CURRENT));
    packet_sender.send_debug("STEPPER_MICROSTEPS: " + std::to_string(STEPPER_MICROSTEPS));
    packet_sender.send_debug("STEPPER_DISTANCE_PER_ROTATION: " + std::to_string(STEPPER_DISTANCE_PER_ROTATION));

    packet_sender.send_debug("SERIAL_BUFFER_SIZE:" + std::to_string(SERIAL_BUFFER_SIZE));

    packet_sender.send_debug("track_length_steps: " + std::to_string(track_length_steps));
    packet_sender.send_debug("track_length_distance: " + std::to_string(track_length_distance));

    packet_sender.send_debug("experiment_done: " + std::to_string(experiment_done));

    packet_sender.send_debug("run_safely: " + std::to_string(trigger_ctx.run_safely));
    packet_sender.send_debug("has_failed: " + std::to_string(trigger_ctx.has_failed));
    packet_sender.send_debug("run_mode: " + RunModeStrings[static_cast<uint8_t>(trigger_ctx.run_mode)]);

    packet_sender.send_debug("limit_finding_mode: " + LimitFindingModeStrings[static_cast<uint8_t>(limit_finding_mode)]);
    packet_sender.send_debug("limit_check_mode: " + LimitCheckModeStrings[static_cast<uint8_t>(limit_check_mode)]);
}
