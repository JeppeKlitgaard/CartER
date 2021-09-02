#include <Utils.h>
#include <Init.h>

#include <algorithm>
#include <string>

#include <malloc.h>
#include <stdlib.h>
#include <stdio.h>

char *ramstart = (char *)0x20070000;
char *ramend = (char *)0x20088000;

byte ctob(const char *c)
{
    return byte(atoi(c));
}


uint32_t free_memory() {
    struct mallinfo mi = mallinfo();

    char *heapend = sbrk(0);
    register char *stack_ptr asm("sp");

    return static_cast<uint32_t>(stack_ptr - heapend + mi.fordblks);
}

void send_memory_info(bool all)
{
    struct mallinfo mi = mallinfo();

    char *heapend = sbrk(0);
    register char *stack_ptr asm("sp");

    if (all) {
        packet_sender.send_debug("MEM| Arena: " + std::to_string(mi.arena));
        packet_sender.send_debug("MEM| Ordblks: " + std::to_string(mi.ordblks));
        packet_sender.send_debug("MEM| Uordblks: " + std::to_string(mi.uordblks));
        packet_sender.send_debug("MEM| Fordblks: " + std::to_string(mi.fordblks));
        packet_sender.send_debug("MEM| Keepcost: " + std::to_string(mi.keepcost));
        packet_sender.send_debug("MEM| RAM Start: " + std::to_string((unsigned long)ramstart));
        packet_sender.send_debug("MEM| Data/Bss end: " + std::to_string((unsigned long)&_end));
        packet_sender.send_debug("MEM| Heap End: " + std::to_string((unsigned long)heapend));
        packet_sender.send_debug("MEM| Stack Ptr: " + std::to_string((unsigned long)stack_ptr));
        packet_sender.send_debug("MEM| RAM End: " + std::to_string((unsigned long)ramend));
        packet_sender.send_debug("MEM| Heap RAM Used: " + std::to_string(mi.uordblks));
        packet_sender.send_debug("MEM| Program RAM Used: " + std::to_string(&_end - ramstart));
        packet_sender.send_debug("MEM| Stack RAM Used: " + std::to_string(ramend - stack_ptr));
    }

    packet_sender.send_debug("MEM| Estimated Free RAM: " + std::to_string(stack_ptr - heapend + mi.fordblks));
}


// https://stackoverflow.com/questions/7875581/c-get-index-of-char-element-in-array
int index_of(const char *array, size_t size, char c)
{
    const char *end = array + size;
    const char *match = std::find(array, end, c);
    return (end == match) ? -1 : (match - array);
}