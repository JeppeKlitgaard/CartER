// #define SERIALUSB

#include <Arduino.h>

#include <DebugUtils.h>

#include <SPI.h>
#include <Wire.h>

#include <Init.h>
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

    // if (rot_encoders.detectMagnet() == 0)
    // {
    //     while (1)
    //     {
    //         if (rot_encoders.detectMagnet() == 1)
    //         {
    //             S.print("Current Magnitude: ");
    //             S.println(rot_encoders.getMagnitude());
    //             break;
    //         }
    //         else
    //         {
    //             S.println("Can not detect magnet");
    //         }
    //         delay(1000);
    //     }
    // }

    setup_limit_switches();

    // Finish up
    S.println("Config finished.");
    S.println("Starting loop.");
    S.println("--------------");
}

void loop()
{
    // Update bouncer
    update_buttons();

    asteppers_run();

    if (b_mode.pressed())
    {
        S.print("Current mode: ");
        S.println(ModeStrings[mode]);

        toggle_mode();

        S.print("Switched to mode: ");
        S.println(ModeStrings[mode]);
    }

    else if (mode == JOYSTICK)
    {
        if (b_left.isPressed())
        {
            if (astepper1.distanceToGo() == 0)
            {
                astepper1.moveDistance(STEPPER_STEP_DISTANCE * LEFT);

                S.println("Moving left...");
            }
        }
        else if (b_right.isPressed())
        {
            if (astepper1.distanceToGo() == 0)
            {
                astepper1.moveDistance(STEPPER_STEP_DISTANCE * RIGHT);

                S.println("Moving right...");
            }
        }

        asteppers_run();
    }
    else if (mode == DEBUG_ROTARY_ENCODERS)
    {
        // S.println(String(raw_angle_to_deg(rot_encoders.getRawAngle()), DEC));
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
