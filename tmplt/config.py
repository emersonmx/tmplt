import os
import json
import click
from deepmerge import always_merger
from tmplt import cli

CONFIG_PATH = click.get_app_dir('tmplt')
CONFIG_FILENAME = 'tmplt.json'
CONFIG_FILEPATH = os.path.join(CONFIG_PATH, CONFIG_FILENAME)


@cli.group()
def config():
    pass


@config.command()
def dump():
    if not os.path.isfile(CONFIG_FILEPATH):
        click.echo(dumps_json(get_default_configs()))
        return
    click.echo(dumps_json(get_merged_configs()))


def dumps_json(obj):
    return json.dumps(obj, indent=4)


def get_default_configs():
    return {
        'templates_path': os.path.join(CONFIG_PATH, 'templates')
    }


def get_configs():
    config_file = os.path.join(CONFIG_PATH, CONFIG_FILENAME)
    if not os.path.isfile(config_file):
        return {}
    with open(config_file, 'r') as c:
        return json.load(c)


def get_merged_configs():
    return always_merger.merge(
        get_default_configs(),
        get_configs()
    )


def get_config(config):
    configs = get_merged_configs()
    return configs.get(config)


def get_config_templates_path():
    return get_config('templates_path')
