#include <TimerInterrupt.h>
#include <Steppers.h>
#include <Init.h>

action_tc0_declaration();

action_ctx trigger_ctx;

void step_timer_callback(void *a_ctx)
{
    action_ctx *ctx = reinterpret_cast<action_ctx *>(a_ctx);

    if (!ctx->run_safely)
    {
        asteppers_run();
    }
    else if (ctx->run_safely && !ctx->has_failed)
    {
        bool was_safe = asteppers_run_safe();
        ctx->has_failed = ctx->has_failed || !was_safe;
    }
    else
    {
        ;
    }
}

void setup_timer_interrupt()
{
    packet_sender.send_debug("Setting up timer interrupt");
    action_tc0.start(STEP_TIMER_PERIOD, step_timer_callback, &trigger_ctx);
}
