import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Optional, Type, cast

import numpy as np

from gym import spaces
from gym.envs.classic_control import rendering
from gym.utils import seeding

from scipy.integrate import solve_ivp

from commander.constants import FLOAT_TYPE
from commander.integration import DerivativesWrapper, IntegratorOptions
from commander.ml.agent.constants import ExternalStateIdx, ExternalStateMap, InternalStateIdx
from commander.ml.agent.type_aliases import GoalParams
from commander.ml.constants import Action, FailureDescriptors
from commander.type_aliases import ExternalState, InternalState, StateChecks, StepInfo

logger = logging.getLogger(__name__)


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
        self,
        name: str = "Cartpole_1",
        max_steps: int = 2500,
        goal_params: Optional[GoalParams] = None,
    ):
        self.name = name

        self.max_steps = max_steps

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
        self._state: InternalState

        self.setup()

        self.initialise_goal(self.goal_params)
        self.initialise_state_spec()

        self.reset()

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

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

    def reset(self) -> ExternalState:
        """
        Called when the agent is initialised or reset.

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

    def initialise_goal(self, goal_params: GoalParams) -> None:
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
        goal_params: Optional[GoalParams] = None,
    ) -> None:

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

        super().__init__(name=name, max_steps=max_steps, goal_params=goal_params)

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

        checks = self.check_state(self.observe())
        done = any(checks.values())

        failure_modes = []
        if not done:
            reward = self.reward(self.observe())

        elif not self.steps_beyond_done:
            # First call after being done
            reward = self.reward(self.observe())

            self.steps_beyond_done += 1

            failure_modes = [k.value for (k, v) in checks.items() if v]
            logger.info(f"Failure modes: {failure_modes}")

        else:
            logger.warn(
                "We are already done. Stop calling `step()`. You may want to call `reset()`."
            )
            self.steps_beyond_done += 1
            reward = 0.0

        return self.observe(), reward, done, {"failure_modes": failure_modes}

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
                self.length,
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
        return self.mass_pole * self.length


class ExperimentalCartpoleAgent(CartpoleAgent):
    ...
