import yaml

from adeploy.common import dict_update_recursive


class Deployment:
    name: str
    release: str
    namespace: str
    config: dict

    def __init__(self, name: str, release: str, namespace: str):
        self.name = name
        self.release = release
        self.namespace = namespace

    def __repr__(self):
        return f'{self.namespace}/{self.name}-{self.release}'

    def load_config(self, config_path: str, defaults: dict = None):
        if not defaults:
            defaults = {}

        self.config = {}
        self.config.update(defaults)
        self.config = dict_update_recursive(self.config, yaml.load(open(config_path), Loader=yaml.FullLoader))

        return self.config
