#include <TimerInterrupt.h>
#include <Steppers.h>
#include <Init.h>

action_tc0_declaration();

struct ctx
{
  ctx() {}
};


ctx action_ctx;

void step_timer_callback(void *a_ctx) {
    asteppers_run();
}

void setup_timer_interrupt() {
    S.println("Setting up timer interrupt.");
    action_tc0.start(STEP_TIMER_PERIOD, step_timer_callback, &action_ctx);
}
