#include <Limits.h>

#include <Mode.h>
#include <Init.h>
#include <Protocol.h>
#include <TimerInterrupt.h>

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
            packet_sender.send_info("LimitFinder: LEFT LIMIT HIT [fast]");
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
            packet_sender.send_info("LimitFinder: LEFT LIMIT RETRACTED");
            toggle_limit_finding_mode();

            astepper1.setMaxSpeedDistance(Speed::SLOW);
        }
        break;

    case LimitFindingMode::LEFT_SLOW:
        if (limit_sw_left.pressed())
        {
            packet_sender.send_info("LimitFinder: LEFT LIMIT HIT [slow]");
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
            packet_sender.send_info("LimitFinder: LEFT LIMIT SET");

            astepper1.setCurrentPosition(0);
            astepper1.setMaxSpeedDistance(Speed::MEDIUM);

            toggle_limit_finding_mode();
        }
        break;

    case LimitFindingMode::RIGHT_FAST:
        if (limit_sw_right.pressed())
        {
            packet_sender.send_info("LimitFinder: RIGHT LIMIT HIT [fast]");
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
            packet_sender.send_info("LimitFinder: RIGHT LIMIT RETRACTED");
            toggle_limit_finding_mode();

            astepper1.setMaxSpeedDistance(Speed::SLOW);
        }
        break;

    case LimitFindingMode::RIGHT_SLOW:
        if (limit_sw_right.pressed())
        {
            packet_sender.send_info("LimitFinder: RIGHT LIMIT HIT [slow]");
            astepper1.stop();

            astepper1.setFarLimit(astepper1.currentPosition());
            track_length_distance = astepper1.getCurrentPositionDistance();
            track_length_steps = astepper1.currentPosition();

            std::unique_ptr<ExperimentInfoPacket> packet = std::make_unique<ExperimentInfoPacket>();
            packet->construct(ExperimentInfoSpecifier::TRACK_LENGTH_STEPS, 0, track_length_steps);
            packet_sender.send(std::move(packet));

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
            packet_sender.send_info("LimitFinder: NOW DONE");
            limit_finding_has_been_done = true;
            trigger_ctx.has_failed = false;

            asteppers_stop();

            // Send back response
            std::unique_ptr<FindLimitsPacket> packet = std::make_unique<FindLimitsPacket>();
            packet_sender.send(std::move(packet));

            toggle_limit_finding_mode();
        }
        break;

    case LimitFindingMode::DONE:
        packet_sender.send_info("LimitFinder: ALREADY DONE");
        break;
    }
    asteppers_run();
}

void enter_limit_finding()
{
    asteppers_enable();
}

void exit_limit_finding()
{
    asteppers_stop();
    asteppers_run_to_position();
    asteppers_disable();
}

void do_limit_finding()
{
    limit_finding_mode = LimitFindingMode::INIT;
}

void toggle_limit_check_mode()
{
    switch (limit_check_mode)
    {
    case LimitCheckMode::INIT:
        limit_check_mode = LimitCheckMode::LEFT_SUPER_FAST;
        break;
    case LimitCheckMode::LEFT_SUPER_FAST:
        limit_check_mode = LimitCheckMode::LEFT_FAST;
        break;
    case LimitCheckMode::LEFT_FAST:
        limit_check_mode = LimitCheckMode::LEFT_RETRACT;
        break;
    case LimitCheckMode::LEFT_RETRACT:
        limit_check_mode = LimitCheckMode::LEFT_SLOW;
        break;
    case LimitCheckMode::LEFT_SLOW:
        limit_check_mode = LimitCheckMode::LEFT_POSITION_GET;
        break;
    case LimitCheckMode::LEFT_POSITION_GET:
        limit_check_mode = LimitCheckMode::REPOSITION;
        break;
    case LimitCheckMode::REPOSITION:
        limit_check_mode = LimitCheckMode::DONE;
        break;
    case LimitCheckMode::DONE:
        limit_check_mode = LimitCheckMode::DONE; // Stay done forever
        break;
    }
}

