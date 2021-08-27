from collections.abc import Callable
from pathlib import Path
from typing import Any, Type


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
