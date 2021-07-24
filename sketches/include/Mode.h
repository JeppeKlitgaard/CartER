#ifndef MODE_H
#define MODE_H

enum Mode
{
    JOYSTICK,
    JOYSTICK_ACCELSTEPPER,
    DEBUG_ROTARY_ENCODERS,
    ONE_CARRIAGE_COMMAND_AND_CONTROL,
};

const String ModeStrings[] = {
    "JOYSTICK",
    "JOYSTICK_ACCELSTEPPER",
    "DEBUG_ROTARY_ENCODERS",
    "ONE_CARRIAGE_COMMAND_AND_CONTROL",
};

extern Mode mode;

void toggle_mode;

#endif
