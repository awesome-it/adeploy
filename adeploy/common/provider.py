import glob
import os
from abc import ABC, abstractmethod
from argparse import Namespace
from logging import Logger
from pathlib import Path

from adeploy.common import Deployment, colors, load_defaults


class Provider(ABC):
    name: str = None
    src_dir: str = None
    build_dir: str = None
    defaults_file: str = None
    namespaces_dir: str = None
    log: Logger = None
    args: Namespace = None

    def __init__(self, name: str, src_dir: str, build_dir: str, namespaces_dir: str, args: Namespace,
                 log: Logger, defaults_file: str = None, **kwargs):

        self.name = name
        self.src_dir = src_dir
        self.build_dir = build_dir
        self.namespaces_dir = namespaces_dir if os.path.isabs(namespaces_dir) else f'{self.src_dir}/{namespaces_dir}'
        self.defaults_file = defaults_file
        self.log = log
        self.args = args

        self.parse_args(kwargs)

    @abstractmethod
    def parse_args(self, args: dict):
        pass

    def load_deployments(self, extensions: list = None):

        defaults = load_defaults(
            log=self.log,
            src_dir=self.src_dir,
            defaults_file=self.defaults_file
        )

        if extensions is None:
            extensions = ['yaml', 'yml']

        filters_namespace = self.args.filters_namespace
        filter_release = self.args.filters_release

        self.log.debug(f'Scanning for deployment variables in "{self.namespaces_dir}/*/*.({"|".join(extensions)})" ...')

        # Structure 1: namespaces / <namespace_name> / <deployment_release>.yml
        # Structure 2: namespaces / <namespace_name> / <deployment_name> / <deployment_release>.yml

        deployments = []

        for ns in [d for d in os.listdir(self.namespaces_dir) if os.path.isdir(os.path.join(self.namespaces_dir, d))]:

            # Structure 2
            deployment_dir = os.path.join(self.namespaces_dir, ns, self.name)
            if not os.path.isdir(deployment_dir):
                # Structure 1
                deployment_dir = os.path.join(self.namespaces_dir, ns)

            for ext in extensions:
                for deployment_release_config in glob.glob(f'{deployment_dir}/*.{ext}'):
                    deployment_release = Path(deployment_release_config).stem

                    deployment = Deployment(self.name, deployment_release, ns)
                    deployment.load_config(deployment_release_config, defaults=defaults)

                    if (filters_namespace and deployment.namespace not in filters_namespace) or \
                            (filter_release and deployment.name not in filter_release):
                        self.log.info(f'... Deployment "{colors.blue(deployment)}" skipped by user filter.')
                        continue

                    self.log.debug(f'... '
                                   f'found deployment "{colors.bold(self.name)}", '
                                   f'release "{colors.bold(deployment_release)}", '
                                   f'namespace "{colors.bold(ns)}" '
                                   f'in "{deployment_release_config}" ')

                    deployments.append(deployment)

        return deployments
