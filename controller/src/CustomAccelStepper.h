#ifndef CUSTOM_ACCEL_STEPPER_H
#define CUSTOM_ACCEL_STEPPER_H

#include <AccelStepper.h>

class CustomAccelStepper : public AccelStepper
{
protected:
    uint8_t _customEnablePin = 0xff;

    int _microsteps = 1;
    int _stepsPerRotation = 200;
    float _distancePerRotation = 1;
    float _anglePerRotation = 360;

    int _distanceToSteps(float distance);
    int _angleToSteps(float angle);

public:
    uint8_t cart_id;

    CustomAccelStepper(
        uint8_t cart_id,
        uint8_t interface = AccelStepper::FULL4WIRE,
        uint8_t pin1 = 2,
        uint8_t pin2 = 3,
        uint8_t pin3 = 4,
        uint8_t pin4 = 5,
        bool enable = true);

    void setMicrosteps(int microsteps);
    void setStepsPerRotation(int steps);
    void setDistancePerRotation(float distance);
    void setAnglePerRotation(float angle);

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

    void setMaxSpeedDistance(float speed);
    void setAccelerationDistance(float acceleration);

    void setCustomEnablePin(uint8_t enablePin);
    void setEnabled(bool enabled);
    bool getEnabled();
    void toggleEnabled();
};

#endif