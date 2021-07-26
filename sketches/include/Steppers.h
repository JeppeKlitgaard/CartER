#ifndef STEPPERS_H_INCLUDED
#define STEPPERS_H_INCLUDED

#include <Steppers.h>
#include <CustomAccelStepper.h>

#include <TMC26XStepper.h>
// Note this is my fork of TMC260XStepper.h, not CainZ's version
// See: https://github.com/JeppeKlitgaard/TMC26XStepper


// Stepper Driver
extern TMC26XStepper stepper1;
extern TMC26XStepper stepper2;

const unsigned int STEPPER_CURRENT = 1000; // mA
const int STEPPER_STEPS_PER_ROTATION = 200;
const float STEPPER_DRIVE_GEAR_OD_MM = 13.0;
const unsigned int STEPPER_MICROSTEPS = 4;
const unsigned int STEPPER_RANDOM_OFFTIME = 0;
const float STEPPER_STEP_DISTANCE = 200.0;
const float STEPPER_BIG_DISTANCE = 5000.0; // Must be bigger than max length movable in mm

const int STEPPER1_CS_PIN = 9;
const int STEPPER1_DIR_PIN = 7;
const int STEPPER1_STEP_PIN = 8;

const int STEPPER2_CS_PIN = 6;
const int STEPPER2_DIR_PIN = 4;
const int STEPPER2_STEP_PIN = 5;

// Stepper
extern CustomAccelStepper astepper1;
extern CustomAccelStepper astepper2;

// STEPS_PER_MM calculation should be done based on measurements, but
// for now we just use math.
const float STEPPER_DISTANCE_PER_ROTATION = 3.141592 * STEPPER_DRIVE_GEAR_OD_MM;

const float MAX_ACCELERATION = 10000.0;

const float LEFT = -1.0;
const float RIGHT = 1.0;

struct Speed {
    public:
        static constexpr float SLOW = 10.0;
        static constexpr float MEDIUM = 50.0;
        static constexpr float FAST = 100.0;
        static constexpr float VERY_FAST = 150.0;
        static constexpr float SUPER_FAST = 300.0;
        static constexpr float ULTRA_FAST = 1000.0;
};

void setup_steppers();
void setup_stepper_drivers();
void start_stepper_drivers();
void setup_asteppers();
void asteppers_run();

#endif
