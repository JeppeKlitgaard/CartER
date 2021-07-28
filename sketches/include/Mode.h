#ifndef MODE_H
#define MODE_H

#include <Arduino.h>

// Mode
enum Mode
{
    JOYSTICK,
    DEBUG_ROTARY_ENCODERS,
    FIND_LIMITS,
    COMMAND_AND_CONTROL,
};

const String ModeStrings[] = {
    "JOYSTICK",
    "DEBUG_ROTARY_ENCODERS",
    "FIND_LIMITS",
    "COMMAND_AND_CONTROL",
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
