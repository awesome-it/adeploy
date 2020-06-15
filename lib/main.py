from __future__ import print_function
import sys
import logging
import argparse

log = logging.getLogger()


def main():
    args = parse_command_line()
    setup_logging(args)

    sys.exit(0)


def parse_command_line():
    parser = argparse.ArgumentParser(description='An universal deployment tool for k8s deployments',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('arg1', help='A positional arg', metavar='<val1>')
    parser.add_argument('arg2', help='Another positional arg', metavar='<val2>')
    parser.add_argument('-arg3', '--arg3', dest='arg3', help='A non positional arg with default vlaue', default='default')
    parser.add_argument('-l', '--log', dest='logfile', help="Path to logfile")
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    return args


def setup_logging(args):
    if args.verbose:
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