#include <Arduino.h>

#include <SPI.h>
#include <Wire.h>

#include <Bounce2.h>
#include <AccelStepper.h>

#include <I2CMultiplexer.h>
#include <RotaryEncoder.h>

#include <AS5600.h> // https://github.com/olkal/Seeed_Arduino_AS5600 <-- Fork
#include <TMC26XStepper.h>
// Note this is my fork of TMC260XStepper.h, not CainZ's version
// See: https://github.com/JeppeKlitgaard/TMC26XStepper

/* Stepper information:
 * Step angle: 1.8 deg (= 200 steps per rotation)
 * Max current: 1.33 A
 * Voltage rating: 2.8 V
 *
*/

// Definitions
#define S Serial

// General
const int BAUD_RATE = 115200;
enum Mode
{
    JOYSTICK,
    JOYSTICK_ACCELSTEPPER,
    DEBUG_ROTARY_ENCODERS,
};

String ModeStrings[] = {
    "JOYSTICK",
    "JOYSTICK_ACCELSTEPPER",
    "DEBUG_ROTARY_ENCODERS",
};

Mode mode = JOYSTICK;

// Buttons
const int BOUNCE_INTERVAL = 5; // debounce, in ms

const int B_MODE_PIN = 24;
const int B_LEFT_PIN = 22;
const int B_RIGHT_PIN = 23;
const int B_STATUS_PIN = 25;

Bounce2::Button b_mode = Bounce2::Button();   // MODE
Bounce2::Button b_left = Bounce2::Button();   // LEFT
Bounce2::Button b_right = Bounce2::Button();  // RIGHT
Bounce2::Button b_status = Bounce2::Button(); // STATUS

// Stepper Driver
TMC26XStepper stepper1;
TMC26XStepper stepper2;

const unsigned int STEPPER_CURRENT = 1000; // mA
const int STEPPER_STEPS_PER_ROTATION = 200;
const unsigned int STEPPER_SPEED = 500;
const unsigned int MICROSTEPS = 4;
const unsigned int RANDOM_OFFTIME = 0;
const unsigned int STEP_SIZE = 10;

const int STEPPER1_CS_PIN = 9;
const int STEPPER1_DIR_PIN = 7;
const int STEPPER1_STEP_PIN = 8;

const int STEPPER2_CS_PIN = 6;
const int STEPPER2_DIR_PIN = 4;
const int STEPPER2_STEP_PIN = 5;

// Stepper
AccelStepper astepper1 = AccelStepper(astepper1.DRIVER, STEPPER1_STEP_PIN, STEPPER1_DIR_PIN);
AccelStepper astepper2 = AccelStepper(astepper2.DRIVER, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);

const unsigned int STEPS_PER_MM = 100;
const unsigned int MAX_SPEED = 1000 * STEPS_PER_MM;
const unsigned int MAX_ACCELERATION = 500 * STEPS_PER_MM;

const int LEFT = -1;
const int RIGHT = 1;

// Rotary Encoder - AS5600 v1.0
AMS_5600 rot_encoders;
// AMS_5600 rot_encoder2;


void setup()
{
    // I2C
    Wire.begin();

    // Serial
    S.begin(BAUD_RATE);
    S.println("===================");
    S.println("CartPole Controller");
    S.println("===================");

    // Buttons
    S.println("Configuring buttons");
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

    // Steppers
    S.println("Configuring stepper drivers");

    // steps/rot, cs, dir, step, current
    stepper1.start(STEPPER_STEPS_PER_ROTATION, STEPPER1_CS_PIN, STEPPER1_DIR_PIN, STEPPER1_STEP_PIN, STEPPER_CURRENT);
    stepper2.start(STEPPER_STEPS_PER_ROTATION, STEPPER2_CS_PIN, STEPPER2_DIR_PIN, STEPPER2_STEP_PIN, STEPPER_CURRENT);

    //char constant_off_time, char blank_time, char hysteresis_start, char hysteresis_end, char hysteresis_decrement
    // stepper1.setSpreadCycleChopper(2, 24, 8, 6, 0);
    stepper1.setConstantOffTimeChopper(7, 54, 13, 12, 1);
    stepper2.setConstantOffTimeChopper(7, 54, 13, 12, 1);
    stepper1.setRandomOffTime(RANDOM_OFFTIME);
    stepper2.setRandomOffTime(RANDOM_OFFTIME);
    // stepper1.setSpeed(STEPPER_SPEED);
    // stepper2.setSpeed(STEPPER_SPEED);

    stepper1.setMicrosteps(MICROSTEPS);
    stepper2.setMicrosteps(MICROSTEPS);

    stepper1.getCurrentStallGuardReading(); // We need this to initialise, apparently
    stepper2.getCurrentStallGuardReading(); // We need this to initialise, apparently

    // stepper1.setStallGuardThreshold(-64, 1);

    // Stepper
    astepper1.setMaxSpeed(MAX_SPEED);
    astepper1.setAcceleration(MAX_ACCELERATION);
    astepper1.setPinsInverted(true, false, false);
    // astepper1.enableOutputs();

    astepper2.setMaxSpeed(MAX_SPEED);
    astepper2.setAcceleration(MAX_ACCELERATION);
    astepper2.setPinsInverted(false, false, false);
    // astepper2.enableOutputs();

    // Rotary Encoders
    S.println("Configuring rotary encoders");

    I2C_select(1);

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
}

void loop()
{
    // Update bouncer
    b_mode.update();
    astepper1.run();
    astepper2.run();
    b_left.update();
    astepper1.run();
    astepper2.run();
    b_right.update();
    astepper1.run();
    astepper2.run();
    // b_status.update();

    if (b_mode.pressed())
    {
        S.print("Current mode: ");
        S.println(ModeStrings[mode]);

        switch (mode)
        {
        case JOYSTICK:
            mode = JOYSTICK_ACCELSTEPPER;
            break;
        case JOYSTICK_ACCELSTEPPER:
            mode = DEBUG_ROTARY_ENCODERS;
            break;
        case DEBUG_ROTARY_ENCODERS:
            mode = JOYSTICK;
            break;
        }

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
    else if (mode == JOYSTICK_ACCELSTEPPER) {
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
        astepper1.run();
        astepper2.run();
    }
    else if (mode == DEBUG_ROTARY_ENCODERS)
    {
        // S.println(String(raw_angle_to_deg(rot_encoders.getRawAngle()), DEC));
    }

}
