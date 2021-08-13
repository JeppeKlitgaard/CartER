#ifndef LIMIT_FINDING_H
#define LIMIT_FINDING_H

#include <CustomArduino.h>
#include <Bounce2.h>

// Buttons
const int LIMIT_SW_BOUNCE_INTERVAL = 1; // debounce, in ms

extern Bounce2::Button limit_sw_left;
extern Bounce2::Button limit_sw_right;

const int LEFT_LIMIT_SW_PIN = 22;
const int RIGHT_LIMIT_SW_PIN = 23;

const int LIMIT_SAFETY_DISTANCE_STEPS = 50;

void setup_limit_switches();
void update_limit_switches();

// Modes
enum class LimitFindingMode
{
    INIT,
    LEFT_FAST,
    LEFT_RETRACT,
    LEFT_SLOW,
    LEFT_POSITION_SET,
    RIGHT_FAST,
    RIGHT_RETRACT,
    RIGHT_SLOW,
    REPOSITION,
    DONE,
};

const String LimitFindingModeStrings[] = {
    "INIT",
    "LEFT_FAST",
    "LEFT_RETRACT",
    "LEFT_SLOW",
    "LEFT_POSITION_SET",
    "RIGHT_FAST",
    "RIGHT_RETRACT",
    "RIGHT_SLOW",
    "REPOSITION",
    "DONE",
};

extern LimitFindingMode limit_finding_mode;
extern float_t track_length_distance;
extern int32_t track_length_steps;

void toggle_limit_finding_mode();

void loop_limit_finding();
void enter_limit_finding();
void exit_limit_finding();
void do_limit_finding();

#endif
