import glob
import os
import shutil
import argparse
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import yaml

from adeploy.common import colors
from adeploy.common.errors import RenderError
from .common import helm_repo_add, helm_repo_pull, helm_template, HelmProvider


class Renderer(HelmProvider):
    chart_dir: Path = None
    repo_url: str = None
    hooks_dir: Path = None

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 renderer for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('-c', '--chart-dir', dest='chart_dir', default='chart',
                            help='Directory containing the Helm chart to deploy. If no chart is available'
                                 'you can specify a repo URL using "--repo" to download the chart')

        parser.add_argument('--repo-url', dest='repo_url', help='Helm repo URL to download chart if chart dir is empty')

        parser.add_argument('--hooks-dir', dest='hooks_dir', default='hooks',
                            help='Directory containing bash scripts that can be used to modify the Helm chart without'
                                 'changing upstream repos')

        return parser

    def parse_args(self, args: dict):

        self.repo_url = args.get('repo_url', None)

        self.chart_dir = Path(args.get('chart_dir'))
        if not self.chart_dir.is_absolute():
            self.chart_dir = self.src_dir.joinpath(self.chart_dir)

        self.hooks_dir = Path(args.get('hooks_dir'))
        if not self.hooks_dir.is_absolute():
            self.hooks_dir = self.src_dir.joinpath(self.hooks_dir)

    def build_chart(self):

        chart_build_dir = self.get_chart_dir()

        try:

            # Chart dir exists, copy to build dir
            if self.chart_dir.is_dir() and os.listdir(str(self.chart_dir)):

                if chart_build_dir.exists():
                    shutil.rmtree(chart_build_dir)

                self.log.info(f'Using chart in "{colors.bold(self.chart_dir)} ...')
                shutil.copytree(str(self.chart_dir), chart_build_dir)

            else:

                if self.repo_url is None:

                    if chart_build_dir.is_dir() and os.listdir(chart_build_dir):
                        self.log.info(f'Re-using previously downloaded chart from "{colors.bold(chart_build_dir)}". '
                                      f'Pass --repo-url to force re-downloaded the chart.')
                        return

                    raise RenderError(f'No chart repo URL specified while chart dir is empty. '
                                      f'Please either add a Helm chart to "{colors.bold(self.chart_dir)}" or '
                                      f'specify a chart repo URL using --repo-url to download the chart repo.')

                self.log.info(f'Adding chart repo from {colors.blue(self.repo_url)} ...')

                if chart_build_dir.exists():
                    shutil.rmtree(chart_build_dir)

                repo = f'repo_{self.name}'

                try:
                    self.log.debug(helm_repo_add(self.log, repo, self.repo_url).stdout.strip())
                except CalledProcessError as e:
                    raise RenderError(f'Error while adding helm repo {self.repo_url}: {e.stderr}')

                try:

                    chart_version = self.get_chart_version()
                    self.log.debug(f'Pulling chart "{colors.bold(self.name)}" version {colors.bold(chart_version)} ...')

                    temp = TemporaryDirectory()
                    self.log.debug(helm_repo_pull(self.log, repo,
                                                  name=self.name,
                                                  version=chart_version,
                                                  dest=temp.name).stdout.strip())

                    shutil.move(f'{temp.name}/{self.name}', chart_build_dir)

                except CalledProcessError as e:
                    raise RenderError(f'Error while pulling helm repo {self.repo_url}: {e.stderr}')

        except shutil.Error as e:
            raise RenderError(f'Error while creating chart build dir "{chart_build_dir}": {e.strerror}')

    def run_hooks(self):

        if self.hooks_dir.is_dir():
            for hook in [Path(h) for h in glob.glob(f'{self.hooks_dir}/*.sh')]:
                self.log.info(f'Running hook "{colors.bold(hook.stem)}" ...')

                cmd = [str(c) for c in [hook, self.src_dir.joinpath(self.get_chart_dir())]]

                self.log.debug(f'... Executing command "{colors.bold(" ".join(cmd))}" '
                               f'in "{colors.bold(self.hooks_dir)}"')

                try:
                    result = subprocess.run(cmd, cwd=str(self.hooks_dir), capture_output=True, text=True)
                    result.check_returncode()
                    self.log.debug(f'... {result.stdout}')
                except CalledProcessError as e:
                    self.log.error(f'... {e.stdout}')
                    self.log.error(colors.red(f'Error when running hook "{colors.bold(hook.stem)}": {e.stderr}'))
                    raise e

                return result

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        self.build_chart()
        self.run_hooks()

        for deployment in self.load_deployments():

            output_path = Path(self.build_dir) \
                .joinpath(deployment.namespace) \
                .joinpath(self.name) \
                .joinpath(deployment.release)

            self.log.info(f'Rendering chart "{colors.bold(self.name)}" '
                          f'version {colors.bold(self.get_chart_version())} '
                          f'and values for deployment "{colors.blue(deployment)}" '
                          f'in "{colors.bold(output_path)}" ...')

            try:

                output_path.mkdir(parents=True, exist_ok=True)
                values_path = f'{output_path}/values.yml'
                with open(values_path, 'w') as fd:
                    yaml.dump(deployment.config, fd)

                output = helm_template(self.log, deployment, self.get_chart_dir(), values_path)
                with open(f'{output_path}/manifest.yml', 'w') as fd:
                    fd.write(output.stdout)

            except CalledProcessError as e:
                raise RenderError(f'Error while rendering chart "{self.name}": {e.stderr}')

        return True