from __future__ import print_function

import logging
import os
import sys

from colorama import init
from importlib_metadata import version, PackageNotFoundError

from . import steps
from .common import colors
from .common.args import parse, setup_parser
from .common.errors import InputError, Error
from .common.helpers import get_provider, get_submodules, get_providers
from .common.logging import setup as setup_logging, get_logger
from .common.kubectl import kubectl_init

log = get_logger('adeploy')


def main():

    if not os.getenv('CI', False):
        init(autoreset=True)

    parser = setup_parser()
    args, unknown_args = parse(parser)
    setup_logging(args)
    kubectl_init(args)
    module = None

    try:

        if args.list_providers:
            list_providers()
            sys.exit(0)

        if args.version:
            try:
                print(version('adeploy'))
            except PackageNotFoundError:
                print('0.0.0')
            sys.exit(0)

        # Load renderer from provider
        provider = get_provider(args.provider)

        if provider is None:
            log.error(colors.red(f'Cannot find supported provider type "{args.provider}". ') +
                      f'Type "--providers" to get a list of supported providers.')
            sys.exit(1)

        # Execute steps
        for (module, class_name) in get_submodules(steps):
            getattr(module, class_name)(provider, args, unknown_args, logging.getLogger(f'adeploy.{class_name}'))

    except InputError as e:
        log.error(colors.red(colors.bold(f'Input error in module "{module}": {str(e)}')))
        sys.exit(1)
    except Error as e:
        log.error(colors.red(colors.bold(f'Error in module "{module}": {str(e)}')))
        sys.exit(1)

    parser.print_help()
    sys.exit(1)


def list_providers():
    log.info(colors.bold('Providers:'))
    for name, provider in get_providers().items():
        description = provider.renderer.get_parser().format_help().split('\n').pop(0)
        log.info(colors.bold(colors.blue(name)) + ': ' + description)
