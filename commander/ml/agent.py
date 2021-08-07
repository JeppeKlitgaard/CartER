from abc import ABC, abstractmethod
from enum import Enum
import logging
from collections.abc import Mapping
from typing import Any, Optional, TypedDict, cast, Union

import numpy as np
import math

from gym import spaces
from gym.envs.classic_control import rendering
from gym.utils import seeding

from scipy.integrate import solve_ivp

from commander.integration import DerivativesWrapper, IntegratorOptions
from commander.ml.constants import Action
from commander.constants import FLOAT_TYPE
from commander.type_aliases import State

_FLOAT_MAX = np.finfo(FLOAT_TYPE).max
_DEFAULT_FAILURE_ANGLE = 2 * np.pi * 12 / 360

logger = logging.getLogger(__name__)


StepInfo = tuple[State, float, bool, Mapping[str, Any]]
StateChecks = dict[str, bool]

class FailureDescriptors(str, Enum):
    MAX_STEPS_REACHED = "steps/max"

    POSITION_LEFT = "position/left"
    POSITION_RIGHT = "position/right"
    ANGLE_LEFT = "angle/left"
    ANGLE_RIGHT = "angle/right"

    IMBALANCE = "imbalance"


DEFAULT_GOAL_PARAMS = object()  # Sentinel for default goal params


