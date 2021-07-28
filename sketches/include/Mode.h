#ifndef MODE_H
#define MODE_H

#include <Arduino.h>

// Mode
enum Mode
{
    JOYSTICK,
    DEBUG_ROTARY_ENCODERS,
    ONE_CARRIAGE_COMMAND_AND_CONTROL,
    FIND_LIMITS,
};

const String ModeStrings[] = {
    "JOYSTICK",
    "DEBUG_ROTARY_ENCODERS",
    "ONE_CARRIAGE_COMMAND_AND_CONTROL",
    "FIND_LIMITS",
};

extern Mode mode;

void toggle_mode();

// Configuration
enum Configuration {
    ONE_CARRIAGES,
    TWO_CARRIAGES,
};

const String ConfigurationStrings[] ={
    "ONE_CARRIAGES",
    "TWO_CARRIAGES",
};

extern const Configuration configuration;

#endif
