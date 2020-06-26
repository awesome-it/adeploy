import os
import sys
import argparse

from .. import common
from .. import providers
from ..common import colors, RenderError


class Test:
    parser = None

    @staticmethod
    def setup_parser(parser):

        parser.add_argument("--test", default=True, help=argparse.SUPPRESS)

        Test.parser = parser

    def __init__(self, args, test_args, log):
        self.args = args
        self.log = log

        if 'test' in self.args:

            sys.exit(0)


if __name__ == '__main__':
    pass
