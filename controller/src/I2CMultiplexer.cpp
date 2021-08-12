#include <I2CMultiplexer.h>

#include <Wire.h>

void I2C_select(uint8_t i)
{
    if (i > 7)
    {
        return;
    }

    Wire.beginTransmission(TCA9548A_ADDR);
    Wire.write(1 << i);
    Wire.endTransmission();
}