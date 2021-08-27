from collections import deque
from collections.abc import Callable
from pathlib import Path
from time import time
from typing import Any, Deque, Type


def raises(
    function: Callable[..., Any], exception: Type[Exception], *args: Any, **kwargs: Any
) -> bool:
    """
    Returns True if the `function` raises `exception` when called with `*args` and `**kwargs`.

    Otherwise returns False.
    """
    try:
        function(*args, **kwargs)
    except exception:
        return True
    else:
        return False


def noop() -> None:
    """
    No operation.
    """
    pass


def get_project_root() -> Path:
    """
    Returns the project root as a Path object.
    """
    this_file = Path(__file__)
    project_root_path = (this_file / ".." / "..").resolve()

    return project_root_path


class FrequencyTicker:
    def __init__(self, window_size: int = 10000, time_func: Callable[[], float] = time) -> None:
        self.window_size = window_size
        self.time_func = time_func

        self.container: Deque[float] = deque(maxlen=self.window_size)

    def clear(self) -> None:
        self.container.clear()

    def tick(self) -> None:
        self.container.append(self.time_func())

    def measure(self) -> float:
        ticks = len(self.container)
        time_delta = self.container[-1] - self.container[0]

        try:
            frequency = ticks / time_delta
        except ZeroDivisionError:
            frequency = 0.0

        return frequency
