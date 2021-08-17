#include <CommandAndControl.h>

#include <Init.h>
#include <Steppers.h>
#include <Limits.h>
#include <Experiment.h>

void loop_command_and_control()
{
    // React to incoming packets
    if (S.available() != 0)
    {
        packet_reactor.tick();
    }

    // Observation
    observation_tick();

    // Do limits
    bool currently_limit_finding = (limit_finding_mode != LimitFindingMode::DONE) || (limit_check_mode != LimitCheckMode::DONE);

    int8_t safety = astepper1.runSafe();

    if (!currently_limit_finding && (safety != 0))
    {
        // We did unsafe step while not limit finding!
        experiment_done = true;
        experiment_done_trigger();
    }
}
