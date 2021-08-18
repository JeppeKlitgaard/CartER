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

| ID (byte) | ID (ASCII) | Packet                   | Direction (Controller ↔ Commander) | Fields                                                         | Comment                                                |
| :-------: | :--------: | ------------------------ | :--------------------------------: | -------------------------------------------------------------- | ------------------------------------------------------ |
|  `0x00`   |   `NUL`    | `NullPacket`             |                N/A                 | `id`                                                           | Does nothing                                           |
|  `0x3F`   |    `?`     | `UnknownPacket`          |                N/A                 | `id`                                                           | An unknown packet was found                            |
|  `0x23`   |    `#`     | `DebugPacket`            |                 ⟶                  | `id`, `msg`                                                    | Debug messages                                         |
|  `0x7E`   |    `~`     | `InfoPacket`             |                 ⟶                  | `id`, `msg`                                                    | Info messages                                          |
|  `0x21`   |    `!`     | `ErrorPacket`            |                 ⟶                  | `id`, `msg`                                                    | Error messages                                         |
|  `0x70`   |    `p`     | `PingPacket`             |                 ⟷                  | `id`, `timestamp`                                              | Other end should respond with a pong                   |
|  `0x50`   |    `P`     | `PongPacket`             |                 ⟷                  | `id`, `timestamp`                                              | Response to ping                                       |
|  ` 0x24`  |    `$`     | `RequestDebugInfoPacket` |                 ⟵                  | `id`                                                           | Requests debug information from controller             |
|  `0x78`   |    `x`     | `SetPositionPacket`      |                 ⟵                  | `id`, `operation`, `cart_id`, `value`                          | Sets relative or absolute position                     |
|  `0x58`   |    `X`     | `GetPositionPacket`      |                 ⟶                  | `id`                                                           | __UNUSED__. Gets position                              |
|  `0x76`   |    `v`     | `SetVelocityPacket`      |                 ⟵                  | `id`, `operation`, `cart_id`, `value`                          | Sets relative or absolute maximum velocity             |
|  `0x56`   |    `V`     | `GetVelocityPacket`      |                 ⟶                  | `id`                                                           | __UNUSED__. Gets maximum velocity                      |
|  `0x7C`   |    `|`     | `FindLimitsPacket`       |                 ⟷                  | `id`                                                           | Instructs controller to perform limit finding routine  |
|  `0x2F`   |    `/`     | `CheckLimitPacket`       |                 ⟷                  | `id`                                                           | Instructs controller to perform limit checking routine |
|  `0xA7`   |    `§`     | `DoJigglePacket`         |                 ⟷                  | `id`                                                           | Instructs controller to perform a jiggle routine       |
|  `0x40`   |    `@`     | `ObservationPacket`      |                 ⟶                  | `id`, `timestamp_micros`, `cart_id`, `position_steps`, `angle` | Observed state                                         |
|  `0x02`   |   `STX`    | `ExperimentStartPacket`  |                 ⟷                  | `id`, `timestamp_micros`                                       | Observed state                                         |
|  `0x03`   |   `ETX`    | `ExperimentEndPacket`    |                 ⟷                  | `id`                                                           | Observed state                                         |
