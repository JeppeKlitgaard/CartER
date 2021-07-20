#include <SPI.h>
#include <Bounce2.h>
#include <AccelStepper.h>
#include <TMC26XStepper.h>
// Note this is my fork of TMC260XStepper.h, not CainZ's version
// See: https://github.com/JeppeKlitgaard/TMC26XStepper

/* Stepper information:
 * Step angle: 1.8 deg (= 200 steps per rotation)
 * Max current: 1.33 A
 * Voltage rating: 2.8 V
 *
*/

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

void setup()
{
    Serial.begin(BAUD_RATE);
    Serial.println("===================");
    Serial.println("CartPole Controller");
    Serial.println("===================");

    Serial.println("Configuring buttons");
    b_left.attach(B_LEFT_PIN, INPUT_PULLUP); // LEFT1
    b_left.interval(BOUNCE_INTERVAL);
    b_left.setPressedState(LOW);

    b_right.attach(B_RIGHT_PIN, INPUT_PULLUP); // RIGHT
    b_right.interval(BOUNCE_INTERVAL);
    b_right.setPressedState(LOW);

    b_status.attach(B_STATUS_PIN, INPUT_PULLUP); // STATUS
    b_status.interval(BOUNCE_INTERVAL);
    b_status.setPressedState(LOW);

    Serial.println("Configuring stepper drivers");

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
    Serial.println("Config finished.");
    Serial.println("Starting loop.");
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

            Serial.println("Moving left...");
        }
    }
    else if (b_right.isPressed())
    {
        if (!stepper1.isMoving())
        {
            stepper1.step(STEP_SIZE * RIGHT1);
            stepper2.step(STEP_SIZE * RIGHT2);

            Serial.println("Moving right...");
        }
    }
    else if (b_status.isPressed())
    {
        Serial.print("Steps left: ");
        Serial.println(stepper1.getStepsLeft());

        Serial.print("Stall Guard: ");
        Serial.println(stepper1.getCurrentStallGuardReading());
    }

    stepper1.move();
    stepper2.move();
}