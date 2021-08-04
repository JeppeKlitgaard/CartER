import click

from commander.cli.simulate import simulate

@click.group()
def cli() -> None:
    ...


@click.command()
def ping() -> None:
    click.echo("Hello world.")


cli.add_command(ping)
cli.add_command(simulate)


def run() -> None:
    cli()


if __name__ == "__main__":
    run()
