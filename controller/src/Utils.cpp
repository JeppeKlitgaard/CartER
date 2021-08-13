#include <Utils.h>

byte ctob(const char *c) {
    return byte(atoi(c));
}


// Free Memory function
#ifdef __arm__
// should use uinstd.h to define sbrk but Due causes a conflict
extern "C" char* sbrk(int incr);
#else  // __ARM__
extern char *__brkval;
#endif  // __arm__

int free_memory() {
  char top;
#ifdef __arm__
  return &top - reinterpret_cast<char*>(sbrk(0));
#elif defined(CORE_TEENSY) || (ARDUINO > 103 && ARDUINO != 151)
  return &top - __brkval;
#else  // __arm__
  return __brkval ? &top - __brkval : &top - __malloc_heap_start;
#endif  // __arm__
}

// https://stackoverflow.com/questions/7875581/c-get-index-of-char-element-in-array
int index_of(const char *array, size_t size, char c)
{
     const char* end = array + size;
     const char* match = std::find(array, end, c);
     return (end == match)? -1 : (match-array);
}