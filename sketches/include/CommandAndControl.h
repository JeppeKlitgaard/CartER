#ifndef COMMAND_AND_CONTROL_H
#define COMMAND_AND_CONTROL_H

#include <Arduino.h>
#include <Utils.h>

const byte PACKET_END = ctob("\n");
const unsigned int MAX_PACKET_SIZE = 25;

const byte SYMBOL_COMMAND_START = ctob("<");
const byte SYMBOL_OBSERVATION_START = ctob(">");


void loop_command_and_control();

#endif