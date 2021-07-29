#ifndef COMMAND_AND_CONTROL_H
#define COMMAND_AND_CONTROL_H

#include <Arduino.h>
#include <Utils.h>
#include <map>

const byte PACKET_END = ctob("\n");
const unsigned int MAX_PACKET_SIZE = 25;


enum class Packet {
    PING,
    PONG,

    UNKNOWN
};

constexpr byte SYMBOL_COMMAND_START = 0x3C; // <
constexpr byte SYMBOL_OBSERVATION_START = 0x3E ; // >

constexpr byte SYMBOL_COMMAND_PING = 0x70; // p
constexpr byte SYMBOL_COMMAND_PONG = 0x50; // P

constexpr byte SYMBOL_OBSERVATION_UNKNOWN = 0x3F; // ?



Packet resolvePacket(byte c);

void loop_command_and_control();

#endif