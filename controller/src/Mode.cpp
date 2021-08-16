#include <Mode.h>

#include <Joystick.h>
#include <Limits.h>

void set_mode(const Mode target_mode)
{
    Mode source_mode = mode;

    // Exit old mode
    switch (source_mode)
    {
    case JOYSTICK:
        exit_joystick();
        break;
    case DEBUG_ROTARY_ENCODERS:
        break;
    case LIMIT_FINDING:
        exit_limit_finding();
        break;
    case COMMAND_AND_CONTROL:
        break;
    }

    // Set and enter new mode
    switch (target_mode)
    {
    case JOYSTICK:
        mode = JOYSTICK;
        enter_joystick();
        break;
    case DEBUG_ROTARY_ENCODERS:
        mode = DEBUG_ROTARY_ENCODERS;
        break;
    case LIMIT_FINDING:
        mode = LIMIT_FINDING;
        enter_limit_finding();
        break;
    case COMMAND_AND_CONTROL:
        mode = COMMAND_AND_CONTROL;
        break;
    }
}

void toggle_mode()
{
    switch (mode)
    {
    case JOYSTICK:
        set_mode(DEBUG_ROTARY_ENCODERS);
        break;
    case DEBUG_ROTARY_ENCODERS:
        set_mode(LIMIT_FINDING);
        break;
    case LIMIT_FINDING:
        set_mode(COMMAND_AND_CONTROL);
        break;
    case COMMAND_AND_CONTROL:
        set_mode(JOYSTICK);
        break;
    }
}