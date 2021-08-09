"""
This module hosts common configurations for the Cartpole problem as
described in some of the popular papers around the problem.
"""
from __future__ import annotations

from typing import Type, TypedDict, Any
import numpy as np

class ExperimentConfiguration(TypedDict):
    agent: ExperimentAgentConfiguration


class ExperimentAgentConfiguration(TypedDict):
    integration_resolution: int
    max_steps: int
    ...

DefaultConfiguration: ExperimentConfiguration = {
    "agent": {
        "integration_resolution": 2,
        "max_steps": 5000,
    }
}

# DeepPILCO
# See: http://mlg.eng.cam.ac.uk/yarin/PDFs/DeepPILCO.pdf
# See: https://github.com/zuoxingdong/DeepPILCO/blob/master/cartpole_swingup.py
DeepPILCOConfiguration = DefaultConfiguration.copy()
DeepPILCOConfiguration["agent"].update({
    "start_pos": 0.0,
    "start_pos_velo": 0.0,
    "start_angle": 0.0,
    "start_angle_velo": 0.0,
    "grav_acc": 9.82,  # m/s
    "mass_cart": 0.5,  # kg
    "mass_pole": 0.5,  # kg
    "friction_cart": 0.1,  # coeff
    "friction_pole": 0.0,  # coeff
    "length": 0.6,  # m
    "force_mag": 10.0,  # N,
    "integration_resolution": 2,
    "tau": 0.02,  # s
    "goal_params": {
        "failure_position": (-2.4, 2.4),
        "failure_position_velo": (-np.inf, np.inf),
        "failure_angle": (- 12 * 2 * np.pi / 360, 12 * 2 * np.pi / 360),
        "failure_angle_velo": (-np.inf, np.inf)
    }
})
