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
    if (trigger_ctx.has_failed && experiment_mode != ExperimentMode::FAILED) {
        unsafe_run_trigger();
    }

    // Update runner to reflect run safety wish
    bool currently_limit_finding = (limit_finding_mode != LimitFindingMode::DONE) || (limit_check_mode != LimitCheckMode::DONE);
    trigger_ctx.run_safely = !currently_limit_finding && limit_finding_has_been_done;

    // int8_t safety = astepper1.runSafe();

    // if (!currently_limit_finding && (safety != 0))
    // {
    //     // We did unsafe step while not limit finding!
    //     experiment_done = true;
    //     experiment_done_trigger();
    // }
}
