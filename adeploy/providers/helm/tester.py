import argparse
from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors, TestError, kubectl_apply, parse_kubectrl_apply
from adeploy.common.deployment import load_deployments
from adeploy.providers.helm.common import helm_install, HelmOutput


class Tester:
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 tester for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--defaults', dest='defaults_file', default='defaults.yml',
                            help='YML file with default variables. Relative to the source dir.')
        parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                            help='Directory containing namespaces and variables for deployments')
        parser.add_argument('-n', '--namespace', dest='filters_namespace', nargs='*',
                            help='Only include specified namespace. Argument can be specified multiple times.')
        parser.add_argument('-r', '--release', dest='filters_release', nargs='*',
                            help='Only include specified deployment release i.e. "prod", "testing". '
                                 'Argument can be specified multiple times.')
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
        self.filters_namespace = kwargs.get('filters_namespace')
        self.filters_release = kwargs.get('filters_release')

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in load_deployments(self.log, self.src_dir, self.namespaces_dir, self.name):

            if (self.filters_namespace and deployment.namespace not in self.filters_namespace) or \
                    (self.filters_release and deployment.name not in self.filters_release):
                self.log.info(f'{colors.orange_bold("Skip")} testing Helm deployment "{colors.blue(deployment)}".')
                continue

            self.log.info(f'Testing Helm deployment "{colors.blue(deployment)}" ...')

            try:
                values_path = Path(self.args.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(f'values.yml')

                result = HelmOutput(
                    helm_install(self.log, deployment, self.chart_dir, str(values_path), dry_run=True).stdout)

                is_update = result.first_deployed != result.last_deployed
                last_update = f', last deployed {colors.bold(result.last_deployed)}' if is_update else ''
                is_success = result.status == 'pending-upgrade'

                self.log.info(f'... ' 
                              f'Chart version {colors.bold(result.chart_version)}, '
                              f'app version {colors.bold(result.app_version)}{last_update}: '
                              f'{colors.green_bold(result.description)}, '
                              f'status {colors.green_bold(result.status) if is_success else colors.red_bold(result.status)}')

                manifest_path = Path(self.args.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(f'manifest.yml')

                # Test to apply via kubectl and server-dry-run
                self.log.info(f'... Testing raw manifests from "{colors.bold(manifest_path)}" (may fail) ...')
                try:
                    result = kubectl_apply(self.log, manifest_path, namespace=deployment.namespace, dry_run='server')
                    parse_kubectrl_apply(self.log, result.stdout, prefix=2*'...')
                except CalledProcessError as e:
                    self.log.warning(colors.orange(f' ... Error when dry-running kubectl apply using raw manifests: {e.stderr}'))
                    self.log.warning(f'Helm install might work anyways, so ignore and continue.')
                    pass

            except CalledProcessError as e:
                raise TestError(f'Error in Helm deployment "{colors.blue(deployment)}": {e.stderr}')
