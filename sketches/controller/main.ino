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
#include <CommandAndControl.h>
#include <Joystick.h>

void setup()
{
    initialise();

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
    S.write(INITIAL_OUTPUT_STOP_MARKER, INITIAL_OUTPUT_STOP_MARKER_LENGTH);
}

void loop()
{
    // Update bouncer
    update_buttons();

    // Do any steps we need to do
    asteppers_run();

    if (b_mode.pressed())
    {
        DP("Current mode: ");
        DPL(ModeStrings[mode]);

        toggle_mode();

        DP("Switched to mode: ");
        DPL(ModeStrings[mode]);
    }

    else if (b_status.pressed())
    {
        print_debug_information();
    }
    else
    {
        switch (mode)
        {
        case JOYSTICK:
            loop_joystick();
            break;

        case DEBUG_ROTARY_ENCODERS:
            DPL(String(rot_encoder1.readAngleDeg(), DEC));
            break;

        case LIMIT_FINDING:
            loop_limit_finding();
            break;

        case COMMAND_AND_CONTROL:
            loop_command_and_control();
            break;

        default:
            DP("Mode unknown: ");
            DPL(ModeStrings[mode]);
            break;
        }
    }
}
