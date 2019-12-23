import os
import json
import click

_CONFIG_PATH = click.get_app_dir('tmplt')
_CONFIG_FILENAME = 'tmplt.json'
_CONFIG_FILEPATH = os.path.join(_CONFIG_PATH, _CONFIG_FILENAME)

_cached_config = None


@click.group()
def config():
    pass


@config.command()
def dump():
    if not os.path.isfile(_CONFIG_FILEPATH):
        click.echo(_dumps_json(_get_default_configs()))
        return
    click.echo(_dumps_json(_get_merged_configs()))


def setup():
    if os.path.isfile(_CONFIG_FILEPATH):
        return

    os.makedirs(_CONFIG_PATH, exist_ok=True)
    configs = _get_merged_configs()
    with open(_CONFIG_FILEPATH, 'w+') as cf:
        cf.write(_dumps_json(configs))
        click.echo('Config file created in {}'.format(_CONFIG_FILEPATH))

    template_path = get_config('templates_path')
    if not os.path.isdir(template_path):
        os.makedirs(template_path, exist_ok=True)


def _dumps_json(obj):
    return json.dumps(obj, indent=4)


def _get_merged_configs():
    global _cached_config
    if not _cached_config:
        from deepmerge import always_merger
        _cached_config = always_merger.merge(
            _get_default_configs(), get_configs()
        )
    return _cached_config


def _get_default_configs():
    return {'templates_path': os.path.join(_CONFIG_PATH, 'templates')}


def get_configs():
    config_file = os.path.join(_CONFIG_PATH, _CONFIG_FILENAME)
    if not os.path.isfile(config_file):
        return {}
    with open(config_file, 'r') as c:
        return json.load(c)


def get_config(config):
    configs = _get_merged_configs()
    return configs.get(config)
