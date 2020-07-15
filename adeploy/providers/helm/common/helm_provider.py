from abc import ABC

from adeploy.common import Provider, Path


class HelmProvider(Provider, ABC):
    def get_chart_dir(self):
        return self.build_dir.joinpath('charts').joinpath(self.name)