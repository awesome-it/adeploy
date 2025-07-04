import glob
import os
import sys
from abc import ABC, abstractmethod
from argparse import Namespace
from logging import Logger
from pathlib import Path
from typing import Optional

from packaging.version import parse as parse_version

from adeploy.common import colors
from adeploy.common.deployment import Deployment
from adeploy.common.errors import RenderError, WrongClusterError
from adeploy.common.kubectl import kubectl_get_current_api_server_url
from adeploy.common.version import get_git_version, get_package_version


class Provider(ABC):
    name: str = None
    src_dir: Path = None
    build_dir: Path = None
    defaults_path: Path = None
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
        self.current_cluster = kubectl_get_current_api_server_url(log=log)

    @abstractmethod
    def parse_args(self, args: dict):
        pass

    @staticmethod
    def get_absolute(base_dir: Path, path: str) -> Path:
        return Path(path if os.path.isabs(path) else base_dir.joinpath(path))

    def get_defaults_file(self) -> Optional[Path]:

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
        return None

    def load_deployments(self):

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
                    deployment = Deployment(self.name, deployment_release, ns, str(self.build_dir))

                    if deployment.skipped(self.args):
                        self.log.info(f'... Deployment "{colors.blue(deployment)}" skipped by user filter.')
                        continue

                    self.log.debug(f'Found deployment "{colors.blue(deployment)}", namespace "{colors.bold(ns)}" ...')

                    deployment.load_config(deployment_release_config, self.get_defaults_file(), self.log)
                    self.log.debug(f'Using config from "{colors.bold(deployment_release_config)}" ...')

                    # Check valid deployment versions
                    version = get_package_version()
                    if not version:
                        # If version cannot be determined then we're likely running from source
                        version = get_git_version()
                    deployment_version = deployment.config.get('_adeploy', {}).get('version', '0.0.0')
                    if parse_version(str(deployment_version)) > parse_version(version.split('-')[0]):
                        raise RenderError(f'Deployment requires at least '
                                          f'adeploy version {deployment_version}, '
                                          f'current version is {version}')

                    # Check valid target cluster
                    deployment_target_cluster = deployment.config.get('_adeploy', {}).get(
                        'target_cluster_apiserver_url', None)
                    if deployment_target_cluster and deployment_target_cluster != self.current_cluster:
                        raise WrongClusterError(f'Deployment target cluster is "{deployment_target_cluster}", '
                                                f'but current cluster is {self.current_cluster}')

                    deployments.append(deployment)

        if self.args.show_configs:
            print("Hello World")
            sys.exit(0)

        return deployments

    def verify_current_cluster_is_last_cluster(self, deployment) -> bool:
        last_cluster = deployment.get_last_cluster()
        if last_cluster and last_cluster != self.current_cluster:
            if not self.args.force:
                self.log.warning(f'Skip deployment "{colors.blue(deployment)}" since the target cluster has changed: ')
                self.log.warning(f'... last cluster is "{colors.red_bold(last_cluster)}"')
                self.log.warning(f'... current cluster is "{colors.red_bold(self.current_cluster)}"')
                self.log.warning(f'Force deployment to current cluster with {colors.bold("--force")}.')
                return False
            else:
                self.log.warning(f'Target cluster has changed but forcing deployment "{colors.blue(deployment)}": ')
                self.log.warning(f'... last cluster is "{colors.bold(last_cluster)}"')
                self.log.warning(f'... current cluster is "{colors.bold(self.current_cluster)}"')
        return True

    def save_current_cluster_as_last_cluster(self, deployment):
        if self.current_cluster:
            self.log.info(f'Saving current cluster as last deployed cluster')
            deployment.set_last_cluster(self.current_cluster, self.args.force)
