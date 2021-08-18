"""
This module hosts common configurations for the Cartpole problem as
described in some of the popular papers around the problem.
"""
from __future__ import annotations

from typing import Type, TypedDict

import numpy as np

from commander.ml.agent.agent import CartpoleAgent
from commander.ml.agent.goal import AgentGoalMixinBase
from commander.ml.agent.state_specification import AgentStateSpecificationBase
from commander.ml.agent.type_aliases import GoalParams


class Configuration(TypedDict, total=False):
    agent: AgentConfiguration


class AgentConfiguration(TypedDict, total=False):
    name: str
    goal_params: GoalParams

    agent: Type[CartpoleAgent]
    goal: Type[AgentGoalMixinBase]
    state_spec: Type[AgentStateSpecificationBase]


class SimulatedConfiguration(Configuration):
    agent: SimulatedAgentConfiguration  # type: ignore[misc]


class SimulatedAgentConfiguration(AgentConfiguration, total=False):
    integration_resolution: int
    max_steps: int
    start_pos: float
    start_pos_velo: float
    start_angle: float
    start_angle_velo: float
    grav_acc: float
    mass_cart: float
    mass_pole: float
    friction_cart: float
    friction_pole: float
    pole_length: float
    force_mag: float
    tau: float


DefaultSimulatedConfiguration: SimulatedConfiguration = {
    "agent": {
        "integration_resolution": 2,
        "max_steps": 5000,
    }
}

# DeepPILCO
# See: http://mlg.eng.cam.ac.uk/yarin/PDFs/DeepPILCO.pdf
# See: https://github.com/zuoxingdong/DeepPILCO/blob/master/cartpole_swingup.py
DeepPILCOConfiguration = DefaultSimulatedConfiguration.copy()
DeepPILCOConfiguration["agent"].update(
    {
        "start_pos": 0.0,
        "start_pos_velo": 0.0,
        "start_angle": 0.0,
        "start_angle_velo": 0.0,
        "grav_acc": 9.82,  # m/s
        "mass_cart": 0.5,  # kg
        "mass_pole": 0.5,  # kg
        "friction_cart": 0.1,  # coeff
        "friction_pole": 0.0,  # coeff
        "pole_length": 0.6,  # m
        "force_mag": 10.0,  # N,
        "tau": 0.02,  # s
        "goal_params": {
            "failure_position": (-2.4, 2.4),
            "failure_position_velo": (-np.inf, np.inf),
            "failure_angle": (-12 * 2 * np.pi / 360, 12 * 2 * np.pi / 360),
            "failure_angle_velo": (-np.inf, np.inf),
        },
    }
)


class ExperimentConfiguration(Configuration):
    agent: ExperimentAgentConfiguration  # type: ignore[misc]


class ExperimentAgentConfiguration(AgentConfiguration, total=False):
    port: str
    baudrate: int


DefaultExperimentConfiguration: ExperimentConfiguration = {
    "agent": {
        "port": "COM3",
        "baudrate": 74880,
    }
}

CartpoleMLExperimentConfiguration = DefaultExperimentConfiguration.copy()
