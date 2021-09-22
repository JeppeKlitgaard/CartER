import logging
import webbrowser as webbrowser_m
from pathlib import Path
from time import sleep

import click
from tensorboard import program
from tensorboard.util.tb_logging import get_logger


@click.command()
@click.pass_context
@click.argument("experiment", default="latest")
@click.option("-w", "--webbrowser/--no-webbrowser", default=True)
def tensorboard(ctx: click.Context, experiment: str, webbrowser: bool) -> None:
    tb = program.TensorBoard()

    logger = get_logger()
    logger.setLevel(logging.INFO)
    logger.info(f"Experiment: {experiment}")

    output_dir = ctx.obj["output_dir"]

    if experiment == "latest":
        with open(output_dir / "latest") as f:
            latest = f.read()

        logdir = output_dir / latest
    else:
        logdir = Path(experiment)

    logdir = logdir.resolve()
    logger.info(f"Logdir: {logdir}")

    tb.configure(argv=[None, "--logdir", str(logdir)])
    tb_url = tb.launch()

    if webbrowser:
        webbrowser_m.open_new_tab(tb_url)

    while True:
        sleep(100.0)
