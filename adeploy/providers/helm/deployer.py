import argparse
from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors, DeployError
from adeploy.common.deployment import load_deployments
from adeploy.providers.helm.common import helm_install, HelmOutput


class Deployer:
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 renderer for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--defaults', dest='defaults_file', default='defaults.yml',
                            help='YML file with default variables. Relative to the source dir.')
        parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                            help='Directory containing namespaces and variables for deployments')
        parser.add_argument('--chart', dest='chart_dir', default='chart',
                            help='Directory containing the Helm chart to deploy. If no chart is available'
                                 'you can specify a repo URL using "--repo" to download the chart')
        parser.add_argument('-n', '--namespace', dest='filters_namespace', nargs='*',
                            help='Only include specified namespace. Argument can be specified multiple times.')
        parser.add_argument('-r', '--release', dest='filters_release', nargs='*',
                            help='Only include specified deployment release i.e. "prod", "testing". '
                                 'Argument can be specified multiple times.')

        return parser

    def __init__(self, name, src_dir, build_dir, args, log, **kwargs):
        self.name = name
        self.src_dir = src_dir
        self.build_dir = build_dir
        self.log = log
        self.args = args

        self.defaults_file = kwargs.get('defaults_file')
        self.namespaces_dir = kwargs.get('namespaces_dir')
        self.chart_dir = kwargs.get('chart_dir')
        self.filters_namespace = kwargs.get('filters_namespace')
        self.filters_release = kwargs.get('filters_release')

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in load_deployments(self.log, self.src_dir, self.namespaces_dir, self.name):

            if (self.filters_namespace and deployment.namespace not in self.filters_namespace) or \
                    (self.filters_release and deployment.name not in self.filters_release):
                self.log.info(f'{colors.orange_bold("Skip")} testing Helm deployment "{colors.blue(deployment)}".')
                continue

            self.log.info(f'Deploying Helm chart "{colors.blue(deployment)}" ...')

            try:
                values_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(f'values.yml')

                result = HelmOutput(
                    helm_install(self.log, deployment, self.chart_dir, str(values_path), dry_run=False).stdout)

                is_update = result.first_deployed != result.last_deployed
                last_update = f', last deployed {colors.bold(result.last_deployed)}' if is_update else ''
                is_success = result.status == 'deployed'

                self.log.info(f'... ' 
                              f'Chart version {colors.bold(result.chart_version)}, '
                              f'app version {colors.bold(result.app_version)}{last_update}: '
                              f'{colors.green_bold(result.description)}, '
                              f'status {colors.green_bold(result.status) if is_success else colors.red_bold(result.status)}')

            except CalledProcessError as e:
                raise DeployError(f'Error while deploying chart "{self.name}": {e.stderr}')

        return True
