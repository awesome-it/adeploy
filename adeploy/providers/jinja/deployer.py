import argparse
import glob
import os.path

from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors
from adeploy.common.kubectl import kubectl_apply, parse_kubectrl_apply
from adeploy.common.errors import DeployError
from adeploy.common.provider import Provider


class Deployer(Provider):

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Deploys k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)
        return parser

    def parse_args(self, args: dict):
        return

    def deploy_manifest(self, manifest_path, prefix=''):
        try:
            result = kubectl_apply(self.log, manifest_path)
            parse_kubectrl_apply(self.log, result.stdout, prefix=prefix)

        except CalledProcessError as e:
            raise DeployError(f'Error in manifest dir "{manifest_path}": {e.stderr}')

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in self.load_deployments():

            if not self.verify_current_cluster_is_last_cluster(deployment):
                continue

            self.log.info(f'Applying manifests for deployment "{colors.blue(deployment)}" in "{deployment.manifests_dir}" ...')

            if not deployment.manifests_dir.exists():
                self.log.info(f'... skip deployment without manifests')
                continue

            files = []
            for ext in ['yaml', 'yml']:
                files.extend(glob.glob(f'{deployment.manifests_dir}/**/*.{ext}', recursive=True))

            for manifest_path in files:
                self.deploy_manifest(manifest_path)

            self.save_current_cluster_as_last_cluster(deployment)
