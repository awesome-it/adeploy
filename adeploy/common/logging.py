import logging

from adeploy.common import colors


def setup(args):
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


def get_logger(name: str = None):
    return logging.getLogger(name)