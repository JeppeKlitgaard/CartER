"""
Adapted from the OpenAI Gym Cartpole environment.

Implements an environment that allows for an arbitrary number of cartpoles
with friction, delay, sampling rate limitations and other constraints found
in a real-world implementation.

This will complement an experimental setup, and ideally the same RL Agent can
be used for both.
"""

from gym.envs.classic_control.cartpole import CartPoleEnv as GymCartPoleEnv
import numpy as np


class CartPoleEnv(GymCartPoleEnv):
    """
    An extended version of the OpenAI Gym Cartpole Environment.
    """

