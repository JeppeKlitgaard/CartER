#ifndef STREAM_WRAPPER_H
#define STREAM_WRAPPER_H

#include <CustomArduino.h>
#include <struct.h>
#include <array>

char read_char(Stream &sbuf);

int8_t read_int8(Stream &sbuf);
uint8_t read_uint8(Stream &sbuf);

int16_t read_int16(Stream &sbuf);
uint16_t read_uint16(Stream &sbuf);

int32_t read_int32(Stream &sbuf);
uint32_t read_uint32(Stream &sbuf);

int64_t read_int64(Stream &sbuf);
uint64_t read_uint64(Stream &sbuf);

int64_t read_int64(Stream &sbuf);
uint64_t read_uint64(Stream &sbuf);

float_t read_float32(Stream &sbuf);
double_t read_float64(Stream &sbuf);

std::array<byte, 4> ulong_to_bytes(unsigned long v);
std::array<byte, 4> uint_to_bytes(unsigned int v);

#endif