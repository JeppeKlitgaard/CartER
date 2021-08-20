#include <Init.h>

#include <Mode.h>
#include <Limits.h>

Mode mode = JOYSTICK;

const Configuration configuration = ONE_CARRIAGES;

LimitFindingMode limit_finding_mode = LimitFindingMode::DONE;
LimitCheckMode limit_check_mode = LimitCheckMode::DONE;
float_t track_length_distance = 0.0;
int32_t track_length_steps = 0;

PacketReactor packet_reactor = PacketReactor(S);
PacketSender packet_sender = PacketSender(S);

bool experiment_done = false;
bool limit_finding_has_been_done = false;
bool is_observing = false;

FailureMode failure_mode = FailureMode::NUL;
uint8_t failure_cart_id = 0;
ExperimentMode experiment_mode = ExperimentMode::DONE;

void initialise()
{
    set_mode(INITIAL_MODE);
}