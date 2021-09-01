#include <CustomArduino.h>

#include <string>

#include <Init.h>
#include <DebugUtils.h>

#include <SPI.h>
#include <Wire.h>

#include <Mode.h>
#include <Buttons.h>
#include <Steppers.h>
#include <I2CMultiplexer.h>
#include <RotaryEncoder.h>
#include <Limits.h>
#include <CommandAndControl.h>
#include <Joystick.h>
#include <TimerInterrupt.h>

void setup()
{
    initialise();

    // Serial
    S.begin(BAUDRATE);

// If using Serial over USB
// This is faster, but also more annoying for development
#ifdef SERIALUSB
    while (!S)
        ;
#endif
    packet_sender.send_info("=== Cartpole Controller ===");

    send_debug_information();

    // I2C
    packet_sender.send_debug("Setting up I2C");
    Wire.begin();

    // Buttons
    setup_buttons();

    // Steppers
    setup_steppers();

    // I2C Multiplexer
    setup_I2C_multiplexer();

    // Rotary Encoders
    setup_rotary_encoders();

    // Limit Switches
    setup_limit_switches();

    // Timer interrupt
    setup_timer_interrupt();

    // Finish up
    packet_sender.send_debug("Config finished");
    packet_sender.send_debug("Starting loop");
    S.write(INITIAL_OUTPUT_STOP_MARKER, INITIAL_OUTPUT_STOP_MARKER_LENGTH);
}

void loop()
{
    // TODO Fix up modes. Uncomment below to activate other modes for now.
    // // Update bouncer
    // update_buttons();

    // // Do any steps we need to do
    // asteppers_run();

    if (b_mode.pressed())
    {
        packet_sender.send_info("Current mode: " + ModeStrings[mode]);

        toggle_mode();

        packet_sender.send_info("Switched to mode: " + ModeStrings[mode]);
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
            packet_sender.send_debug(std::to_string(rot_encoder1.readAngleDeg()));
            break;

        case LIMIT_FINDING:
            loop_limit_finding();
            break;

        case COMMAND_AND_CONTROL:
            loop_command_and_control();
            break;

        default:
            packet_sender.send_error("Mode unknown: " + ModeStrings[mode]);
            break;
        }
    }
}
