from time import sleep

import click
from tensorboard import program
import webbrowser as webbrowser_m


@click.command()
@click.pass_context
@click.argument("experiment", default="latest")
@click.option("-w", "--webbrowser/--no-webbrowser", default=True)
def tensorboard(ctx: click.Context, experiment: str, webbrowser: bool) -> None:
    tb = program.TensorBoard()

    output_dir = ctx.obj["output_dir"]

    if experiment == "latest":
        with open(output_dir / "latest") as f:
            latest = f.read()

        logdir = output_dir / latest
    else:
        logdir = output_dir / experiment

    tb.configure(argv=[None, "--logdir", str(logdir)])
    tb.launch()

    if webbrowser:
        webbrowser_m.open_new_tab("http://localhost:6006")

    while True:
        sleep(100.0)
