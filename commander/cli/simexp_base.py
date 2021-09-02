import logging
from enum import Enum, unique
from typing import Any, Callable, Type, Union

import numpy as np

import click
import matplotlib.pyplot as plt
import stable_baselines3
import yappi
from click.core import Command
from matplotlib import animation
from matplotlib.animation import FFMpegWriter
from serial.tools import list_ports
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback

from commander.ml.agent import (
    AgentSwingupGoalMixin,
    AgentTimeGoalMixin,
    SimulatedCartpoleAgent,
    make_agent,
)
from commander.ml.agent.agent import ExperimentalCartpoleAgent
from commander.ml.agent.constants import ExperimentalInternalStateIdx, SimulatedInternalStateIdx
from commander.ml.agent.goal import AgentGoalMixinBase, AgentRewardPotentialGoalMixin
from commander.ml.agent.state_specification import (
    AgentPositionalKnowledgeStateSpecification,
    AgentTotalKnowledgeStateSpecification,
    make_state_spec,
)
from commander.ml.configurations import (
    CartpoleMLExperimentConfiguration,
    DeepPILCOConfiguration,
    ExperimentAgentConfiguration,
    SimulatedAgentConfiguration,
)
from commander.ml.environment import (
    ExperimentalCartpoleEnv,
    SimulatedCartpoleEnv,
    get_sb3_env_root_env,
    make_sb3_env,
)
from commander.ml.tensorboard import GeneralCartpoleMLCallback
from commander.ml.utils import restore_step, vectorise_observations

SAVE_NAME_BASE: str = "cartpoleml_simulation_"

logger = logging.getLogger(__name__)


@unique
class SimulationExperimentCommand(str, Enum):
    EXPERIMENT = "experiment"
    SIMULATE = "simulate"


@unique
class Algorithm(str, Enum):
    # Note: Not all of these actually work with our action space and multiple agents
    # Known working: A2C, PPO
    A2C = "A2C"
    PPO = "PPO"


