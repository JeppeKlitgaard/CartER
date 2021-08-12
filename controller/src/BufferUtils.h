#ifndef STREAM_WRAPPER_H
#define STREAM_WRAPPER_H

#include <CustomArduino.h>

#include <array>

unsigned long read_unsigned_long(Stream &buf);

std::array<byte, 4> ulong_to_bytes(unsigned long v);
std::array<byte, 4> uint_to_bytes(unsigned int v);

#endif