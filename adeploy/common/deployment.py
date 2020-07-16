from logging import Logger
from pathlib import Path

import yaml

from adeploy.common import dict_update_recursive, colors
from adeploy.common.jinja import env as jinja_env


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

            # Compile defaults with default Jinja renderer i.e. to provide globals and filters
            env = jinja_env.create([defaults_file.parent], log)
            jinja_env.register_globals(env, self, log)
            defaults = yaml.load(env.get_template(defaults_file.name).render(), Loader=yaml.FullLoader)

            self.config.update(defaults)

        # Compile config with default Jinja renderer i.e. to provide globals and filters
        env = jinja_env.create([config_path.parent], log)
        jinja_env.register_globals(env, self, log)
        defaults = yaml.load(env.get_template(defaults_file.name).render(), Loader=yaml.FullLoader)

        return dict_update_recursive(self.config,
                                     yaml.load(env.get_template(config_path.name).render(), Loader=yaml.FullLoader))
