"""
Provides the state specification interface for use with agents.
"""

from abc import ABC, abstractmethod
from gym import spaces
from enum import IntEnum
from typing import Type, cast
from commander.type_aliases import InternalState, ExternalState
import numpy as np
from commander.constants import FLOAT_TYPE


_FLOAT_MAX = np.finfo(FLOAT_TYPE).max


class AgentStateSpecificationBase(ABC):
    """
    Mixin that defines what an idealised world state looks like
    as well as how this is observed, perhaps not ideally, by an agent.

    This mixin can be used to hide certain dimensions of observations or
    indeed introduce random noise into each observation in an OOP-friendly
    manner.
    """

    observation_space: spaces.Space

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
    def external_state_idx(self) -> Type[IntEnum]:
        """
        Should return an IntEnum that will map a label to the appropriate
        index of the `np.array` of the `observe` method.
        """
        ...

    @property
    @abstractmethod
    def internal_state_idx(self) -> Type[IntEnum]:
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


class AgentTotalKnowledgeStateSpecification(AgentStateSpecificationBase):
    """
    This mixin gives the agent full, perfect knowledge of the underlying world state.

    This means the agent will have access to:
    - Position [X]
    - Velocity [DX]
    - Angular Position [THETA]
    - Angular Velocity [DTHETA]
    """

    def initialise_state_spec(self) -> None:
        # Calculate size of spaces.
        # Factors of 2 are to ensure that even failing observations are still within
        # the observation space.
        low = np.array(
            [
                self.goal_params["failure_position"][0] * 2,  # Position
                -_FLOAT_MAX,  # Velocity can be any float
                self.goal_params["failure_angle"][0] * 2,  # Angle
                -_FLOAT_MAX,  # Angular velocity
            ],
            dtype=FLOAT_TYPE,
        )
        high = np.array(
            [
                self.goal_params["failure_position"][1] * 2,  # Position
                _FLOAT_MAX,  # Velocity can be any float
                self.goal_params["failure_angle"][1] * 2,  # Angle
                _FLOAT_MAX,  # Angular velocity
            ],
            dtype=FLOAT_TYPE,
        )

        self.observation_space = spaces.Box(low, high, dtype=FLOAT_TYPE)


    class internal_state_idx(IntEnum):
        X = 0
        DX = 1
        THETA = 2
        DTHETA = 3

    external_state_idx = internal_state_idx

    def externalise_state(self, internal_state: InternalState) -> ExternalState:
        return cast(ExternalState, internal_state)


class AgentPositionalKnowledgeStateSpecification(AgentStateSpecificationBase):
    """
    This mixin gives the agent limited knowledge of the system and indeed
    a single observation does not fully describe the system in a way
    that allows the agent to act in an unambigiuous manner.

    For this reason, this should be used with some method of frame stacking
    in order to encode the first derivatives of the positional data.
    """

    def initialise_state_spec(self) -> None:
        # Calculate size of spaces.
        # Factors of 2 are to ensure that even failing observations are still within
        # the observation space.
        low = np.array(
            [
                self.goal_params["failure_position"][0] * 2,  # Position
                self.goal_params["failure_angle"][0] * 2,  # Angle
            ],
            dtype=FLOAT_TYPE,
        )
        high = np.array(
            [
                self.goal_params["failure_position"][1] * 2,  # Position
                self.goal_params["failure_angle"][1] * 2,  # Angle
            ],
            dtype=FLOAT_TYPE,
        )

        self.observation_space = spaces.Box(low, high, dtype=FLOAT_TYPE)

    class internal_state_idx(IntEnum):
        X = 0
        DX = 1
        THETA = 2
        DTHETA = 3

    class external_state_idx(IntEnum):
        X = 0
        THETA = 1

    def externalise_state(self, _state: InternalState) -> ExternalState:
        external_state = np.array(
            [_state[self.internal_state_idx.X], _state[self.internal_state_idx.THETA]]
        )

        return cast(ExternalState, external_state)
