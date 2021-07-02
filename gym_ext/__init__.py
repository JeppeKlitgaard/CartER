from gym.envs.registration import register


def register_cartpole(
    id: str = "CartPole-v2",
    max_episode_steps: int = 1000,
    reward_threshold: float = 950.0,
) -> None:

    entry_point = "gym_ext.cartpole:CartPoleEnv"
    register(
        id=id,
        entry_point=entry_point,
        max_episode_steps=max_episode_steps,
        reward_threshold=reward_threshold,
    )


def register_all() -> None:
    register_cartpole()
