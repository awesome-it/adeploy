import argparse
import sys
from pathlib import Path

from adeploy import steps
from adeploy.common import colors
from adeploy.common.helpers import get_submodules

__args: argparse.Namespace
__unknown_args: argparse.Namespace


def get_args():
    global __args
    return __args


def parse(parser: argparse.ArgumentParser):
    global __args, __unknown_args

    # Pass --help to a provider if a provider was already specified
    if ('--help' in sys.argv or '-h' in sys.argv) and ('--provider' in sys.argv or '-p' in sys.argv):
        real_args = list(filter(lambda x: x not in ['--help', '-h'], sys.argv))
        args, unknown_args = parser.parse_known_args(real_args[1:])
        unknown_args.append('--help')
    else:
        args, unknown_args = parser.parse_known_args()

    __args = args
    __unknown_args = unknown_args

    return args, unknown_args


def setup_parser():
    parser = argparse.ArgumentParser(description='An awesome universal deployment tool for k8s',
                                     usage=colors.bold(
                                         f'adeploy -p {colors.blue("provider")} {colors.gray("[optional args ...]")} '
                                         f'{colors.blue("build-step")} {colors.gray("[optional build args ...]")} '
                                         f'{colors.blue("src_dir")} [{colors.blue("src_dir")} ...]'))

    parser.add_argument('-l', '--log', dest='logfile', help='Path to logfile')

    parser.add_argument('-d', '--debug', action='store_true')

    parser.add_argument('-s', '--skip-colors', dest='skip_colors', action='store_true')

    parser.add_argument('-f', '--force', dest='force', action='store_true')

    parser.add_argument('-p', '--provider', dest='provider',
                        help='The provider to use, type --providers to get a list of supported providers.',
                        required='--providers' not in sys.argv and '--version' not in sys.argv)

    parser.add_argument('--providers', dest='list_providers', action='store_true',
                        help='A list of supported providers')

    parser.add_argument('-n', '--name', dest="deployment_name", default=None,
                        help='Specify a deployment name. This will overwrite deployment name derived from repo dir')

    parser.add_argument('--adeploy-dir', dest='adeploy_dir',
                        help='Configuration directory for adeploy', default=Path.home().joinpath('.adeploy'),
                        metavar='adeploy_dir', type=Path)

    parser.add_argument('--build-dir', dest='build_dir',
                        help='Build directory for output', default='./build', metavar='build_dir')

    parser.add_argument('--defaults', dest='defaults_path', default='defaults.yml',
                        help='YML file or directory containing <deployment_name>.yml with default variables. '
                             'Relative to source dirs.')

    parser.add_argument('--namespaces', dest='namespaces_dir', default='namespaces',
                        help='Directory containing namespaces and variables for deployments')

    parser.add_argument('--recreate-secrets', dest='recreate_secrets', action='store_true',
                        help='Force to re-create secrets. This might invoke a password store to retrieve secrets.')

    parser.add_argument('--filter-namespace', dest='filters_namespace', nargs='+', action='append',
                        help='Only include specified namespace. Argument can be specified multiple times.')

    parser.add_argument('--filter-release', dest='filters_release', nargs='+', action='append',
                        help='Only include specified deployment release i.e. "prod", "testing". '
                             'Argument can be specified multiple times.')

    parser.add_argument('--show-configs', dest='show_configs', action='store_true', default=False,
                        help='Print out rendered namespace configurations and quit.')

    parser.add_argument('--gopass-repo', dest='gopass_repo', nargs='+', action='append',
                        help='Gopass repo names, where the awesome secrets are stored. This argument can be specified '
                             'multiple times for multiple Gpoass repos. This params can also be specified by the env '
                             'var ADEPLOY_GOPASS_REPOS where comma separated list of Gopass repo names is expected. '
                             'If args are specified, these take precedence and the env var is ignored.')

    parser.add_argument('--version', action='store_true', help='Print version and exit')

    subparsers = parser.add_subparsers(title=f'Available build steps', metavar=colors.bold('build-steps'))

    for (module, class_name) in get_submodules(steps):
        module_name = module.__name__
        subparser = subparsers.add_parser(module_name,
                                          help=f'Call module "{module_name}", '
                                               f'type: {sys.argv[0]} {module_name} --help for more options')
        subparser.add_argument("src_dirs",
                               help="Directory containing deployment sources",
                               nargs='*', default='.', metavar='src_dir')

        if module_name == 'config':
            subparser.add_argument("-o,--out", dest='config_out', default="",
                                   help="Filename to store the rendered namespace configurations as JSON.")

        subparser.add_argument(f'--{module_name}', default=True, help=argparse.SUPPRESS)

    return parser
