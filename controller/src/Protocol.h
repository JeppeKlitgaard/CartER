#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <CustomArduino.h>

#include <vector>
#include <string>
#include <variant>

#include <PString.h>
#include <Packet.h>
#include <Init.h>
#include <Mode.h>

/** Protocol is little-endian.
  */

// Enums
// Mode
enum class SetOperation : char
{
    SUBTRACT = '-',
    EQUAL = '=',
    ADD = '+',
    NUL = '0',
};

// Unknown
class UnknownPacket : public InboundPacket
{
public:
    static const byte id = 0x3F; // ?

    UnknownPacket();
    using Packet::construct;

    virtual byte get_id() const override;

    virtual void read(Stream &sbuf) override;
};

class MessageBasePacket : public BidirectionalPacket
{
public:
    std::string _msg;

    MessageBasePacket();
    using OutboundPacket::construct;
    void construct(std::string msg);

    virtual byte get_id() const override = 0;
    virtual RawPacket to_raw_packet() const override;
    virtual void read(Stream &sbuf) override;
};

// Debug
class DebugPacket : public MessageBasePacket
{
public:
    static const byte id = 0x23; // #

    DebugPacket();
    using MessageBasePacket::construct;

    virtual byte get_id() const override;
};

// Info
class InfoPacket : public MessageBasePacket
{
public:
    static const byte id = 0x7E; // #

    InfoPacket();
    using MessageBasePacket::construct;

    virtual byte get_id() const override;
};

// Error
class ErrorPacket : public MessageBasePacket
{
public:
    static const byte id = 0x21; // !

    ErrorPacket();
    using MessageBasePacket::construct;

    virtual byte get_id() const override;
};

// PingPongBase
class PingPongBasePacket : public BidirectionalPacket
{
public:
    unsigned long ping_timestamp;

    PingPongBasePacket();
    using Packet::construct;
    virtual void construct(unsigned long timestamp);

    virtual byte get_id() const override = 0;

    virtual RawPacket to_raw_packet() const override;
    virtual void read(Stream &sbuf) override;
};

// Ping
class PingPacket : public PingPongBasePacket
{

public:
    static const byte id = 0x70; // p

    PingPacket();
    using PingPongBasePacket::construct;

    virtual byte get_id() const override;
};

// Pong
class PongPacket : public PingPongBasePacket
{
public:
    static const byte id = 0x50; // P

    PongPacket();
    using PingPongBasePacket::construct;

    virtual byte get_id() const override;
};

// RequestDebugInfo
class RequestDebugInfoPacket : public OnlyIDPacket
{
public:
    static const byte id = 0x24; // |

    RequestDebugInfoPacket();
    using OnlyIDPacket::construct;

    virtual byte get_id() const override;
};

// SetQuantityBase
class SetQuantityBasePacket : public InboundPacket
{
public:
    SetOperation operation;
    uint8_t cart_id;
    int16_t value;

    SetQuantityBasePacket();
    using Packet::construct;

    virtual byte get_id() const override = 0;

    virtual void read(Stream &sbuf) override;
};

// SetPosition
class SetPositionPacket : public SetQuantityBasePacket
{
public:
    static const byte id = 0x78; // x

    SetPositionPacket();
    using SetQuantityBasePacket::construct;

    virtual byte get_id() const override;
};

// SetVelocity
class SetVelocityPacket : public SetQuantityBasePacket
{
public:
    static const byte id = 0x76; // v

    SetVelocityPacket();
    using SetQuantityBasePacket::construct;

    virtual byte get_id() const override;
};

// SetMaxVelocity
class SetMaxVelocityPacket : public SetQuantityBasePacket
{
public:
    static const byte id = 0x77; // w

    SetMaxVelocityPacket();
    using SetQuantityBasePacket::construct;

    virtual byte get_id() const override;
};

// FindLimits
class FindLimitsPacket : public OnlyIDPacket
{
public:
    static const byte id = 0x7C; // |

    FindLimitsPacket();
    using OnlyIDPacket::construct;

    virtual byte get_id() const override;
};

// CheckLimit
class CheckLimitPacket : public OnlyIDPacket
{
public:
    static const byte id = 0x2F; // /

    CheckLimitPacket();
    using OnlyIDPacket::construct;

    virtual byte get_id() const override;
};

// SoftLimitReached
class SoftLimitReachedPacket : public OnlyIDPacket
{
public:
    static const byte id = 0x5C; // \...

    SoftLimitReachedPacket();
    using OnlyIDPacket::construct;

    virtual byte get_id() const override;
};

// DoJiggle
class DoJigglePacket : public OnlyIDPacket
{
public:
    static const byte id = 0xA7; // §

    DoJigglePacket();
    using OnlyIDPacket::construct;

    virtual byte get_id() const override;
};

// Observation
class ObservationPacket : public OutboundPacket
{
public:
    uint32_t _timestamp_micros;
    uint8_t _cart_id;
    int32_t _position_steps;
    float_t _angle_degs;

    static const byte id = 0x40; // @

    ObservationPacket();
    using OutboundPacket::construct;

    virtual byte get_id() const override;

    virtual void construct(uint32_t timestamp_micros, uint8_t cart_id, int32_t position_steps, float_t angle_degs);
    virtual RawPacket to_raw_packet() const override;
};

// ExperimentStart
class ExperimentStartPacket : public BidirectionalPacket
{
public:
    uint32_t _timestamp_micros;

    static const byte id = 0x02; // STX (start-of-text)

    ExperimentStartPacket();
    using OutboundPacket::construct;

    virtual byte get_id() const override;

    virtual void construct(uint32_t timestamp_micros);
    virtual RawPacket to_raw_packet() const override;

    virtual void read(Stream &sbuf) override;
};

// ExperimentStop
class ExperimentStopPacket : public OnlyIDPacket
{
public:
    static const byte id = 0x03; // ETX (end-of-text)

    ExperimentStopPacket();
    using OnlyIDPacket::construct;

    virtual byte get_id() const override;
};

// ExperimentDone
class ExperimentDonePacket : public BidirectionalPacket
{
public:
    uint8_t _cart_id;
    FailureMode _failure_mode;

    static const byte id = 0x04; // EOT (end-of-transmission)

    ExperimentDonePacket();
    using BidirectionalPacket::construct;

    virtual byte get_id() const override;

    virtual void construct(uint8_t cart_id, FailureMode failure_mode);
    virtual RawPacket to_raw_packet() const override;
    virtual void read(Stream &sbuf) override;
};

enum class ExperimentInfoSpecifier
{
    NUL = 0,
    POSITION_DRIFT = 1,
    FAILURE_MODE = 2,
    TRACK_LENGTH_STEPS = 3,
};

// ExperimentInfo
class ExperimentInfoPacket : public OutboundPacket
{
public:
    ExperimentInfoSpecifier _specifier;
    uint8_t _cart_id;
    std::variant<FailureMode, int32_t> _value;

    static const byte id = 0x3A; // :

    ExperimentInfoPacket();
    using OutboundPacket::construct;

    virtual byte get_id() const override;

    virtual void construct(ExperimentInfoSpecifier specifier, uint8_t cart_id, std::variant<FailureMode, int32_t> value);
    virtual RawPacket to_raw_packet() const override;
};

#endif
