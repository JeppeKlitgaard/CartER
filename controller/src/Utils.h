#ifndef UTILS_H
#define UTILS_H

#include <CustomArduino.h>
#include <cstddef>
#include <memory>

#include <type_traits>
#include <utility>
#include <algorithm>
#include <iterator>

byte ctob(const char *c);

int free_memory();

int index_of(const char *array, size_t size, char c);

#endif