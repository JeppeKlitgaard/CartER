#include <DebugUtils.h>

#include <Init.h>
#include <Limits.h>
#include <Steppers.h>
#include <Utils.h>

void print_debug_information()
{
    S.println("=======================");
    S.println("START DEBUG INFORMATION");
    S.println("=======================");

    // Steppers
    S.print("STEPPER_CURRENT: ");
    S.println(STEPPER_CURRENT);

    S.print("STEPPER_MICROSTEPS: ");
    S.println(STEPPER_MICROSTEPS);

    S.print("STEPPER_DISTANCE_PER_ROTATION: ");
    S.println(STEPPER_DISTANCE_PER_ROTATION);

    S.println("=====================");
    S.println("END DEBUG INFORMATION");
    S.println("=====================");
    S.println();
}

void send_debug_information()
{
    packet_sender.send_debug("Free memory: " + std::to_string(free_memory()));
    packet_sender.send_debug("STEPPER_CURRENT: " + std::to_string(STEPPER_CURRENT));
    packet_sender.send_debug("STEPPER_MICROSTEPS: " + std::to_string(STEPPER_MICROSTEPS));
    packet_sender.send_debug("STEPPER_DISTANCE_PER_ROTATION: " + std::to_string(STEPPER_DISTANCE_PER_ROTATION));
    packet_sender.send_debug("track_length_steps: " + std::to_string(track_length_steps));
    packet_sender.send_debug("track_length_distance: " + std::to_string(track_length_distance));
    packet_sender.send_debug("experiment_done: " + std::to_string(experiment_done));
}
