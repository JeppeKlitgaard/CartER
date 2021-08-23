#include <Protocol.h>

#include <array>
#include <memory>

#include <BufferUtils.h>
#include <Packet.h>
#include <DebugUtils.h>

// Unknown
UnknownPacket::UnknownPacket() {}
byte UnknownPacket::get_id() const { return UnknownPacket::id; }
void UnknownPacket::read(Stream &sbuf){};

// MessageBase
MessageBasePacket::MessageBasePacket() {}
void MessageBasePacket::construct(std::string msg)
{
    _msg = msg;
}

RawPacket MessageBasePacket::to_raw_packet() const
{
    RawPacket raw_packet;
    raw_packet.add(this->get_id());
    raw_packet.add(this->_msg);
    raw_packet.add_newline();

    return raw_packet;
}

void MessageBasePacket::read(Stream &sbuf)
{
    uint32_t _size = read_uint32(sbuf);

    std::string _msg(_size, 0);

    sbuf.readBytes(&_msg[0], _msg.size());
}

// Debug
DebugPacket::DebugPacket() {}
byte DebugPacket::get_id() const { return DebugPacket::id; }

InfoPacket::InfoPacket() {}
byte InfoPacket::get_id() const { return InfoPacket::id; }

// Error
ErrorPacket::ErrorPacket() {}
byte ErrorPacket::get_id() const { return ErrorPacket::id; }

// PingPongBase
PingPongBasePacket::PingPongBasePacket()
{
    ping_timestamp = 0;
}
// byte PingPongBasePacket::get_id() const { return 0x70; }

void PingPongBasePacket::read(Stream &sbuf)
{
    ping_timestamp = read_uint32(sbuf);
}

void PingPongBasePacket::construct(unsigned long timestamp)
{
    ping_timestamp = timestamp;
}

RawPacket PingPongBasePacket::to_raw_packet() const
{
    RawPacket raw_packet;

    raw_packet.add(this->get_id());

    std::array<byte, 4> timestamp = ulong_to_bytes(this->ping_timestamp);
    raw_packet.add(timestamp);

    return raw_packet;
}

// Ping
PingPacket::PingPacket() {}
byte PingPacket::get_id() const { return PingPacket::id; }

// Pong
PongPacket::PongPacket() {}
byte PongPacket::get_id() const { return PongPacket::id; }

// RequestDebugInfo
RequestDebugInfoPacket::RequestDebugInfoPacket() {}
byte RequestDebugInfoPacket::get_id() const { return RequestDebugInfoPacket::id; }

// SetQuantityBase
SetQuantityBasePacket::SetQuantityBasePacket() : operation{SetOperation::NUL}, cart_id{0}, value{0} {}

void SetQuantityBasePacket::read(Stream &sbuf)
{
    char operation_char = read_char(sbuf);

    operation = static_cast<SetOperation>(operation_char);
    cart_id = read_uint8(sbuf);
    value = read_int16(sbuf);
}

// SetPosition
SetPositionPacket::SetPositionPacket() {}
byte SetPositionPacket::get_id() const { return SetPositionPacket::id; }

// SetVelocity
SetVelocityPacket::SetVelocityPacket() {}
byte SetVelocityPacket::get_id() const { return SetVelocityPacket::id; }

// SetMaxVelocity
SetMaxVelocityPacket::SetMaxVelocityPacket() {}
byte SetMaxVelocityPacket::get_id() const { return SetMaxVelocityPacket::id; }

// FindLimits
FindLimitsPacket::FindLimitsPacket() {}
byte FindLimitsPacket::get_id() const { return FindLimitsPacket::id; }

// CheckLimit
CheckLimitPacket::CheckLimitPacket() {}
byte CheckLimitPacket::get_id() const { return CheckLimitPacket::id; }

// SoftLimitReached
SoftLimitReachedPacket::SoftLimitReachedPacket() {}
byte SoftLimitReachedPacket::get_id() const { return SoftLimitReachedPacket::id; }

