#ifndef UTILS_H
#define UTILS_H

#include <CustomArduino.h>

extern char _end;
extern "C" char *sbrk(int i);

byte ctob(const char *c);


uint32_t free_memory();

void send_memory_info(bool all = false);

int index_of(const char *array, size_t size, char c);

template <typename T>
int sgn(T val)
{
    return (T(0) < val) - (val < T(0));
}

#endif