import glob
import os
import yaml
from pathlib import Path
from adeploy.common import colors


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


def load_deployments(log, src_dir, namespaces_dir, deployment_name, defaults=None, extensions=None):

    if defaults is None:
        defaults = {}

    if extensions is None:
        extensions = ['yaml', 'yml']
    if not os.path.isabs(namespaces_dir):
        namespaces_dir = f'{src_dir}/{namespaces_dir}'

    log.debug(f'Scanning for deployment variables in "{namespaces_dir}/*/*.({"|".join(extensions)})" ...')

    # Structure 1: namespaces / <namespace_name> / <deployment_variant>.yml
    # Structure 2: instances / <namespace_name> / <deployment_name> / <deployment_variant>.yml

    deployments = []

    for ns in [d for d in os.listdir(namespaces_dir) if os.path.isdir(os.path.join(namespaces_dir, d))]:

        # Structure 2
        deployment_dir = os.path.join(namespaces_dir, ns, deployment_name)
        if not os.path.isdir(deployment_dir):
            # Structure 1
            deployment_dir = os.path.join(namespaces_dir, ns)

        for ext in extensions:
            for deployment_variant_config in glob.glob(f'{deployment_dir}/*.{ext}'):
                deployment_variant = Path(deployment_variant_config).stem
                log.debug(f'... found deployment "{colors.bold(deployment_name)}", '
                               f'variant "{colors.bold(deployment_variant)}, '
                               f'namespace "{colors.bold(ns)}" '
                               f'in "{deployment_variant_config}" ')

                deployment = Deployment(deployment_name, deployment_variant, ns)
                deployment.load_config(deployment_variant_config, defaults=defaults)
                deployments.append(deployment)

    return deployments


def get_deployment_name(src_dir):
    return os.path.basename(src_dir)
