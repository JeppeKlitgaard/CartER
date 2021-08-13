#ifndef MODE_H
#define MODE_H

#include <CustomArduino.h>

// Mode
enum Mode
{
    JOYSTICK,
    DEBUG_ROTARY_ENCODERS,
    LIMIT_FINDING,
    COMMAND_AND_CONTROL,
};

const String ModeStrings[] = {
    "JOYSTICK",
    "DEBUG_ROTARY_ENCODERS",
    "LIMIT_FINDING",
    "COMMAND_AND_CONTROL",
};

extern Mode mode;

void set_mode(const Mode target_mode);
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

// Failure
enum class FailureMode {
    POSITION_RIGHT,
    POSITION_LEFT,

    ANGLE_RIGHT,
    ANGLE_LEFT,

    OTHER,
};

const String FailureModeStrings[] = {
    "position/right",
    "position/left",

    "angle/right",
    "angle/left",

    "other/other",
};

extern const Configuration configuration;
extern FailureMode failure_mode;
extern uint8_t failure_cart_id;

#endif
