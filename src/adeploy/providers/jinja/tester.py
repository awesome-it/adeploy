import argparse
import glob
import json
from pathlib import Path
from subprocess import CalledProcessError

from adeploy.common import colors
from adeploy.common.errors import TestError
from adeploy.common.kubectl import (
    kubectl_apply,
    kubectl_set_default_namespace,
    kubectl_set_fake_namespace,
    parse_kubectrl_apply,
)
from adeploy.common.provider import Provider


class Tester(Provider):
    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            description="Jinja tester for k8s manifests written in Jinja",
            usage=argparse.SUPPRESS,
        )
        return parser

    def parse_args(self, args: dict):
        return

    def test_maifest(self, manifest_path, prefix=""):
        try:
            default_ns, fake_ns = kubectl_set_fake_namespace(self.log)
            manifests = kubectl_apply(
                self.log, manifest_path, dry_run="client", output="json"
            )
            kubectl_set_default_namespace(self.log, default_ns)

            result = kubectl_apply(self.log, manifest_path, dry_run="server")
            parse_kubectrl_apply(
                self.log,
                result.stdout,
                manifests=json.loads(manifests.stdout),
                fake_ns=fake_ns,
                default_ns=default_ns,
                prefix=prefix,
            )

        except CalledProcessError as e:
            raise TestError(f'Error in manifest dir "{manifest_path}": {e.stderr}')

    def run(self):
        self.log.debug(f'Working on deployment "{self.name}" ...')

        for deployment in self.load_deployments():
            manifests_dir = (
                Path(self.build_dir)
                .joinpath(deployment.namespace)
                .joinpath(self.name)
                .joinpath(deployment.release)
            )

            self.log.info(
                f'Testing manifests for deployment "{colors.blue(deployment)}" in "{manifests_dir}" ...'
            )

            files = []
            for ext in ["yaml", "yml"]:
                files.extend(glob.glob(f"{manifests_dir}/**/*.{ext}", recursive=True))

            for manifest_path in files:
                self.test_maifest(manifest_path)
