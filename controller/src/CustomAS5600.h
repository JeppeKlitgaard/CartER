#ifndef CUSTOM_AS5600_H
#define CUSTOM_AS5600_H

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wregister"
#include <AS5600.h> // https://github.com/olkal/Seeed_Arduino_AS5600 <-- Fork
#pragma GCC diagnostic pop

class CustomAMS_5600 : public AMS_5600
{
public:
    CustomAMS_5600();

    virtual void start(uint8_t addr) = 0;
    virtual float readAngleDeg() = 0;
};

class RealCustomAMS_5600 : public CustomAMS_5600
{
private:
    const uint8_t _UNSELECT_ADDR = 7;
    const float _BIT_DEG_RESOLUTION = 0.087;

protected:
    uint8_t _addr = 7;

    float _rawAngleToDeg(unsigned int rawAngle);
    void _select();
    void _unselect();

public:
    virtual void start(uint8_t addr) override;
    virtual float readAngleDeg() override;
};

class FakeCustomAMS_5600 : public CustomAMS_5600
{
    virtual void start(uint8_t addr) override;
    virtual float readAngleDeg() override;
};

#endif
