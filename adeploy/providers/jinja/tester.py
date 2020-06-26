import argparse

from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors, TestError, sys
from .common.deployment import load_deployments, get_deployment_name
from .common import kubectl, kubectl_apply


class Tester:
    def __init__(self, src_dir, args, log, **kwargs):
        self.src_dir = src_dir
        self.log = log
        self.args = args

        self.namespaces_dir = kwargs.get('namespaces_dir')
        self.templates_dir = kwargs.get('templates_dir')

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Jinja tester for k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                            help='Directory containing namespaces and variables for deployments')

        return parser

    def run(self):

        deployment_name = get_deployment_name(self.src_dir)
        self.log.debug(f'Working on deployment "{deployment_name}" ...')

        for deployment in load_deployments(self.log, self.src_dir, self.namespaces_dir, deployment_name):

            manifest_path = Path(self.args.build_dir)\
                .joinpath(deployment.namespace)\
                .joinpath(deployment_name)\
                .joinpath(deployment.variant)

            self.log.info(f'Testing manifests for deployment "{colors.blue(deployment)}" in "{manifest_path}" ...')

            try:
                kubectl_apply(self.log, manifest_path, namespace=deployment.namespace, dry_run='server')
            except CalledProcessError as e:
                raise TestError(f'Error in manifest dir "{manifest_path}": {e.stderr}')