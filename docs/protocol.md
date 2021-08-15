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
