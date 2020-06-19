import sys
import argparse

from colorama import init, Style, Fore
from .. import common
from .. import providers


class Render:

    @staticmethod
    def setup_parser(parser):
        parser.add_argument("--render", dest="render", default=True, action="store_true", help=argparse.SUPPRESS)
        parser.add_argument("--src-dir", dest="src_dir", help="Directory containing deployment sources "
                                                              "i.e. Kustomize or Helm Chart",
                            required='--providers' not in sys.argv)
        parser.add_argument("--type", dest="provider_type",
                            help="The provider type to use, type --providers to get a list "
                                 "of supported providers.", default=None)
        parser.add_argument("--providers", dest="list_providers", action="store_true",
                            help="A list of supported providers")

    def __init__(self, args, render_args, log):
        self.args = args
        self.log = log

        if 'render' in self.args:

            if self.args.list_providers:
                self.list_providers()
                sys.exit(0)

            if self.args.provider_type is None:
                log.error(f'{Fore.RED}'
                          f'No provider specified. Please specify a provider type using "--type". '
                          f'{Fore.RESET}'
                          f'Type "--providers" to get a list of supported providers.')
                sys.exit(1)

            # Load renderer from provider
            provider = common.get_provider(self.args.provider_type)

            if provider is None:
                log.error(f'{Fore.RED}'
                          f'Cannot find supported provider type "{self.args.provider_type}". '
                          f'{Fore.RESET}'
                          f'Type "--providers" to get a list of supported providers.')
                sys.exit(1)

            renderer = getattr(provider, 'Renderer')(self.args, self.log)
            render_args = renderer.get_parser().parse_args(render_args)

            self.log.info(f'{Fore.BLUE}Rendering{Fore.RESET} '
                          f'"{Style.BRIGHT}{self.args.src_dir}{Style.RESET_ALL}" '
                          f'in "{Style.BRIGHT}{self.args.build_dir}{Style.RESET_ALL}" '
                          f'using provider "{Style.BRIGHT}{self.args.provider_type}{Style.RESET_ALL}" ...')

            if renderer.run(src_dir=self.args.src_dir, **vars(render_args)):
                sys.exit(0)

            sys.exit(1)

    def list_providers(self):
        self.log.info('Providers:')
        for (name, module, _) in common.get_submodules(providers):
            renderer = getattr(module, 'Renderer')(self.args, self.log)
            description = renderer.get_parser().format_help().split('\n')[2]
            self.log.info(f'{Style.BRIGHT}{Fore.BLUE}{name}{Style.RESET_ALL}{Fore.RESET}: {description}')

if __name__ == '__main__':
    pass
