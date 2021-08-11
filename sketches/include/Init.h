#ifndef INIT_H
#define INIT_H


#include <Arduino.h>
#include <PacketReactor.h>
#include <PacketSender.h>
#include <Mode.h>

#define DEBUG
// #define SERIALUSB


// Definitions
#ifdef SERIALUSB
#define S SerialUSB
#else
#define S Serial
#endif

void initialise();

const Mode INITIAL_MODE = COMMAND_AND_CONTROL;

const unsigned int STRING_BUF_SIZE = 100;

// Networking
const unsigned int BAUD_RATE = 74880;
// Can't get higher rates to work on Due (Programming Port)
// Will switch to USB Native when final, but this is annoying for
// developing.

#endif