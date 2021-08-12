#ifndef ROTARY_ENCODER_H
#define ROTARY_ENCODER_H

#include <CustomAS5600.h>

const unsigned int ROT_ENCODER_1_ADDR = 0;
const unsigned int ROT_ENCODER_2_ADDR = 1;
const unsigned int NO_SELECT_ADDR = 7;

// Rotary Encoder - AS5600 v1.0
extern CustomAMS_5600 rot_encoder1;
extern CustomAMS_5600 rot_encoder2;

void setup_rotary_encoders();

#endif