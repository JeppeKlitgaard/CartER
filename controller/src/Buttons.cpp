#include <Buttons.h>

#include <DebugUtils.h>

Bounce2::Button b_left = Bounce2::Button();   // LEFT
Bounce2::Button b_right = Bounce2::Button();  // RIGHT
Bounce2::Button b_speed = Bounce2::Button();  // SPEED
Bounce2::Button b_status = Bounce2::Button(); // STATUS
Bounce2::Button b_mode = Bounce2::Button();   // MODE

void setup_buttons()
{
    packet_sender.send_debug("Configuring buttons");

    // LEFT
    b_left.attach(B_LEFT_PIN, INPUT_PULLUP);
    b_left.interval(BOUNCE_INTERVAL);
    b_left.setPressedState(LOW);

    // RIGHT
    b_right.attach(B_RIGHT_PIN, INPUT_PULLUP);
    b_right.interval(BOUNCE_INTERVAL);
    b_right.setPressedState(LOW);

    // SPEED
    b_speed.attach(B_SPEED_PIN, INPUT_PULLUP);
    b_speed.interval(BOUNCE_INTERVAL);
    b_speed.setPressedState(LOW);

    // STATUS
    b_status.attach(B_STATUS_PIN, INPUT_PULLUP);
    b_status.interval(BOUNCE_INTERVAL);
    b_status.setPressedState(LOW);

    // MODE
    b_mode.attach(B_MODE_PIN, INPUT_PULLUP);
    b_mode.interval(BOUNCE_INTERVAL);
    b_mode.setPressedState(LOW);
}

void update_buttons()
{
    b_left.update();
    b_right.update();
    b_speed.update();
    b_status.update();
    b_mode.update();
}