#include <CustomArduino.h>

// I2C Multiplexer
const uint8_t TCA9548A_ADDR = 0x70;

// Selects one of the I2C ports on the multiplexer
void I2C_select(uint8_t i);
