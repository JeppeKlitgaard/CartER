import logging
from enum import Enum, unique
from typing import Any, Callable, Type

import click
from click.core import Command

from commander.ml.agent import AgentSwingupGoalMixin, AgentTimeGoalMixin
from commander.ml.agent.goal import AgentGoalMixinBase, AgentRewardPotentialGoalMixin
from commander.ml.agent.state_specification import (
    AgentPositionalKnowledgeStateSpecification,
    AgentTotalKnowledgeStateSpecification,
)

SAVE_NAME_BASE: str = "cartpoleml_simulation_"

logger = logging.getLogger(__name__)


@unique
class Algorithm(str, Enum):
    # Note: Not all of these actually work with our action space and multiple agents
    # Known working: A2C, PPO
    A2C = "A2C"
    DDPG = "DDPG"
    DQN = "DQN"
    HER = "HER"
    PPO = "PPO"
    SAC = "SAC"
    TD3 = "TD3"


ALGORITHM_POLICY_PARAMS_MAP: dict[Algorithm, dict[str, Any]] = {
    Algorithm.PPO: {
        "n_steps": 32 * 8,
        "batch_size": 64,
        "gae_lambda": 0.8,
        "gamma": 0.98,
        "n_epochs": 20,
        "ent_coef": 0.0,
        "learning_rate": lambda x: 0.001 * x,
        "clip_range": lambda x: 0.2 * x,
    }
}


@unique
class ConfigurationGoal(str, Enum):
    BALANCE = "BALANCE"
    SWINGUP = "SWINGUP"
    BOUNCE = "BOUNCE"


CONFIGURATION_GOAL_MAP: dict[str, Type[AgentGoalMixinBase]] = {
    "BALANCE": AgentTimeGoalMixin,
    "SWINGUP": AgentSwingupGoalMixin,
    "BOUNCE": AgentRewardPotentialGoalMixin,
}


@unique
class ConfigurationStateSpec(str, Enum):
    TOTAL_KNOWLEDGE = "TOTAL_KNOWLEDGE"
    POSITIONAL_KNOWLEDGE = "POSITIONAL_KNOWLEDGE"


CONFIGURATION_STATE_SPEC_MAP = {
    "TOTAL_KNOWLEDGE": AgentTotalKnowledgeStateSpecification,
    "POSITIONAL_KNOWLEDGE": AgentPositionalKnowledgeStateSpecification,
}


def simexp_common_decorator(func: Callable[..., None]) -> Command:
    func = click.option("--profile/--no-profile", default=False)(func)
    func = click.option("-p", "--port", type=str, default="AUTODETECT")(func)
    func = click.option("--train/--no-train", default=True)(func)
    func = click.option("--load/--no-load", default=True)(func)
    func = click.option("--render/--no-render", default=True)(func)
    func = click.option("--render-with-best/--no-render-with-best", default=True)(func)
    func = click.option("--tensorboard/--no-tensorboard", default=True)(func)
    func = click.option("--record/--no-record", default=True)(func)
    func = click.option("-t", "--total-timesteps", type=int, default=100000)(func)
    func = click.option(
        "-c",
        "--carts",
        type=int,
        default=1,
    )(func)
    func = click.option(
        "-g",
        "--goal",
        type=click.Choice([_.value for _ in ConfigurationGoal], case_sensitive=False),
        default=ConfigurationGoal.BOUNCE,
    )(func)
    func = click.option(
        "-s",
        "--state-spec",
        type=click.Choice([_.value for _ in ConfigurationStateSpec], case_sensitive=False),
        default=ConfigurationStateSpec.POSITIONAL_KNOWLEDGE,
    )(func)
    func = click.option(
        "-a",
        "--algorithm",
        type=click.Choice([_.value for _ in Algorithm], case_sensitive=False),
        default=Algorithm.PPO,
    )(func)
    func = click.option("-n", "--num-frame-stacking", type=int, default=-1)(func)

    func = click.pass_context(func)
    func = click.command()(func)

    return func
