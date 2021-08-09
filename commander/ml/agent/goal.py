from enum import Enum
from abc import ABC, abstractmethod
from commander.type_aliases import InternalState, ExternalState, StateChecks

DEFAULT_GOAL_PARAMS = object()  # Sentinel for default goal params

from typing import TypedDict, Any, Union
from commander.ml.constants import Action, FailureDescriptors

import numpy as np


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
    def reward(self, state: ExternalState) -> float:
        ...

    @abstractmethod
    def _check_state(self, state: ExternalState) -> StateChecks:
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
    _DEFAULT_FAILURE_ANGLE = 2 * np.pi * 12 / 360

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
    def reward(self, state: ExternalState) -> float:
        return 1.0

    def _check_state(self, state: ExternalState) -> StateChecks:
        x = state[self.external_state_idx.X]
        theta = state[self.external_state_idx.THETA]

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

    def reward(self, state: ExternalState) -> float:
        x = state[self.external_state_idx.X]
        theta = state[self.external_state_idx.THETA]

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
        state = self.observe()
        theta = state[self.external_state_idx.THETA]

        if np.sin(theta + np.pi / 2.0) > 0.0:
            self.time_spent_above_horizon += self.tau

    def _check_state(self, state: ExternalState) -> StateChecks:
        x = state[self.external_state_idx.X]

        checks = {
            FailureDescriptors.POSITION_LEFT: x < self.failure_position[0],
            FailureDescriptors.POSITION_RIGHT: x > self.failure_position[1],
            FailureDescriptors.IMBALANCE: self.reward(state) < 0
            and self.time_spent_above_horizon >= self.failure_time_above_threshold,
        }

        return checks
