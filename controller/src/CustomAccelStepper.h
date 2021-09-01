#ifndef CUSTOM_ACCEL_STEPPER_H
#define CUSTOM_ACCEL_STEPPER_H

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wregister"
#include <AccelStepper.h>
#pragma GCC diagnostic pop

enum class RunSafetyCheck
{
    SAFE = 0,
    LOW_LIMIT_FAIL = 1,
    HIGH_LIMIT_FAIL = 2,
};

class CustomAccelStepper : public AccelStepper
{
protected:
    uint8_t _customEnablePin = 0xff;

    int _microsteps = 1;
    int _stepsPerRotation = 200;
    float _distancePerRotation = 1;
    float _anglePerRotation = 360;

    int32_t _farLimit = 0;
    int32_t _limitSafetyMargin = 0;

public:
    uint8_t cart_id;

    explicit CustomAccelStepper(
        uint8_t cart_id_,
        uint8_t interface = AccelStepper::FULL4WIRE,
        uint8_t pin1 = 2,
        uint8_t pin2 = 3,
        uint8_t pin3 = 4,
        uint8_t pin4 = 5,
        bool enable = true);

    int32_t distanceToSteps(float distance);
    float_t stepsToDistance(int32_t steps);
    float_t stepsToDistance(float_t steps);
    int32_t angleToSteps(float angle);

    void setMicrosteps(int microsteps);
    void setStepsPerRotation(int steps);
    void setDistancePerRotation(float distance);
    void setAnglePerRotation(float angle);

    void setFarLimit(int32_t farLimit);
    int32_t getFarLimit();

    void setLimitSafetyMargin(int32_t limitSafetyMargin);
    void setLimitSafetyMarginDistance(float_t limitSafetyMargin);
    int32_t getLimitSafetyMargin();
    float_t getLimitSafetyMarginDistance();

    RunSafetyCheck runSafe();
    RunSafetyCheck runSafeSpeed();

    float getCurrentPositionDistance();
    void setCurrentPositionDistance(float absolute);

    void moveDistance(float relative);
    void moveToDistance(float absolute);
    void runDistance(float relative);
    void runToDistance(float absolute);

    void moveToAngle(float angle);
    void runToAngle(float angle);

    void moveCond(long relative);
    void moveDistanceCond(float relative);

    float_t maxSpeedDistance();
    void setMaxSpeedDistance(float speed);
    void setAccelerationDistance(float acceleration);

    void setCustomEnablePin(uint8_t enablePin);
    void setEnabled(bool enabled);
    bool getEnabled();
    void toggleEnabled();
};

#endif