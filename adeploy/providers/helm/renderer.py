import os
import shutil
import argparse
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import yaml
import glob
import sys

from pathlib import Path
from adeploy.common import colors, RenderError
from adeploy.common.deployment import Deployment, get_deployment_name
from .common import helm_repo_add, helm_repo_pull


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

        return parser

    def load_chart(self, extensions=None):

        chart_dir = self.chart_dir
        if not os.path.isabs(chart_dir):
            chart_dir = f'{self.src_dir}/{chart_dir}'

        if not os.path.exists(chart_dir) or not os.listdir(chart_dir):

            if self.repo_url is None:
                raise RenderError(f'No chart repo URL specified while chart dir is empty. '
                                  f'Please either add a Helm chart to "{colors.bold(self.chart_dir)}" or '
                                  f'specify a chart repo URL using --repo to download the chart repo.')

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

    def load_defaults(self):

        defaults_file = self.defaults_file
        if not os.path.isabs(self.defaults_file):
            defaults_file = f'{self.src_dir}/{self.defaults_file}'

        self.log.debug(f'Loading defaults from "{defaults_file}" ...')
        return yaml.load(open(defaults_file), Loader=yaml.FullLoader)

    def load_deployments(self, deployment_name, defaults=None, extensions=None):

        if defaults is None:
            defaults = {}

        if extensions is None:
            extensions = ['yaml', 'yml']

        namespaces_dir = self.namespaces_dir
        if not os.path.isabs(self.namespaces_dir):
            namespaces_dir = f'{self.src_dir}/{namespaces_dir}'

        self.log.debug(f'Scanning for deployment variables in "{namespaces_dir}/*/*.({"|".join(extensions)})" ...')

        # Structure 1: namespaces / <namespace_name> / <deployment_release>.yml
        # Structure 2: instances / <namespace_name> / <deployment_name> / <deployment_release>.yml

        deployments = []

        for ns in [d for d in os.listdir(namespaces_dir) if os.path.isdir(os.path.join(namespaces_dir, d))]:

            # Structure 2
            deployment_dir = os.path.join(namespaces_dir, ns, deployment_name)
            if not os.path.isdir(deployment_dir):
                # Structure 1
                deployment_dir = os.path.join(namespaces_dir, ns)

            for ext in extensions:
                for deployment_release_config in glob.glob(f'{deployment_dir}/*.{ext}'):
                    deployment_release = Path(deployment_release_config).stem
                    self.log.debug(f'... '
                                   f'found deployment "{colors.bold(deployment_name)}", '
                                   f'release "{colors.bold(deployment_release)}, '
                                   f'namespace "{colors.bold(ns)}" '
                                   f'in "{deployment_release_config}" ')

                    deployment = Deployment(deployment_name, deployment_release, ns)
                    deployment.load_config(deployment_release_config, defaults=defaults)
                    deployments.append(deployment)

        return deployments

    def run(self):

        deployment_name = get_deployment_name(self.src_dir, self.args.deployment_name)
        self.log.debug(f'Working on deployment "{deployment_name}" ...')

        chart_dir = self.load_chart()
        defaults = self.load_defaults()
        deployments = self.load_deployments(deployment_name, defaults=defaults)

        for deployment in deployments:

            """            
            # Register globals from common.globals
            for name, func_creator in [f for f in getmembers(globals) if isfunction(f[1])]:
                self.log.debug(
                    f'Registering global function "{name}" for deployment "{str(deployment)}" from "{getfile(func_creator)}"')
                env.globals.update({name.replace('create_', ''): func_creator(deployment)})

            for template in templates:
                values = {
                    'name': deployment.release.replace('.', '-'),
                    'namespace': deployment.namespace,
                    'deployment': deployment.config,
                    'node_selector': deployment.config.get('node', {}),
                    'default_versions': defaults.get('versions', {}),
                }

                output_path = Path(self.args.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(deployment_name) \
                    .joinpath(deployment.release) \
                    .joinpath(Path(template).name)

                self.log.info(f'Rendering "{colors.bold(output_path)}" '
                              f'from "{colors.bold(template)}" '
                              f'for deployment "{colors.blue(deployment)}" ...')

                Path(output_path.parent).mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as output_fd:
                    output_fd.write(env.get_template(Path(template).name).render(**values))
            """

        return True
