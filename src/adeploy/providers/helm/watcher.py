import argparse
import sys

from .common import HelmProvider


class Watcher(HelmProvider):

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(description='Helm v3 renderer for k8s manifests',
                                         usage=argparse.SUPPRESS)
        return parser

    def parse_args(self, args: dict):
        pass

    def run(self):

        self.log.error(f'Watch mode is not supported by the helm provider...')
        sys.exit(1)
