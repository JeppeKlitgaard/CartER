#include <LimitFinding.h>

#include <Mode.h>
#include <Steppers.h>

#include <DebugUtils.h>

Bounce2::Button limit_sw_left = Bounce2::Button();
Bounce2::Button limit_sw_right = Bounce2::Button();

void setup_limit_switches()
{
    DPL("Configuring limit switches.");

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
            S.println("LEFT LIMIT HIT!");
            astepper1.stop();

            toggle_limit_finding_mode();
            astepper1.moveDistance(20 * RIGHT);
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * LEFT);
        }

        break;

    case LimitFindingMode::LEFT_RETRACT:
        if (astepper1.distanceToGo() == 0)
        {
            DPL("Done left retracting.");
            toggle_limit_finding_mode();

            astepper1.setMaxSpeedDistance(Speed::SLOW);

            break;
        }

    case LimitFindingMode::LEFT_SLOW:
        if (limit_sw_left.pressed())
        {
            S.println("LEFT LIMIT HIT!");
            astepper1.stop();

            astepper1.setMaxSpeedDistance(Speed::FAST);
            astepper1.moveDistance(50 * RIGHT);

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
            DPL("Setting left position");

            astepper1.setCurrentPositionDistance(0.0);

            toggle_limit_finding_mode();
        }
        break;
    case LimitFindingMode::RIGHT_FAST:
        if (limit_sw_right.pressed())
        {
            S.println("RIGHT LIMIT HIT!");
            astepper1.stop();

            toggle_limit_finding_mode();
            astepper1.moveDistance(20 * LEFT);
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * RIGHT);
        }

        break;
    case LimitFindingMode::RIGHT_RETRACT:
        if (astepper1.distanceToGo() == 0)
        {
            DPL("Done right retracting.");
            toggle_limit_finding_mode();

            astepper1.setMaxSpeedDistance(Speed::SLOW);
        }
        break;
    case LimitFindingMode::RIGHT_SLOW:
        if (limit_sw_right.pressed())
        {
            S.println("RIGHT LIMIT HIT!");
            astepper1.stop();

            astepper1.setMaxSpeedDistance(Speed::FAST);
            track_length_distance = astepper1.getCurrentPositionDistance() - 50.0;

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
            DPL("Done repositioning.");
            toggle_limit_finding_mode();
        }
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