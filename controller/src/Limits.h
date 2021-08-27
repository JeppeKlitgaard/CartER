#ifndef LIMITS_H
#define LIMITS_H

#include <CustomArduino.h>

#include <string>

#include <Bounce2.h>
#include <Steppers.h>

// Buttons
const int LIMIT_SW_BOUNCE_INTERVAL = 2; // debounce, in ms

extern Bounce2::Button limit_sw_left;
extern Bounce2::Button limit_sw_right;

const int LEFT_LIMIT_SW_PIN = 22;
const int RIGHT_LIMIT_SW_PIN = 23;

const float_t LIMIT_RETRACTION_DISTANCE = 5.0;
const float_t LIMIT_SAFETY_DISTANCE = 20.0;

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

inline const std::string LimitFindingModeStrings[] = {
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

enum class LimitCheckMode
{
    INIT,
    LEFT_SUPER_FAST,
    LEFT_FAST,
    LEFT_RETRACT,
    LEFT_SLOW,
    LEFT_POSITION_GET,
    REPOSITION,
    DONE,
};

inline const std::string LimitCheckModeStrings[] = {
    "INIT",
    "LEFT_SUPER_FAST",
    "LEFT_FAST",
    "LEFT_RETRACT",
    "LEFT_SLOW",
    "LEFT_POSITION_GET",
    "REPOSITION",
    "DONE",
};

const float_t LIMIT_CHECK_SUPER_FAST_MARGIN_DISTANCE = 10.0;

extern LimitCheckMode limit_check_mode;

const uint16_t JIGGLE_COUNT = 50;
const uint32_t JIGGLE_SPEED_DISTANCE = Speed::SUPER_FAST;

extern float_t track_length_distance;
extern int32_t track_length_steps;


// Limit finding
void toggle_limit_finding_mode();
void loop_limit_finding();
void enter_limit_finding();
void exit_limit_finding();
void do_limit_finding();

// Limit check
void toggle_limit_check_mode();
void loop_limit_check();
void do_limit_check();
void react_limit_check(int32_t left_limit_new_position);

// Jiggle
void do_jiggle();

#endif
