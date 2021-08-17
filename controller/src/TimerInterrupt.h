#ifndef TIMER_INTERRUPT_H
#define TIMER_INTERRUPT_H

#include <CustomArduino.h>
#include <tc_lib.h>

const uint32_t STEP_TIMER_PERIOD = 1000;// in 1e-8 sec

void setup_timer_interrupt();

void step_timer_callback();

#endif