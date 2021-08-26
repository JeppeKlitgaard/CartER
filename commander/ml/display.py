from types import ModuleType
from typing import Optional

from pyglet.canvas.xlib import NoSuchDisplayException

# Display detection
rendering: Optional[ModuleType]
try:
    from gym.envs.classic_control import rendering
except NoSuchDisplayException:
    rendering = None
