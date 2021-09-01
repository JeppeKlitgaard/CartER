#include <CustomArduino.h>

// I2C Multiplexer
const uint8_t TCA9548A_ADDR = 0x70;

const int I2C_RST_PIN = 28;
const uint32_t I2C_RESET_HALFTIME = 50; // ms

void setup_I2C_multiplexer();
void reset_I2C_multiplexer();
// Selects one of the I2C ports on the multiplexer
void I2C_select(uint8_t i);
