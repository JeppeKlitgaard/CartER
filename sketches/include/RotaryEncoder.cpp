#include <RotaryEncoder.h>
#include <DebugUtils.h>

float raw_angle_to_deg(unsigned int raw_angle) {
    // 12 bit => 360/2^12 => 0.087 of a degree
    float angle_deg = raw_angle * BIT_DEG_RESOLUTION;

    return angle_deg;
}

void setup_rotary_encoders() {
    DPL("Setting up rotary encoders.");
}