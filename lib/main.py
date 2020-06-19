from __future__ import print_function
import sys
import logging
import argparse
import os
import pkgutil

from colorama import init, Style, Fore
from importlib.metadata import version, PackageNotFoundError

from . import steps
from . import common


def main():
    parser = setup_parser()
    args = parser.parse_args()
    setup_logging(args)

    try:
        if args.version:
            try:
                print(version(__name__))
            except PackageNotFoundError:
                print('0.0.0')
            sys.exit(0)

        # Initialize classes for deployment steps
        for (module, action_class) in get_action_classes():
            if action_class.__name__ != steps.__class__.__name__:
                action_class(args, logging.getLogger(f'adeploy.{steps.__class__.__name__}'))

    except common.InputError as e:
        log.error(Fore.RED + Style.BRIGHT + "Input error in module \"%s\": %s" % (module, str(e)))
        sys.exit(1)
    except common.Error as e:
        log.error(Fore.RED + Style.BRIGHT + "Error in module \"%s\": %s" % (module, str(e)))
        sys.exit(1)

    parser.print_help()
    sys.exit(1)


def get_action_classes():
    action_classes = []
    pkgpath = os.path.dirname(steps.__file__)
    for modname in [name for _, name, _ in pkgutil.iter_modules([pkgpath])]:
        if f'lib.steps.{modname}' in sys.modules:
            module = sys.modules[f'lib.steps.{modname}']
            class_name = modname.title()
            action_classes.append((modname, getattr(module, class_name)))

    return action_classes


def setup_parser():
    parser = argparse.ArgumentParser(description='An awesome universal deployment tool for k8s',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-l', '--log', dest='logfile', help="Path to logfile")
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('--version', action="store_true", help="Print version and exit")

    subparsers = parser.add_subparsers()

    for (module, action_class) in get_action_classes():
        setup_parser_method = getattr(action_class, "setup_parser")
        if callable(setup_parser_method):
            setup_parser_method(subparsers.add_parser(module,
                                                      help="Call module \"%s\", type: %s %s --help for more options" % (
                                                      module, sys.argv[0], module)))

    return parser


def setup_logging(args):
    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    if args.logfile:
        logging.basicConfig(level=loglevel, filename=args.logfile,
                            format='%(asctime)s %(levelname)-8s %(name)-10s %(message)s')
    else:
        logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)-8s %(name)-10s %(message)s')

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
