from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Mapping
from math import radians
from time import sleep, time
from typing import TYPE_CHECKING, Any, Deque, Optional, Type, TypeVar, cast

import numpy as np

from gym import spaces
from gym.utils import seeding

from scipy.integrate import solve_ivp

from commander.constants import FLOAT_TYPE
from commander.experiment import ExperimentState
from commander.integration import DerivativesWrapper, IntegratorOptions
from commander.ml.agent.constants import ExternalStateIdx, ExternalStateMap, InternalStateIdx
from commander.ml.agent.type_aliases import GoalParams
from commander.ml.constants import Action, FailureDescriptors
from commander.ml.display import rendering
from commander.network import NetworkManager
from commander.network.constants import DEFAULT_BAUDRATE, DEFAULT_PORT, CartID, SetOperation
from commander.network.protocol import CartSpecificPacket, ObservationPacket, SetVelocityPacket
from commander.type_aliases import ExternalState, InternalState, StateChecks, StepInfo
from commander.utils import FrequencyTicker

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from commander.ml.environment import CartpoleEnv, ExperimentalCartpoleEnv


class CartpoleAgent(ABC):
    """
    Base class for all Cartpole Agents.
    """

    failure_position: tuple[float, float]  # m
    failure_position_velo: tuple[float, float]  # m/s
    failure_angle: tuple[float, float]  # rad
    failure_angle_velo: tuple[float, float]  # rad/s

    @property
    @abstractmethod
    def _DEFAULT_GOAL_PARAMS(self) -> GoalParams:
        ...

    observation_space: spaces.Space

    def __init__(
        self: CartpoleAgentT,
        name: str = "Cartpole_1",
        pole_length: float = 1.0,
        max_steps: int = 2500,
        goal_params: Optional[GoalParams] = None,
    ):
        self.name = name
        self.pole_length = pole_length
        self.max_steps = max_steps

        self.env: Optional[CartpoleEnv[CartpoleAgentT]] = None

        self.info: Mapping[str, Any] = {}

        goal_params = {} if goal_params is None else goal_params
        goal_params = self._DEFAULT_GOAL_PARAMS | goal_params
        self.goal_params = goal_params

        # Can only apply two actions, back or forth
        self.action_space = spaces.Discrete(2)

        self.np_random: np.random.RandomState
        self.seed()

        self.viewer: Optional[rendering.Viewer] = None

        # This is private for a reason
        self._state: Optional[InternalState] = None

        self.setup()

        self.update_goal(self.goal_params)
        self.initialise_state_spec()

        self.initialise()

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def set_environment(self: CartpoleAgentT, env: CartpoleEnv[CartpoleAgentT]) -> None:
        self.env = env

    @abstractmethod
    def reward(self, state: ExternalState) -> float:
        """
        This function takes in a state and returns the appropriate reward.
        """
        ...

    @abstractmethod
    def initialise_state_spec(self) -> None:
        """
        Initialises the state specfication.

        This method should set `observation_space` and is called after
        the initialisation of the AgentGoal.
        """
        ...

    @property
    @abstractmethod
    def external_state_idx(self) -> Type[ExternalStateIdx]:
        """
        Should return an IntEnum that will map a label to the appropriate
        index of the `np.array` of the `observe` method.
        """
        ...

    @property
    @abstractmethod
    def internal_state_idx(self) -> Type[InternalStateIdx]:
        """
        Should return an IntEnum that will map a label to the appropriate
        index of the `np.array` of the `_state` attribute.
        """
        ...

    @abstractmethod
    def externalise_state(self, internal_state: InternalState) -> ExternalState:
        """
        This allows us to hide (or potentially invent) knowledge for our agent
        while keeping a different state for the use of physical simulation.

        This is important for the framestacking implementation that hides
        the positional and angular velocities in order to force the agent to
        infer this from the stacked observation frames.
        """
        ...

    def check_state(self, state: ExternalState) -> StateChecks:
        """
        This function takes in a state and returns True if the state is not failed.
        """
        checks = self._check_state(state)
        checks[FailureDescriptors.MAX_STEPS_REACHED] = self.steps >= self.max_steps

        return checks

    @abstractmethod
    def _check_state(self, state: ExternalState) -> StateChecks:
        """
        This is the actual method that does the majority of state checking.

        This should be overridden rather than `check_state` in most cases.

        This method should be implemented by the AgentGoalMixin in most cases.
        """
        ...

    def observe(self) -> ExternalState:
        """
        Returns the current external state of the environment as seen by the agent.
        """
        if self._state is None:
            raise IOError("State not yet available.")
        else:
            return self.externalise_state(self._state)

    def observe_as_dict(self) -> ExternalStateMap:
        """
        Returns the current external state as a dictionary.
        """
        obs_ = self.observe()

        observation = cast(
            ExternalStateMap,
            {self.external_state_idx(x).name.lower(): obs_[x] for x in range(len(obs_))},
        )

        return observation

    @abstractmethod
    def setup(self) -> None:
        """
        Called once when first initialised.

        Not called when agent is reset!
        """
        ...

    def initialise(self) -> None:
        """
        Called when the agent is initialised.
        """
        self.reset()

    def reset(self) -> ExternalState:
        """
        Called when the agent is reset.

        This should not generally be overridden. Rather, the `_reset_` method
        is appropriate for that.

        Further, the `reset_goal` method is the appropriate method to implement
        AgentGoalMixin-specific resets.

        Returns:
            External state of new agent
        """
        self.steps_beyond_done: int = 0
        self.steps: int = 0

        self.reset_goal()
        return self._reset()

    @abstractmethod
    def _reset(self) -> ExternalState:
        """
        This should be overridden by the CartpoleAgent subclass.
        """
        ...

    def update_goal(self, goal_params: GoalParams) -> None:
        """
        Called by the agent after the main classes __init__ function
        to allow mixins to initialise.

        `goal_params` are passed through.
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
        """
        Does a step and returns the StepInfo related to the step.

        In order to easily implement additional step logic in AgentGoalMixins
        two additional methods `pre_step` and `post_step` will be called by this method.

        This should in general not be overridden.
        """
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

    def __init__(
        self,
        name: str = "Cartpole_1",
        grav_acc: float = 9.8,  # m/s^2
        mass_cart: float = 5.0,  # kg
        mass_pole: float = 0.1,  # kg
        friction_cart: float = 0.01,  # coefficient
        friction_pole: float = 0.001,  # coefficient
        pole_length: float = 1.0,  # m
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
        goal_params: Optional[GoalParams] = None,
    ) -> None:

        self.grav_acc = grav_acc

        self.mass_cart = mass_cart
        self.mass_pole = mass_pole

        self.friction_cart = friction_cart
        self.friction_pole = friction_pole

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

        super().__init__(
            name=name, pole_length=pole_length, max_steps=max_steps, goal_params=goal_params
        )

    def _make_random_symmetrical(
        self, mean: float, spread: float, minimum: float, maximum: float
    ) -> InternalState:
        new_state = self.np_random.uniform(
            low=max(mean - spread, minimum), high=min(mean + spread, maximum)
        )

        return cast(InternalState, new_state)

    def setup(self) -> None:
        self.derivatives_wrapper = DerivativesWrapper()

    def _reset(self) -> ExternalState:
        self._state = np.array(
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

        return self.observe()

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
        self._state = self._integrate(
            IntegratorOptions.RK45, (0, self.tau), self.tau / self.integration_resolution, force
        )

        info: StepInfo = {}

        return info

    def _integrate(
        self, method: IntegratorOptions, t_span: tuple[float, float], t_step: float, force: float
    ) -> InternalState:
        t = np.arange(t_span[0], t_span[1], t_step)
        sol = solve_ivp(
            fun=self.derivatives_wrapper.equation,
            t_span=t_span,
            y0=self._state,
            method=method,
            t_eval=t,
            args=(
                force,
                self.grav_acc,
                self.friction_cart,
                self.friction_pole,
                self.pole_length,
                self.mass_pole,
                self.mass_length,
                self.mass,
            ),
        )

        new_state = cast(InternalState, np.fromiter((x[-1] for x in sol.y), FLOAT_TYPE))

        return new_state

    @property
    def mass(self) -> float:
        return self.mass_cart + self.mass_pole

    @property
    def mass_length(self) -> float:
        return self.mass_pole * self.pole_length


class ExperimentalCartpoleAgent(CartpoleAgent):
    network_manager: NetworkManager
    observation_buffer_size: int = 1

    def __init__(
        self,
        name: str = "Cartpole_1",
        cart_id: CartID = CartID.ONE,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        settled_x_threshold: float = 5.0,
        settled_theta_threshold: float = radians(0.25),
        observation_maximum_interval: int = 10 * 1000,  # us
        action_minimum_interval: float = 0.003,  # s
        action_maximum_interval: float = 0.010,  # s
        max_steps: int = 2500,
        goal_params: Optional[GoalParams] = None,
    ):

        self.cart_id = cart_id

        self.port = port
        self.baudrate = baudrate

        self.settled_x_threshold = settled_x_threshold
        self.settled_theta_threshold = settled_theta_threshold

        self.action_minimum_interval = action_minimum_interval
        self.action_maximum_interval = action_maximum_interval
        self.observation_maximum_interval = observation_maximum_interval

        super().__init__(name=name, max_steps=max_steps, goal_params=goal_params)

    def setup(self) -> None:
        self.action_freq_ticker = FrequencyTicker()

    def initialise(self) -> None:
        self._pre_reset()

    def setup_by_environment(
        self, network_manager: NetworkManager, observation_buffer_size: int
    ) -> None:
        self.network_manager = network_manager
        self.observation_buffer_size = observation_buffer_size

    def _pre_reset(self) -> None:
        """
        Specific to ExperimentAgent.

        Called by environment prior to the reset that needs to return
        observations.
        """
        self.observation_buffer: Deque[ExternalState] = deque(maxlen=self.observation_buffer_size)
        self.last_observation_interval: float = 0
        self.last_observation_time: int = 0
        self.last_action_time: float = 0.0
        self.action_freq_ticker.clear()
        self._state: Optional[InternalState] = None
        self.angle_offset: float = 0

    def _reset(self) -> ExternalState:
        state = self.observe()

        self.last_observation_time = 0
        self.last_action_time = 0.0

        return state

    def set_angle_offset(self) -> None:
        state = self.observe_as_dict()
        self.angle_offset = state["theta"] - np.pi

    def absorb_packet(self, packet: CartSpecificPacket) -> None:
        if isinstance(packet, ObservationPacket):
            if packet.timestamp_micros > self.last_observation_time:
                self.env: ExperimentalCartpoleEnv = self.env
                if (
                    (observation_interval := packet.timestamp_micros - self.last_observation_time)
                    > self.observation_maximum_interval
                    and self.last_observation_time != 0
                    and self.env.environment_state["experiment_state"] != ExperimentState.ENDING
                    and self.env.environment_state["experiment_state"] != ExperimentState.RESETTING
                ):
                    logger.warn(
                        "Observation interval too long: %s > %s",
                        observation_interval,
                        self.observation_maximum_interval,
                    )

                self.last_observation_time = packet.timestamp_micros
                self.last_observation_interval = observation_interval / 1e6  # μs -> s

                x = packet.position_steps
                theta = radians(packet.angle) - self.angle_offset

                self._state = np.array(
                    (
                        x,
                        theta,
                    )
                )

                self.observation_buffer.append(self.observe())

        else:
            raise TypeError(f"Agent does not handle {type(packet)}")

    def is_settled(self) -> bool:
        """
        Returns True if the cart is considered settled."""
        xs = [state[self.external_state_idx.X] for state in self.observation_buffer]
        thetas = [state[self.external_state_idx.THETA] for state in self.observation_buffer]

        return all(
            [
                max(xs) - min(xs) <= self.settled_x_threshold,
                max(thetas) - min(thetas) <= self.settled_theta_threshold,
            ]
        )

    def get_angle_drift(self) -> float:
        # We have just been jiggled, so now is a good time to check angle drift
        logger.info("%s| Checking angle drift.", self.name)
        state = self.observe_as_dict()

        angle_drift = state["theta"] - np.pi

        logger.info("%s| Angle drift: %s rad.", self.name, angle_drift)

        return angle_drift

    def _step(self, action: Action) -> StepInfo:
        action_interval: Optional[float] = None

        if self.last_action_time != 0.0:
            if (action_interval := time() - self.last_action_time) < self.action_minimum_interval:
                logger.debug("Action frequency too fast, blocking until min interval passed")
                sleep(self.action_minimum_interval - action_interval)

            elif action_interval > self.action_maximum_interval:
                logger.warn(
                    "Action frequency too slow: %s > %s",
                    action_interval,
                    self.action_maximum_interval,
                )

        self.last_action_time = time()
        self.action_freq_ticker.tick()

        value = 50

        value *= 1 if action == Action.FORWARDS else -1

        velo_pkt = SetVelocityPacket(SetOperation.ADD, cart_id=self.cart_id, value=value)
        # pos_pkt = SetPositionPacket(SetOperation.ADD, cart_id=self.cart_id, value=value)
        # self.network_manager.send_packet(pos_pkt)
        self.network_manager.send_packet(velo_pkt)

        info: StepInfo = {
            "action_interval": action_interval,
            "action_frequency": self.action_freq_ticker.measure(),
            "observation_interval": self.last_observation_interval,
        }

        return info


CartpoleAgentT = TypeVar("CartpoleAgentT", bound=CartpoleAgent)
