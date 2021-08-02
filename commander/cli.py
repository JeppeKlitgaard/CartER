import click


@click.group()
def cli() -> None:
    ...


@click.command()
def ping() -> None:
    click.echo("Hello world.")


cli.add_command(ping)


def run() -> None:
    cli()


if __name__ == "__main__":
    run()
