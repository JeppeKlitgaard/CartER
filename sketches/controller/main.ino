#include <Arduino.h>

#include <Init.h>
#include <DebugUtils.h>

#include <SPI.h>
#include <Wire.h>

#include <Mode.h>
#include <Buttons.h>
#include <Steppers.h>
#include <I2CMultiplexer.h>
#include <RotaryEncoder.h>
#include <LimitFinding.h>

void setup()
{
    // Serial
    S.begin(BAUD_RATE);

// If using Serial over USB
// This is faster, but also more annoying for development
#ifdef SERIALUSB
    while (!S)
        ;
#endif

    S.println("===================");
    S.println("CartPole Controller");
    S.println("===================");

#ifdef DEBUG
    print_debug_information();
#endif

    // I2C
    DPL("Setting up I2C.");
    Wire.begin();

    // Buttons
    setup_buttons();

    // Steppers
    setup_steppers();

    // Rotary Encoders
    setup_rotary_encoders();

    // Limit Switches
    setup_limit_switches();

    // Finish up
    S.println("Config finished.");
    S.println("Starting loop.");
    S.println("--------------");
    S.println();
}

void loop()
{
    // Update bouncer
    update_buttons();

    // Do any steps we need to do
    asteppers_run();

    if (b_speed.pressed()) {
        asteppers_toggle_enabled();
    }

    if (b_mode.pressed())
    {
        DP("Current mode: ");
        DPL(ModeStrings[mode]);

        toggle_mode();

        DP("Switched to mode: ");
        DPL(ModeStrings[mode]);
    }

    else if (mode == JOYSTICK)
    {
        if (b_left.isPressed())
        {
            if (astepper1.distanceToGo() == 0)
            {
                astepper1.moveDistance(STEPPER_STEP_DISTANCE * LEFT);
                DPL("Moving left...");
            }
        }
        else if (b_right.isPressed())
        {
            if (astepper1.distanceToGo() == 0)
            {
                astepper1.moveDistance(STEPPER_STEP_DISTANCE * RIGHT);
                DPL("Moving right...");
            }
        }

        // Call again to ensure we call this quickly enough
        asteppers_run();
    }
    else if (mode == DEBUG_ROTARY_ENCODERS)
    {
        DPL(String(rot_encoder1.readAngleDeg(), DEC));
    }

    else if (mode == FIND_LIMITS)
    {
        loop_limit_finding();
    }

    else
    {
        DP("Mode unknown: ");
        DPL(ModeStrings[mode]);
    }
}
