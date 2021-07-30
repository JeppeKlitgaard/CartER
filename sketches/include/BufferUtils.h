#ifndef STREAM_WRAPPER_H
#define STREAM_WRAPPER_H

#include <Arduino.h>

#include <array>

unsigned long read_unsigned_long(Stream &buf);

std::array<byte, 4> ulong_to_bytes(unsigned long l);

#endif