import argparse
import glob
import json
import os
from pathlib import Path

import jinja2

from adeploy.common import colors
from adeploy.common.errors import RenderError
from adeploy.common.jinja import env as jinja_env
from adeploy.common.provider import Provider


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

    def parse_args(self, args):
        self.templates_dir = args.get('templates_dir')
        self.macros_dirs = args.get('macros_dirs')

    def load_templates(self, extensions=None):

        if extensions is None:
            extensions = ['yaml', 'yml']

        templates_dir = self.templates_dir
        if not os.path.isabs(templates_dir):
            templates_dir = f'{self.src_dir}/{templates_dir}'

        if templates_dir[-1] == '/':
            templates_dir = templates_dir[:-1]

        self.log.debug(f'Scanning source dir with pattern "{templates_dir}/**/*.({"|".join(extensions)})" ...')

        files = []
        for ext in extensions:
            files.extend(glob.glob(f'{templates_dir}/**/*.{ext}', recursive=True))

        # Ignore files starting with "_" and "."
        files = [f for f in files if Path(f).name[0] not in ['.', '_']]

        if len(files) == 0:
            raise RenderError(f'No template files found in "{templates_dir}"')

        self.log.debug(f'Found templates: ')
        [self.log.debug(f'- {f}') for f in files]

        return templates_dir, sorted([f.replace(f'{templates_dir}/', '') for f in files])

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        template_dir, templates = self.load_templates()

        jinja_pathes = ['.', '..', template_dir, str(Path(template_dir).parent), str(Path(template_dir).parent.parent)]
        self.log.debug(f'Using Jinja file system loader with pathes: {", ".join(jinja_pathes)}')
        env = jinja_env.create(jinja_pathes, self.log)

        for deployment in self.load_deployments():

            jinja_env.register_globals(env, deployment, self.log)

            self.log.info(f'Rendering deployment "{colors.blue(deployment)}" ...')

            for template in templates:
                values = deployment.get_template_values()

                output_path = Path(self.build_dir) \
                    .joinpath(deployment.namespace) \
                    .joinpath(self.name) \
                    .joinpath(deployment.release) \
                    .joinpath(template)

                self.log.info(f'... render "{colors.bold(template)}" in "{colors.bold(output_path)}" ...')

                try:
                    data = env.get_template(template).render(**values)
                    if len(data.replace('---','').replace('\n', '').strip()) > 0:
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'w') as fd:
                            fd.write(data)

                except jinja2.exceptions.TemplateNotFound as e:
                    self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
                    raise RenderError(f'Jinja template error: Template "{e}" not found in "{template}"')

                except jinja2.exceptions.TemplateError as e:
                    self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
                    raise RenderError(f'Jinja template error in "{colors.bold(template)}": {e}')

        return True
