from abc import ABC

from adeploy.common.helpers import get_defaults
from adeploy.common.provider import Provider


class HelmProvider(Provider, ABC):
    def get_chart_dir(self):
        return self.build_dir.joinpath('charts').joinpath(self.name)

    def get_chart_version(self):
        defaults = get_defaults(self.get_defaults_file(), log=self.log)
        return defaults.get('_chart', {}).get('version', None) if defaults else None