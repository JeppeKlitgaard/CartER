#include <Init.h>

#include <Mode.h>
#include <LimitFinding.h>

Mode mode = JOYSTICK;

const Configuration configuration = ONE_CARRIAGES;

LimitFindingMode limit_finding_mode = LimitFindingMode::INIT;
float track_length_distance = 0.0;

PacketReactor packet_reactor = PacketReactor(S);
PacketSender packet_sender = PacketSender(S);


void initialise()
{
    set_mode(INITIAL_MODE);
}