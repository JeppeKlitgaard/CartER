#include <Joystick.h>

#include <DebugUtils.h>

#include <Buttons.h>
#include <Steppers.h>

void loop_joystick()
{
    // Speed control
    if (b_speed.pressed())
    {
        asteppers_toggle_enabled();
    }

    if (b_left.isPressed())
    {
        if (astepper1.distanceToGo() == 0)
        {
            astepper1.moveDistance(STEPPER_STEP_DISTANCE * LEFT);
            packet_sender.send_debug("Moving left...");
        }
    }
    else if (b_right.isPressed())
    {
        if (astepper1.distanceToGo() == 0)
        {
            astepper1.moveDistance(STEPPER_STEP_DISTANCE * RIGHT);
            packet_sender.send_debug("Moving right...");
        }
    }

    // Call again to ensure we call this quickly enough
    asteppers_run();
}

void enter_joystick()
{
    asteppers_enable();
}

void exit_joystick()
{
    asteppers_disable();
}
