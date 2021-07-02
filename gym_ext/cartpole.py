"""
Adapted from the OpenAI Gym Cartpole environment.

Implements an environment that allows for an arbitrary number of cartpoles
with friction, delay, sampling rate limitations and other constraints found
in a real-world implementation.

This will complement an experimental setup, and ideally the same RL Agent can
be used for both.
"""

from enum import Enum
from typing import Any, Optional, cast

import numpy as np
from numpy.random.mtrand import RandomState

from gym import Env, logger, spaces
from gym.envs.classic_control import rendering
from gym.utils import seeding

from scipy.integrate import solve_ivp

from gym_ext.constants import FLOAT_TYPE
from gym_ext.equations import derivatives_wrapper
from gym_ext.typing import State


class ActionEnumerator(int, Enum):
    FORWARDS = 0
    BACKWARDS = 1


class IntegratorOptions(str, Enum):
    RK45 = "RK45"
    LSODA = "LSODA"


_FLOAT_MAX = np.finfo(FLOAT_TYPE).max

_DEFAULT_FAILURE_ANGLE = 2 * np.pi * 12 / 360


# We subclass Env since we change basically everything in implementation anyway,
# Thus no need to subclass existing CartPoleEnv
class CartPoleEnv(Env):  # type: ignore[misc]
    """
    An extended version of the OpenAI Gym Cartpole Environment.

    Source:
        This is adapted from the OpenAI CartPole Environment.


        This environment corresponds to the version of the cart-pole problem
        described by Barto, Sutton, and Anderson and more accurately described
        by Florian later.

    Observation:
        Type: Box(4)
        Num     Observation               Min                     Max
        0       Cart Position             -4.8                    4.8
        1       Cart Velocity             -Inf                    Inf
        2       Pole Angle                -0.418 rad (-24 deg)    0.418 rad (24 deg)
        3       Pole Angular Velocity     -Inf                    Inf
    """

    def __init__(
        self,
        grav_acc: float = 9.8,  # m/s^2
        mass_cart: float = 1.0,  # kg
        mass_pole: float = 0.1,  # kg
        friction_cart: float = 0.01,  # coefficient
        friction_pole: float = 0.001,  # coefficient
        length: float = 1,  # m
        failure_angle: tuple[float, float] = (
            -_DEFAULT_FAILURE_ANGLE,
            _DEFAULT_FAILURE_ANGLE,
        ),  # rad
        failure_position: tuple[float, float] = (-2.4, 2.4),  # m
        starting_spread: float = 0.05,
        force_mag: float = 10.0,  # N
        tau: float = 0.02,  # s, seconds between state updates
        integrator: IntegratorOptions = IntegratorOptions.RK45,  # integration method
        integration_resolution: int = 100,  # number of steps to subdivide tau into
    ):
        self.grav_acc = grav_acc

        self.mass_cart = mass_cart
        self.mass_pole = mass_pole

        self.friction_cart = friction_cart
        self.friction_pole = friction_pole

        self.length = length

        self.failure_angle = failure_angle
        self.failure_position = failure_position

        self.starting_spread = starting_spread

        self.force_mag = force_mag
        self.tau = tau

        self.integrator = integrator
        self.integration_resolution = integration_resolution

        self.spec = {
            "reward_threshold": 1000,
            "max_episode_steps": 10,
        }

        # Calculate size of spaces.
        # Factors of 2 are to ensure that even failing observations are still within
        # the observation space.
        low = np.array(
            [
                self.failure_position[0] * 2,  # Position
                -_FLOAT_MAX,  # Velocity can be any float
                self.failure_angle[0] * 2,  # Angle
                -_FLOAT_MAX,  # Angular velocity
            ],
            dtype=FLOAT_TYPE,
        )
        high = np.array(
            [
                self.failure_position[1] * 2,  # Position
                _FLOAT_MAX,  # Velocity can be any float
                self.failure_angle[1] * 2,  # Angle
                _FLOAT_MAX,  # Angular velocity
            ],
            dtype=FLOAT_TYPE,
        )

        # Can only apply two actions, back or forth
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(low, high, dtype=FLOAT_TYPE)

        self.np_random: RandomState
        self.seed()

        self.viewer: Optional[rendering.Viewer] = None
        self.state: Optional[State] = None

        self.steps_beyond_done = 0

    @property
    def mass(self) -> float:
        return self.mass_cart + self.mass_pole

    @property
    def mass_length(self) -> float:
        return self.mass * self.length

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _integrate(
        self, method: IntegratorOptions, t_span: tuple[float, float], t_step: float, force: float
    ) -> State:
        t = np.arange(t_span[0], t_span[1], t_step)
        sol = solve_ivp(
            fun=derivatives_wrapper,
            t_span=t_span,
            y0=self.state,
            method=method,
            t_eval=t,
            args=(
                force,
                self.grav_acc,
                self.friction_cart,
                self.friction_pole,
                self.length,
                self.mass_pole,
                self.mass_length,
                self.mass,
            ),
        )

        new_state = cast(State, np.fromiter((x[-1] for x in sol.y), FLOAT_TYPE))

        return new_state

    def _check_state(self, state: State) -> bool:
        x = state[0]
        theta = state[2]

        conditions = (
            x < self.failure_position[0],
            x > self.failure_position[1],
            theta < self.failure_angle[0],
            theta > self.failure_angle[1],
        )

        return any(conditions)

    def step(self, action: int) -> tuple[State, float, bool, dict[str, Any]]:
        """
        Performs a single step in the environment using the given action.

        The state information available to our agent is the position of the
        cart and the angle of the pole as well as their first derivatives.

        Using the approach described in Florian's paper
        https://coneural.org/florian/papers/05_cart_pole.pdf

        We are able to obtain the second derivatives of position and angle as
        well.

        These can then be numerically integrated to update the environment
        based on the action.
        """
        if not self.action_space.contains(action):
            raise ValueError(f"Action {action} not in action space. Invalid.")

        # Resolve direction of force
        force = self.force_mag if action == 1 else -self.force_mag

        # Update state
        self.state = self._integrate(
            IntegratorOptions.RK45, (0, self.tau), self.tau / self.integration_resolution, force
        )

        done = self._check_state(self.state)

        if not done:
            reward = 1.0

        elif not self.steps_beyond_done:
            # First call after being done
            reward = 1.0

            self.steps_beyond_done += 1

        else:
            logger.warn(
                "We are already done. Stop calling `step()`. You may want to call `reset()`."
            )
            self.steps_beyond_done += 1
            reward = 0.0

        return self.state, reward, done, {}

    def reset(self) -> State:
        self.state = self.np_random.uniform(
            low=-self.starting_spread, high=self.starting_spread, size=(4,)
        )
        self.steps_beyond_done = 0

        return self.state

    def render(self, mode: str = "human") -> Any:
        screen_width = 600
        screen_height = 400

        world_width = abs(self.failure_position[0] - self.failure_position[1]) * 0.95
        scale = screen_width / world_width
        carty = 100  # TOP OF CART
        polewidth = 10.0
        polelen = scale * (2 * self.length)
        cartwidth = 50.0
        cartheight = 30.0

        if self.viewer is None:
            self.viewer = rendering.Viewer(screen_width, screen_height)
            l, r, t, b = -cartwidth / 2, cartwidth / 2, cartheight / 2, -cartheight / 2
            axleoffset = cartheight / 4.0
            cart = rendering.FilledPolygon([(l, b), (l, t), (r, t), (r, b)])
            self.carttrans = rendering.Transform()
            cart.add_attr(self.carttrans)
            self.viewer.add_geom(cart)
            l, r, t, b = -polewidth / 2, polewidth / 2, polelen - polewidth / 2, -polewidth / 2
            pole = rendering.FilledPolygon([(l, b), (l, t), (r, t), (r, b)])
            pole.set_color(0.8, 0.6, 0.4)
            self.poletrans = rendering.Transform(translation=(0, axleoffset))
            pole.add_attr(self.poletrans)
            pole.add_attr(self.carttrans)
            self.viewer.add_geom(pole)
            self.axle = rendering.make_circle(polewidth / 2)
            self.axle.add_attr(self.poletrans)
            self.axle.add_attr(self.carttrans)
            self.axle.set_color(0.5, 0.5, 0.8)
            self.viewer.add_geom(self.axle)
            self.track = rendering.Line((0, carty), (screen_width, carty))
            self.track.set_color(0, 0, 0)
            self.viewer.add_geom(self.track)

            self._pole_geom = pole

        if self.state is None:
            return None

        # Edit the pole polygon vertex
        pole = self._pole_geom
        l, r, t, b = -polewidth / 2, polewidth / 2, polelen - polewidth / 2, -polewidth / 2
        pole.v = [(l, b), (l, t), (r, t), (r, b)]

        x = self.state
        cartx = x[0] * scale + screen_width / 2.0  # MIDDLE OF CART
        self.carttrans.set_translation(cartx, carty)
        self.poletrans.set_rotation(-x[2])

        return self.viewer.render(return_rgb_array=mode == "rgb_array")

    def close(self) -> None:
        if self.viewer:
            self.viewer.close()
            self.viewer = None
