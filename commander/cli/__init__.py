import click

from commander.cli.simulate import simulate
from commander.log import setup_logging


@click.group()
def cli() -> None:
    ...


@click.command()
def ping() -> None:
    click.echo("Hello world.")


cli.add_command(ping)
cli.add_command(simulate)


def run() -> None:
    setup_logging()
    cli()


if __name__ == "__main__":
    run()
