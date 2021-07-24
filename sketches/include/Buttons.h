#ifndef BUTTONS_H_INCLUDED
#define BUTTONS_H_INCLUDED

#include <Bounce2.h>

// Buttons
const int BOUNCE_INTERVAL = 5; // debounce, in ms

extern Bounce2::Button b_mode;   // MODE
extern Bounce2::Button b_left;   // LEFT
extern Bounce2::Button b_right;  // RIGHT
extern Bounce2::Button b_status; // STATUS

const int B_MODE_PIN = 24;
const int B_LEFT_PIN = 22;
const int B_RIGHT_PIN = 23;
const int B_STATUS_PIN = 25;

void setup_buttons();
void update_buttons();

#endif
