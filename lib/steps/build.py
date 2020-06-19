import sys
import argparse


class Build:

    @staticmethod
    def setup_parser(parser):
        parser.add_argument("--categories", dest="categories", action="store_true", help=argparse.SUPPRESS)

        subparsers = parser.add_subparsers()

        list_categories = subparsers.add_parser("list", help="List available categories (default), type: %s categories list --help for more options" % sys.argv[0])
        list_categories.add_argument("-l", "--list", dest="categories_list", action="store_true", default=True, help=argparse.SUPPRESS)

        pull_categories = subparsers.add_parser("pull", help="Pull categories from the server, type: %s categories pull --help for more options" % sys.argv[0])
        pull_categories.add_argument("-p", "--pull", dest="categories_pull", action="store_true", help=argparse.SUPPRESS)

    def __init__(self, config, log):
        self.config = config
        self.log = log

        if "categories_list" in self.config:
            #self.list()
            sys.exit(0)

        elif "categories_pull" in self.config:
            #self.pull()
            sys.exit(0)

        # List categories by default
        #elif "categories" in self.config:
            #from atimetracker.atimetracker import main
            #sys.argv.append("list")
            #main()


if __name__ == '__main__':
    pass