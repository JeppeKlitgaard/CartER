#ifndef BUTTONS_H_INCLUDED
#define BUTTONS_H_INCLUDED

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wregister"
#include <Bounce2.h>
#pragma GCC diagnostic pop

// Buttons
const int BOUNCE_INTERVAL = 5; // debounce, in ms

extern Bounce2::Button b_left;   // LEFT
extern Bounce2::Button b_right;  // RIGHT
extern Bounce2::Button b_speed;  // SPEED
extern Bounce2::Button b_status; // STATUS
extern Bounce2::Button b_mode;   // MODE

const int B_LEFT_PIN = 14;
const int B_RIGHT_PIN = 15;
const int B_SPEED_PIN = 16;
const int B_STATUS_PIN = 17;
const int B_MODE_PIN = 18;

void setup_buttons();
void update_buttons();

#endif
