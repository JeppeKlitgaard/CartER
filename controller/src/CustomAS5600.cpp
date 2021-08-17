#include <CustomAS5600.h>
#include <DebugUtils.h>

#include <I2CMultiplexer.h>

CustomAMS_5600::CustomAMS_5600() {}

/**
 * Converts a bit value to a float value in degrees.
 * @param rawAngle
 * @return
 */
float CustomAMS_5600::_rawAngleToDeg(unsigned int rawAngle)
{
    // 12 bit => 360/2^12 => 0.087 of a degree
    float angleDeg = rawAngle * _BIT_DEG_RESOLUTION;

    return angleDeg;
}

/**
 * Selects the rotary encoder using the I2C interface
 */
void CustomAMS_5600::_select()
{
    I2C_select(_addr);
}

/**
 * Unselects the rotary encoder using the I2C interface
 */
void CustomAMS_5600::_unselect()
{
    I2C_select(_UNSELECT_ADDR);
}

/**
 * Starts the rotary encoder.
 * May block indefinitely if I2C not connected
 * @param addr
 */
void CustomAMS_5600::start(uint8_t addr)
{
    _addr = addr;

    _select();

    while (1)
    {
        if (detectMagnet() == 1)
        {
            DP("Current Magnitude: ");
            DPL(getMagnitude());
            break;
        }
        else
        {
            DPL("Can not detect magnet");
        }
        delay(100); // ms
    }

    DP("Rotary Encoder @");
    DP(_addr);
    DPL(" has following:");

    DP("Magnitude: ");
    DPL(getMagnitude());

    DP("Strength (1=too weak, 2=good, 3=too strong): ");
    DPL(getMagnetStrength());

    DP("Detected: ");
    DPL(detectMagnet());

    _unselect();
}

/**
 * Returns the angle degree as a float
 * @return
 */
float CustomAMS_5600::readAngleDeg()
{
    _select();
    float angleDeg = _rawAngleToDeg(getRawAngle());
    _unselect();

    return angleDeg;
}
