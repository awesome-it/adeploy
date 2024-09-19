import argparse
from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors
from adeploy.common.errors import DeployError
from adeploy.providers.helm.common import helm_install, HelmOutput, HelmProvider, get_defaults


class Deployer(HelmProvider):
    skip_schema_validation: bool

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 renderer for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--skip-schema-validation', action='store_true',
                            help='Skip JSON schema validation of input variables. This might sometimes be required if '
                                 'you the Chart repo has a "values.schema.json" while you have specified additional '
                                 'properties i.e. "_chart: {}" in your namespace configuration. '
                                 'See "helm template --help".')
        return parser

    def parse_args(self, args: dict):
        chart_defaults = get_defaults(self.get_defaults_file(), log=self.log).get('_chart', {})
        self.name = chart_defaults.get('name', self.name)
        self.skip_schema_validation = args.get('skip_schema_validation')

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in self.load_deployments():

            self.log.info(f'Deploying Helm chart "{colors.blue(deployment)}" ...')
            if not self.verify_current_cluster_is_last_cluster(deployment):
                continue
            try:
                values_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(f'values.yml')

                result = HelmOutput(
                    helm_install(self.log, deployment, self.get_chart_dir(), str(values_path), dry_run=False,
                                 skip_schema_validation=self.skip_schema_validation).stdout)

                is_update = result.first_deployed != result.last_deployed
                last_update = f', last deployed {colors.bold(result.last_deployed)}' if is_update else ''
                is_success = result.status == 'deployed'

                self.log.info(f'... '
                              f'Chart version {colors.bold(result.chart_version)}, '
                              f'app version {colors.bold(result.app_version)}{last_update}: '
                              f'{colors.green_bold(result.description)}, '
                              f'status {colors.green_bold(result.status) if is_success else colors.red_bold(result.status)}')
                self.save_current_cluster_as_last_cluster(deployment)
            except CalledProcessError as e:
                raise DeployError(f'Error while deploying chart "{self.name}": {e.stderr}')
