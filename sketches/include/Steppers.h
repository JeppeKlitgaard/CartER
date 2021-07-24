#ifndef STEPPERS_H_INCLUDED
#define STEPPERS_H_INCLUDED

#include <AccelStepper.h>
#include <TMC26XStepper.h>
// Note this is my fork of TMC260XStepper.h, not CainZ's version
// See: https://github.com/JeppeKlitgaard/TMC26XStepper


// Stepper Driver
extern TMC26XStepper stepper1;
extern TMC26XStepper stepper2;

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
extern AccelStepper astepper1;
extern AccelStepper astepper2;

const unsigned int STEPS_PER_MM = 100;
const unsigned int MAX_SPEED = 1000 * STEPS_PER_MM;
const unsigned int MAX_ACCELERATION = 500 * STEPS_PER_MM;

enum Direction {
    LEFT = -1,
    RIGHT = 1,
};

void setup_steppers();
void setup_stepper_drivers();
void start_stepper_drivers();
void setup_asteppers();
void asteppers_run();

#endif
