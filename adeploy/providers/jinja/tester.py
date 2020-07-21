import argparse
import json

from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors
from adeploy.common.kubectl import kubectl_apply, parse_kubectrl_apply
from adeploy.common.errors import TestError
from adeploy.common.provider import Provider


class Tester(Provider):
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Jinja tester for k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)
        return parser

    def parse_args(self, args: dict):
        return

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in self.load_deployments():

            manifest_path = Path(self.build_dir) \
                .joinpath(deployment.namespace) \
                .joinpath(self.name) \
                .joinpath(deployment.release)

            self.log.info(f'Testing manifests for deployment "{colors.blue(deployment)}" in "{manifest_path}" ...')

            try:
                manifests = kubectl_apply(self.log, manifest_path, dry_run='client', output='json')
                result = kubectl_apply(self.log, manifest_path, dry_run='server')
                parse_kubectrl_apply(self.log, result.stdout, manifests=json.loads(manifests.stdout),
                                     deployment=deployment)

            except CalledProcessError as e:
                raise TestError(f'Error in manifest dir "{manifest_path}": {e.stderr}')
