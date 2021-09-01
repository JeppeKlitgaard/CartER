from pathlib import Path

import click

from commander.cli.simexp_base import SimulationExperimentCommand, simexp_command
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


cli.add_command(tensorboard)
cli.add_command(simexp_command(SimulationExperimentCommand.SIMULATE))
cli.add_command(simexp_command(SimulationExperimentCommand.EXPERIMENT))


def run() -> None:
    setup_logging()
    cli(obj={})


if __name__ == "__main__":
    run()