class CartpoleAgent:
    """
    Base class for all Cartpole Agents.
    """

    def __init__(
        self,
        name: str = "Cartpole_1",
        grav_acc: float = 9.8,  # m/s^2
        mass_cart: float = 5.0,  # kg
        mass_pole: float = 0.1,  # kg
        friction_cart: float = 0.01,  # coefficient
        friction_pole: float = 0.001,  # coefficient
        length: float = 1,  # m
        start_pos: float = 0.0,
        start_pos_spread: float = 0.05,
        start_pos_velo: float = 0.0,
        start_pos_velo_spread: float = 0.05,
        start_angle: float = 0.0,
        start_angle_spread: float = 0.05,
        start_angle_velo: float = 0.0,
        start_angle_velo_spread: float = 0.05,
        force_mag: float = 100.0,  # N
        tau: float = 0.02,  # s, seconds between state updates
        integrator: IntegratorOptions = IntegratorOptions.RK45,  # integration method
        integration_resolution: int = 100,  # number of steps to subdivide tau into
        max_steps: int = 2500,
        goal_params: Optional[Mapping[str, Any]] = None,
    ):
        self.name = name

        self.grav_acc = grav_acc

        self.mass_cart = mass_cart
        self.mass_pole = mass_pole

        self.friction_cart = friction_cart
        self.friction_pole = friction_pole

        self.length = length

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

        self.max_steps = max_steps

        self.info: Mapping[str, Any] = {}

        goal_params = {} if goal_params is None else goal_params
        goal_params = self._DEFAULT_GOAL_PARAMS | goal_params

        # Calculate size of spaces.
        # Factors of 2 are to ensure that even failing observations are still within
        # the observation space.
        low = np.array(
            [
                goal_params["failure_position"][0] * 2,  # Position
                -_FLOAT_MAX,  # Velocity can be any float
                goal_params["failure_angle"][0] * 2,  # Angle
                -_FLOAT_MAX,  # Angular velocity
            ],
            dtype=FLOAT_TYPE,
        )
        high = np.array(
            [
                goal_params["failure_position"][1] * 2,  # Position
                _FLOAT_MAX,  # Velocity can be any float
                goal_params["failure_angle"][1] * 2,  # Angle
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

        goal_params = {} if goal_params is None else goal_params
        self.initialise_goal(**self._DEFAULT_GOAL_PARAMS | goal_params)

        self.reset()

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reward(self, state: State) -> float:
        """
        This function takes in a state and returns the appropriate reward.
        """
        raise NotImplementedError("Override this.")

    def check_state(self, state: State) -> StateChecks:
        """
        This function takes in a state and returns True if the state is not failed.
        """
        checks = self._check_state(state)
        checks[FailureDescriptors.MAX_STEPS_REACHED] = self.steps >= self.max_steps

        return checks


    def _check_state(self, state: State) -> StateChecks:
        raise NotImplementedError("Override this.")


    def observe(self) -> State:
        return self.state

    def setup(self) -> None:
        """
        Called once when first initialised.

        Not called when agent is reset!
        """
        raise NotImplementedError("Override this.")

    def reset(self) -> State:
        self.steps_beyond_done: int = 0
        self.steps: int = 0

        self.reset_goal()
        return self._reset()

    def _reset(self) -> State:
        raise NotImplementedError("Override this.")

    def initialise_goal(self, goal_params: Mapping[str, Any]) -> None:
        """
        Called by the agent after the main classes __init__ function
        to allow mixins to initialise.

        goal_params are passed through.
        """

    def reset_goal(self) -> None:
        """
        Called by main class to tell goal mixin to reset.
        """

    def pre_step(self, action: Action) -> None:
        """
        Called before the step.

        Allows mixins to do stuff before steps.
        """

    def step(self, action: Action) -> StepInfo:
        self.pre_step(action)
        step_info = self._step(action)
        self.post_step(action)

        self.steps += 1

        return step_info

    def _step(self, action: Action) -> StepInfo:
        raise NotImplementedError("Override this.")

    def post_step(self, action: Action) -> None:
        """
        Called after the step.

        Allows mixins to do stuff after steps.
        """


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

    def _reset(self) -> State:
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

        self.derivatives_wrapper.reset()

        return self.state

    def _step(self, action: Action) -> StepInfo:
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

        checks = self.check_state(self.state)
        done = any(checks.values())

        if not done:
            reward = self.reward(self.state)

        elif not self.steps_beyond_done:
            # First call after being done
            reward = self.reward(self.state)

            self.steps_beyond_done += 1

            failure_modes = [k.value for (k, v) in checks.items() if v]
            logger.info(f"Failure modes: {failure_modes}")

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
        return self.mass_pole * self.length


class ExperimentalCartpoleAgent(CartpoleAgent):
    ...


class CommonGoalParams(TypedDict, total=False):
    failure_position: tuple[float, float]  # m
    failure_position_velo: tuple[float, float]  # m/s
    failure_angle: tuple[float, float]  # rad
    failure_angle_velo: tuple[float, float]  # rad/s

    # Swingup
    failure_time_above_threshold: float  # s
    punishment_positional_failure: float


class AgentGoalMixinBase(ABC):
    """
    Mixin that defines the goals and limits of the agent.

    This should be enough to significantly change the behaviour of the system
    without having to reimplement the mechanical logic.
    """

    @property
    @abstractmethod
    def _DEFAULT_GOAL_PARAMS(self) -> CommonGoalParams:
        ...

    def initialise_goal(self, **kwargs: Any) -> None:
        ...

    def reset_goal(self) -> None:
        ...

    @abstractmethod
    def reward(self, state: State) -> float:
        ...

    @abstractmethod
    def _check_state(self, state: State) -> StateChecks:
        ...

    def pre_step(self, action: Action) -> None:
        ...

    def post_step(self, action: Action) -> None:
        ...


class AgentTimeGoalMixin(AgentGoalMixinBase):
    """
    This agent is fails when the cartpole leaves the allowed position region
    or the pole angle leaves the allowed angular region.
    """

    _DEFAULT_GOAL_PARAMS: Union[CommonGoalParams, dict[str, Any]] = {
        "failure_position": (-2.4, 2.4),  # m
        "failure_position_velo": (-np.inf, np.inf),  # m/s
        "failure_angle": (
            -_DEFAULT_FAILURE_ANGLE,
            _DEFAULT_FAILURE_ANGLE,
        ),  # rad
        "failure_angle_velo": (-np.inf, np.inf),  # rad/s
    }


    def initialise_goal(
        self,
        failure_position: tuple[float, float],  # m
        failure_position_velo: tuple[float, float],  # m/s
        failure_angle: tuple[float, float],  # rad
        failure_angle_velo: tuple[float, float],  # rad/s
        **kwargs: Any,
    ) -> None:

        self.failure_position = failure_position
        self.failure_position_velo = failure_position_velo
        self.failure_angle = failure_angle
        self.failure_angle_velo = failure_angle_velo

    # TODO: Abstract failure parameters
    def reward(self, state: State) -> float:
        return 1.0

    def _check_state(self, state: State) -> StateChecks:
        x = state[0]
        theta = state[2]

        checks = {
            FailureDescriptors.POSITION_LEFT: x < self.failure_position[0],
            FailureDescriptors.POSITION_RIGHT: x > self.failure_position[1],
            FailureDescriptors.ANGLE_RIGHT: theta < self.failure_angle[0],
            FailureDescriptors.ANGLE_LEFT: theta > self.failure_angle[1],
        }

        return checks


class AgentSwingupGoalMixin(AgentGoalMixinBase):
    """
    This agent is rewarded based on how upright the pole is.
    It fails if the pole has been above the horizontal for more than 10 seconds
    and then falls below the horizon (i.e. it has lost balance)."""

    _DEFAULT_GOAL_PARAMS: Union[CommonGoalParams, dict[str, Any]] = {
        "failure_position": (-10.0, 10.0),  # m
        "failure_position_velo": (-np.inf, np.inf),  # m/s
        "failure_angle": (-np.inf, np.inf),  # rad
        "failure_angle_velo": (-np.inf, np.inf),  # rad/s
        "failure_time_above_threshold": 10.0,  # s
        "punishment_positional_failure": 10000,
    }



    def initialise_goal(
        self,
        failure_position: tuple[float, float],  # m
        failure_position_velo: tuple[float, float],  # m/s
        failure_angle: tuple[float, float],  # rad
        failure_angle_velo: tuple[float, float],  # rad/s
        failure_time_above_threshold: float,  # s
        punishment_positional_failure: float,
        **kwargs: Any,
    ) -> None:

        self.failure_position = failure_position
        self.failure_position_velo = failure_position_velo
        self.failure_angle = failure_angle
        self.failure_angle_velo = failure_angle_velo
        self.failure_time_above_threshold = failure_time_above_threshold

        self.punishment_positional_failure = punishment_positional_failure

        self.reset_goal()

    def reset_goal(self) -> None:
        self.time_spent_above_horizon = 0.0

    def reward(self, state: State) -> float:
        x = state[0]
        theta = state[2]

        position_failure = any(
            (
                x < self.failure_position[0],
                x > self.failure_position[1],
            )
        )

        if position_failure:
            reward = -self.punishment_positional_failure
        else:
            reward = ((1.0 + np.sin(theta + np.pi / 2.0)) * 2.0) ** 2

        return reward

    def post_step(self, action: Action) -> None:
        theta = self.state[2]
        if np.sin(theta + np.pi / 2.0) > 0.0:
            self.time_spent_above_horizon += self.tau

    def _check_state(self, state: State) -> StateChecks:
        x = state[0]

        checks = {
            FailureDescriptors.POSITION_LEFT: x < self.failure_position[0],
            FailureDescriptors.POSITION_RIGHT: x > self.failure_position[1],
            FailureDescriptors.IMBALANCE: self.reward(state) < 0
            and self.time_spent_above_horizon >= self.failure_time_above_threshold,
        }

        return checks


def make_agent(goal: AgentGoalMixinBase, agent: CartpoleAgent, *args, **kwargs):
    class Agent(goal, agent):
        ...

    return Agent(*args, **kwargs)
