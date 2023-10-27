import argparse
import glob
import json
import os
import shutil
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEventHandler

import jinja2

from adeploy.common import colors
from adeploy.common.errors import RenderError
from adeploy.common.jinja import env as jinja_env
from adeploy.common.provider import Provider
from adeploy.common.yaml import update


class Renderer(Provider):
    templates_dir: str = None
    macros_dirs: str = None
    watch_for_changes: bool = False
    watchers: list = []
    restart_rendering = False

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Jinja renderer for k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)

        parser.add_argument("--templates", dest="templates_dir", default='templates',
                            help='Directory containing Jinja flavored templates')

        parser.add_argument("--macros", dest='macros_dirs', nargs='+',
                            help='Directory containing Jinja macros to use. Can be specified mutliple times.'
                                 'By default, macros are loaded from the template dir and its parent dir')
        parser.add_argument("-w", "--watch", dest='watch_for_changes', action='store_true', default=False,
                            help='Keep running, watch for changes, render immediately')
        return parser

    def parse_args(self, args):
        self.templates_dir = args.get('templates_dir')
        self.macros_dirs = args.get('macros_dirs')
        self.watch_for_changes = args.get('watch_for_changes')

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

    def render_template(self, deployment, template, env):
        values = deployment.get_template_values()

        output_path = Path(self.build_dir) \
            .joinpath(deployment.namespace) \
            .joinpath(self.name) \
            .joinpath(deployment.release) \
            .joinpath(template)

        self.log.info(f'... render "{colors.bold(template)}" in "{colors.bold(output_path)}" ...')

        try:
            data = env.get_template(template).render(**values)
            if len(data.replace('---', '').replace('\n', '').strip()) > 0:
                data = update(self.log, data, deployment)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as fd:
                    fd.write(data)

        except jinja2.exceptions.TemplateNotFound as e:
            self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
            raise RenderError(f'Jinja template error: Template "{e}" not found in "{template}"')

        except jinja2.exceptions.TemplateSyntaxError as e:
            self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
            raise RenderError(
                f'Jinja template syntax error in "{colors.bold(e.filename)}", line {colors.bold(e.lineno)}: {e}')

        except jinja2.exceptions.TemplateError as e:
            self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
            raise RenderError(f'Jinja template error in "{colors.bold(template)}": {e}')

    def run(self):

        self.log.debug(f'Working on deployment "{self.name}" ...')

        template_dir, templates = self.load_templates()

        jinja_pathes = ['.', '..', template_dir, str(Path(template_dir).parent), str(Path(template_dir).parent.parent)]
        self.log.debug(f'Using Jinja file system loader with pathes: {", ".join(jinja_pathes)}')
        env = jinja_env.create(jinja_pathes, self.log)

        for deployment in self.load_deployments():

            jinja_env.register_globals(env, deployment, self.log)

            self.log.info(f'Rendering deployment "{colors.blue(deployment)}" ...')

            if self.watch_for_changes:
                self.create_restart_watcher(
                    path=os.path.join(self.namespaces_dir, deployment.namespace, f'{deployment.release}.yml'),
                    recursive=False
                )
            for template in templates:
                self.render_template(deployment, template, env)
                if self.watch_for_changes:
                    self.create_template_watcher(deployment, template, env, jinja_pathes)

        if not self.watch_for_changes:
            return True
        # Watch for changes
        self.create_restart_watcher(path=os.path.join(self.src_dir, self.templates_dir), recursive=True)
        self.create_restart_watcher(path=str(self.defaults_path), recursive=False)
        self.log.info(f'Initial rendering finished. Watching for changes ...')
        try:
            while True:
                time.sleep(1)
                if self.restart_rendering:
                    self.log.debug(f'Stopping all file watchers...')
                    for observer in self.watchers:
                        observer.stop()
                        observer.join()
                    self.watchers = []
                    shutil.rmtree(self.build_dir)
                    self.restart_rendering = False
                    self.run()
        except KeyboardInterrupt:
            return True

    def get_restarting_event_handler(self) -> FileSystemEventHandler:
        event_handler = FileSystemEventHandler()
        event_handler.on_created = lambda event: self.handle_create_and_delete_event(event)
        event_handler.on_deleted = lambda event: self.handle_create_and_delete_event(event)
        return event_handler

    def create_restart_watcher(self, path: str, recursive: bool):
        self.log.debug(f'Watching for changes in "{path}" ...')
        observer = Observer()
        observer.schedule(self.get_restarting_event_handler(), path, recursive)
        self.watchers.append(observer)
        observer.start()

    def create_template_watcher(self, deployment, template, env, paths):
        for path in paths:
            if os.path.exists(os.path.join(path, template)):
                template_path = os.path.join(path, template)
                self.log.debug(f'Watching for changes in template "{template_path}" ...')
                observer = Observer()
                event_handler = FileSystemEventHandler()
                event_handler.on_modified = lambda event: self.handle_modified_event(deployment, template, env, event)
                observer.schedule(event_handler, template_path, recursive=False)
                self.watchers.append(observer)
                observer.start()
                return
        raise RenderError(f'Could not create watcher for template "{template}"')

    def handle_create_and_delete_event(self, event):
        self.restart_rendering = True

    def handle_modified_event(self, deployment, template, env, event):
        if isinstance(event, FileModifiedEvent):
            self.log.debug(f'{template} modified. Rendering...')
            try:
                self.render_template(deployment, template, env)
            except RenderError as e:
                self.log.error(colors.red(f'Error rendering template "{template}":'))
                self.log.error(colors.red_bold(str(e)))
