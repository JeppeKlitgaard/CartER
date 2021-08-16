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

// FindLimits
FindLimitsPacket::FindLimitsPacket() {}
byte FindLimitsPacket::get_id() const { return FindLimitsPacket::id; }

// CheckLimit
CheckLimitPacket::CheckLimitPacket() {}
byte CheckLimitPacket::get_id() const { return CheckLimitPacket::id; }

// ExperimentDone
ExperimentDonePacket::ExperimentDonePacket() : _failure_mode{FailureMode::NUL}, _cart_id{0} {}
byte ExperimentDonePacket::get_id() const { return ExperimentDonePacket::id; }

void ExperimentDonePacket::construct(FailureMode failure_mode, uint8_t cart_id)
{
    _failure_mode = failure_mode;
    _cart_id = cart_id;
}

RawPacket ExperimentDonePacket::to_raw_packet() const
{
    RawPacket raw_packet;

    raw_packet.add(this->get_id());

    raw_packet.add(static_cast<int8_t>(this->_failure_mode));
    raw_packet.add(this->_cart_id);

    return raw_packet;
}

void ExperimentDonePacket::read(Stream &sbuf)
{
    _failure_mode = static_cast<FailureMode>(read_int8(sbuf));
    _cart_id = read_uint8(sbuf);
}
