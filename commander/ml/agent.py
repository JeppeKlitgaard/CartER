import logging
from collections.abc import Mapping
from typing import Any, Optional, cast

import numpy as np

from gym import spaces
from gym.envs.classic_control import rendering
from gym.utils import seeding

from scipy.integrate import solve_ivp

from commander.integration import DerivativesWrapper, IntegratorOptions
from commander.ml.constants import FLOAT_TYPE, Action
from commander.type_aliases import State

_FLOAT_MAX = np.finfo(FLOAT_TYPE).max
_DEFAULT_FAILURE_ANGLE = 2 * np.pi * 12 / 360

logger = logging.getLogger(__name__)


StepInfo = tuple[State, float, bool, Mapping[str, Any]]


class CartpoleAgent:
    """
    Base class for all Cartpole Agents.
    """

    def __init__(
        self,
        name: str = "Cartpole_1",
        grav_acc: float = 9.8,  # m/s^2
        mass_cart: float = 1.0,  # kg
        mass_pole: float = 0.1,  # kg
        friction_cart: float = 0.01,  # coefficient
        friction_pole: float = 0.001,  # coefficient
        length: float = 1,  # m
        failure_position: tuple[float, float] = (-2.4, 2.4),  # m
        failure_position_velo: tuple[float, float] = (-np.inf, np.inf),  # m/s
        failure_angle: tuple[float, float] = (
            -_DEFAULT_FAILURE_ANGLE,
            _DEFAULT_FAILURE_ANGLE,
        ),  # rad
        failure_angle_velo: tuple[float, float] = (-np.inf, np.inf),  # rad/s
        start_pos: float = 0,
        start_pos_spread: float = 0.05,
        start_pos_velo: float = 0,
        start_pos_velo_spread: float = 0.05,
        start_angle: float = 0,
        start_angle_spread: float = 0.05,
        start_angle_velo: float = 0,
        start_angle_velo_spread: float = 0.05,
        force_mag: float = 10.0,  # N
        tau: float = 0.02,  # s, seconds between state updates
        integrator: IntegratorOptions = IntegratorOptions.RK45,  # integration method
        integration_resolution: int = 100,  # number of steps to subdivide tau into
    ):
        self.name = name

        self.grav_acc = grav_acc

        self.mass_cart = mass_cart
        self.mass_pole = mass_pole

        self.friction_cart = friction_cart
        self.friction_pole = friction_pole

        self.length = length

        self.failure_position = failure_position
        self.failure_position_velo = failure_position_velo
        self.failure_angle = failure_angle
        self.failure_angle_velo = failure_angle_velo

        self.start_pos = start_pos
        self.start_pos_spread = start_pos_spread
        self.start_pos_velo = start_pos_velo
        self.start_pos_velo_spread = start_pos_velo_spread
        self.start_angle = start_angle
        self.start_angle_spread = start_angle_spread
        self.start_angle_velo = start_angle_velo
        self.start_angle_velo_spread = start_angle_velo_spread

        self.force_mag = force_mag
        self.tau = tau

        self.integrator = integrator
        self.integration_resolution = integration_resolution

        self.info: Mapping[str, Any] = {}

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

        self.np_random: np.random.RandomState
        self.seed()

        self.viewer: Optional[rendering.Viewer] = None
        self.state: State

        self.steps_beyond_done = 0

        self.setup()
        self.reset()

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def observe(self) -> State:
        return self.state

    def setup(self) -> None:
        """
        Called once when first initialised.

        Not called when agent is reset!
        """
        raise NotImplementedError("Override this.")

    def reset(self) -> State:
        raise NotImplementedError("Override this.")

    def step(self, action: Action) -> StepInfo:
        raise NotImplementedError("Override this.")


class SimulatedCartpoleAgent(CartpoleAgent):
    """
    Class for a simulated cartpole agent.
    """

    def _make_random_symmetrical(
        self, mean: float, spread: float, minimum: float, maximum: float
    ) -> State:
        new_state = self.np_random.uniform(
            low=max(mean - spread, minimum), high=min(mean + spread, maximum)
        )

        return cast(State, new_state)

    def setup(self) -> None:
        self.derivatives_wrapper = DerivativesWrapper()

    def reset(self) -> State:
        self.state = np.array(
            [
                self._make_random_symmetrical(
                    self.start_pos,
                    self.start_pos_spread,
                    self.failure_position[0],
                    self.failure_position[1],
                ),
                self._make_random_symmetrical(
                    self.start_pos_velo,
                    self.start_pos_velo_spread,
                    self.failure_position_velo[0],
                    self.failure_position_velo[1],
                ),
                self._make_random_symmetrical(
                    self.start_angle,
                    self.start_angle_spread,
                    self.failure_angle[0],
                    self.failure_angle[1],
                ),
                self._make_random_symmetrical(
                    self.start_angle_velo,
                    self.start_angle_velo_spread,
                    self.failure_angle_velo[0],
                    self.failure_angle_velo[1],
                ),
            ],
        )

        self.steps_beyond_done = 0

        self.derivatives_wrapper.reset()

        return self.state

    def step(self, action: Action) -> StepInfo:
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

    def _integrate(
        self, method: IntegratorOptions, t_span: tuple[float, float], t_step: float, force: float
    ) -> State:
        t = np.arange(t_span[0], t_span[1], t_step)
        sol = solve_ivp(
            fun=self.derivatives_wrapper.equation,
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

    @property
    def mass(self) -> float:
        return self.mass_cart + self.mass_pole

    @property
    def mass_length(self) -> float:
        return self.mass * self.length

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


class ExperimentalCartpoleAgent(CartpoleAgent):
    ...
