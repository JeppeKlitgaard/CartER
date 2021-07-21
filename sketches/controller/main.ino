#include <Arduino.h>

#include <SPI.h>
#include <Wire.h>

#include <Bounce2.h>
#include <AccelStepper.h>

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

// Buttons
const int BOUNCE_INTERVAL = 5; // debounce, in ms

const int B_LEFT_PIN = 22;
const int B_RIGHT_PIN = 23;
const int B_STATUS_PIN = 24;

Bounce2::Button b_left = Bounce2::Button();   // LEFT1
Bounce2::Button b_right = Bounce2::Button();  // RIGHT
Bounce2::Button b_status = Bounce2::Button(); // STATUS

// Stepper
TMC26XStepper stepper1;
TMC26XStepper stepper2;

const unsigned int STEPPER_CURRENT = 1000; // mA
const int STEPPER_STEPS_PER_ROTATION = 200;
const unsigned int STEPPER_SPEED = 500;
const unsigned int MICROSTEPS = 16;
const unsigned int RANDOM_OFFTIME = 0;
const unsigned int STEP_SIZE = 50;

const int STEPPER1_CS_PIN = 9;
const int STEPPER1_DIR_PIN = 7;
const int STEPPER1_STEP_PIN = 8;

const int STEPPER2_CS_PIN = 6;
const int STEPPER2_DIR_PIN = 4;
const int STEPPER2_STEP_PIN = 5;

const int LEFT1 = -1;
const int LEFT2 = 1;
const int RIGHT1 = 1;
const int RIGHT2 = -1;

// Rotary Encoder - AS5600 v1.0
AMS_5600 rot_encoders;
// AMS_5600 rot_encoder2;


int angle1 = 0;
int angle2 = 0;
int langle1 = 0;
int langle2 = 0;

// I2C Multiplexer
const uint8_t TCA9548A_ADDR = 0x70;


// Selects one of the I2C ports on the multiplexer
void I2C_select(uint8_t i) {
    if (i > 7) {
        return;
    }

    Wire.beginTransmission(TCA9548A_ADDR);
    Wire.write(1 << i);
    Wire.endTransmission();
}

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
    b_left.attach(B_LEFT_PIN, INPUT_PULLUP); // LEFT1
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
    stepper1.setSpeed(STEPPER_SPEED);
    stepper2.setSpeed(STEPPER_SPEED);

    stepper1.setMicrosteps(MICROSTEPS);
    stepper2.setMicrosteps(MICROSTEPS);

    stepper1.getCurrentStallGuardReading(); // We need this to initialise, apparently
    stepper2.getCurrentStallGuardReading(); // We need this to initialise, apparently

    // stepper1.setStallGuardThreshold(-64, 1);

    // Rotary Encoders
    S.println("Configuring rotary encoders");

    I2C_select(1);
    S.println(rot_encoders.detectMagnet());

    if (rot_encoders.detectMagnet() == 0)
    {
        while (1)
        {
            if (rot_encoders.detectMagnet() == 1)
            {
                S.print("Current Magnitude: ");
                S.println(rot_encoders.getMagnitude());
                break;
            }
            else
            {
                S.println("Can not detect magnet");
            }
            delay(1000);
        }

    }

    // Finish up
    S.println("Config finished.");
    S.println("Starting loop.");
}

    void loop()
    {
        // Update bouncer
        b_left.update();
        b_right.update();
        b_status.update();

        if (b_left.isPressed())
        {
            if (!stepper1.isMoving())
            {
                stepper1.step(STEP_SIZE * LEFT1);
                stepper2.step(STEP_SIZE * LEFT2);

                S.println("Moving left...");
            }
        }
        else if (b_right.isPressed())
        {
            if (!stepper1.isMoving())
            {
                stepper1.step(STEP_SIZE * RIGHT1);
                stepper2.step(STEP_SIZE * RIGHT2);

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