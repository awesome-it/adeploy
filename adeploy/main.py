from __future__ import print_function

import argparse
import logging
import sys

from colorama import init
from importlib_metadata import version, PackageNotFoundError

from . import common
from . import steps
from .common import colors

log = logging.getLogger('adeploy')


def main():
    init(autoreset=True)

    parser = setup_parser()

    # Pass --help to a provider if a provider was already specified
    if ('--help' in sys.argv or '-h' in sys.argv) and ('--provider' in sys.argv or '-p' in sys.argv):
        real_args = list(filter(lambda x: x not in ['--help', '-h'], sys.argv))
        args, unknown_args = parser.parse_known_args(real_args[1:])
        unknown_args.append('--help')
    else:
        args, unknown_args = parser.parse_known_args()

    setup_logging(args)
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
        provider = common.get_provider(args.provider)

        if provider is None:
            log.error(colors.red(f'Cannot find supported provider type "{args.provider}". ') +
                      f'Type "--providers" to get a list of supported providers.')
            sys.exit(1)

        # Execute steps
        for (module, class_name) in common.get_submodules(steps):
            getattr(module, class_name)(provider, args, unknown_args, logging.getLogger(f'adeploy.{class_name}'))

    except common.InputError as e:
        log.error(colors.red(colors.bold(f'Input error in module "{module}": {str(e)}')))
        sys.exit(1)
    except common.Error as e:
        log.error(colors.red(colors.bold(f'Error in module "{module}": {str(e)}')))
        sys.exit(1)

    parser.print_help()
    sys.exit(1)


def setup_parser():
    parser = argparse.ArgumentParser(description='An awesome universal deployment tool for k8s',
                                     usage=colors.bold(
                                         f'adeploy -p {colors.blue("provider")} {colors.gray("[optional args ...]")} {colors.blue("build-step")} {colors.gray("[optional build args ...]")} {colors.blue("src_dir")} [{colors.blue("src_dir")} ...]'))

    parser.add_argument('-l', '--log', dest='logfile', help='Path to logfile')

    parser.add_argument('-d', '--debug', action='store_true')

    parser.add_argument('-s', '--skip-colors', dest='skip_colors', action='store_true')

    parser.add_argument('-p', '--provider', dest='provider',
                        help='The provider to use, type --providers to get a list of supported providers.',
                        required='--providers' not in sys.argv and '--version' not in sys.argv)

    parser.add_argument('--providers', dest='list_providers', action='store_true',
                        help='A list of supported providers')

    parser.add_argument('-n', '--name', dest="deployment_name", default=None,
                        help='Specify a deployment name. This will overwrite deployment name derived from repo dir')

    parser.add_argument('--build-dir', dest='build_dir',
                        help='Build directory for output', default='./build', metavar='build_dir')

    parser.add_argument('--defaults', dest='defaults_file', default='defaults.yml',
                        help='YML file with default variables. Relative to source dirs.')

    parser.add_argument('--filter-namespace', dest='filters_namespace', nargs='*',
                        help='Only include specified namespace. Argument can be specified multiple times.')

    parser.add_argument('--filter-release', dest='filters_release', nargs='*',
                        help='Only include specified deployment release i.e. "prod", "testing". '
                             'Argument can be specified multiple times.')

    parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                        help='Directory containing namespaces and variables for deployments')

    parser.add_argument('--version', action='store_true', help='Print version and exit')

    subparsers = parser.add_subparsers(title=f'Available build steps', metavar=colors.bold('build-steps'))

    for (module, class_name) in common.get_submodules(steps):
        module_name = module.__name__
        subparser = subparsers.add_parser(module_name,
                                          help=f'Call module "{module_name}", '
                                               f'type: {sys.argv[0]} {module_name} --help for more options')
        subparser.add_argument("src_dirs",
                               help="Directory containing deployment sources i.e. Kustomize or Helm Chart",
                               nargs='*', default='.', metavar='src_dir')
        subparser.add_argument(f'--{module_name}', default=True, help=argparse.SUPPRESS)

    return parser


def setup_logging(args):
    colors.skip_colors(args.skip_colors)

    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    if args.logfile:
        logging.basicConfig(level=loglevel, filename=args.logfile,
                            format='%(asctime)s %(levelname)-8s %(name)-10s %(message)s')
    else:
        logging.basicConfig(level=loglevel,
                            format=f'%(asctime)s %(levelname)-8s ' + colors.bold('%(name)-10s') + ' %(message)s')

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def list_providers():
    log.info(colors.bold('Providers:'))
    for name, provider in common.get_providers().items():
        description = provider.renderer.get_parser().format_help().split('\n').pop(0)
        log.info(colors.bold(colors.blue(name)) + ': ' + description)
