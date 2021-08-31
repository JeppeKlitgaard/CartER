import platform
from typing import Any, cast

if platform.system() == "Windows":
    from gym.envs.classic_control import rendering
else:
    from pyglet.canvas.xlib import NoSuchDisplayException

    # Display detection
    try:
        from gym.envs.classic_control import rendering
    except NoSuchDisplayException:
        rendering = cast(Any, None)


__all__ = ("rendering",)
