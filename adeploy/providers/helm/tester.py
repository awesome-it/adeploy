import argparse
from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors, TestError, kubectl_apply, parse_kubectrl_apply
from adeploy.providers.helm.common import helm_install, HelmOutput, HelmProvider


class Tester(HelmProvider):

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 tester for k8s manifests',
                                         usage=argparse.SUPPRESS)
        return parser

    def parse_args(self, args: dict):
        return

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in self.load_deployments():

            self.log.info(f'Testing Helm deployment "{colors.blue(deployment)}" ...')

            try:
                values_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(f'values.yml')

                result = HelmOutput(
                    helm_install(self.log, deployment, self.get_chart_dir(), str(values_path), dry_run=True).stdout)

                is_update = result.first_deployed != result.last_deployed
                last_update = f', last deployed {colors.bold(result.last_deployed)}' if is_update else ''
                is_success = result.status == 'pending-upgrade' or result.status == 'pending-install'

                self.log.info(f'... '
                              f'Chart version {colors.bold(result.chart_version)}, '
                              f'app version {colors.bold(result.app_version)}{last_update}: '
                              f'{colors.green_bold(result.description)}, '
                              f'status {colors.green_bold(result.status) if is_success else colors.red_bold(result.status)}')

                manifest_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(f'manifest.yml')

                # Test to apply via kubectl and server-dry-run
                self.log.info(f'... Testing raw manifests from "{colors.bold(manifest_path)}" (may fail) ...')
                try:
                    result = kubectl_apply(self.log, manifest_path, namespace=deployment.namespace, dry_run='server')
                    parse_kubectrl_apply(self.log, result.stdout, prefix=2 * '...')
                except CalledProcessError as e:
                    self.log.warning(
                        colors.orange(f' ... Error when dry-running kubectl apply using raw manifests: {e.stderr}'))
                    self.log.warning(f'Helm install might work anyways, so ignore and continue.')
                    pass

            except CalledProcessError as e:
                raise TestError(f'Error in Helm deployment "{colors.blue(deployment)}": {e.stderr}')
