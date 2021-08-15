# Introduction

CartpoleML is an open-source learning platform that enables the user to quickly
start experimenting with simulated and physical multi-agent reinforcement learning
projects quickly.

CartpoleML is still being actively developed and uses state-of-the-art
reinforcement-learning libraries for greater reproducibility.

## Author

The CartpoleML project is an undergraduate research project undertaken by Jeppe Klitgaard
at the Biological and Soft Systems group at Cavendish Laboratory, University of Cambridge 
under supervision of Dr Pietro Cicuta and Dr Pietro Lio.

Queries can be made to [jk782@cam.ac.uk](mailto:jk782@cam.ac.uk) or through the GitHub
repository located at [JeppeKlitgaard/CartpoleML](https://github.com/JeppeKlitgaard/CartpoleML)

## Citation

CartpoleML can be cited in publications using:

    @misc{cartpoleml,
    author = {Jeppe Klitgaard, Pietro Cicuta, Pietro Lio},
    title = {CartpoleML},
    year = {2021},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/JeppeKlitgaard/CartpoleML}},
    }

## Project overview

The project consists of two main components:

- `Commander`: The Python-based codebase that runs simulations, does both learning and
    inference, and communicates with the `Controller` using a low-level networking protocol
- `Controller`: The C/C++ based codebase that runs on Arduino SAM-based (32-bit ARM) microprocessors (namely the Arduino Due). The `Controller` handles sensors, motors, and communicating with the `Commander` over a serial interface.


## Underlying technologies

CartpoleML uses the following underlying technologies.

### Commander

- [`poetry`](https://python-poetry.org/): Project and package management
- [`stable_baselines3`](https://stable-baselines3.readthedocs.io/): `pytorch`-based standard implementations of common model-free
    reinforcement learning algorithms
- [`tensorboard`](https://www.tensorflow.org/tensorboard): For studying parameters and other output from the experiments
- [`pettingzoo`](https://www.pettingzoo.ml/): Standardising the multi-agent environment

### Controller

- [`platformio`](https://platformio.org/): Framework for embedded programming

## Installation
First clone the CartpoleML repository.

### Commander
1. Install `poetry`
2. Run `poetry install`

### Controller
1. Install `platformio`
2. Run `pio lib install` in the `./controller` folder
3. Run `pio run`

## Project layout

    mkdocs.yml          # Documentation configuration file.
    docs/**             # Documentation files.
    pyproject.toml      # Poetry project configuration.
    commander/**        # Commander code.
    controller/
        platformio.ini  # Platform.io project configuration.
        **              # Controlelr code.
    notebooks/**        # Notebooks that are helpful in debugging or studying experiment.