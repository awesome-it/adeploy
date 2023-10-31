import argparse
import os
import shutil
import time
from logging import Logger
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEventHandler

from adeploy.common import colors
from adeploy.common.errors import DeployError, RenderError, TestError
from adeploy.common.provider import Provider


class Watcher(Provider):
    templates_dir: str = None
    macros_dirs: str = None
    auto_test: bool = False
    auto_deploy: bool = False
    deploy_on_start : bool = False
    watchers: list = []
    restart_rendering = False
    renderer = None
    tester = None
    deployer = None

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Watch for changes in a Jinja project. Renders, tests and deploys',
                                         usage=argparse.SUPPRESS)

        parser.add_argument("--templates", dest="templates_dir", default='templates',
                            help='Directory containing Jinja flavored templates')

        parser.add_argument("--macros", dest='macros_dirs', nargs='+',
                            help='Directory containing Jinja macros to use. Can be specified mutliple times.'
                                 'By default, macros are loaded from the template dir and its parent dir')
        parser.add_argument("--test", dest='auto_test', action='store_true', default=False,
                            help='Automatically test on changes.')
        parser.add_argument("--deploy", dest='auto_deploy', action='store_true', default=False,
                            help='Automatically deploy on changes. (requires --test)')
        parser.add_argument("--deploy-on-start", dest='deploy_on_start', action='store_true', default=False,
                            help='Deploy on start.')
        return parser

    def parse_args(self, args):
        self.templates_dir = args.get('templates_dir')
        self.macros_dirs = args.get('macros_dirs')
        self.auto_test = args.get('auto_test')
        self.auto_deploy = args.get('auto_deploy')
        self.deploy_on_start = args.get('deploy_on_start')

    def __init__(self, name: str, src_dir: str or Path, build_dir: str or Path, namespaces_dir: str or Path,
                 args: argparse.Namespace, log: Logger, provider, **kwargs):
        super().__init__(name, src_dir, build_dir, namespaces_dir, args, log, **kwargs)
        self.renderer = provider.renderer(
            name=name,
            templates_dir=self.templates_dir,
            src_dir=src_dir,
            build_dir=build_dir,
            namespaces_dir=self.args.namespaces_dir,
            defaults_path=str(self.args.defaults_path),
            args=self.args,
            log=self.log)
        self.tester = provider.tester(
            name=name,
            src_dir=src_dir,
            build_dir=build_dir,
            namespaces_dir=self.args.namespaces_dir,
            defaults_path=self.args.defaults_path,
            args=self.args,
            log=self.log)
        self.deployer = provider.deployer(
            name=name,
            src_dir=src_dir,
            build_dir=build_dir,
            namespaces_dir=self.args.namespaces_dir,
            defaults_path=self.args.defaults_path,
            args=self.args,
            log=self.log)

    def run(self):
        self.log.debug(f'Working on deployment "{self.name}" ...')
        template_dir, templates = self.renderer.load_templates()
        for deployment in self.renderer.load_deployments():
            if not self.deploy_on_start:
                self.log.info(f'Rendering deployment "{colors.blue(deployment)}" ...')
            else:
                self.log.info(f'Deploying deployment "{colors.blue(deployment)}" ...')
            self.create_restart_watcher(
                path=os.path.join(self.namespaces_dir, deployment.namespace, f'{deployment.release}.yml'),
                recursive=False
            )
            for template in templates:
                self.renderer.render_template(deployment, template, prefix='Initial rendering:')
                if self.deploy_on_start and os.path.exists(self.renderer.get_template_output_path(deployment, template)):
                    self.tester.test_maifest(self.renderer.get_template_output_path(deployment, template),
                                             prefix="Initial testing:")
                    self.deployer.deploy_manifest(self.renderer.get_template_output_path(deployment, template),
                                                  prefix="Initial deployment:")
                self.create_template_watcher(deployment, template, self.renderer.jinja_pathes)

        # Watch for changes
        self.create_restart_watcher(path=os.path.join(self.src_dir, self.templates_dir), recursive=True)
        self.create_restart_watcher(path=str(self.defaults_path), recursive=False)
        self.log.info(f'Startup finished. Watching for changes ...')
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

    def create_template_watcher(self, deployment, template, paths):
        for path in paths:
            if os.path.exists(os.path.join(path, template)):
                template_path = os.path.join(path, template)
                self.log.debug(f'Watching for changes in template "{template_path}" ...')
                observer = Observer()
                event_handler = FileSystemEventHandler()
                event_handler.on_modified = lambda event: self.handle_modified_event(deployment, template, event)
                observer.schedule(event_handler, template_path, recursive=False)
                self.watchers.append(observer)
                observer.start()
                return
        raise RenderError(f'Could not create watcher for template "{template}"')

    def handle_create_and_delete_event(self, event):
        if event.src_path.endswith('~'):
            return
        self.restart_rendering = True

    def handle_modified_event(self, deployment, template, event):
        if isinstance(event, FileModifiedEvent):
            self.log.debug(f'{template} modified. Rendering...')
            try:
                self.renderer.render_template(deployment, template, prefix="Autorender:")
                if self.auto_test:
                    self.tester.test_maifest(self.renderer.get_template_output_path(deployment, template),
                                             prefix="Autotest:")
                    if self.auto_deploy:
                        self.deployer.deploy_manifest(self.renderer.get_template_output_path(deployment, template),
                                                      prefix="Autodeploy:")
            except RenderError as e:
                self.log.error(colors.red(f'Error rendering template "{template}":'))
                self.log.error(colors.red_bold(str(e)))
            except TestError as e:
                self.log.error(colors.red(f'Error testing rendered manifest for "{template}":'))
                self.log.error(colors.red_bold(str(e)))
            except DeployError as e:
                self.log.error(colors.red(f'Error deploying rendered manifest for "{template}":'))
                self.log.error(colors.red_bold(str(e)))
