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

void setup()
{

    // Serial
    S.begin(BAUD_RATE);

#ifdef SERIALUSB
    while (!S)
        ;
#endif

    S.println("===================");
    S.println("CartPole Controller");
    S.println("===================");

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



        S.print("Switched to mode: ");
        S.println(ModeStrings[mode]);
    }

    if (mode == JOYSTICK)
    {

        if (b_left.isPressed())
        {
            if (!stepper1.isMoving())
            {
                stepper1.step(STEP_SIZE * LEFT);
                stepper2.step(STEP_SIZE * LEFT);

                S.println("Moving left...");
            }
        }
        else if (b_right.isPressed())
        {
            if (!stepper1.isMoving())
            {
                stepper1.step(STEP_SIZE * RIGHT);
                stepper2.step(STEP_SIZE * RIGHT);

                S.println("Moving right...");
            }
        }
        else if (b_status.isPressed())
        {
            S.print("Steps left: ");
            S.println(stepper1.getStepsLeft());

            S.print("Stall Guard: ");
            S.println(stepper1.getCurrentStallGuardReading());
        }

        stepper1.move();
        stepper2.move();
    }
    else if (mode == JOYSTICK_ACCELSTEPPER)
    {
        if (b_left.isPressed())
        {
            if (astepper1.distanceToGo() == 0)
            {
                astepper1.move(STEP_SIZE * STEPS_PER_MM * LEFT);
                astepper2.move(STEP_SIZE * STEPS_PER_MM * LEFT);

                S.println("Moving left...");
            }
        }
        else if (b_right.isPressed())
        {
            if (astepper1.distanceToGo() == 0)
            {
                astepper1.move(STEP_SIZE * STEPS_PER_MM * RIGHT);
                astepper2.move(STEP_SIZE * STEPS_PER_MM * RIGHT);

                S.println("Moving right...");
            }
        }

        asteppers_run();
    }
    else if (mode == DEBUG_ROTARY_ENCODERS)
    {
        // S.println(String(raw_angle_to_deg(rot_encoders.getRawAngle()), DEC));
    }
}
