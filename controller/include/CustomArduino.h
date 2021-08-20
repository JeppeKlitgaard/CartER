#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wregister"

#include <Arduino.h>

#undef max
#undef min

#undef SERIAL_BUFFER_SIZE
#define SERIAL_BUFFER_SIZE 2048

#pragma GCC diagnostic pop
