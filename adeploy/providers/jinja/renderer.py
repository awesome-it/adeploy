import os
import shutil
import argparse


class Renderer:
    def __init__(self, args, log):
        self.log = log
        self.args = args

    def get_parser(self):
        parser = argparse.ArgumentParser(description='Jinja renderer for k8s manifests written in Jinja',
                                         usage=argparse.SUPPRESS)

        parser.add_argument("--var", dest="var", help="Testing purpose")

        return parser

    def run(self, src_dir, var):

        #if not os.path.exists(seelf.args.build_dir):
        #    os.mkdir(self.args.build_dir)

        #shutil.copy(source_dir, self.args.build_dir)
        #print(src_dir)
        #print(var)

        return True