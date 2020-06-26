import yaml


class Deployment:

    name: str
    variant: str
    namespace: str
    config: dict

    def __init__(self, name: str, variant: str, namespace: str):

        self.name = name
        self.variant = variant
        self.namespace = namespace

    def __repr__(self):
        return f'{self.namespace}/{self.name}-{self.variant}'

    def load_config(self, config_path: str, defaults: dict = None):

        if not defaults:
            defaults = {}

        self.config = {}
        self.config.update(defaults)
        self.config.update(yaml.load(open(config_path), Loader=yaml.FullLoader))

        return self.config
