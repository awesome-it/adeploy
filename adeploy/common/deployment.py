import copy
import os
import shutil
from logging import Logger
from pathlib import Path

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

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

    def __init__(self, name: str, release: str, namespace: str, build_dir: str):
        self.name = name
        self.release = release
        self.namespace = namespace
        self.hooks = {}

        self.build_dir = Path(build_dir)

        self.manifests_dir = Path(build_dir) \
            .joinpath(self.namespace) \
            .joinpath(self.name) \
            .joinpath(self.release)

        self.last_cluster_file = Path(build_dir) \
            .joinpath('.last_cluster') \
            .joinpath(self.namespace) \
            .joinpath(self.name) \
            .joinpath(self.release)

    def __repr__(self):
        return f'{self.namespace}/{self.name}-{self.release}'

    def skipped(self, args):
        filters_namespace = [t[0] for t in args.filters_namespace] if args.filters_namespace else None
        filters_release = [t[0] for t in args.filters_release] if args.filters_release else None

        if (filters_namespace and self.namespace not in filters_namespace) or \
                (filters_release and self.name not in filters_release and self.release not in filters_release):
            return True

        return False

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
            template = env.get_template(config_path.name).render(defaults=self.config, **self.get_template_values())
            self.config = dict_update_recursive(self.config, yaml.load(template, Loader=yaml.FullLoader))

        except ScannerError as e:
            raise Error(f'Unexpected error while scanning YAML "{colors.bold(config_path)}": {e}\n'
                        f'{colors.bold("Template")}:\n{template}')

        except ParserError as e:
            raise Error(f'Unexpected error while parsing YAML "{colors.bold(config_path)}": {e}\n'
                        f'{colors.bold("Template")}:\n{template}')

        return self.config

    def get_template_values(self):

        values = copy.deepcopy(self.config)
        values.update({
            'name': self.name.replace('.', '-'),
            'release': self.release.replace('.', '-'),
            'namespace': self.namespace,
            'deployment': jinja_dict.JinjaDict(self.config),

            # Some legacy variables
            'node_selector': self.config.get('node', {}),
            'default_versions': self.config.get('versions', {})
        })

        return jinja_dict.JinjaDict(values)

    def get_last_cluster(self):
        try:
            return self.last_cluster_file.read_text().strip()
        except FileNotFoundError:
            return None

    def set_last_cluster(self, cluster, force=False):
        if force or not self.last_cluster_file.exists():
            self.last_cluster_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.last_cluster_file, 'w') as f:
                f.write(cluster)

    def clean_build_dir(self):

        dirs_to_remove = [
            self.manifests_dir,  # Contains the rendered manifests
            self.build_dir / self.name,  # Contains secrets
        ]

        for d in dirs_to_remove:
            shutil.rmtree(d, ignore_errors=True)

        return dirs_to_remove
