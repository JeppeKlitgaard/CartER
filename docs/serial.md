# Serial

The communication between the controller and the commander is done over a serial
interface. This allows for real-time communication, though only when proper hardware
implementations are in place on both ends.

In most cases, serial peripherals for a PC and for the Arduino will not be available,
at which point it makes sense to fall back to the Serial-over-USB capability of the
Arduino Due.

Note that this introduces latency due to the finite frame exchange interval of the USB
protocol. In practice this means a round-trip time of ≈ 4ms when using Serial-over-USB.

## Round-trip time

The round-trip time is defined as the time from sending a _ping_ until the 
corresponding _pong_ has been received.

Below is a measurement of $5 \cdot 10^4$ `ping-pong` episodes. 

The vast majority of episodes seem to fall around the $4\, \text{ms}$ mark.

![Serial-over-USB Round-trip Time](img/serial-over-usb-rtt.png){align=center}

