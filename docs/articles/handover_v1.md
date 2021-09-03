# Handover from 10 week internship

This document describes the handover of the project after my (Jeppe Klitgaard)
10 week internship.

!!! important "Last minute change"
    Before I went home on 2021-09-03 (last day) I got an epiphany that some of the weird
    error behaviour I have been experiencing in the last few days originates from
    noise from the stepper motor wires.

    I have cut some of the cable management zip ties and rearranged the wires to
    reduce this effect, as well as disconnected the screw mounting block for the rotary encoders.

    If it does turn out that this has fixed the issue, the cables for the steppers will need to be rerouted
    to reduce noise transmission after which point the cable management and the rotary encoders
    should be able to be reinstated without issue.

    It is possible that the noise has damaged some pins or parts of the Arduino Due,
    in which case the Due would need to be replaced. This seems unlikely, however.

    - Jeppe

## What works

- Commander: Simulated Environment (Implemented as a `PettingZoo`-style `ParallelEnv`)
- Commander: Experimental Environment (Implemented as a `PettingZoo`-style `ParallelEnv`)
- Commander: Various CLI tools and utilities
- Commander: Networking protocol (serial-over-USB based, binary protocol using CPP POD's)
- Commander: Tensorboard integration with many diagonsitic metrics
- Commander: Profiling utility (`yappi`-based)
- Commander: Unified Simulation/Experiment CLI interface for running experiments
- Commander: Thorough logging for easier debugging
- Commander: Code is compliant with: `mypy (strict)`, `black`, `flake8`, and `isort`.
- Commander: Code requires Python 3.9+
- Commander: GPU (CUDA) integrated ML
- Commander: PPO model (from `stable-baselines3`)
- Commander: A2C model (from `stable-baselines3`)
- Controller: Networking protocol
- Controller: Interrupt-based stepping
- Controller: Limit finding and checking
- Controller: Pendulum jiggling
- Controller: Checks for angle and position wander during episode (logged in Tensorboard)
- Controller: Lossy network stream realignment
- Controller: High-level logic controllable over serial
- Hardware: The whole 3D printed setup
- Hardware: Steppers
- Hardware: Stepper drivers
- Hardware: 115200 baud Serial-over-USB
- Hardware: Belt tensioning system

## What does not work

### Rotary encoders
The rotary encoders have been acting very weird in the last few days.
They are now disabled when the `FakeRotaryEncoders` flag is `true`, which has solved intermittent blocking
and crashes. The crashes did not occur consistently or even at a particular point in the code.

Sometimes the Arduino would randomly not exit the jiggling loop, for example.
This is incredibly odd, as no I2C logic is run during that loop, nor by the stepping interrupt.

Perhaps the rotary encoder chip is bad and causes undefined behaviour on the Arduino due to
not acting as a nice I2C slave. Perhaps the Arduino has somehow been damaged,
though hopefully this would not cause such inconsistent, intermittent failures.

This may also be tangentially related to the fact that the rotary encoder does not experience
a magnetic field of ideal strength. This is due to the proximity of the diametrically magnetised
coin magnet to the ferromagnetic ball bearing. This distance should be increased in a later
hardware revision (very easy and unintrusive, just didn't have the time).

This, however, should also not result in the behaviour I saw.

It is also possible that this stems from a bug in the code of the rotary encoder library (AMS_5600),
which I did not fully investigate.

It could also be due to an error in the I2C multiplexer used. Since the Due has two I2C interfaces,
the multiplexer is not strictly needed, though some modification of the AMS_5600 library would
be needed to use both I2C interfaces.

### Random Arduino Resets
I am getting random Arduino resets and I cannot for the life of me figure out why.

The latest theory is that the noise from the wires going to the stepper motors is causing
overvoltages on some logic lines that will then trigger a reset.

This could be tested by disabling the motor power supply and running the experiment for a few
hours. If no resets occur, it is likely a problem related to electrical noise. I haven't had time
to try this, so please go ahead and try. It is some very long hanging fruit!

### Learning on the physical system

I have not yet been able to get significant learning using the experimental setup. I believe as of today (my last day),
the experiment will now run for extended periods of time (after disabling the rotary encoders), and so it may learn over the coming weekend.

It could also be that the PPO/A2C algorithms used are not pleased with the inconsistent step intervals (these arise from learning causing the thread to block for tens of millisecs, as well as delays in the USB protocol and on the host computer).

From Tensorboard it is clear that the correct rewards are being calculated and actions are being taken, though
these do not seem to lead to improved behaviour over time - perhaps I simply haven't given it enough time yet.

I don't have any obvious explanations for why the learning is not better than it currently is. I may have missed a critical bug somewhere, but since rewards and actions are both working as expected, I don't think this will be the case. Perhaps model-free reinforcement learning is just very difficult, particularly on noisy, physical systems?

It could also be that the hyperparameters need significant tuning in order to get stable learning to occur.

### Two-carriage configuration

Most of the code is set up to handle two carriages already, though currently the
limit finding/checking routines would need to be updated to work for a two-carriage system as well.

The hardware and electronics are fully compatible with both a one- and two-carriage configuration.

Likely there is also some code on the environment (not agent) level in the Commander that would need fine-tuning.

The two-carriage configuration should only be persued once the one-carriage configuration is fully working and finalised.

## What could be improved

### New Microcontroller

Dealing with the Arduino Due has been somewhat frustrating, and while changing to a different
one at this stage would require some effort, I believe that it would be worth it.

Problematically the Arduino Due has not seen significant work done on it's core software in many years
and the documentation for the board is even poorer than the already poor documentation for 8-bit AVR Arduino boards.

I changed away from the Arduino build system fairly early on after getting frustrated with the terrible usability problems
of it as well as its practically non-existant support for multiple files. Instead, the project now uses `platform.io`, which
is orders of magnitude more reliable, intuitive, and well-designed.

Ultimately, I think the same should be done for the Arduino.

Since CartER aims to be easy to set up for others and should rely on off-the-shelf parts, I think the [STM Nucleo-144] could be a very powerful option:

- Built-in debugger
- 400 MHz clock speed
- Ethernet support
- Higher baudrates possible (limited to 115200 on Due due to bug in Arduino Core😞)
- Many pins broken out
- Cheap
- Readily available
- `mbed`-compatible

When doing this, it would be very worthwhile to switch away from the Arduino Wiring framework entirely, as this is incredibly poorly documented
and only ever intended for hobbyist use.

Arduino was groundbreaking in that it made access to hobby-level microcontrollers easy and open,
but since then Arm has developed `mbed` which is also open and is infinitely more polished.

`mbed` even has a full RTOS version, which could be very useful for this project.
This would likely make it possible to reduce fiddliness around the I2C connection with the rotary encoder, as well as a generally nicer code layout.

`mbed` + [STM Nucleo-144] is supported in `platform.io`.
There is an existing library for modern TMC stepper drivers for `mbed` and writing a quick library for the rotary encoder
should not take long.

### New stepper drivers

Rather than relying on the rather old TMC26X drivers, these should be changed for TMC2208/TMC2209 drivers.

These have far better support and documentation.

They are cheap and more readily available than the TMC26X drivers, which are strictly inferior.

### Real-time (or close to it) Networking

Using Serial-over-USB is far from ideal and seems to give a 4ms round-trip time in the best of cases (See: [Serial](/development/serial)).

Since the STM board has Ethernet capability built in, it might be useful to use Ethernet for networking.
This would allow far lower latency and much more reliable communication than the current implementation.

A real-time ethernet system like EtherCAT could be used if timing becomes critical, though this will likely be overkill.

Alternatively a proper serial connection could be used.
This would require a simple level-shifting board on the controller-side and a serial board to be installed in the computer.

Both of these options are cheap and readily available.

Arguably Ethernet is more commonly found, though configuration can also be more complicated.

## Getting set up

A good way of working is using VSCode with the `Remote: SSH` functionality.

That way, you get to develop on the powerful workstation and run experiments and simulations on it directly,
but while still using your own IDE configuration and the familiar keyboard of your laptop.

These lines, for example, were written in the rest area upstairs, but on the workstation downstairs in the Physics Lab through seamless integration via SSH and VSCode.

More advice on how to get set up can be found in the other sections of the documentation.

[STM Nucleo-144]: https://www.st.com/en/evaluation-tools/nucleo-h743zi.html
