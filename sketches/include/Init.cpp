#include <Init.h>

#include <Mode.h>
#include <LimitFinding.h>

Mode mode = JOYSTICK;
const Configuration configuration = ONE_CARRIAGES;

LimitFindingMode limit_finding_mode = LimitFindingMode::INIT;
float track_length_distance = 0.0;
