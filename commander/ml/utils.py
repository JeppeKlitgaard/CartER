from collections.abc import Iterable
from typing import cast

from gym.vector import VectorEnv

from stable_baselines3.common.vec_env.base_vec_env import VecEnvStepReturn

from commander.type_aliases import AgentNameT, ExternalState, StepInfo, StepReturn


def restore_step(env: VectorEnv, step_return: VecEnvStepReturn) -> StepReturn:
    """
    Restores PettingZoo-like StepReturn from a Stable Baselines3
    VecEnvStepReturn.
    """
    par_env = env.unwrapped.par_env  # Unwrap to parallel_env (note: not CartpoleEnv)

    agents: Iterable[AgentNameT] = par_env.agents

    observations: dict[AgentNameT, ExternalState] = {
        agent: observation.tolist() for (agent, observation) in zip(agents, step_return[0])
    }
    rewards: dict[AgentNameT, float] = {
        agent: reward for (agent, reward) in zip(agents, step_return[1])
    }
    dones = {agent: bool(done) for (agent, done) in zip(agents, step_return[2])}
    infos: dict[AgentNameT, StepInfo] = {
        agent: info for (agent, info) in zip(agents, step_return[3])
    }

    return observations, rewards, dones, infos


def vectorise_observations(observation: dict[AgentNameT, ExternalState]) -> list[list[float]]:
    """
    Vectorises a PettingZoo-like StepReturn.
    """

    return list(cast(Iterable[list[float]], observation.values()))
