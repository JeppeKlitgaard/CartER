#include <Mode.h>

#include <Joystick.h>
#include <LimitFinding.h>

void toggle_mode() {
    switch (mode)
    {
    case JOYSTICK:
        exit_joystick();
        mode = DEBUG_ROTARY_ENCODERS;
        // enter_rot_encoders();
        break;
    case DEBUG_ROTARY_ENCODERS:
        // exit_rot_encoders();
        mode = LIMIT_FINDING;
        enter_limit_finding();
        break;
    case LIMIT_FINDING:
        exit_limit_finding();
        mode = COMMAND_AND_CONTROL;
        // enter_command_and_control();
        break;
    case COMMAND_AND_CONTROL:
        // exit_command_and_control();
        mode = JOYSTICK;
        enter_joystick();
        break;
    }
}