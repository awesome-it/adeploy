import os
import argparse
import jinja2
import glob

from inspect import getmembers, isfunction, getfile
from pathlib import Path
from adeploy.common import colors, RenderError, load_defaults
from adeploy.common.deployment import load_deployments

from .common import filters, globals


class Renderer:
    def __init__(self, name, src_dir, build_dir, args, log, **kwargs):
        self.name = name
        self.src_dir = src_dir
        self.build_dir = build_dir
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

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        template_dir, templates = self.load_templates()

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
                self.log.debug(f'Registering global function "{name}" '
                               f'for deployment "{str(deployment)}" '
                               f'from "{getfile(func_creator)}"')
                env.globals.update({name.replace('create_', ''): func_creator(deployment)})

            for template in templates:
                values = {
                    'name': deployment.name.replace('.','-'),
                    'release': deployment.release.replace('.','-'),
                    'namespace': deployment.namespace,
                    'deployment': deployment.config,
                    'node_selector': deployment.config.get('node', {}),
                    'default_versions': defaults.get('versions', {}),
                }

                output_path = Path(self.build_dir)\
                    .joinpath(deployment.namespace)\
                    .joinpath(self.name)\
                    .joinpath(deployment.release)\
                    .joinpath(Path(template).name)

                self.log.info(f'Rendering "{colors.bold(output_path)}" '
                              f'from "{colors.bold(template)}" '
                              f'for deployment "{colors.blue(deployment)}" ...')

                Path(output_path.parent).mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as output_fd:
                    output_fd.write(env.get_template(Path(template).name).render(**values))

        return True
