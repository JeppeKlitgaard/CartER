#include <RotaryEncoder.h>
#include <DebugUtils.h>
#include <I2CMultiplexer.h>
#include <Mode.h>

AMS_5600 rot_encoder1;
AMS_5600 rot_encoder2;

float raw_angle_to_deg(unsigned int raw_angle)
{
    // 12 bit => 360/2^12 => 0.087 of a degree
    float angle_deg = raw_angle * BIT_DEG_RESOLUTION;

    return angle_deg;
}

static void _init_rot_encoder(AMS_5600 &rot_encoder) {
    if (rot_encoder.detectMagnet() == 0)
    {
        while (1)
        {
            if (rot_encoder.detectMagnet() == 1)
            {
                DP("Current Magnitude: ");
                DPL(rot_encoder.getMagnitude());
                break;
            }
            else
            {
                DPL("Can not detect magnet");
            }
            delay(100); // ms
        }
    }
}

void setup_rotary_encoders()
{
    DPL("Setting up rotary encoders.");

    DPL("Setting up rotary encoder 1.");
    I2C_select(ROT_ENCODER_1_ADDR);
    _init_rot_encoder(rot_encoder1);

    if (configuration == TWO_CARRIAGES)
    {
        DPL("Setting up rotary encoder 2.");
        I2C_select(ROT_ENCODER_2_ADDR);
        _init_rot_encoder(rot_encoder2);

    }

    // Set no select for I2C to ensure we fail if we miss setting the correct I2C.
    I2C_select(NO_SELECT_ADDR);
}