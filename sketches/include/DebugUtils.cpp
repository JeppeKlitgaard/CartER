#include <DebugUtils.h>

#include <Init.h>
#include <LimitFinding.h>
#include <Steppers.h>

void print_debug_information() {
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
