#include <I2CMultiplexer.h>
#include <Wire.h>
#include <DebugUtils.h>

void setup_I2C_multiplexer()
{
    packet_sender.send_debug("Setting up I2C multiplexer");
    pinMode(I2C_RST_PIN, OUTPUT);

    packet_sender.send_debug("Reset I2C multiplexer");
    reset_I2C_multiplexer();
}

void reset_I2C_multiplexer()
{
    digitalWrite(I2C_RST_PIN, LOW);
    delay(I2C_RESET_HALFTIME);
    digitalWrite(I2C_RST_PIN, HIGH);
    delay(I2C_RST_PIN);
}

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