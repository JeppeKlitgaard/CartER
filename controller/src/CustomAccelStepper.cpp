#include <CustomAccelStepper.h>
#include <DebugUtils.h>

CustomAccelStepper::CustomAccelStepper(
    uint8_t cart_id_,
    uint8_t interface,
    uint8_t pin1,
    uint8_t pin2,
    uint8_t pin3,
    uint8_t pin4,
    bool enable) : AccelStepper(interface, pin1, pin2, pin3, pin4, enable)
{
    cart_id = cart_id_;
}

/**
 * Converts a distance to an integer number of steps
 * @param distance
 * @return
 */
int32_t CustomAccelStepper::distanceToSteps(float distance)
{
    return distance * _microsteps * _stepsPerRotation / _distancePerRotation;
}

/**
 * Converts steps to a distance
 * @param steps
 * @return
 */
float_t CustomAccelStepper::stepsToDistance(int32_t steps)
{
    return (steps / _microsteps) * _distancePerRotation / _stepsPerRotation;
}

/**
 * Converts an angle to an integer number of steps
 * @param angle
 * @return
 */
int32_t CustomAccelStepper::angleToSteps(float angle)
{
    return angle * _microsteps * _stepsPerRotation / _anglePerRotation;
}

/**
 * Set the _microsteps value.
 * @param microsteps
 */
void CustomAccelStepper::setMicrosteps(int microsteps)
{
    _microsteps = microsteps;
}

/**
 * Set the number of steps a step motor should do to complete one full rotation.
 * @param steps
 */
void CustomAccelStepper::setStepsPerRotation(int steps)
{
    _stepsPerRotation = steps;
}

/**
 * Set the distance which the step motor cover with one full rotation.
 * @param distance
 */
void CustomAccelStepper::setDistancePerRotation(float distance)
{
    _distancePerRotation = distance;
}

/**
 * Set the angle per rotation property.
 * @param angle
 */
void CustomAccelStepper::setAnglePerRotation(float angle)
{
    _anglePerRotation = angle;
}

/**
 * Set the far limit switch.
 * We assume that the left limit is 0, this can be set using setCurrentPosition()
 * @param farLimit
 */
void CustomAccelStepper::setFarLimit(int32_t farLimit)
{
    _farLimit = farLimit;
}

/**
 * Get the far limit
 * @return
 */
int32_t CustomAccelStepper::getFarLimit()
{
    return _farLimit;
}

/**
 * Set the limit safety margin. This is used by runSafe()
 * @param limitSafetyMargin
 */
void CustomAccelStepper::setLimitSafetyMargin(int32_t limitSafetyMargin)
{
    _limitSafetyMargin = limitSafetyMargin;
}

/**
 * Set the limit safety margin. This is used by runSafe()
 * @param limitSafetyMarginDistance
 */
void CustomAccelStepper::setLimitSafetyMarginDistance(float_t limitSafetyMarginDistance)
{
    _limitSafetyMargin = distanceToSteps(limitSafetyMarginDistance);
}

/**
 * Get the limit safety margin. This is used by runSafe()
 * @return
 */
int32_t CustomAccelStepper::getLimitSafetyMargin()
{
    return _limitSafetyMargin;
}

/**
 * Get the limit safety margin. This is used by runSafe()
 * @return
 */
float_t CustomAccelStepper::getLimitSafetyMarginDistance()
{
    return stepsToDistance(_limitSafetyMargin);
}

/**
 * Does a step in a manner that allows for easy safety implementation.
 * Returns 0 if the position is safe.
 * Returns -1 if the position is unsafe (below 0 + limitSafetyMargin)
 * Returns +1 if the position is unsafe (above farLimit + limitSafetyMargin)
 * Calling stop() is then the responsibility of the developer.
 * @return
 */
int8_t CustomAccelStepper::runSafe()
{
    run();

    int32_t currPos = currentPosition();

    if (currPos < _limitSafetyMargin)
    {
        return -1;
    }
    else if (currPos > _farLimit - _limitSafetyMargin)
    {
        return +1;
    }
    else
    {
        return 0;
    }
}

/**
 * Return the current distance from the origin.
 * @return
 */
float CustomAccelStepper::getCurrentPositionDistance()
{
    return currentPosition() / (_microsteps * _stepsPerRotation / _distancePerRotation);
}

/**
 * Sets the current absolute position of the motor to be equal to the absolute distance given
 * @param absolute
 */
void CustomAccelStepper::setCurrentPositionDistance(float absolute)
{
    setCurrentPosition(distanceToSteps(absolute));
}

/**
 * Move the motor to a new relative distance.
 * @param distance
 */
void CustomAccelStepper::moveDistance(float distance)
{
    move(distanceToSteps(distance));
}

/**
 * The motor travel a certain distance.
 * @param distance
 */
void CustomAccelStepper::moveToDistance(float distance)
{
    moveTo(distanceToSteps(distance));
}

/**
 * Move and run the motor to a new relative distance.
 * @param distance
 */
void CustomAccelStepper::runDistance(float distance)
{
    move(distanceToSteps(distance));
    runToPosition();
}

/**
 * The motor goes to the new specified distance.
 * @param distance
 */
void CustomAccelStepper::runToDistance(float distance)
{
    moveToDistance(distance);
    runToPosition();
}

/**
 * The motor goes to the new specified angle.
 * @param angle
 */
void CustomAccelStepper::moveToAngle(float angle)
{
    moveTo(angleToSteps(angle));
}

/**
 * The motor goes to the new specified angle.
 * @param angle
 */
void CustomAccelStepper::runToAngle(float angle)
{
    moveToAngle(angle);
    runToPosition();
}

void CustomAccelStepper::moveCond(long relative)
{
    if (distanceToGo() == 0)
    {
        move(relative);
    }
}

void CustomAccelStepper::moveDistanceCond(float relative)
{
    if (distanceToGo() == 0)
    {
        moveDistance(relative);
    }
}

/**
 * Sets the maximum speed to the distance unitted speed.
 * @param speed
 */
void CustomAccelStepper::setMaxSpeedDistance(float speed)
{
    setMaxSpeed(distanceToSteps(speed));
}

/**
 * Sets the acceleration to the distance unitted acceleration
 * @param acceleration
 */
void CustomAccelStepper::setAccelerationDistance(float acceleration)
{
    setAcceleration(distanceToSteps(acceleration));
}

/**
 * Since base methods are not defined as virtual and attributes are private
 * We need to set this in order to use the enable methods from CustomAccelStepper
 * This also calls AccelStepper.setEnablePin()
 * @param enablePin
 */
void CustomAccelStepper::setCustomEnablePin(uint8_t enablePin)
{
    _customEnablePin = enablePin;
    setEnablePin(enablePin);
}

/**
 * Convenience method for enabling/disabling outputs with a parameter.
 * Wraps enableOutputs() and disableOutputs()
 * @param enabled
 */
void CustomAccelStepper::setEnabled(bool enabled)
{
    if (enabled)
    {
        enableOutputs();
    }
    else
    {
        disableOutputs();
    }
}

/**
 * Returns the enabled status as a bool.
 * @return
 */
bool CustomAccelStepper::getEnabled()
{
    return digitalRead(_customEnablePin);
}

/**
 * Toggles enabled status
 */
void CustomAccelStepper::toggleEnabled()
{
    setEnabled(!getEnabled());
}
