#include <BufferUtils.h>
#include <struct.h>
#include <Init.h>

// char
char read_char(Stream &sbuf)
{
    const int size = 1;
    char buf[size];

    sbuf.readBytes(buf, size);

    char rval;

    struct_unpack(buf, "b", &rval);

    return rval;
}

// 8 bit int
int8_t read_int8(Stream &sbuf)
{
    const int size = 1;
    char buf[size];

    sbuf.readBytes(buf, size);

    int8_t rval;

    struct_unpack(buf, "b", &rval);

    return rval;
}

uint8_t read_uint8(Stream &sbuf)
{
    const int size = 1;
    char buf[size];

    sbuf.readBytes(buf, size);

    uint8_t rval;

    struct_unpack(buf, "B", &rval);

    return rval;
}

// 16 bit int
int16_t read_int16(Stream &sbuf)
{
    const int size = 2;
    char buf[size];

    sbuf.readBytes(buf, size);

    int16_t rval;

    struct_unpack(buf, "<h", &rval);

    return rval;
}

uint16_t read_uint16(Stream &sbuf)
{
    const int size = 2;
    char buf[size];

    sbuf.readBytes(buf, size);

    uint16_t rval;

    struct_unpack(buf, "<H", &rval);

    return rval;
}

// 32 bit int
int32_t read_int32(Stream &sbuf)
{
    const int size = 4;
    char buf[size];

    sbuf.readBytes(buf, size);

    int32_t rval;

    struct_unpack(buf, "<i", &rval);

    return rval;
}

uint32_t read_uint32(Stream &sbuf)
{
    const int size = 4;
    char buf[size];

    sbuf.readBytes(buf, size);

    uint32_t rval;

    struct_unpack(buf, "<I", &rval);

    return rval;
}

// 64 bit int
int64_t read_int64(Stream &sbuf)
{
    const int size = 8;
    char buf[size];

    sbuf.readBytes(buf, size);

    int64_t rval;

    struct_unpack(buf, "<i", &rval);

    return rval;
}

uint64_t read_uint64(Stream &sbuf)
{
    const int size = 8;
    char buf[size];

    sbuf.readBytes(buf, size);

    uint64_t rval;

    struct_unpack(buf, "<I", &rval);

    return rval;
}

// 32 bit float (float_t)
float_t read_float32(Stream &sbuf)
{
    const int size = 4;
    char buf[size];

    sbuf.readBytes(buf, size);

    float_t rval;

    struct_unpack(buf, "<f", &rval);

    return rval;
}

// 64 bit float (double_t)
double_t read_float64(Stream &sbuf)
{
    const int size = 8;
    char buf[size];

    sbuf.readBytes(buf, size);

    double_t rval;

    struct_unpack(buf, "<d", &rval);

    return rval;
}
// // Do not use with serial.Timeout
// unsigned long read_unsigned_long(Stream &buf)
// {
//     static_assert(sizeof(unsigned long) == 4, "Unsigned long is not right size");

//     byte bytes[4];
//     buf.readBytes(bytes, 4);

//     unsigned long l = (bytes[0]) |
//                       (bytes[1]) << 8 |
//                       (bytes[2]) << 16 |
//                       (bytes[3]) << 24;
//     return l;
// }

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