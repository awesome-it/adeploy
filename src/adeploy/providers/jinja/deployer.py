import argparse
import glob
import os.path

from pathlib import Path
from subprocess import CalledProcessError

import yaml

from adeploy.common import colors
from adeploy.common.kubectl import kubectl_apply, parse_kubectrl_apply
from adeploy.common.errors import DeployError
from adeploy.common.provider import Provider


class Deployer(Provider):

    @staticmethod
    def manifest_is_configmap(manifest_path) -> bool:
        try:
            with open(manifest_path, 'r') as f:
                deployment_data = yaml.safe_load(f.read())
                return deployment_data.get('kind', '') == 'ConfigMap'
        except yaml.YAMLError as e:
            raise DeployError(f'Error parsing manifest file "{manifest_path}": {e}')


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

            configmap_files = [file for file in files if self.manifest_is_configmap(file)]
            non_configmap_files = [file for file in files if not self.manifest_is_configmap(file)]

            for manifest_path in configmap_files:
                self.deploy_manifest(manifest_path)

            for manifest_path in non_configmap_files:
                self.deploy_manifest(manifest_path)

            self.save_current_cluster_as_last_cluster(deployment)
