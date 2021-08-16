#ifndef UTILS_H
#define UTILS_H

#include <CustomArduino.h>

byte ctob(const char *c);

int free_memory();

int index_of(const char *array, size_t size, char c);

template <typename T>
int sgn(T val)
{
    return (T(0) < val) - (val < T(0));
}

#endif