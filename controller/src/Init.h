#ifndef INIT_H
#define INIT_H

#include <CustomArduino.h>
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

const size_t INITIAL_OUTPUT_STOP_MARKER_LENGTH = 22;
const byte INITIAL_OUTPUT_STOP_MARKER[22] = {0x45, 0x4E, 0x44, 0x20, 0x4F, 0x46, 0x20, 0x49, 0x4E, 0x49, 0x54, 0x49, 0x41, 0x4C, 0x49, 0x53, 0x41, 0x54, 0x49, 0x4F, 0x4E, 0x0A};

const unsigned int STRING_BUF_SIZE = 100;

// Networking
const unsigned int BAUD_RATE = 74880;
// Can't get higher rates to work on Due (Programming Port)
// Will switch to USB Native when final, but this is annoying for
// developing.

#endif