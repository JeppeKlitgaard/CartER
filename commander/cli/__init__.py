from pathlib import Path

import click

from commander.cli.experiment import experiment
from commander.cli.simulate import simulate
from commander.cli.tensorboard import tensorboard
from commander.log import setup_logging


@click.group()
@click.pass_context
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path, writable=True, readable=True),
    default=Path("./output_data"),
)
def cli(ctx: click.Context, output_dir: Path) -> None:
    ctx.ensure_object(dict)

    ctx.obj["output_dir"] = output_dir


@click.command()
def ping() -> None:
    click.echo("Hello world.")


cli.add_command(ping)
cli.add_command(simulate)
cli.add_command(tensorboard)
cli.add_command(experiment)


def run() -> None:
    setup_logging()
    cli(obj={})


if __name__ == "__main__":
    run()
