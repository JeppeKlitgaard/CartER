#include <BufferUtils.h>

// Do not use with serial.Timeout
unsigned long read_unsigned_long(Stream &buf)
{
    static_assert(sizeof(unsigned long) == 4, "Unsigned long is not right size");

    byte bytes[4];
    buf.readBytes(bytes, 4);

    unsigned long l = static_cast<unsigned long>(bytes[0]) |
                      static_cast<unsigned long>(bytes[1]) << 8 |
                      static_cast<unsigned long>(bytes[2]) << 16 |
                      static_cast<unsigned long>(bytes[3]) << 24;

    return l;
}
