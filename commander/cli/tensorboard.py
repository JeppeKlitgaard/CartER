from tensorboard import program

import click

from time import sleep

@click.command()
@click.pass_context
@click.argument("experiment", default="latest")
def tensorboard(ctx: click.Context, experiment: str):
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

    while True:
        sleep(100.0)