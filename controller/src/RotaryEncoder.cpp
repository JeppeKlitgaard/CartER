#include <RotaryEncoder.h>
#include <DebugUtils.h>
#include <I2CMultiplexer.h>
#include <Mode.h>

CustomAMS_5600 rot_encoder1;
CustomAMS_5600 rot_encoder2;

void setup_rotary_encoders()
{
    DPL("Setting up rotary encoders.");

    DPL("Setting up rotary encoder 1.");
    rot_encoder1.start(ROT_ENCODER_1_ADDR);

    if (configuration == TWO_CARRIAGES)
    {
        DPL("Setting up rotary encoder 2.");
        rot_encoder2.start(ROT_ENCODER_2_ADDR);
    }
}