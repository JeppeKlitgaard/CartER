import logging
from typing import Any

from serial.tools import list_ports

import numpy as np

import click
import matplotlib.pyplot as plt
import stable_baselines3
from matplotlib import animation
from matplotlib.animation import FFMpegWriter

from commander.cli.simexp_base import (
    ALGORITHM_POLICY_PARAMS_MAP,
    CONFIGURATION_GOAL_MAP,
    CONFIGURATION_STATE_SPEC_MAP,
    Algorithm,
    ConfigurationStateSpec,
    simexp_common_decorator,
)
from commander.ml.agent import make_agent
from commander.ml.agent.agent import ExperimentalCartpoleAgent
from commander.ml.agent.constants import ExperimentalInternalStateIdx
from commander.ml.agent.state_specification import make_state_spec
from commander.ml.configurations import CartpoleMLExperimentConfiguration
from commander.ml.environment import ExperimentalCartpoleEnv, get_sb3_env_root_env, make_sb3_env
from commander.ml.tensorboard import GeneralCartpoleMLCallback

SAVE_NAME_BASE: str = "cartpoleml_simulation_"

logger = logging.getLogger(__name__)


@simexp_common_decorator
def experiment(
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
) -> None:

    if port == "AUTODETECT":
        port = list_ports.comports()[0].device

    if num_frame_stacking == -1:
        num_frame_stacking = 1 if state_spec == ConfigurationStateSpec.TOTAL_KNOWLEDGE else 4

    _experiment_name_partials = [
        "experiment",
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

    agent_params = CartpoleMLExperimentConfiguration["agent"].copy()

    agent_params["goal_params"] = {
        "failure_angle": (-np.inf, np.inf),
        "failure_position": (-np.inf, np.inf),
    }

    agent_params["agent"] = ExperimentalCartpoleAgent  # type: ignore [misc]
    agent_params["goal"] = CONFIGURATION_GOAL_MAP[goal]
    agent_params["state_spec"] = make_state_spec(
        CONFIGURATION_STATE_SPEC_MAP[state_spec], ExperimentalInternalStateIdx  # type: ignore [misc]
    )

    agents = []
    for i in range(carts):
        params = agent_params.copy()
        params["name"] = f"Cartpole_{i+1}"

        agents.append(make_agent(**params))

    env_params: dict[str, Any] = {
        "num_frame_stacking": num_frame_stacking,
        "port": port,
        "agents": agents,
    }

    # Algorithm-dependent hyperparameters
    policy_params = ALGORITHM_POLICY_PARAMS_MAP[Algorithm(algorithm)]

    # Callbacks
    general_cartpoleml_callback = GeneralCartpoleMLCallback()

    callbacks = [general_cartpoleml_callback]

    algorithm_obj = getattr(stable_baselines3, algorithm)
    env = make_sb3_env(ExperimentalCartpoleEnv, **env_params)
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

            logger.info("Reraising exception for debugging purposes")

            raise Exception from exc
        else:
            model.save(model_path)

    # if render:
    #     env = make_env(**env_params)
    #     env.reset()

    #     if render_with_best:
    #         render_model_path = best_model_path / "best_model"
    #     else:
    #         render_model_path = model_path

    #     model = algorithm_obj.load(render_model_path)

    #     if record:
    #         fig = plt.figure()
    #         images = []

    #     obs = env.reset()
    #     for agent in env.agent_iter():
    #         obs, reward, done, info = env.last()

    #         action, state = model.predict(obs) if not done else (None, None)

    #         env.step(action)
    #         if record:
    #             image = plt.imshow(env.render(mode="rgb_array"), animated=True)
    #             plt.axis("off")
    #             plt.title("CartpoleML Simulation")

    #             images.append([image])

    #         else:
    #             env.render()

    #         if done:
    #             logger.info(f"Reward: {reward}")
    #             env.close()
    #             obs = env.reset()

    #             if record:
    #                 print("Saving animation...")
    #                 ani = animation.ArtistAnimation(
    #                     fig,
    #                     images,
    #                     interval=env.unwrapped.timestep * 1000,
    #                     blit=True,
    #                     repeat_delay=1000,
    #                 )

    #                 writer = FFMpegWriter(fps=30)

    #                 ani.save(f"{animation_path}", dpi=200, writer=writer)
    #                 print(f"Animation saved as {animation_path}")

    #             break
