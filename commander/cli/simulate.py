from enum import Enum

import click
import os
import matplotlib.pyplot as plt
import stable_baselines3
from matplotlib import animation
from stable_baselines3.common.vec_env.vec_monitor import VecMonitor

from commander.ml.agent import SimulatedCartpoleAgent
from commander.ml.environment import make_env, make_sb3_env

SAVE_NAME_BASE: str = "cartpoleml_simulation_"


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
def simulate(
    train: bool,
    load: bool,
    render: bool,
    tensorboard: bool,
    record: bool,
    total_timesteps: int,
    configuration: str,
    algorithm: str,
):
    agent_1 = SimulatedCartpoleAgent(name="Cartpole_1", start_pos=-1, integration_resolution=5)
    agent_2 = SimulatedCartpoleAgent(name="Cartpole_2", start_pos=1, length=0.75, integration_resolution=5)

    if configuration == Configuration.TWO_CARTS:
        agents = [agent_1, agent_2]
    elif configuration == Configuration.ONE_CART:
        agents = [agent_1]

    save_name = SAVE_NAME_BASE + algorithm
    algorithm_obj = getattr(stable_baselines3, algorithm)

    env = make_sb3_env(agents=agents)
    env = VecMonitor(env)

    if train:
        _kwargs = {
            "policy": "MlpPolicy",
            "env": env,
            "verbose": 2,
            "tensorboard_log": save_name + "_tensorboard" if tensorboard else None
        }

        if load and os.path.exists(save_name + ".zip"):
            model = algorithm_obj.load(save_name, **_kwargs)
        else:
            model = algorithm_obj(**_kwargs)

        try:
            model.learn(total_timesteps=total_timesteps)
        except KeyboardInterrupt:
            print("Stopping learning and saving model")

        model.save(save_name)

    if render:
        env = make_env(agents=agents)
        model = algorithm_obj.load(save_name)

        if record:
            fig = plt.figure()
            images = []

        obs = env.reset()
        for agent in env.agent_iter():
            obs, reward, done, info = env.last()

            print(f"{obs=}, {reward=}, {done=}, {info=}")

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
                        fig, images, interval=20, blit=True, repeat_delay=1000
                    )
                    ani.save(f"{save_name}.avi", dpi=300)
                    print(f"Animation saved as {save_name}.avi")

                break
