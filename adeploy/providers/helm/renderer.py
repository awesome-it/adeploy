import os
import shutil
import argparse
import yaml
import jinja2
import glob

from inspect import getmembers, isfunction, getfile
from pathlib import Path
from adeploy.common import colors, RenderError
from adeploy.common.deployment import Deployment
from .common import filters, globals


class Renderer:
    def __init__(self, src_dir, args, log, **kwargs):
        self.src_dir = src_dir
        self.log = log
        self.args = args
        self.defaults_file = kwargs.get('defaults_file')
        self.namespaces_dir = kwargs.get('namespaces_dir')
        self.templates_dir = kwargs.get('templates_dir')
        self.macros_dirs = kwargs.get('macros_dirs')

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Jinja renderer for k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)

        parser.add_argument('--defaults', dest='defaults_file', default='defaults.yml',
                            help='YML file with default variables. Relative to the source dir.')
        parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                            help='Directory containing namespaces and variables for deployments')
        parser.add_argument("--templates", dest="templates_dir", default='templates',
                            help='Directory containing Jinja flavored templates')
        parser.add_argument("--macros", dest='macros_dirs', nargs='+',
                            help='Directory containing Jinja macros to use. Can be specified mutliple times.'
                                 'By default, macros are loaded from the template dir and its parent dir')

        return parser

    def get_deployment_name(self):
        deployment_name = os.path.basename(self.src_dir)
        self.log.debug(f'Working on deployment "{deployment_name}" ...')
        return deployment_name

    def load_templates(self, extensions=None):

        if extensions is None:
            extensions = ['yaml', 'yml', 'jinja']

        templates_dir = self.templates_dir
        if not os.path.isabs(templates_dir):
            templates_dir = f'{self.src_dir}/{templates_dir}'

        self.log.debug(f'Scanning source dir with pattern "{templates_dir}/*.({"|".join(extensions)})" ...')

        files = []
        for ext in extensions:
            files.extend(glob.glob(f'{templates_dir}/*.{ext}'))

        if len(files) == 0:
            raise RenderError(f'No template files found in "{templates_dir}"')

        self.log.debug(f'Found templates: ')
        [self.log.debug(f'- {f}') for f in files]

        return templates_dir, files

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

        deployment_name = self.get_deployment_name()
        template_dir, templates = self.load_templates()
        defaults = self.load_defaults()
        deployments = self.load_deployments(deployment_name, defaults=defaults)

        jinja_pathes = ['.', '..', template_dir, str(Path(template_dir).parent), str(Path(template_dir).parent.parent)]
        self.log.debug(f'Using Jinja file system loader with pathes: {", ".join(jinja_pathes)}')

        env = jinja2.Environment(
            # This is to load macros from template dir and the parent dir
            loader=jinja2.FileSystemLoader(jinja_pathes),
            autoescape=jinja2.select_autoescape(['json']),
            # Add support for expressions statements, see https://stackoverflow.com/a/39858522/381166
            extensions=['jinja2.ext.do'],
        )

        # Register filters from common.filters
        for name, func in [f for f in getmembers(filters) if isfunction(f[1])]:
            self.log.debug(f'Registering filter "{name}" from "{getfile(func)}"')
            env.filters[name] = func

        for deployment in deployments:

            # Register globals from common.globals
            for name, func_creator in [f for f in getmembers(globals) if isfunction(f[1])]:
                self.log.debug(f'Registering global function "{name}" for deployment "{str(deployment)}" from "{getfile(func_creator)}"')
                env.globals.update({name.replace('create_', ''): func_creator(deployment)})

            for template in templates:
                values = {
                    'name': deployment.release.replace('.','-'),
                    'namespace': deployment.namespace,
                    'deployment': deployment.config,
                    'node_selector': deployment.config.get('node', {}),
                    'default_versions': defaults.get('versions', {}),
                }

                output_path = Path(self.args.build_dir)\
                    .joinpath(deployment.namespace)\
                    .joinpath(deployment_name)\
                    .joinpath(deployment.release)\
                    .joinpath(Path(template).name)

                self.log.info(f'Rendering "{colors.bold(output_path)}" '
                              f'from "{colors.bold(template)}" '
                              f'for deployment "{colors.blue(deployment)}" ...')

                Path(output_path.parent).mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as output_fd:
                    output_fd.write(env.get_template(Path(template).name).render(**values))

        return True
