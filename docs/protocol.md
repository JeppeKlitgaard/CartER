# Protocol

The protocol used for serial communication is implemented using POD's (Plain Old Datatypes)
and serialised to little-endian binary before being sent back and forth over a serial interface.

Using a proper serial-connection rather than rely on the Serial-over-USB that comes standard
with the Arduino Due is recommended to avoid the ≈ 4ms round-trip time in USB packet delivery.

## Implementation - Commander

The protocol is best understood by reading through the `protocol.py` file on the
commander. It should be fairly easily understood by those familiar with Python.

It uses the standard library `struct` to pack and unpack data.

## Implementation - Controller

The protocol must match the one implemented on the `commander` exactly, as any difference
in packet lengths will lead to future misalignment that cannot easily be corrected for.

A `struct`-like library is also used on the controller to allow for easy matching between the
controller and commander protocol implementations.

## Packet overview

| ID (byte) | ID (ASCII) | Packet                   | Direction (Controller ↔ Commander) | Comment                                                |
| :-------: | :--------: | ------------------------ | :--------------------------------: | ------------------------------------------------------ |
|  `0x00`   |   `NUL`    | `NullPacket`             |                N/A                 | Does nothing                                           |
|  `0x70`   |    `p`     | `PingPacket`             |                 ⟷                  | Other end should respond with a pong                   |
|  `0x50`   |    `P`     | `PongPacket`             |                 ⟷                  | Response to ping                                       |
|  `0x23`   |    `#`     | `DebugPacket`            |                 ⟶                  | Debug messages                                         |
|  `0x7E`   |    `~`     | `InfoPacket`             |                 ⟶                  | Info messages                                          |
|  `0x21`   |    `!`     | `ErrorPacket`            |                 ⟶                  | Error messages                                         |
|  ` 0x24`  |    `$`     | `RequestDebugInfoPacket` |                 ⟵                  | Requests debug information from controller             |
|  `0x3F`   |    `?`     | `UnknownPacket`          |                N/A                 | An unknown packet was found                            |
|  `0x78`   |    `x`     | `SetPositionPacket`      |                 ⟵                  | Sets relative or absolute position                     |
|  `0x58`   |    `X`     | `GetPositionPacket`      |                 ⟶                  | __UNUSED__. Gets position                              |
|  `0x76`   |    `v`     | `SetVelocityPacket`      |                 ⟵                  | Sets relative or absolute maximum velocity             |
|  `0x56`   |    `V`     | `GetVelocityPacket`      |                 ⟶                  | __UNUSED__. Gets maximum velocity                      |
|  `0x7C`   |    `|`     | `FindLimitsPacket`       |                 ⟵                  | Instructs controller to perform limit finding routine  |
|  `0x2F`   |    `/`     | `CheckLimitPacket`       |                 ⟵                  | Instructs controller to perform limit checking routine |
|  `0x40`   |    `@`     | `ObservationPacket`      |                 ⟶                  | Observed state                                         |
