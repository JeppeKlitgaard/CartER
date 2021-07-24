#include <Buttons.h>

#include <DebugUtils.h>

Bounce2::Button b_mode = Bounce2::Button();   // MODE
Bounce2::Button b_left = Bounce2::Button();   // LEFT
Bounce2::Button b_right = Bounce2::Button();  // RIGHT
Bounce2::Button b_status = Bounce2::Button(); // STATUS

void setup_buttons()
{
    DPL("Configuring buttons.");
    b_mode.attach(B_MODE_PIN, INPUT_PULLUP); // LEFT
    b_mode.interval(BOUNCE_INTERVAL);
    b_mode.setPressedState(LOW);

    b_left.attach(B_LEFT_PIN, INPUT_PULLUP); // LEFT
    b_left.interval(BOUNCE_INTERVAL);
    b_left.setPressedState(LOW);

    b_right.attach(B_RIGHT_PIN, INPUT_PULLUP); // RIGHT
    b_right.interval(BOUNCE_INTERVAL);
    b_right.setPressedState(LOW);

    b_status.attach(B_STATUS_PIN, INPUT_PULLUP); // STATUS
    b_status.interval(BOUNCE_INTERVAL);
    b_status.setPressedState(LOW);
}

void update_buttons() {
    b_mode.update();
    b_left.update();
    b_right.update();
}