#ifndef ROTARY_ENCODER_H
#define ROTARY_ENCODER_H

#include <CustomAS5600.h>

// Fake rotary encoder data in order to avoid dodgy I2C
// This is for debugging purposes, mainly.
const bool FAKE_ROTARY_ENCODERS = true;

const unsigned int ROT_ENCODER_1_ADDR = 0;
const unsigned int ROT_ENCODER_2_ADDR = 1;
const unsigned int NO_SELECT_ADDR = 7;

// Rotary Encoder - AS5600 v1.0
extern CustomAMS_5600 *rot_encoder1;
extern CustomAMS_5600 *rot_encoder2;

void setup_rotary_encoders();
void start_rotary_encoders();

CustomAMS_5600 *get_rot_encoder_by_id(uint8_t cart_id);

#endif