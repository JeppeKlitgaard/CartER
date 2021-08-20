#include <RotaryEncoder.h>
#include <DebugUtils.h>
#include <I2CMultiplexer.h>
#include <Mode.h>

CustomAMS_5600 rot_encoder1;
CustomAMS_5600 rot_encoder2;

void setup_rotary_encoders()
{
    packet_sender.send_debug("Setting up supply pins for rotary encoders.");
    pinMode(ROT_ENCODER_1_SUPPLY_PIN, OUTPUT);
    if (configuration == TWO_CARRIAGES)
    {
        pinMode(ROT_ENCODER_2_SUPPLY_PIN, OUTPUT);
    }

    packet_sender.send_debug("Power-cycling rotary encoders.");
    power_cycle_rotary_encoders();

    packet_sender.send_debug("Starting rotary encoders.");
    start_rotary_encoders();
}

void start_rotary_encoders()
{
    packet_sender.send_debug("Starting rotary encoder 1.");
    rot_encoder1.start(ROT_ENCODER_1_ADDR);

    if (configuration == TWO_CARRIAGES)
    {
        packet_sender.send_debug("Starting rotary encoder 2.");
        rot_encoder2.start(ROT_ENCODER_2_ADDR);
    }
}

void power_cycle_rotary_encoders()
{
    digitalWrite(ROT_ENCODER_1_SUPPLY_PIN, LOW);

    if (configuration == TWO_CARRIAGES)
    {
        digitalWrite(ROT_ENCODER_2_SUPPLY_PIN, LOW);
    }

    delay(ROT_ENCODERS_POWER_CYCLE_HALFTIME);

    digitalWrite(ROT_ENCODER_1_SUPPLY_PIN, HIGH);
    if (configuration == TWO_CARRIAGES)
    {
        digitalWrite(ROT_ENCODER_2_SUPPLY_PIN, HIGH);
    }

    delay(ROT_ENCODERS_POWER_CYCLE_HALFTIME);
}

CustomAMS_5600 &get_rot_encoder_by_id(uint8_t cart_id)
{
    switch (cart_id)
    {
    case 1:
        return rot_encoder1;
    case 2:
        return rot_encoder2;
    default:
        packet_sender.send_debug("Invalid cart_id: " + std::to_string(cart_id));
        throw std::out_of_range("Invalid cart_id");
    }
}
