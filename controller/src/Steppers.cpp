#include <Steppers.h>
#include <CustomAccelStepper.h>

#include <DebugUtils.h>
#include <Init.h>
#include <Mode.h>

/*
 ! Stepper information:
 * Step angle: 1.8 deg (= 200 steps per rotation)
 * Max current: 1.33 A
 * Voltage rating: 2.8 V
 *
*/

TMC26XStepper stepper1;
TMC26XStepper stepper2;

CustomAccelStepper astepper1 = CustomAccelStepper(astepper1.DRIVER, STEPPER1_STEP_PIN, STEPPER1_DIR_PIN);
CustomAccelStepper astepper2 = CustomAccelStepper(astepper2.DRIVER, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);

void setup_steppers()
{
    DPL("Setting up steppers.");
    setup_asteppers();
    setup_stepper_drivers();
    start_stepper_drivers();
}

void setup_stepper_drivers()
{
    DPL("Setting up stepper drivers.");
    DPL("Setting up stepper driver 1.");
    // steps/rot, cs, dir, step, current
    stepper1.start(STEPPER_STEPS_PER_ROTATION, STEPPER1_CS_PIN, STEPPER1_DIR_PIN, STEPPER1_STEP_PIN, STEPPER_CURRENT);

    //char constant_off_time, char blank_time, char hysteresis_start, char hysteresis_end, char hysteresis_decrement
    // stepper1.setSpreadCycleChopper(2, 24, 8, 6, 0);
    stepper1.setConstantOffTimeChopper(7, 54, 13, 12, 1);
    stepper1.setRandomOffTime(STEPPER_RANDOM_OFFTIME);

    stepper1.setMicrosteps(STEPPER_MICROSTEPS);

    if (configuration == TWO_CARRIAGES)
    {
        DPL("Setting up stepper driver 2.");
        stepper2.start(STEPPER_STEPS_PER_ROTATION, STEPPER2_CS_PIN, STEPPER2_DIR_PIN, STEPPER2_STEP_PIN, STEPPER_CURRENT);
        stepper2.setConstantOffTimeChopper(7, 54, 13, 12, 1);
        stepper2.setRandomOffTime(STEPPER_RANDOM_OFFTIME);
        stepper2.setMicrosteps(STEPPER_MICROSTEPS);
    }
}

void start_stepper_drivers()
{
    DPL("Starting stepper drivers.");
    DPL("Starting stepper driver 1.");
    stepper1.getCurrentStallGuardReading(); // We need this to initialise, apparently

    if (configuration == TWO_CARRIAGES)
    {
        DPL("Starting stepper driver 1.");
        stepper2.getCurrentStallGuardReading(); // We need this to initialise, apparently
    }
}

/**
 * Should be called before the stepper driver is set up.
 */
void setup_asteppers()
{
    DPL("Starting stepper library.");
    DPL("Initiating astepper 1.");
    astepper1.setEnablePin(STEPPER1_EN_PIN);
    astepper1.setMicrosteps(STEPPER_MICROSTEPS);
    astepper1.setStepsPerRotation(STEPPER_STEPS_PER_ROTATION);
    astepper1.setDistancePerRotation(STEPPER_DISTANCE_PER_ROTATION);
    astepper1.setMaxSpeedDistance(Speed::MEDIUM);
    astepper1.setAccelerationDistance(MAX_ACCELERATION);
    astepper1.setPinsInverted(true, false, true);
    astepper1.setEnabled(true);

    if (configuration == TWO_CARRIAGES)
    {
        DPL("Initiating astepper 2.");
        astepper2.setEnablePin(STEPPER2_EN_PIN);
        astepper2.setMicrosteps(STEPPER_MICROSTEPS);
        astepper2.setStepsPerRotation(STEPPER_STEPS_PER_ROTATION);
        astepper2.setDistancePerRotation(STEPPER_DISTANCE_PER_ROTATION);
        astepper2.setMaxSpeedDistance(Speed::MEDIUM);
        astepper2.setAccelerationDistance(MAX_ACCELERATION);
        astepper2.setPinsInverted(false, false, true);
        astepper2.setEnabled(true);
    }
}

// There is definitely a smarter way to define these and in the future I
// will probably refactor this to be smarter.
void asteppers_run()
{
    astepper1.run();
    if (configuration == TWO_CARRIAGES)
    {
        astepper2.run();
    }
}

void asteppers_enable()
{
    astepper1.enableOutputs();

    if (configuration == TWO_CARRIAGES)
    {
        astepper2.enableOutputs();
    }
}

void asteppers_disable()
{
    astepper1.disableOutputs();

    if (configuration == TWO_CARRIAGES)
    {
        astepper2.disableOutputs();
    }
}

void asteppers_toggle_enabled()
{
    astepper1.toggleEnabled();

    if (configuration == TWO_CARRIAGES)
    {
        astepper2.toggleEnabled();
    }
}

void asteppers_stop() {
    astepper1.stop();
    if (configuration == TWO_CARRIAGES)
    {
        astepper2.stop();
    }

}

void asteppers_run_to_position() {
    astepper1.runToPosition();
    if (configuration == TWO_CARRIAGES)
    {
        astepper2.runToPosition();
    }
}