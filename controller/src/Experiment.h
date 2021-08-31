#ifndef EXPERIMENT_H
#define EXPERIMENT_H

#include <CustomArduino.h>

const uint32_t OBSERVATION_INTERVAL_US = 4000;  // microseconds
extern uint32_t last_observation_us;

const uint32_t MEMORY_INTERVAL_US = 10 * 1000 * 1000;  // microseconds
extern uint32_t last_memory_us;

void observation_tick();

void send_observation(uint8_t cart_id);

void experiment_start();
void experiment_stop();

void unsafe_run_trigger();

#endif