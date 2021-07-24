#include <Mode.h>

void toggle_mode() {
    switch (mode)
    {
    case JOYSTICK:
        mode = JOYSTICK_ACCELSTEPPER;
        break;
    case JOYSTICK_ACCELSTEPPER:
        mode = DEBUG_ROTARY_ENCODERS;
        break;
    case DEBUG_ROTARY_ENCODERS:
        mode = ONE_CARRIAGE_COMMAND_AND_CONTROL;
        break;
    case ONE_CARRIAGE_COMMAND_AND_CONTROL:
        mode = JOYSTICK;
        break;
    }
}