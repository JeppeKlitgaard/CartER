#include <BufferUtils.h>
#include <Init.h>

#include <struct.h>

uint32_t unpack_uint_32(Stream &sbuf) {
    char buf[4];
    sbuf.readBytes(buf, 4);

    uint32_t rval;

    struct_unpack(buf, "i", &rval);

    return rval;
}

// Do not use with serial.Timeout
unsigned long read_unsigned_long(Stream &buf)
{
    static_assert(sizeof(unsigned long) == 4, "Unsigned long is not right size");

    byte bytes[4];
    buf.readBytes(bytes, 4);

    unsigned long l = (bytes[0]) |
                      (bytes[1]) << 8 |
                      (bytes[2]) << 16 |
                      (bytes[3]) << 24;
    return l;
}

std::array<byte, 4> ulong_to_bytes(unsigned long v)
{
    static_assert(sizeof(unsigned long) == 4, "Unsigned long is not right size");

    return std::array<byte, 4>{
        static_cast<byte>((v)&0xFF),
        static_cast<byte>((v >> 8) & 0xFF),
        static_cast<byte>((v >> 16) & 0xFF),
        static_cast<byte>((v >> 24) & 0xFF),
    };
}

std::array<byte, 4> uint_to_bytes(unsigned int v)
{
    static_assert(sizeof(unsigned int) == 4, "Unsigned int is not right size");

    return std::array<byte, 4>{
        static_cast<byte>((v >> 24) & 0xFF),
        static_cast<byte>((v >> 16) & 0xFF),
        static_cast<byte>((v >> 8) & 0xFF),
        static_cast<byte>((v)&0xFF),
    };
}