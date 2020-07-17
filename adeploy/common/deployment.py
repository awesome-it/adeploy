from logging import Logger
from pathlib import Path

import yaml
from yaml.parser import ParserError

from adeploy.common.errors import Error
from adeploy.common.helpers import dict_update_recursive
from adeploy.common.jinja import env as jinja_env
from adeploy.common import colors


class Deployment:
    name: str
    release: str
    namespace: str
    config: dict

    def __init__(self, name: str, release: str, namespace: str):
        self.name = name
        self.release = release
        self.namespace = namespace

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
                env = jinja_env.create([defaults_file.parent], deployment=self, log=log)
                defaults = yaml.load(env.get_template(defaults_file.name).render(), Loader=yaml.FullLoader)
                self.config.update(defaults)

            except ParserError as e:
                raise Error(f'Unexpected error while parsing YAML "{colors.bold(defaults_file)}": {e}')

        try:
            # Compile config with default Jinja renderer i.e. to provide globals and filters
            env = jinja_env.create([config_path.parent], deployment=self, log=log)
            return dict_update_recursive(self.config,
                                         yaml.load(env.get_template(config_path.name).render(), Loader=yaml.FullLoader))

        except ParserError as e:
            raise Error(f'Unexpected error while parsing YAML "{colors.bold(config_path)}": {e}')
