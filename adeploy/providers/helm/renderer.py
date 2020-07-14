import os
import shutil
import argparse
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import yaml

from adeploy.common import colors, RenderError, load_defaults
from adeploy.common.deployment import Deployment, get_deployment_name, load_deployments
from .common import helm_repo_add, helm_repo_pull, helm_template


class Renderer:
    def __init__(self, name, src_dir, args, log, **kwargs):
        self.name = name
        self.src_dir = src_dir
        self.log = log
        self.args = args

        self.defaults_file = kwargs.get('defaults_file')
        self.namespaces_dir = kwargs.get('namespaces_dir')
        self.chart_dir = kwargs.get('chart_dir')
        self.repo_url = kwargs.get('repo_url', None)
        self.filters_namespace = kwargs.get('filters_namespace')
        self.filters_release = kwargs.get('filters_release')

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 renderer for k8s manifests',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--defaults', dest='defaults_file', default='defaults.yml',
                            help='YML file with default variables. Relative to the source dir.')
        parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                            help='Directory containing namespaces and variables for deployments')
        parser.add_argument('--chart', dest='chart_dir', default='chart',
                            help='Directory containing the Helm chart to deploy. If no chart is available'
                                 'you can specify a repo URL using "--repo" to download the chart')
        parser.add_argument('--repo-url', dest='repo_url', help='Helm repo URL to download chart if chart dir is empty')
        parser.add_argument('-n', '--namespace', dest='filters_namespace', nargs='*',
                            help='Only include specified namespace. Argument can be specified multiple times.')
        parser.add_argument('-r', '--release', dest='filters_release', nargs='*',
                            help='Only include specified deployment release i.e. "prod", "testing". '
                                 'Argument can be specified multiple times.')

        return parser

    def load_chart(self):

        chart_dir = self.chart_dir
        if not os.path.isabs(chart_dir):
            chart_dir = f'{self.src_dir}/{chart_dir}'

        if not os.path.exists(chart_dir) or not os.listdir(chart_dir):

            if self.repo_url is None:
                raise RenderError(f'No chart repo URL specified while chart dir is empty. '
                                  f'Please either add a Helm chart to "{colors.bold(self.chart_dir)}" or '
                                  f'specify a chart repo URL using --repo-url to download the chart repo.')

            self.log.info(f'Chart directory "{colors.bold(chart_dir)}" is empty, '
                          f'downloading chart repo from {colors.blue(self.repo_url)} ...')

            repo = f'repo_{self.name}'

            try:
                self.log.debug(helm_repo_add(self.log, repo, self.repo_url).stdout.strip())
            except CalledProcessError as e:
                raise RenderError(f'Error while adding helm repo {self.repo_url}: {e.stderr}')

            try:
                if os.path.exists(chart_dir):
                    os.rmdir(chart_dir)

                temp = TemporaryDirectory()
                self.log.debug(helm_repo_pull(self.log, repo, self.name, temp.name).stdout.strip())
                shutil.move(f'{temp.name}/{self.name}', chart_dir)

            except CalledProcessError as e:
                raise RenderError(f'Error while adding helm repo {self.repo_url}: {e.stderr}')

            except shutil.Error as e:
                raise RenderError(f'Error while creating chart dir "{chart_dir}": {e.strerror}')

        return chart_dir

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        chart_dir = self.load_chart()

        defaults = load_defaults(
            log=self.log,
            src_dir=self.src_dir,
            defaults_file=self.defaults_file
        )

        deployments = load_deployments(
            log=self.log,
            src_dir=self.src_dir,
            namespaces_dir=self.namespaces_dir,
            deployment_name=self.name,
            defaults=defaults)

        for deployment in deployments:

            output_path = Path(self.args.build_dir) \
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

                output = helm_template(self.log, deployment, chart_dir, values_path)
                with open(f'{output_path}/manifest.yml', 'w') as fd:
                    fd.write(output.stdout)

            except CalledProcessError as e:
                raise RenderError(f'Error while rendering chart "{self.name}": {e.stderr}')

        return True
