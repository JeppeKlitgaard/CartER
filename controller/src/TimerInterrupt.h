#ifndef TIMER_INTERRUPT_H
#define TIMER_INTERRUPT_H

#include <CustomArduino.h>
#include <tc_lib.h>

const uint32_t STEP_TIMER_PERIOD = 1000;// in 1e-8 sec

enum class RunMode {
    REGULAR,
    CONSTANT_SPEED,
};

struct action_ctx
{
    action_ctx()
    {
        run_safely = false;
        has_failed = false;
        run_mode = RunMode::REGULAR;

    }

    bool run_safely;
    bool has_failed;
    RunMode run_mode;

};

extern action_ctx trigger_ctx;

void setup_timer_interrupt();

void step_timer_callback();

#endif