import argparse
import glob
import json
import os
from logging import Logger
from pathlib import Path

import jinja2
from ruamel.yaml import YAML
from ruamel.yaml.error import MarkedYAMLError

from adeploy.common import colors
from adeploy.common.deployment import Deployment
from adeploy.common.errors import RenderError
from adeploy.common.jinja import env as jinja_env
from adeploy.common.provider import Provider
from adeploy.common.yaml import update


class Renderer(Provider):
    templates_dir: str = None
    macros_dirs: str = None

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Jinja renderer for k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)

        parser.add_argument("--templates", dest="templates_dir", default='templates',
                            help='Directory containing Jinja flavored templates')

        parser.add_argument("--macros", dest='macros_dirs', nargs='+',
                            help='Directory containing Jinja macros to use. Can be specified mutliple times.'
                                 'By default, macros are loaded from the template dir and its parent dir')
        return parser

    def __init__(self, templates_dir, name: str, src_dir: str or Path, build_dir: str or Path,
                 namespaces_dir: str or Path, args: argparse.Namespace, log: Logger, **kwargs):
        super().__init__(name, src_dir, build_dir, namespaces_dir, args, log, **kwargs)
        if not os.path.isabs(templates_dir):
            self.templates_dir = f'{self.src_dir}/{templates_dir}'

        if self.templates_dir[-1] == '/':
            self.templates_dir = self.templates_dir[:-1]
        self.jinja_pathes = ['.', '..', self.templates_dir, str(Path(self.templates_dir).parent),
                             str(Path(self.templates_dir).parent.parent)]
        self.log.debug(f'Using Jinja file system loader with pathes: {", ".join(self.jinja_pathes)}')
        self.env = jinja_env.create(self.jinja_pathes, log=self.log, templates_dir=self.templates_dir)

        yaml = YAML(typ='rt')
        yaml.default_flow_style = False
        yaml.preserve_quotes = True
        yaml.sort_keys = False
        self.yaml = yaml

    def parse_args(self, args):
        self.templates_dir = args.get('templates_dir')
        self.macros_dirs = args.get('macros_dirs')

    def load_templates(self, extensions=None):

        if extensions is None:
            extensions = ['yaml', 'yml']

        self.log.debug(f'Scanning source dir with pattern "{self.templates_dir}/**/*.({"|".join(extensions)})" ...')

        files = []
        for ext in extensions:
            files.extend(glob.glob(f'{self.templates_dir}/**/*.{ext}', recursive=True))

        # Ignore files starting with "_" and "."
        files = [f for f in files if Path(f).name[0] not in ['.', '_']]

        if len(files) == 0:
            raise RenderError(f'No template files found in "{self.templates_dir}"')

        self.log.debug(f'Found templates: ')
        [self.log.debug(f'- {f}') for f in files]

        return self.templates_dir, sorted([f.replace(f'{self.templates_dir}/', '') for f in files])

    def get_template_output_path(self, deployment, template):
        return Path(self.build_dir) \
            .joinpath(deployment.namespace) \
            .joinpath(self.name) \
            .joinpath(deployment.release) \
            .joinpath(template)

    def render_template(self, deployment: Deployment, template_path: str, prefix: str = '...'):
        jinja_env.register_globals(self.env, deployment, self.log, self.templates_dir)
        values = deployment.get_template_values()
        try:
            rendered_template = self.env.get_template(template_path).render(**values)
        except jinja2.exceptions.TemplateNotFound as e:
            self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
            raise RenderError(f'Jinja template error: Template "{e}" not found in "{template_path}"')

        except jinja2.exceptions.TemplateSyntaxError as e:
            self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
            raise RenderError(
                f'Jinja template syntax error in "{colors.bold(e.filename)}", line {colors.bold(e.lineno)}: {e}')

        except jinja2.exceptions.TemplateError as e:
            self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
            raise RenderError(f'Jinja template error in "{colors.bold(template_path)}": {e}')

        try:
            output_path = self.get_template_output_path(deployment, template_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            documents = self.yaml.load_all(rendered_template)

            documents = [d for d in documents if d is not None]
            if len(documents) == 0:
                self.log.warning(f'{prefix} {colors.bold(template_path)} is empty ...')

            for index, doc in enumerate(documents):
                doc = update(self.log, doc, deployment)

                object_kind = doc.get('kind', None)
                object_name = doc.get('metadata', {}).get('name', None)
                object_output_path = output_path.with_suffix(f'.{index}.yml') if len(documents) > 1 else output_path

                with open(object_output_path, 'w') as fd:
                    self.log.info(f'{prefix} render {colors.bold(object_kind)} "{colors.bold(object_name)}" '
                                  f'from "{colors.bold(template_path)}" '
                                  f'in "{colors.bold(object_output_path)}" ...')
                    self.yaml.dump(doc, fd)

        except MarkedYAMLError as e:
            raise RenderError(f'YAML error in "{colors.bold(template_path)}": {e}')

    def run(self):
        self.log.debug(f'Working on deployment "{self.name}" ...')
        self.clean_build_dir()
        template_dir, templates = self.load_templates()
        for deployment in self.load_deployments():
            self.log.info(f'Rendering deployment "{colors.blue(deployment)}" ...')
            for template in templates:
                self.render_template(deployment, template)
        return True
