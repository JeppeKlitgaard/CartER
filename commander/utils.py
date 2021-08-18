from collections.abc import Callable
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
