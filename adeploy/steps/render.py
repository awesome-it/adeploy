import os
import sys
import argparse

from colorama import init, Style, Fore
from .. import common
from .. import providers
from ..common import colors, RenderError


class Render:
    parser = None

    @staticmethod
    def setup_parser(parser):

        parser.add_argument("--render", default=True, help=argparse.SUPPRESS)

        if '--providers' not in sys.argv:
            parser.add_argument("src_dirs", help="Directory containing deployment sources i.e. Kustomize or Helm Chart",
                                nargs='+', metavar='dir')

        parser.add_argument("-p", "--provider", dest="provider",
                            help="The provider to use, type --providers to get a list of supported providers.",
                            required='--providers' not in sys.argv)

        parser.add_argument("--providers", dest="list_providers", action="store_true",
                            help="A list of supported providers")

        Render.parser = parser

    def __init__(self, args, render_args, log):
        self.args = args
        self.log = log

        if 'render' in self.args:

            if self.args.list_providers:
                self.list_providers()
                sys.exit(0)

            # Load renderer from provider
            provider = common.get_provider(self.args.provider)

            if provider is None:
                log.error(colors.red(f'Cannot find supported provider type "{self.args.provider}". ') +
                          f'Type "--providers" to get a list of supported providers.')
                sys.exit(1)

            num_warnings = 0

            for src_dir in self.args.src_dirs:

                if not os.path.isdir(src_dir):
                    self.log.warning(colors.orange(f'"{src_dir}" is not a directory, skip'))
                    num_warnings += 1
                    continue

                self.log.info(
                    colors.green_bold('Rendering ') + colors.bold(src_dir) + ' in ' +
                    colors.bold(self.args.build_dir) + ' using the provider ' +
                    colors.bold(self.args.provider)
                )

                try:
                    Renderer = getattr(provider, 'Renderer')

                    renderer = Renderer(
                        src_dir=src_dir,
                        args=self.args,
                        log=self.log,
                        **vars(Renderer.get_parser().parse_args(render_args)))

                    renderer.run()

                except RenderError as e:
                    self.log.error(colors.red(f'Render error in source directory "{src_dir}":'))
                    self.log.error(colors.red_bold(str(e)))
                    sys.exit(1)

            if num_warnings > 0:
                self.log.warning(colors.orange(f'Rendering finished with {num_warnings} warnings'))
            else:
                self.log.info(colors.green_bold(f'Rendering finished'))

            sys.exit(0)

    def list_providers(self):
        self.log.info('Providers:')
        for (name, module, _) in common.get_submodules(providers):
            description = getattr(module, 'Renderer').get_parser().format_help().split('\n').pop(0)
            self.log.info(colors.bold(colors.blue(name)) + ': ' + description)


if __name__ == '__main__':
    pass
