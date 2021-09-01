#ifndef ROTARY_ENCODER_H
#define ROTARY_ENCODER_H

#include <CustomAS5600.h>

const unsigned int ROT_ENCODER_1_ADDR = 0;
const unsigned int ROT_ENCODER_2_ADDR = 1;
const unsigned int NO_SELECT_ADDR = 7;

const int ROT_ENCODER_1_SUPPLY_PIN = 26;
const int ROT_ENCODER_2_SUPPLY_PIN = 27;

const uint32_t ROT_ENCODERS_POWER_CYCLE_HALFTIME = 50; // ms

// Rotary Encoder - AS5600 v1.0
extern CustomAMS_5600 rot_encoder1;
extern CustomAMS_5600 rot_encoder2;

void setup_rotary_encoders();
void start_rotary_encoders();
void power_cycle_rotary_encoders();

CustomAMS_5600 &get_rot_encoder_by_id(uint8_t cart_id);

#endif