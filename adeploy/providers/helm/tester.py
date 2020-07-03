import argparse

from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors, TestError, sys
from adeploy.common.deployment import load_deployments, get_deployment_name


class Tester:
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 tester for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--defaults', dest='defaults_file', default='defaults.yml',
                            help='YML file with default variables. Relative to the source dir.')
        parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                            help='Directory containing namespaces and variables for deployments')
        parser.add_argument('--chart', dest='chart_dir', default='chart',
                            help='Directory containing the Helm chart to deploy')
        return parser

    def __init__(self, name, src_dir, args, log, **kwargs):
        self.name = name
        self.src_dir = src_dir
        self.log = log
        self.args = args

        self.defaults_file = kwargs.get('defaults_file')
        self.namespaces_dir = kwargs.get('namespaces_dir')
        self.chart_dir = kwargs.get('chart_dir')

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in load_deployments(self.log, self.src_dir, self.namespaces_dir, self.name):

            manifest_path = Path(self.args.build_dir) \
                .joinpath(deployment.namespace) \
                .joinpath(self.name) \
                .joinpath(deployment.release)

            if (self.filters_namespace and deployment.namespace not in self.filters_namespace) or \
                    (self.filters_name and deployment.name not in self.filters_name):
                self.log.info(f'{colors.orange_bold("Skip")} testing manifests '
                              f'for deployment "{colors.blue(deployment)}" in "{manifest_path}".')
                continue

            self.log.info(f'Testing manifests for deployment "{colors.blue(deployment)}" in "{manifest_path}" ...')

            try:
                result = "" #kubectl_apply(self.log, manifest_path, namespace=deployment.namespace, dry_run='server')
                for line in result.stdout.split("\n"):
                    token = line.split(" ")
                    if len(token) > 3:
                        resource = token[0]
                        status = token[1]

                        self.log.info(f'... {colors.bold(resource)}: '
                                      f'{colors.gray(status) if status == "unchanged" else colors.green(status)}')

            except CalledProcessError as e:
                raise TestError(f'Error in manifest dir "{manifest_path}": {e.stderr}')
