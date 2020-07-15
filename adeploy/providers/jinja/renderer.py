import os
import argparse
import glob

from pathlib import Path
from adeploy.common import colors, RenderError, load_defaults
from adeploy.common.deployment import load_deployments

from adeploy.common.jinja import globals, env as jinja_env


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
        env = jinja_env.create(jinja_pathes, self.log)

        for deployment in deployments:

            jinja_env.register_globals(env, deployment, self.log)

            for template in templates:
                values = {
                    'name': deployment.name.replace('.', '-'),
                    'release': deployment.release.replace('.', '-'),
                    'namespace': deployment.namespace,
                    'deployment': deployment.config,
                    'node_selector': deployment.config.get('node', {}),
                    'default_versions': defaults.get('versions', {}),
                }

                output_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(Path(template).name)

                self.log.info(f'Rendering "{colors.bold(output_path)}" '
                              f'from "{colors.bold(template)}" '
                              f'for deployment "{colors.blue(deployment)}" ...')

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as fd:
                    fd.write(env.get_template(Path(template).name).render(**values))

            for secret in globals.get_secrets():
                secret_output_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath('secrets') \
                    .joinpath(secret.name + '.yml')

                self.log.info(f'Rendering "{colors.bold(secret_output_path)}" '
                              f'for secret "{colors.bold(secret.name)}" '
                              f'for deployment "{colors.blue(deployment)}" ...')

                secret.render(secret_output_path)

        return True
