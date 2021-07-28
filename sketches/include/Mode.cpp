#include <Mode.h>

#include <Joystick.h>

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
        mode = FIND_LIMITS;
        // enter_find_limits();
        break;
    case FIND_LIMITS:
        // exit_find_limits();
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