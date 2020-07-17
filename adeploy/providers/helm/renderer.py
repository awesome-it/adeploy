import os
import shutil
import argparse
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import yaml

from adeploy.common import colors
from adeploy.common.errors import RenderError
from .common import helm_repo_add, helm_repo_pull, helm_template, HelmProvider


class Renderer(HelmProvider):

    chart_dir: str = None
    repo_url: str = None

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 renderer for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('-c', '--chart', dest='chart_dir', default='chart',
                            help='Directory containing the Helm chart to deploy. If no chart is available'
                                 'you can specify a repo URL using "--repo" to download the chart')

        parser.add_argument('--repo-url', dest='repo_url', help='Helm repo URL to download chart if chart dir is empty')

        return parser

    def parse_args(self, args: dict):
        self.chart_dir = args.get('chart_dir')
        self.repo_url = args.get('repo_url', None)

    def build_chart(self):

        chart_dir = Path(self.chart_dir)

        if not chart_dir.is_absolute():
            chart_dir = self.src_dir.joinpath(chart_dir)

        chart_build_dir = self.get_chart_dir()

        try:

            # Chart dir exists, copy to build dir
            if chart_dir.is_dir() and os.listdir(chart_dir):

                if chart_build_dir.exists():
                    shutil.rmtree(chart_build_dir)

                self.log.info(f'Using chart in "{colors.bold(chart_dir)} ...')
                shutil.copytree(chart_dir, chart_build_dir)

            else:

                if self.repo_url is None:

                    if chart_build_dir.is_dir() and os.listdir(chart_build_dir):
                        self.log.info(f'Re-using previously downlaoded chart from "{colors.bold(chart_build_dir)}". '
                                      f'Pass --repo-url to force re-downloaded the chart.')
                        return

                    raise RenderError(f'No chart repo URL specified while chart dir is empty. '
                                      f'Please either add a Helm chart to "{colors.bold(self.chart_dir)}" or '
                                      f'specify a chart repo URL using --repo-url to download the chart repo.')

                self.log.info(f'Chart directory "{colors.bold(chart_dir)}" is empty, '
                              f'downloading chart repo from {colors.blue(self.repo_url)} ...')

                if chart_build_dir.exists():
                    shutil.rmtree(chart_build_dir)

                repo = f'repo_{self.name}'

                try:
                    self.log.debug(helm_repo_add(self.log, repo, self.repo_url).stdout.strip())
                except CalledProcessError as e:
                    raise RenderError(f'Error while adding helm repo {self.repo_url}: {e.stderr}')

                try:

                    temp = TemporaryDirectory()
                    self.log.debug(helm_repo_pull(self.log, repo, self.name, temp.name).stdout.strip())
                    shutil.move(f'{temp.name}/{self.name}', chart_build_dir)

                except CalledProcessError as e:
                    raise RenderError(f'Error while adding helm repo {self.repo_url}: {e.stderr}')

        except shutil.Error as e:
            raise RenderError(f'Error while creating chart build dir "{chart_build_dir}": {e.strerror}')

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')
        self.build_chart()

        for deployment in self.load_deployments():

            output_path = Path(self.build_dir) \
                .joinpath(deployment.namespace) \
                .joinpath(self.name) \
                .joinpath(deployment.release)

            self.log.info(f'Rendering chart "{colors.bold(self.name)}" and values '
                          f'for deployment "{colors.blue(deployment)}" '
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