void loop_limit_check()
{
    update_limit_switches();

    switch (limit_check_mode)
    {
    case LimitCheckMode::INIT:
        astepper1.setMaxSpeedDistance(Speed::ULTRA_FAST);
        astepper1.moveToDistance(LIMIT_CHECK_SUPER_FAST_MARGIN_DISTANCE);

        toggle_limit_check_mode();

        break;

    case LimitCheckMode::LEFT_SUPER_FAST:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_info("LimitChecker: LEFT SUPER FAST MARGIN HIT");
            astepper1.setMaxSpeedDistance(Speed::MEDIUM);

            toggle_limit_check_mode();
        }

        break;

    case LimitCheckMode::LEFT_FAST:
        if (limit_sw_left.pressed())
        {
            packet_sender.send_info("LimitChecker: LEFT LIMIT HIT [fast]");
            astepper1.stop();

            toggle_limit_check_mode();
            astepper1.moveDistance(LIMIT_RETRACTION_DISTANCE * RIGHT);
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * LEFT);
        }

        break;

    case LimitCheckMode::LEFT_RETRACT:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_info("LimitChecker: LEFT LIMIT RETRACTED");
            toggle_limit_check_mode();

            astepper1.setMaxSpeedDistance(Speed::SLOW);

        }
        break;

    case LimitCheckMode::LEFT_SLOW:
        if (limit_sw_left.pressed())
        {
            packet_sender.send_info("LimitChecker: LEFT LIMIT HIT [slow]");
            astepper1.stop();

            toggle_limit_check_mode();
        }
        else if (configuration == ONE_CARRIAGES)
        {
            astepper1.moveDistanceCond(STEPPER_BIG_DISTANCE * LEFT);
        }
        break;

    case LimitCheckMode::LEFT_POSITION_GET:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_info("LimitChecker: LEFT LIMIT GET");

            react_limit_check(astepper1.currentPosition());
            astepper1.setCurrentPosition(0);
            astepper1.setMaxSpeedDistance(Speed::ULTRA_FAST);
            astepper1.moveToDistance(track_length_distance / 2.0);

            toggle_limit_check_mode();
        }
        break;

    case LimitCheckMode::REPOSITION:
        if (astepper1.distanceToGo() == 0)
        {
            packet_sender.send_info("LimitChecker: NOW DONE");
            trigger_ctx.has_failed = false;
            toggle_limit_check_mode();

            asteppers_stop();

            // Send back response
            std::unique_ptr<CheckLimitPacket> packet = std::make_unique<CheckLimitPacket>();
            packet_sender.send(std::move(packet));

        }
        break;

    case LimitCheckMode::DONE:
        packet_sender.send_info("LimitChecker: ALREADY DONE");
        break;
    }
    asteppers_run();
}

void do_limit_check()
{
    limit_check_mode = LimitCheckMode::INIT;
}

void react_limit_check(int32_t left_limit_new_position) {
    packet_sender.send_info("LimitChecker: New limit was " + std::to_string(left_limit_new_position));

    std::unique_ptr<ExperimentInfoPacket> packet = std::make_unique<ExperimentInfoPacket>();
    packet->construct(ExperimentInfoSpecifier::POSITION_DRIFT, 1, left_limit_new_position);

    packet_sender.send(std::move(packet));
}


void do_jiggle() {
    float_t astepper1_orig_speed = astepper1.maxSpeed();
    float_t astepper2_orig_speed;
    astepper1.setMaxSpeedDistance(JIGGLE_SPEED_DISTANCE);

    if (configuration == TWO_CARRIAGES) {
        astepper2_orig_speed = astepper2.maxSpeed();
        astepper2.setMaxSpeedDistance(JIGGLE_SPEED_DISTANCE);
    }

    trigger_ctx.run_mode = RunMode::REGULAR;

    uint16_t jiggle_counter = 0;

    while (jiggle_counter < JIGGLE_COUNT) {
        int32_t direction = (jiggle_counter % 2 == 0) ? 1 : -1;
        int32_t steps = static_cast<int>(STEPPER_MICROSTEPS) * direction;

        astepper1.move(steps);

        if (configuration == TWO_CARRIAGES) {
            astepper2.moveCond(steps);
        }

        astepper1.runToPosition();

        if (configuration == TWO_CARRIAGES) {
            astepper2.runToPosition();
        }

        jiggle_counter++;
    }


    astepper1.setMaxSpeed(astepper1_orig_speed);
    if (configuration == TWO_CARRIAGES) {
        astepper2.setMaxSpeed(astepper2_orig_speed);
    }

    asteppers_stop();

    // Send back response
    std::unique_ptr<DoJigglePacket> packet = std::make_unique<DoJigglePacket>();
    packet_sender.send(std::move(packet));
}
