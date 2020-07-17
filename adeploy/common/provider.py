import glob
import os
from abc import ABC, abstractmethod
from argparse import Namespace
from logging import Logger
from pathlib import Path

from adeploy.common import colors
from adeploy.common.deployment import Deployment


class Provider(ABC):
    name: str = None
    src_dir: Path = None
    build_dir: Path = None
    defaults_file: Path = None
    namespaces_dir: Path = None
    log: Logger = None
    args: Namespace = None

    extensions: list = ['yml', 'yaml']

    def __init__(self, name: str, src_dir: str or Path, build_dir: str or Path, namespaces_dir: str or Path,
                 args: Namespace, log: Logger, defaults_path: str or Path = None, **kwargs):

        self.name = name
        self.src_dir = Path(src_dir)
        self.build_dir = Path(build_dir)
        self.namespaces_dir = Provider.get_absolute(self.src_dir, namespaces_dir)
        self.log = log
        self.args = args
        self.defaults_path = Provider.get_absolute(self.src_dir, defaults_path)
        self.parse_args(kwargs)

    @abstractmethod
    def parse_args(self, args: dict):
        pass

    @staticmethod
    def get_absolute(base_dir: Path, path: str) -> Path:
        return Path(path if os.path.isabs(path) else base_dir.joinpath(path))

    def get_defaults_file(self) -> Path:

        if self.defaults_path.exists():

            # <defaults_path>
            if self.defaults_path.is_file():
                return self.defaults_path

        defaults_path = self.defaults_path if self.defaults_path.is_dir() else self.src_dir.joinpath('defaults')
        if defaults_path.is_dir():

            # <defaults_path>/<deployment_name>.(yml|yaml)
            for defaults_file in [defaults_path.joinpath(self.name).with_suffix(f'.{ext}') for ext in self.extensions]:
                if defaults_file.is_file():
                    return defaults_file

        # Try yaml and yml as suffix
        for defaults_file in [self.defaults_path.with_suffix(f'.{ext}') for ext in self.extensions]:
            if defaults_file.is_file():
                return defaults_file

        self.log.warning(f'Could not find a default file from path "{colors.bold(self.defaults_path)}", continue ...')

    def load_deployments(self):

        filters_namespace = self.args.filters_namespace
        filter_release = self.args.filters_release

        self.log.debug(
            f'Scanning for deployment variables in "{self.namespaces_dir}/*/*.({"|".join(self.extensions)})" ...')

        # Structure 1: namespaces / <namespace_name> / <deployment_release>.yml
        # Structure 2: namespaces / <namespace_name> / <deployment_name> / <deployment_release>.yml

        deployments = []

        for ns in [d for d in os.listdir(str(self.namespaces_dir)) if self.namespaces_dir.joinpath(d).is_dir()]:

            # Structure 2
            deployment_dir = self.namespaces_dir.joinpath(ns).joinpath(self.name)
            if not deployment_dir.is_dir():
                # Structure 1
                deployment_dir = self.namespaces_dir.joinpath(ns)

            for ext in self.extensions:
                for deployment_release_config in [Path(p) for p in glob.glob(f'{deployment_dir}/*.{ext}')]:
                    deployment_release = deployment_release_config.stem
                    deployment = Deployment(self.name, deployment_release, ns)

                    if (filters_namespace and deployment.namespace not in filters_namespace) or \
                            (filter_release and deployment.name not in filter_release):
                        self.log.info(f'... Deployment "{colors.blue(deployment)}" skipped by user filter.')
                        continue

                    self.log.debug(f'Found deployment "{colors.blue(deployment)}", namespace "{colors.bold(ns)}" ...')

                    deployment.load_config(deployment_release_config, self.get_defaults_file(), self.log)
                    self.log.debug(f'Using config from "{colors.bold(deployment_release_config)}" ...')

                    deployments.append(deployment)

        return deployments
