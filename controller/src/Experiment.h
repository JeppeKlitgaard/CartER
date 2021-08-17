#ifndef EXPERIMENT_H
#define EXPERIMENT_H

#include <CustomArduino.h>

const uint32_t OBSERVATION_INTERVAL_US = 5000;  // microseconds
extern uint32_t last_observation_us;

void observation_tick();

void send_observation(uint8_t cart_id);

void experiment_start();
void experiment_stop();

#endif