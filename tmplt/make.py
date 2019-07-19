import os
import json
import subprocess
import click

from jinja2 import Environment, FileSystemLoader, select_autoescape

from tmplt import cli
from tmplt.config import CONFIG_FILENAME
from tmplt.config import get_config_templates_path, get_configs


PROJECT_FILENAME = 'project.json'
PROJECT_TEMPLATE_DIRNAME = 'template'
PRE_MAKE_FILENAME = 'pre-make'
POST_MAKE_FILENAME = 'post-make'


def _get_project_path(template):
    return os.path.join(_get_template_path(template), PROJECT_FILENAME)


def _get_project_filename(template):
    return os.path.join(template, PROJECT_FILENAME)


def _get_template_path(template):
    return os.path.join(get_config_templates_path(), template)


def _get_project_template_path(template):
    return os.path.join(
        _get_template_path(template), PROJECT_TEMPLATE_DIRNAME
    )


def _get_script_path(template, script):
    return os.path.join(_get_template_path(template), script)


def _run_script(path, input=None):
    encoded_input=bytes(json.dumps(input), 'utf8') if input else None
    subprocess.run([path], shell=True, check=True, input=encoded_input)


class TemplateRender(object):
    def __init__(self, path):
        self.env = Environment(
            loader=FileSystemLoader(path),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render_file(self, path, **kwargs):
        template = self.env.get_template(path)
        return template.render(**kwargs)

    def render_string(self, content, **kwargs):
        template = self.env.from_string(content)
        return template.render(**kwargs)


class TemplateBuilder(object):
    def __init__(self, render, configs, template):
        self.render = render
        self.configs = configs
        self.template = template
        self.project_configs = self._get_project_configs()

    def _get_project_configs(self):
        project_path = _get_project_path(self.template)
        if not os.path.isfile(project_path):
            return {}
        template_filepath = _get_project_filename(self.template)
        return json.loads(
            self.render.render_file(template_filepath, configs=self.configs)
        )

    def build(self):
        self._prompt_user()
        self._run_pre_make_script()
        project_template_path = _get_project_template_path(self.template)
        for root, dirs, files in os.walk(
            project_template_path, followlinks=True
        ):
            for directory in dirs:
                self._build_directory(root, directory)
            for file in files:
                self._build_file(root, file)
        self._run_post_make_script()

    def _prompt_user(self):
        for k, v in self.project_configs.items():
            value = v
            if isinstance(v, str):
                value = click.prompt(
                    'Please choose a value for "{}"'.format(k),
                    default=v
                )
            elif isinstance(v, list):
                value = click.prompt(
                    'Please choose a value for "{}"'.format(k),
                    default=v[0] if v else None,
                    type=click.Choice(v)
                )
            self.project_configs[k] = value

    def _build_directory(self, root, directory):
        template_path = _get_project_template_path(self.template)
        reldirname = os.path.relpath(
            os.path.join(root, directory), template_path
        )
        rendered_dirname = self.render.render_string(
            reldirname, **self.project_configs
        )
        os.makedirs(rendered_dirname, exist_ok=True)

    def _build_file(self, root, file):
        absfilepath = os.path.join(root, file)
        template_filepath = os.path.relpath(
            absfilepath, get_config_templates_path()
        )
        project_template_path = _get_project_template_path(self.template)
        relfile = os.path.relpath(absfilepath, project_template_path)
        rendered_relfile = self.render.render_string(
            relfile, **self.project_configs
        )
        with open(rendered_relfile, 'w+') as f:
            content = self.render.render_file(
                template_filepath, **self.project_configs
            )
            f.write(content)

    def _run_pre_make_script(self):
        script_path = _get_script_path(self.template, PRE_MAKE_FILENAME)
        if not os.path.isfile(script_path):
            return
        _run_script(script_path, self.project_configs)

    def _run_post_make_script(self):
        script_path = _get_script_path(self.template, POST_MAKE_FILENAME)
        if not os.path.isfile(script_path):
            return
        _run_script(script_path, self.project_configs)


@cli.command()
@click.argument('templates', nargs=-1)
def make(templates):
    if not templates:
        _list_templates()
        return
    for template in templates:
        _make_template(template)


def _list_templates():
    click.echo('Templates available')
    for template in sorted(os.listdir(get_config_templates_path())):
        if not _template_exists(template):
            continue

        project_path = _get_project_path(template)
        click.echo(
            '- {} ({})'.format(os.path.basename(template), project_path)
        )


def _make_template(template):
    _throw_if_template_not_exists(template)
    click.echo('Making template {}...'.format(template))
    _build_template(template)
    click.echo('Done.')


def _throw_if_template_not_exists(template):
    if not _template_exists(template):
        raise click.BadParameter('{} does not exists'.format(template))


def _template_exists(template):
    project_path = _get_project_path(template)
    if os.path.isfile(project_path):
        return True
    if os.path.isdir(_get_project_template_path(template)):
        return True
    if os.path.isfile(_get_script_path(template, PRE_MAKE_FILENAME)):
        return True
    if os.path.isfile(_get_script_path(template, POST_MAKE_FILENAME)):
        return True
    return False


def _build_template(template):
    render = TemplateRender(get_config_templates_path())
    TemplateBuilder(render, get_configs(), template).build()
