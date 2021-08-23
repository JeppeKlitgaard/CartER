#include <Steppers.h>

#include <DebugUtils.h>
#include <Init.h>
#include <Mode.h>
#include <Utils.h>
#include <Limits.h>

/*
 ! Stepper information:
 * Step angle: 1.8 deg (= 200 steps per rotation)
 * Max current: 1.33 A
 * Voltage rating: 2.8 V
 *
*/

TMC26XStepper stepper1;
TMC26XStepper stepper2;

CustomAccelStepper astepper1 = CustomAccelStepper(1, astepper1.DRIVER, STEPPER1_STEP_PIN, STEPPER1_DIR_PIN);
CustomAccelStepper astepper2 = CustomAccelStepper(2, astepper2.DRIVER, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);

void setup_steppers()
{
    packet_sender.send_debug("Setting up steppers.");
    setup_asteppers();
    setup_stepper_drivers();
    start_stepper_drivers();
}

void setup_stepper_drivers()
{
    packet_sender.send_debug("Setting up stepper drivers.");
    packet_sender.send_debug("Setting up stepper driver 1.");
    // steps/rot, cs, dir, step, current
    stepper1.start(STEPPER_STEPS_PER_ROTATION, STEPPER1_CS_PIN, STEPPER1_DIR_PIN, STEPPER1_STEP_PIN, STEPPER_CURRENT);

    //char constant_off_time, char blank_time, char hysteresis_start, char hysteresis_end, char hysteresis_decrement
    // stepper1.setSpreadCycleChopper(2, 24, 8, 6, 0);
    stepper1.setConstantOffTimeChopper(7, 54, 13, 12, 1);
    stepper1.setRandomOffTime(STEPPER_RANDOM_OFFTIME);

    stepper1.setMicrosteps(STEPPER_MICROSTEPS);

    if (configuration == TWO_CARRIAGES)
    {
        packet_sender.send_debug("Setting up stepper driver 2.");
        stepper2.start(STEPPER_STEPS_PER_ROTATION, STEPPER2_CS_PIN, STEPPER2_DIR_PIN, STEPPER2_STEP_PIN, STEPPER_CURRENT);
        stepper2.setConstantOffTimeChopper(7, 54, 13, 12, 1);
        stepper2.setRandomOffTime(STEPPER_RANDOM_OFFTIME);
        stepper2.setMicrosteps(STEPPER_MICROSTEPS);
    }
}

void start_stepper_drivers()
{
    packet_sender.send_debug("Starting stepper drivers.");
    packet_sender.send_debug("Starting stepper driver 1.");
    stepper1.getCurrentStallGuardReading(); // We need this to initialise, apparently

    if (configuration == TWO_CARRIAGES)
    {
        packet_sender.send_debug("Starting stepper driver 1.");
        stepper2.getCurrentStallGuardReading(); // We need this to initialise, apparently
    }
}

void setup_astepper(CustomAccelStepper &astepper)
{
    packet_sender.send_debug("Initiating astepper " + std::to_string(astepper.cart_id));

    int en_pin = (astepper.cart_id == 1) ? STEPPER1_EN_PIN : STEPPER2_EN_PIN;

    astepper.setEnablePin(en_pin);
    astepper.setMicrosteps(STEPPER_MICROSTEPS);
    astepper.setStepsPerRotation(STEPPER_STEPS_PER_ROTATION);
    astepper.setDistancePerRotation(STEPPER_DISTANCE_PER_ROTATION);
    astepper.setMaxSpeedDistance(Speed::MEDIUM);
    astepper.setLimitSafetyMarginDistance(STEPPER_SAFETY_MARGIN_DISTANCE);
    astepper.setAccelerationDistance(MAX_ACCELERATION);
    astepper.setPinsInverted(true, false, true);
    astepper.setEnabled(true);
}
/**
 * Should be called before the stepper driver is set up.
 */
void setup_asteppers()
{
    packet_sender.send_debug("Starting stepper library.");
    setup_astepper(astepper1);

    if (configuration == TWO_CARRIAGES)
    {
        setup_astepper(astepper2);
    }
}

CustomAccelStepper &get_astepper_by_id(uint8_t cart_id)
{
    switch (cart_id)
    {
    case 1:
        return astepper1;
    case 2:
        return astepper2;
    default:
        packet_sender.send_debug("Invalid cart_id: " + std::to_string(cart_id));
        throw std::out_of_range("Invalid cart_id");
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

/**
 * Runs an astepper in a safe way that respects the currently imposed limits
 * Note: Does not call stop(). Do this in trigger_callback
 * @return whether run was safe or not
 */
bool astepper_run_safe(CustomAccelStepper &astepper) {
    RunSafetyCheck limit_check = astepper.runSafe();

    switch (limit_check) {
        case RunSafetyCheck::LOW_LIMIT_FAIL:
            failure_mode = FailureMode::POSITION_LEFT;
            failure_cart_id = astepper.cart_id;
            return false;

        case RunSafetyCheck::HIGH_LIMIT_FAIL:
            failure_mode = FailureMode::POSITION_RIGHT;
            failure_cart_id = astepper.cart_id;
            return false;

        default:
            return true;
    }
}

/**
 * Runs the asteppers in a safe manner
 */
bool asteppers_run_safe()
{
    bool was_safe = astepper_run_safe(astepper1);

    if (was_safe && configuration == TWO_CARRIAGES) {
        was_safe = astepper_run_safe(astepper2);
    }

    return was_safe;
}


// There is definitely a smarter way to define these and in the future I
// will probably refactor this to be smarter.
void asteppers_run_speed()
{
    astepper1.runSpeed();
    if (configuration == TWO_CARRIAGES)
    {
        astepper2.runSpeed();
    }
}

/**
 * Runs an astepper in a safe way that respects the currently imposed limits
 * Constant speed version
 * Note: Does not call stop(). Do this in trigger_callback
 * @return whether run was safe or not
 */
bool astepper_run_safe_speed(CustomAccelStepper &astepper) {
    RunSafetyCheck limit_check = astepper.runSafeSpeed();

    switch (limit_check) {
        case RunSafetyCheck::LOW_LIMIT_FAIL:
            failure_mode = FailureMode::POSITION_LEFT;
            failure_cart_id = astepper.cart_id;
            return false;

        case RunSafetyCheck::HIGH_LIMIT_FAIL:
            failure_mode = FailureMode::POSITION_RIGHT;
            failure_cart_id = astepper.cart_id;
            return false;

        default:
            return true;
    }
}

/**
 * Runs the asteppers in a safe manner, constant speed version
 */
bool asteppers_run_safe_speed()
{
    bool was_safe = astepper_run_safe_speed(astepper1);

    if (was_safe && configuration == TWO_CARRIAGES) {
        was_safe = astepper_run_safe_speed(astepper2);
    }

    return was_safe;
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

void asteppers_stop()
{
    astepper1.stop();
    if (configuration == TWO_CARRIAGES)
    {
        astepper2.stop();
    }
}

void asteppers_run_to_position()
{
    astepper1.runToPosition();
    if (configuration == TWO_CARRIAGES)
    {
        astepper2.runToPosition();
    }
}