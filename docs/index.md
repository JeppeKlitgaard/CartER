# Introduction

CartER [_Cartpole Environment for Reinforcement learning_] is an open-source learning platform that enables the user to quickly
start experimenting with simulated and physical multi-agent reinforcement learning
projects quickly.

CartER is still being actively developed and uses state-of-the-art
reinforcement-learning libraries for greater reproducibility.

## Author

The CartER project is an undergraduate research project undertaken by Jeppe Klitgaard
at the Biological and Soft Systems group at Cavendish Laboratory, University of Cambridge 
under supervision of Professor Pietro Cicuta and Professor Pietro Lio.

Queries can be made to [jk782@cam.ac.uk](mailto:jk782@cam.ac.uk) or through the GitHub
repository located at [JeppeKlitgaard/CartER](https://github.com/JeppeKlitgaard/CartER)

## Citation

CartER can be cited in publications using:

    @misc{carter,
    author = {Jeppe Klitgaard, Pietro Cicuta, Pietro Lio},
    title = {CartER},
    year = {2021},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/JeppeKlitgaard/CartER}},
    }

## Documentation overview

The documentation is incomplete and should not be taken as gospel.

It is divided into a number of categories:

- __Development__: Documentation surrounding the development of the project.  
    Useful for advanced use or further development of the platform.
- __Building__: Documentation on acquiring hardware, 3D-printing parts, and assemblying the project.
- __Usage__: Guides on how to use the platform for machine learning.
- __Articles__: A collection of articles related to the project.
- __Videos__: A collection of videos of the project in action.

## Project overview

The project consists of two main components:

- `Commander`: The Python-based codebase that runs simulations, does both learning and
    inference, and communicates with the `Controller` using a low-level networking protocol
- `Controller`: The C/C++ based codebase that runs on Arduino SAM-based (32-bit ARM) microprocessors (namely the Arduino Due). The `Controller` handles sensors, motors, and communicating with the `Commander` over a serial interface.


## Underlying technologies

CartER uses the following underlying technologies.

### Commander

- [`poetry`](https://python-poetry.org/): Project and package management
- [`stable_baselines3`](https://stable-baselines3.readthedocs.io/): `pytorch`-based standard implementations of common model-free
    reinforcement learning algorithms
- [`tensorboard`](https://www.tensorflow.org/tensorboard): For studying parameters and other output from the experiments
- [`pettingzoo`](https://www.pettingzoo.ml/): Standardising the multi-agent environment

### Controller

- [`platformio`](https://platformio.org/): Framework for embedded programming
