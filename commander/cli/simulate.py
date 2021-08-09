from commander.ml.agent.state_specification import AgentTotalKnowledgeStateSpecification
import logging
from enum import Enum
from pathlib import Path

import numpy as np

import click
import matplotlib.pyplot as plt
import stable_baselines3
from matplotlib import animation
from matplotlib.animation import FFMpegWriter
from stable_baselines3.common.callbacks import EvalCallback

from commander.ml.configurations import DeepPILCOConfiguration

from commander.ml.agent import (
    AgentPositionalKnowledgeStateSpecification,
    AgentSwingupGoalMixin,
    AgentTimeGoalMixin,
    SimulatedCartpoleAgent,
    make_agent,
)
from commander.ml.environment import make_env, make_sb3_env
from commander.ml.tensorboard import (
    FailureModeCallback,
    SimulatedTimeCallback,
    VideoRecorderCallback,
)

SAVE_NAME_BASE: str = "cartpoleml_simulation_"

logger = logging.getLogger(__name__)


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


class ConfigurationGoal(str, Enum):
    BALANCE = "BALANCE"
    SWINGUP = "SWINGUP"


CONFIGURATION_GOAL_MAP = {
    "BALANCE": AgentTimeGoalMixin,
    "SWINGUP": AgentSwingupGoalMixin,
}


class ConfigurationStateSpec(str, Enum):
    TOTAL_KNOWLEDGE = "TOTAL_KNOWLEDGE"
    POSITIONAL_KNOWLEDGE = "POSITIONAL_KNOWLEDGE"


CONFIGURATION_STATE_SPEC_MAP = {
    "TOTAL_KNOWLEDGE": AgentTotalKnowledgeStateSpecification,
    "POSITIONAL_KNOWLEDGE": AgentPositionalKnowledgeStateSpecification,
}


@click.command()
@click.pass_context
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
    default=ConfigurationGoal.BALANCE,
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
def simulate(
    ctx: click.Context,
    train: bool,
    load: bool,
    render: bool,
    render_with_best: bool,
    tensorboard: bool,
    record: bool,
    total_timesteps: int,
    carts: str,
    goal: str,
    state_spec: str,
    algorithm: str,
    num_frame_stacking: int,
) -> None:

    if num_frame_stacking == -1:
        num_frame_stacking = 1 if state_spec == ConfigurationStateSpec.TOTAL_KNOWLEDGE else 4

    _experiment_name_partials = [
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

    agent_params = DeepPILCOConfiguration["agent"].copy()
    agent_params["agent"] = SimulatedCartpoleAgent
    agent_params["goal"] = CONFIGURATION_GOAL_MAP[goal]
    agent_params["state_spec"] = CONFIGURATION_STATE_SPEC_MAP[state_spec]

    agents = []
    for i in range(carts):
        params = agent_params.copy()
        params["name"] = f"Cartpole_{i+1}"

        agents.append(make_agent(**params))

    env_params = {"agents": agents, "world_size": (-5, 5), "num_frame_stacking": num_frame_stacking}

    # Algorithm-dependent hyperparameters
    policy_params = {}
    if algorithm == Algorithm.PPO:
        policy_params["n_steps"] = 32 * 8
        policy_params["batch_size"] = 64
        policy_params["gae_lambda"] = 0.8
        policy_params["gamma"] = 0.98
        policy_params["n_epochs"] = 20
        policy_params["ent_coef"] = 0.0
        policy_params["learning_rate"] = lambda x: 0.001 * x
        policy_params["clip_range"] = lambda x: 0.2 * x

    # Callbacks
    eval_env = make_sb3_env(**env_params)
    eval_callback = EvalCallback(
        eval_env, best_model_save_path=str(best_model_path), eval_freq=int(total_timesteps / 25)
    )
    simulated_time_callback = SimulatedTimeCallback()
    failure_mode_callback = FailureModeCallback()

    callbacks = [eval_callback, simulated_time_callback, failure_mode_callback]

    algorithm_obj = getattr(stable_baselines3, algorithm)

    env = make_sb3_env(**env_params)
    logger.info(
        f"Observation spaces: env={env.observation_space.shape}, "
        f"agent={env.unwrapped.par_env.unwrapped._agents[0].observation_space.shape}"
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
        except KeyboardInterrupt:
            print("Stopping learning and saving model")

        model.save(model_path)

    if render:
        env = make_env(**env_params)
        env.reset()

        if render_with_best:
            render_model_path = best_model_path / "best_model"
        else:
            render_model_path = model_path

        model = algorithm_obj.load(render_model_path)

        if record:
            fig = plt.figure()
            images = []

        obs = env.reset()
        for agent in env.agent_iter():
            obs, reward, done, info = env.last()

            action, state = model.predict(obs) if not done else (None, None)

            env.step(action)
            if record:
                image = plt.imshow(env.render(mode="rgb_array"), animated=True)
                plt.axis("off")
                plt.title("CartpoleML Simulation")

                images.append([image])

            else:
                env.render()

            if done:
                logger.info(f"Reward: {reward}")
                env.close()
                obs = env.reset()

                if record:
                    print("Saving animation...")
                    ani = animation.ArtistAnimation(
                        fig,
                        images,
                        interval=env.unwrapped.timestep * 1000,
                        blit=True,
                        repeat_delay=1000,
                    )

                    writer = FFMpegWriter(fps=30)

                    ani.save(f"{animation_path}", dpi=200, writer=writer)
                    print(f"Animation saved as {animation_path}")

                break
