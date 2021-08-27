#include <TimerInterrupt.h>
#include <Steppers.h>
#include <Init.h>

action_tc0_declaration();

action_ctx trigger_ctx;

void step_timer_callback(void *a_ctx)
{
    action_ctx *ctx = reinterpret_cast<action_ctx *>(a_ctx);

    switch (ctx->run_mode)
    {
    case RunMode::REGULAR:
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
            asteppers_run();
        }

        break;

    case RunMode::CONSTANT_SPEED:
        if (!ctx->run_safely)
        {
            asteppers_run_speed();
        }
        else if (ctx->run_safely && !ctx->has_failed)
        {
            bool was_safe = asteppers_run_safe_speed();
            ctx->has_failed = ctx->has_failed || !was_safe;
        }
        else
        {
            asteppers_run_speed();
        }

        break;
    }
}

void setup_timer_interrupt()
{
    packet_sender.send_debug("Setting up timer interrupt");
    action_tc0.start(STEP_TIMER_PERIOD, step_timer_callback, &trigger_ctx);
}
