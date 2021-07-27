#ifndef ROTARY_ENCODER_H
#define ROTARY_ENCODER_H

#include <AS5600.h> // https://github.com/olkal/Seeed_Arduino_AS5600 <-- Fork

const unsigned int ROT_ENCODER_1_ADDR = 0;
const unsigned int ROT_ENCODER_2_ADDR = 1;
const unsigned int NO_SELECT_ADDR = 7;

// Rotary Encoder - AS5600 v1.0
extern AMS_5600 rot_encoder1;
extern AMS_5600 rot_encoder2;

const float BIT_DEG_RESOLUTION = 0.087;

float raw_angle_to_deg(unsigned int raw_angle);

void setup_rotary_encoders();

#endif