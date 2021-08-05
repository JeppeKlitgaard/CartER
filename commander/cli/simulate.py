import logging
import os
from enum import Enum
from pathlib import Path

import click
import matplotlib.pyplot as plt
import stable_baselines3
from matplotlib import animation
from stable_baselines3.common.vec_env.vec_monitor import VecMonitor
from stable_baselines3.common.callbacks import EvalCallback

from commander.ml.agent import SimulatedCartpoleAgent
from commander.ml.environment import make_env, make_sb3_env
from commander.ml.tensorboard import SimulatedTimeCallback

from matplotlib.animation import FFMpegWriter

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


class Configuration(str, Enum):
    TWO_CARTS = "TWO_CARTS"
    ONE_CART = "ONE_CART"


@click.command()
@click.option("--train/--no-train", default=True)
@click.option("--load/--no-load", default=True)
@click.option("--render/--no-render", default=True)
@click.option("--render-with-best/--no-render-with-best", default=True)
@click.option("--tensorboard/--no-tensorboard", default=True)
@click.option("--record/--no-record", default=True)
@click.option("-t", "--total-timesteps", type=int, default=100000)
@click.option(
    "-c",
    "--configuration",
    type=click.Choice([_.value for _ in Configuration], case_sensitive=False),
    default=Configuration.TWO_CARTS,
)
@click.option(
    "-a",
    "--algorithm",
    type=click.Choice([_.value for _ in Algorithm], case_sensitive=False),
    default=Algorithm.PPO,
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path, writable=True, readable=True),
    default=Path("./output_data"),
)
def simulate(
    train: bool,
    load: bool,
    render: bool,
    render_with_best: bool,
    tensorboard: bool,
    record: bool,
    total_timesteps: int,
    configuration: str,
    algorithm: str,
    output_dir: Path,
):

    # Setup paths
    selected_output_dir = output_dir / algorithm
    selected_output_dir = selected_output_dir.resolve()
    save_name = SAVE_NAME_BASE + algorithm
    save_path = selected_output_dir / save_name

    model_path = selected_output_dir / "model.zip"
    best_model_path = selected_output_dir / "best_model"
    tensorboard_path = selected_output_dir / "tensorboard_logs"
    animation_path = selected_output_dir / "animation.mp4"

    # Setup agents
    agent_1 = SimulatedCartpoleAgent(name="Cartpole_1", start_pos=-1, integration_resolution=5)
    agent_2 = SimulatedCartpoleAgent(
        name="Cartpole_2", start_pos=1, length=0.75, integration_resolution=5
    )

    # Changes to match in 3.10
    if configuration == Configuration.TWO_CARTS:
        agents = [agent_1, agent_2]
    elif configuration == Configuration.ONE_CART:
        agents = [agent_1]

    # Algorithm-dependent hyperparameters
    policy_params = {}
    if algorithm == Algorithm.PPO:
        # policy_params["target_kl"] = 0.85
        policy_params["learning_rate"] = lambda x: 0.003 * x
        pass

    # Callbacks
    eval_env = make_sb3_env(agents=agents)
    eval_callback = EvalCallback(
        eval_env, best_model_save_path=best_model_path, eval_freq=total_timesteps / 25
    )
    simulated_time_callback = SimulatedTimeCallback()
    callbacks = [eval_callback, simulated_time_callback]

    algorithm_obj = getattr(stable_baselines3, algorithm)

    env = make_sb3_env(agents=agents)

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
        env = make_env(agents=agents)

        if render_with_best:
            render_model_path = best_model_path / "best_model.zip"
        else:
            render_model_path = model_path

        model = algorithm_obj.load(render_model_path)

        if record:
            fig = plt.figure()
            images = []

        obs = env.reset()
        for agent in env.agent_iter():
            obs, reward, done, info = env.last()

            # print(f"{obs=}, {reward=}, {done=}, {info=}")

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
                env.close()
                obs = env.reset()

                if record:
                    print("Saving animation...")
                    ani = animation.ArtistAnimation(
                        fig, images, interval=env.unwrapped.timestep * 1000, blit=True, repeat_delay=1000
                    )

                    writer = FFMpegWriter(fps=30)

                    ani.save(f"{animation_path}", dpi=200, writer=writer)
                    print(f"Animation saved as {animation_path}")

                break
