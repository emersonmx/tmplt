import click

from tmplt import config, make


@click.group()
def cli():
    pass


cli.add_command(config.config)
cli.add_command(make.make)

config.setup()
