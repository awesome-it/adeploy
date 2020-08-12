import argparse
import json
import os
import tempfile
from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors
from adeploy.common.kubectl import kubectl_apply, parse_kubectrl_apply
from adeploy.common.errors import TestError
from adeploy.providers.helm.common import helm_install, HelmOutput, HelmProvider


class Tester(HelmProvider):

    skip_raw_test: bool

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 tester for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--skip-raw-test', dest='skip_raw_test', action='store_true',
                            help='Skip testing dry-run on raw manifests using kubectl.')

        return parser

    def parse_args(self, args: dict):
        self.skip_raw_test = args.get('skip_raw_test')

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

                if self.skip_raw_test:
                    self.log.info(f'Skip testing of raw manifests.')
                    continue

                manifest_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(f'manifest.yml')

                # Test to apply via kubectl and server-dry-run
                self.log.info(f'... Testing raw manifests from "{colors.bold(manifest_path)}" (may fail) ...')
                manifest_files = []
                try:
                    # Split manifest into single resources ...
                    with open(manifest_path) as fd_in:
                        for manifest in fd_in.read().split('---'):
                            if len(manifest.replace('\n', '').strip()) > 0:
                                fd_out = tempfile.NamedTemporaryFile(delete=False, mode='w')
                                fd_out.write(manifest)
                                fd_out.close()
                                manifest_files.append(fd_out.name)

                    for single_manifest_path in manifest_files:

                        # Get manifests to fetch destination namespace
                        manifests = kubectl_apply(self.log, single_manifest_path, dry_run='client', output='json')

                        try:
                            # First try including namespace
                            result = kubectl_apply(self.log, single_manifest_path, namespace=deployment.namespace, dry_run='server')
                        except CalledProcessError:
                            # Fallback without namespace i.e. defined in template and != deployment.namespace
                            result = kubectl_apply(self.log, single_manifest_path, dry_run='server')

                        parse_kubectrl_apply(self.log, result.stdout, manifests=json.loads(manifests.stdout),
                                             deployment_ns=deployment.namespace, prefix=2 * '...')

                except CalledProcessError as e:
                    self.log.warning(
                        colors.orange(f' ... Error when dry-running kubectl apply using raw manifests: {e.stderr[:255] + (e.stderr[255:] and "...")}'))
                    self.log.warning(f'Helm install might work anyways, so ignore and continue.')
                    pass

                # Clean up
                finally:
                    for path in manifest_files:
                        os.remove(path)

            except CalledProcessError as e:
                raise TestError(f'Error in Helm deployment "{colors.blue(deployment)}": {e.stderr}')
