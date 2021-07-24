#include <Steppers.h>

#include <DebugUtils.h>

/*
 ! Stepper information:
 * Step angle: 1.8 deg (= 200 steps per rotation)
 * Max current: 1.33 A
 * Voltage rating: 2.8 V
 *
*/


TMC26XStepper stepper1;
TMC26XStepper stepper2;

AccelStepper astepper1 = AccelStepper(astepper1.DRIVER, STEPPER1_STEP_PIN, STEPPER1_DIR_PIN);
AccelStepper astepper2 = AccelStepper(astepper2.DRIVER, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);

void setup_steppers() {
    DPL("Setting up steppers.");
    setup_stepper_drivers();
    start_stepper_drivers();
    setup_asteppers();
}

void setup_stepper_drivers() {
    DPL("Setting up stepper drivers.");
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
}

void start_stepper_drivers() {
    DPL("Starting stepper drivers.");
    stepper1.getCurrentStallGuardReading(); // We need this to initialise, apparently
    stepper2.getCurrentStallGuardReading(); // We need this to initialise, apparently
}

void setup_asteppers() {
    DPL("Starting stepper drivers.");
    astepper1.setMaxSpeed(MAX_SPEED);
    astepper1.setAcceleration(MAX_ACCELERATION);
    astepper1.setPinsInverted(true, false, false);
    // astepper1.enableOutputs();

    astepper2.setMaxSpeed(MAX_SPEED);
    astepper2.setAcceleration(MAX_ACCELERATION);
    astepper2.setPinsInverted(false, false, false);
    // astepper2.enableOutputs();
}

void asteppers_run() {
    astepper1.run();
    astepper2.run();
}