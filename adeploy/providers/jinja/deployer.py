import argparse

from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors, TestError, sys
from .common.deployment import load_deployments, get_deployment_name
from .common import kubectl, kubectl_apply


class Deployer:
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Deploys k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                            help='Directory containing namespaces and variables for deployments')
        parser.add_argument('-n', '--namespace', dest='filters_namespace', nargs='*',
                            help='Only include specified namespace. Argument can be specified multiple times.')
        parser.add_argument('-r', '--release', dest='filters_release', nargs='*',
                            help='Only include specified deployment release i.e. "prod", "testing". '
                                 'Argument can be specified multiple times.')
        return parser

    def __init__(self, src_dir, args, log, **kwargs):
        self.src_dir = src_dir
        self.log = log
        self.args = args

        self.namespaces_dir = kwargs.get('namespaces_dir')
        self.templates_dir = kwargs.get('templates_dir')
        self.filters_namespace = kwargs.get('filters_namespace')
        self.filters_release = kwargs.get('filters_release')

    def run(self):

        deployment_name = get_deployment_name(self.src_dir)
        self.log.debug(f'Working on deployment "{deployment_name}" ...')

        for deployment in load_deployments(self.log, self.src_dir, self.namespaces_dir, deployment_name):

            manifest_path = Path(self.args.build_dir) \
                .joinpath(deployment.namespace) \
                .joinpath(deployment_name) \
                .joinpath(deployment.release)

            if (self.filters_namespace and deployment.namespace not in self.filters_namespace) or \
                    (self.filters_release and deployment.release not in self.filters_release):
                self.log.info(f'{colors.orange_bold("Skip")} applying manifests '
                              f'for deployment "{colors.blue(deployment)}" in "{manifest_path}".')
                continue

            self.log.info(f'Applying manifests for deployment "{colors.blue(deployment)}" in "{manifest_path}" ...')

            try:
                result = kubectl_apply(self.log, manifest_path, namespace=deployment.namespace)
                for line in result.stdout.split("\n"):
                    token = line.split(" ")
                    if len(token) > 3:
                        resource = token[0]
                        status = token[1]

                        self.log.info(f'... {colors.bold(resource)}: '
                                      f'{colors.gray(status) if status == "unchanged" else colors.green(status)}')

            except CalledProcessError as e:
                raise TestError(f'Error in manifest dir "{manifest_path}": {e.stderr}')
