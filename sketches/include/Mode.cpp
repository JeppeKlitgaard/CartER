#include <Mode.h>

void toggle_mode() {
    switch (mode)
    {
    case JOYSTICK:
        mode = DEBUG_ROTARY_ENCODERS;
        break;
    case DEBUG_ROTARY_ENCODERS:
        mode = ONE_CARRIAGE_COMMAND_AND_CONTROL;
        break;
    case ONE_CARRIAGE_COMMAND_AND_CONTROL:
        mode = FIND_LIMITS;
        break;
    case FIND_LIMITS:
        mode = JOYSTICK;
        break;
    }
}