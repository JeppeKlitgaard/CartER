#ifndef MODE_H
#define MODE_H

#include <CustomArduino.h>

#include <string>

// Mode
enum Mode
{
    JOYSTICK,
    DEBUG_ROTARY_ENCODERS,
    LIMIT_FINDING,
    COMMAND_AND_CONTROL,
};

inline const std::string ModeStrings[] = {
    "JOYSTICK",
    "DEBUG_ROTARY_ENCODERS",
    "LIMIT_FINDING",
    "COMMAND_AND_CONTROL",
};

extern Mode mode;

void set_mode(const Mode target_mode);
void toggle_mode();

// Configuration
enum Configuration
{
    ONE_CARRIAGES,
    TWO_CARRIAGES,
};

const String ConfigurationStrings[] = {
    "ONE_CARRIAGES",
    "TWO_CARRIAGES",
};

// Failure
enum class FailureMode : int8_t
{
    NUL = 0,

    POSITION_LEFT = -1,
    POSITION_RIGHT = 1,

    ANGLE_LEFT = -2,
    ANGLE_RIGHT = 2,

    OTHER = 127,
};

const String FailureModeStrings[] = {
    "position/right",
    "position/left",

    "angle/right",
    "angle/left",

    "other/other",
};

enum class ExperimentMode {
    RUNNING,
    FAILED,
    DONE,
};

extern const Configuration configuration;
extern FailureMode failure_mode;
extern uint8_t failure_cart_id;
extern ExperimentMode experiment_mode;

#endif
