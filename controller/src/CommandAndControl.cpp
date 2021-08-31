#include <CommandAndControl.h>

#include <Init.h>
#include <Steppers.h>
#include <Limits.h>
#include <Experiment.h>
#include <Buttons.h>
#include <TimerInterrupt.h>

void loop_command_and_control()
{
    update_buttons();

    // React to incoming packets
    if (S.available() != 0)
    {
        packet_reactor.tick();
    }

    // Observation
    observation_tick();

    // If we have failed, we should end experiment
    if (trigger_ctx.has_failed && experiment_mode != ExperimentMode::FAILED)
    {
        unsafe_run_trigger();
    }

    // Update runner to reflect run safety wish
    bool currently_limit_finding = (limit_finding_mode != LimitFindingMode::DONE) || (limit_check_mode != LimitCheckMode::DONE);
    trigger_ctx.run_safely = !currently_limit_finding && limit_finding_has_been_done;
    trigger_ctx.run_mode = (currently_limit_finding || trigger_ctx.has_failed) ? RunMode::REGULAR : RunMode::CONSTANT_SPEED;

    if (currently_limit_finding && limit_finding_mode != LimitFindingMode::DONE)
    {
        loop_limit_finding();
    }
    else if (currently_limit_finding && limit_check_mode != LimitCheckMode::DONE)
    {
        loop_limit_check();
    }
}