ALGORITHM_POLICY_PARAMS_MAP: dict[Algorithm, dict[str, Any]] = {
    Algorithm.PPO: {
        "n_steps": 256,
        "batch_size": 32,
        "gae_lambda": 0.95,
        "gamma": 0.98,
        "n_epochs": 5,
        "ent_coef": 0.001,
        "learning_rate": lambda x: 0.001 * x,
        "clip_range": lambda x: 0.2 * x,
    },
    Algorithm.A2C: {}
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


def simexp_command(command: SimulationExperimentCommand) -> Command:
    @click.command(name=command.value)
    @click.pass_context
    @click.option("-p", "--port", type=str, default="AUTODETECT")
    @click.option("--train/--no-train", default=True)
    @click.option("--load/--no-load", default=True)
    @click.option("--render/--no-render", default=True)
    @click.option("--render-with-best/--no-render-with-best", default=True)
    @click.option("--tensorboard/--no-tensorboard", default=True)
    @click.option("--record/--no-record", default=True)
    @click.option("-t", "--total-timesteps", type=int, default=100000)
    @click.option(
        "-c",
        "--carts",
        type=int,
        default=1,
    )
    @click.option(
        "-g",
        "--goal",
        type=click.Choice([_.value for _ in ConfigurationGoal], case_sensitive=False),
        default=ConfigurationGoal.BOUNCE,
    )
    @click.option(
        "-s",
        "--state-spec",
        type=click.Choice([_.value for _ in ConfigurationStateSpec], case_sensitive=False),
        default=ConfigurationStateSpec.POSITIONAL_KNOWLEDGE,
    )
    @click.option(
        "-a",
        "--algorithm",
        type=click.Choice([_.value for _ in Algorithm], case_sensitive=False),
        default=Algorithm.PPO,
    )
    @click.option("-n", "--num-frame-stacking", type=int, default=-1)
    @click.option("--profile/--no-profile", default=False)
    def inner(
        ctx: click.Context,
        port: str,
        train: bool,
        load: bool,
        render: bool,
        render_with_best: bool,
        tensorboard: bool,
        record: bool,
        total_timesteps: int,
        carts: int,
        goal: str,
        state_spec: str,
        algorithm: str,
        num_frame_stacking: int,
        profile: bool,
    ) -> None:

        if profile:
            yappi.start()
            yappi.set_clock_type("CPU")

        if command is SimulationExperimentCommand.SIMULATE:
            ...

        elif command is SimulationExperimentCommand.EXPERIMENT:
            if port == "AUTODETECT":
                port = list_ports.comports()[0].device
        else:
            raise NotImplementedError

        if num_frame_stacking == -1:
            num_frame_stacking = 1 if state_spec == ConfigurationStateSpec.TOTAL_KNOWLEDGE else 4

        _experiment_name_partials = [
            command,
            algorithm.upper(),
            str(carts) + "carts",
            goal.lower(),
            state_spec.lower(),
            "F" + str(num_frame_stacking),
        ]

        experiment_name = "_".join(_experiment_name_partials)

        # Setup paths
        output_dir = ctx.obj["output_dir"]
        selected_output_dir = output_dir / experiment_name
        selected_output_dir = selected_output_dir.resolve()

        model_path = selected_output_dir / "model.zip"
        best_model_path = selected_output_dir / "best_model"
        tensorboard_path = selected_output_dir / "tensorboard_logs"
        animation_path = selected_output_dir / "animation.mp4"

        output_dir.mkdir(exist_ok=True)

        # Set latest
        with open(output_dir / "latest", "w") as f:
            f.write(experiment_name)

        env_class: Union[Type[SimulatedCartpoleEnv], Type[ExperimentalCartpoleEnv]]
        agent_params: Union[ExperimentAgentConfiguration, SimulatedAgentConfiguration]
        if command is SimulationExperimentCommand.SIMULATE:
            env_class = SimulatedCartpoleEnv

            agent_params = DeepPILCOConfiguration["agent"].copy()
            agent_params["agent"] = SimulatedCartpoleAgent  # type: ignore [misc]
            agent_params["goal"] = CONFIGURATION_GOAL_MAP[goal]
            agent_params["state_spec"] = make_state_spec(
                CONFIGURATION_STATE_SPEC_MAP[state_spec],  # type: ignore [misc]
                SimulatedInternalStateIdx,
            )

            if CONFIGURATION_GOAL_MAP[goal] is AgentRewardPotentialGoalMixin:
                agent_params["start_angle"] = np.pi
                agent_params["start_pos"] = 0.5
                agent_params["goal_params"]["failure_position"] = (0, 1.0)
                agent_params["goal_params"]["failure_angle"] = (-np.inf, np.inf)
                agent_params["goal_params"]["track_length"] = 0.98

        elif command is SimulationExperimentCommand.EXPERIMENT:
            env_class = ExperimentalCartpoleEnv

            agent_params = CartpoleMLExperimentConfiguration["agent"].copy()

            agent_params["goal_params"] = {
                "failure_angle": (-np.inf, np.inf),
                "failure_position": (-np.inf, np.inf),
            }

            agent_params["agent"] = ExperimentalCartpoleAgent  # type: ignore [misc]
            agent_params["goal"] = CONFIGURATION_GOAL_MAP[goal]
            agent_params["state_spec"] = make_state_spec(
                CONFIGURATION_STATE_SPEC_MAP[state_spec],  # type: ignore [misc]
                ExperimentalInternalStateIdx,
            )
        else:
            raise NotImplementedError

        agents = []
        for i in range(carts):
            params = agent_params.copy()
            params["name"] = f"Cartpole_{i+1}"  # type: ignore[index]

            agents.append(make_agent(**params))

        env_params: dict[str, Any] = {
            "num_frame_stacking": num_frame_stacking,
            "agents": agents,
        }
        if command is SimulationExperimentCommand.SIMULATE:
            ...
        elif command is SimulationExperimentCommand.EXPERIMENT:
            env_params["port"] = port

        # Algorithm-dependent hyperparameters
        policy_params = ALGORITHM_POLICY_PARAMS_MAP[Algorithm(algorithm)]

        # Callbacks
        callbacks: list[BaseCallback] = []
        callbacks.append(GeneralCartpoleMLCallback())

        if command is SimulationExperimentCommand.SIMULATE:
            eval_env = make_sb3_env(SimulatedCartpoleEnv, **env_params)
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=str(best_model_path),
                eval_freq=int(total_timesteps / 25),
            )
            callbacks.append(eval_callback)

        algorithm_obj = getattr(stable_baselines3, algorithm)
        try:
            env = make_sb3_env(env_class, **env_params)
        except KeyboardInterrupt as exc:
            logger.info("Reraising exception for debugging purposes")
            raise Exception from exc

        logger.info(
            f"Observation spaces: env={env.observation_space.shape}, "
            f"agent={get_sb3_env_root_env(env)._agents[0].observation_space.shape}"
        )
        if train:
            _kwargs = {
                "policy": "MlpPolicy",
                "env": env,
                "verbose": 2,
                "tensorboard_log": tensorboard_path if tensorboard else None,
            }

            kwargs = _kwargs | policy_params

            if load and model_path.exists():
                logger.info(f"Loading existing model: '{model_path}'")
                model = algorithm_obj.load(model_path, **kwargs)
            else:
                model = algorithm_obj(**kwargs)

            try:
                model.learn(total_timesteps=total_timesteps, callback=callbacks)
            except KeyboardInterrupt as exc:
                logger.info("Stopping learning and saving model")
                model.save(model_path)

                if profile:
                    yappi.stop()
                    stats = yappi.get_func_stats()
                    stats.save("profiling.prof", "pstat")

                if command is SimulationExperimentCommand.EXPERIMENT:
                    logger.info("Reraising exception for debugging purposes")
                    raise Exception from exc
            else:
                model.save(model_path)

        if render:
            sim_env_params = env_params.copy()
            del sim_env_params["port"]

            env = make_sb3_env(SimulatedCartpoleEnv, **sim_env_params)
            env.reset()

            root_env = get_sb3_env_root_env(env)

            if render_with_best:
                render_model_path = best_model_path / "best_model"
            else:
                render_model_path = model_path

            model = algorithm_obj.load(render_model_path)

            if record:
                fig = plt.figure()
                images = []

            obs = env.reset()
            done = False
            total_rewards = {agent: 0.0 for agent in root_env.agents}

            while not done:
                actions, states = model.predict(obs)

                step_return = env.step(actions)
                observations, rewards, dones, infos = restore_step(env, step_return)
                obs = vectorise_observations(observations)

                for (agent, reward) in rewards.items():
                    total_rewards[agent] += reward

                done = any(dones.values())

                if record:
                    image = plt.imshow(env.render(mode="rgb_array"), animated=True)
                    plt.axis("off")
                    plt.title("CartpoleML Simulation")

                    images.append([image])

                else:
                    env.render()

                if done:
                    logger.info(f"Rewards: {total_rewards}")
                    env.close()

                    if record:
                        print("Saving animation...")
                        ani = animation.ArtistAnimation(
                            fig,
                            images,
                            interval=root_env.timestep * 1000,
                            blit=True,
                            repeat_delay=1000,
                        )

                        writer = FFMpegWriter(fps=30)

                        ani.save(f"{animation_path}", dpi=200, writer=writer)
                        print(f"Animation saved as {animation_path}")

    return inner
