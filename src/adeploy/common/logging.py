import logging

from adeploy.common import colors


def setup(args):
    colors.skip_colors(args.skip_colors)

    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    if args.logfile:
        logging.basicConfig(level=loglevel, filename=args.logfile, format=get_log_format(args, loglevel))
    else:
        logging.basicConfig(level=loglevel, format=get_log_format(args, loglevel))

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str = None):
    return logging.getLogger(name)


def get_log_format(args, loglevel):

    if args.logfile:
        return '%(asctime)s %(levelname)-8s %(name)s %(message)s'

    if loglevel == logging.DEBUG:
        return '%(levelname)-8s ' + colors.bold('%(name)s') + ' %(message)s'

    return colors.bold('%(name)s') + ' %(message)s'