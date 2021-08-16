#include <LimitFinding.h>

#include <Mode.h>
#include <Steppers.h>
#include <Init.h>

#include <DebugUtils.h>

Bounce2::Button limit_sw_left = Bounce2::Button();
Bounce2::Button limit_sw_right = Bounce2::Button();

void setup_limit_switches()
{
    packet_sender.send_debug("Configuring limit switches.");

    // LEFT
    limit_sw_left.attach(LEFT_LIMIT_SW_PIN, INPUT_PULLUP);
    limit_sw_left.interval(LIMIT_SW_BOUNCE_INTERVAL);
    limit_sw_left.setPressedState(LOW);

    // RIGHT
    limit_sw_right.attach(RIGHT_LIMIT_SW_PIN, INPUT_PULLUP);
    limit_sw_right.interval(LIMIT_SW_BOUNCE_INTERVAL);
    limit_sw_right.setPressedState(LOW);
}

void update_limit_switches()
{
    limit_sw_left.update();
    limit_sw_right.update();
}

void toggle_limit_finding_mode()
{
    switch (limit_finding_mode)
    {
    case LimitFindingMode::INIT:
        limit_finding_mode = LimitFindingMode::LEFT_FAST;
        break;
    case LimitFindingMode::LEFT_FAST:
        limit_finding_mode = LimitFindingMode::LEFT_RETRACT;
        break;
    case LimitFindingMode::LEFT_RETRACT:
        limit_finding_mode = LimitFindingMode::LEFT_SLOW;
        break;
    case LimitFindingMode::LEFT_SLOW:
        limit_finding_mode = LimitFindingMode::LEFT_POSITION_SET;
        break;
    case LimitFindingMode::LEFT_POSITION_SET:
        limit_finding_mode = LimitFindingMode::RIGHT_FAST;
        break;
    case LimitFindingMode::RIGHT_FAST:
        limit_finding_mode = LimitFindingMode::RIGHT_RETRACT;
        break;
    case LimitFindingMode::RIGHT_RETRACT:
        limit_finding_mode = LimitFindingMode::RIGHT_SLOW;
        break;
    case LimitFindingMode::RIGHT_SLOW:
        limit_finding_mode = LimitFindingMode::REPOSITION;
        break;
    case LimitFindingMode::REPOSITION:
        limit_finding_mode = LimitFindingMode::DONE;
        break;
    case LimitFindingMode::DONE:
        limit_finding_mode = LimitFindingMode::DONE; // Stay done forever
        break;
    }
}

void loop_limit_finding()
{
    update_limit_switches();

    switch (limit_finding_mode)
    {
    case LimitFindingMode::INIT:
        astepper1.setMaxSpeedDistance(Speed::FAST);

        toggle_limit_finding_mode();

        break;

    case LimitFindingMode::LEFT_FAST:
        if (limit_sw_left.pressed())
        {
            packet_sender.send_debug("LimitFinder: LEFT LIMIT HIT [fast]");
            astepper1.stop();

            toggle_limit_finding_mode();
            astepper1.moveDistance(LIMIT_RETRACTION_DISTANCE * RIGHT);
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * LEFT);
        }

        break;

    case LimitFindingMode::LEFT_RETRACT:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_debug("LimitFinder: LEFT LIMIT RETRACTED");
            toggle_limit_finding_mode();

            astepper1.setMaxSpeedDistance(Speed::SLOW);

            break;
        }

    case LimitFindingMode::LEFT_SLOW:
        if (limit_sw_left.pressed())
        {
            packet_sender.send_debug("LimitFinder: LEFT LIMIT HIT [slow]");
            astepper1.stop();


            toggle_limit_finding_mode();
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * LEFT);
        }

        break;
    case LimitFindingMode::LEFT_POSITION_SET:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_debug("LimitFinder: LEFT LIMIT SET");

            astepper1.setCurrentPosition(0);
            astepper1.setMaxSpeedDistance(Speed::FAST);

            toggle_limit_finding_mode();
        }
        break;
    case LimitFindingMode::RIGHT_FAST:
        if (limit_sw_right.pressed())
        {
            packet_sender.send_debug("LimitFinder: RIGHT LIMIT HIT [fast]");
            astepper1.stop();

            toggle_limit_finding_mode();
            astepper1.moveDistance(LIMIT_RETRACTION_DISTANCE * LEFT);
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * RIGHT);
        }

        break;
    case LimitFindingMode::RIGHT_RETRACT:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_debug("LimitFinder: RIGHT LIMIT RETRACTED");
            toggle_limit_finding_mode();

            astepper1.setMaxSpeedDistance(Speed::SLOW);
        }
        break;
    case LimitFindingMode::RIGHT_SLOW:
        if (limit_sw_right.pressed())
        {
            packet_sender.send_debug("LimitFinder: RIGHT LIMIT HIT [slow]");
            astepper1.stop();

            astepper1.setFarLimit(astepper1.currentPosition());
            track_length_distance = astepper1.getCurrentPositionDistance();
            track_length_steps = astepper1.currentPosition();

            astepper1.setMaxSpeedDistance(Speed::ULTRA_FAST);
            astepper1.moveToDistance(track_length_distance / 2.0);

            toggle_limit_finding_mode();
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * RIGHT);
        }
        break;

    case LimitFindingMode::REPOSITION:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_debug("LimitFinder: NOW DONE");
            toggle_limit_finding_mode();
        }
        break;

    case LimitFindingMode::DONE:
        packet_sender.send_debug("LimitFinder: ALREADY DONE");
        break;
    }
    asteppers_run();
}

void enter_limit_finding() {
    asteppers_enable();
}

void exit_limit_finding() {
    asteppers_stop();
    asteppers_run_to_position();
    asteppers_disable();
}

void do_limit_finding() {
    limit_finding_mode = LimitFindingMode::INIT;

    while (limit_finding_mode != LimitFindingMode::DONE) {
        loop_limit_finding();
    }
}