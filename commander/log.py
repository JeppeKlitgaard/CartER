import logging

def setup_logging() -> None:
    logging.basicConfig(level=logging.DEBUG)

    logging.getLogger("numba").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    logging.debug("Sat up logging...")