// DoJiggle
DoJigglePacket::DoJigglePacket() {}
byte DoJigglePacket::get_id() const { return DoJigglePacket::id; }

// Observation
ObservationPacket::ObservationPacket() : _timestamp_micros{0}, _cart_id{0}, _position_steps{0}, _angle_degs{0.0} {}
byte ObservationPacket::get_id() const { return ObservationPacket::id; }

void ObservationPacket::construct(uint32_t timestamp_micros, uint8_t cart_id, int32_t position_steps, float_t angle_degs)
{
    _timestamp_micros = timestamp_micros;
    _cart_id = cart_id;
    _position_steps = position_steps;
    _angle_degs = angle_degs;
}

RawPacket ObservationPacket::to_raw_packet() const
{
    RawPacket raw_packet;

    raw_packet.add(this->get_id());

    raw_packet.add(this->_timestamp_micros);
    raw_packet.add(this->_cart_id);
    raw_packet.add(this->_position_steps);
    raw_packet.add(this->_angle_degs);

    return raw_packet;
}

// ExperimentStart
ExperimentStartPacket::ExperimentStartPacket() : _timestamp_micros{0} {}
byte ExperimentStartPacket::get_id() const { return ExperimentStartPacket::id; }

void ExperimentStartPacket::construct(uint32_t timestamp_micros)
{
    _timestamp_micros = timestamp_micros;
}

RawPacket ExperimentStartPacket::to_raw_packet() const
{
    RawPacket raw_packet;

    raw_packet.add(this->get_id());

    raw_packet.add(this->_timestamp_micros);

    return raw_packet;
}

void ExperimentStartPacket::read(Stream &sbuf)
{
    _timestamp_micros = read_uint32(sbuf);
}

// ExperimentStop
ExperimentStopPacket::ExperimentStopPacket() {}
byte ExperimentStopPacket::get_id() const { return ExperimentStopPacket::id; }

// ExperimentDone
ExperimentDonePacket::ExperimentDonePacket() : _cart_id{0}, _failure_mode{FailureMode::NUL} {}
byte ExperimentDonePacket::get_id() const { return ExperimentDonePacket::id; }

void ExperimentDonePacket::construct(uint8_t cart_id, FailureMode failure_mode)
{
    _cart_id = cart_id;
    _failure_mode = failure_mode;
}

RawPacket ExperimentDonePacket::to_raw_packet() const
{
    RawPacket raw_packet;

    raw_packet.add(this->get_id());

    raw_packet.add(this->_cart_id);
    raw_packet.add(static_cast<int8_t>(this->_failure_mode));

    return raw_packet;
}

void ExperimentDonePacket::read(Stream &sbuf)
{
    _cart_id = read_uint8(sbuf);
    _failure_mode = static_cast<FailureMode>(read_int8(sbuf));
}

// ExperimentInfo
ExperimentInfoPacket::ExperimentInfoPacket() : _specifier{ExperimentInfoSpecifier::NUL}, _cart_id{0}, _value{0} {}
byte ExperimentInfoPacket::get_id() const { return ExperimentInfoPacket::id; }

void ExperimentInfoPacket::construct(ExperimentInfoSpecifier specifier, uint8_t cart_id, std::variant<FailureMode, int32_t> value)
{
    _specifier = specifier;
    _cart_id = cart_id;
    _value = value;
}

RawPacket ExperimentInfoPacket::to_raw_packet() const
{
    RawPacket raw_packet;

    raw_packet.add(this->get_id());

    raw_packet.add(static_cast<uint8_t>(this->_specifier));
    raw_packet.add(this->_cart_id);

    switch (this->_specifier) {
        case ExperimentInfoSpecifier::NUL :
            break;

        case ExperimentInfoSpecifier::POSITION_DRIFT :
            raw_packet.add(std::get<int32_t>(this->_value));
            break;

        case ExperimentInfoSpecifier::FAILURE_MODE :
            raw_packet.add(static_cast<int8_t>(std::get<FailureMode>(this->_value)));
            break;
    }

    return raw_packet;
}
