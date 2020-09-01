from logging import Logger
from pathlib import Path

import yaml
from yaml.parser import ParserError

from adeploy.common.errors import Error
from adeploy.common.helpers import dict_update_recursive, get_defaults
from adeploy.common.jinja import env as jinja_env, dict as jinja_dict
from adeploy.common import colors


class Deployment:
    name: str
    release: str
    namespace: str
    config: dict
    hooks: dict

    def __init__(self, name: str, release: str, namespace: str):
        self.name = name
        self.release = release
        self.namespace = namespace
        self.hooks = {}

    def __repr__(self):
        return f'{self.namespace}/{self.name}-{self.release}'

    def load_config(self, config_path: Path, defaults_file: Path = None, log: Logger = None):

        if log:
            if not defaults_file:
                log.warning(f'Not using defaults, continue ...')
            else:
                log.info(f'Using defaults from "{colors.bold(defaults_file)}" ...')

        self.config = {}

        if defaults_file:

            try:

                # Compile defaults with default Jinja renderer i.e. to provide globals and filters
                defaults = get_defaults(defaults_file,
                                        deployment=self, log=log,
                                        template_values=self.get_template_values())
                if defaults is not None:
                    self.config.update(defaults)

            except ParserError as e:
                raise Error(f'Unexpected error while parsing YAML "{colors.bold(defaults_file)}": {e}')

        try:
            # Compile config with default Jinja renderer i.e. to provide globals and filters
            env = jinja_env.create([config_path.parent], deployment=self, log=log)
            self.config = dict_update_recursive(self.config, yaml.load(
                env.get_template(config_path.name).render(defaults=self.config, **self.get_template_values()),
                Loader=yaml.FullLoader))

        except ParserError as e:
            raise Error(f'Unexpected error while parsing YAML "{colors.bold(config_path)}": {e}')

        return self.config

    def get_template_values(self):
        return {
            'name': self.name.replace('.', '-'),
            'release': self.release.replace('.', '-'),
            'namespace': self.namespace,
            'deployment': jinja_dict.JinjaDict(self.config),

            # Some legacy variables
            'node_selector': self.config.get('node', {}),
            'default_versions': self.config.get('versions', {}),
        }
