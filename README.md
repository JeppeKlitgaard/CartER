CartER
==========

CartER is my summer project at the Biological and Soft Systems Sector of Cavendish Laboratory, University of Cambridge.

It involves a physical experiment with two pendula that are driven by stepper motors managed by an Arduino Due.

The observation space also includes the rotational position for each pendulum, which is measured using magnetic rotary encoders.

The goal is to use Reinforcement Learning (RL) algorithms to accomplish certain tasks (for example, balancing or swing-up) for increasingly difficult mechanical configurations that may include springs connecting the two pendula.

An in-sillica approach is also done in Python, though the experimental part of the project is an important part and the simulated approach is only complementary.

## Command-line usage

Install with:

```sh
poetry install
```

And then see simulations using:

```sh
carter simulate
```

Note that simulate has a few configurable options. See the help page:

```sh
carter --help
```

## Build system

CartER makes use of the PlatformIO toolchain for managing the embedded
controller code for the Arduino Due that powers the project.

The libraries used are defined in `./controller/platformio.ini` along with the
build configuration.
