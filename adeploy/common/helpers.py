import collections.abc
import os
import pkgutil
import subprocess
from collections import namedtuple

import yaml

from adeploy import providers
from . import colors


def get_submodules(pkg):
    modules = []
    for module_finder, name, ispkg in pkgutil.iter_modules([os.path.dirname(pkg.__file__)]):
        module = module_finder.find_module(name).load_module(name)
        class_name = dir(module)[0]
        modules.append((module, class_name))

    return modules


def get_provider(name):
    return get_providers().get(name, None)


def get_providers() -> dict:
    found = {}
    for module_finder, name, ispkg in pkgutil.iter_modules([os.path.dirname(providers.__file__)]):
        if ispkg:
            module = module_finder.find_module(name).load_module(name)
            found[name] = namedtuple('Provider', 'renderer tester deployer')(
                renderer=getattr(module, 'Renderer'),
                tester=getattr(module, 'Tester'),
                deployer=getattr(module, 'Deployer')
            )

    return found


def run_command(log, cmd) -> subprocess.CompletedProcess:
    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()
    return result


def load_defaults(log, src_dir, defaults_file):
    defaults_file = defaults_file
    if not os.path.isabs(defaults_file):
        defaults_file = f'{src_dir}/{defaults_file}'

    log.debug(f'Loading defaults from "{defaults_file}" ...')
    return yaml.load(open(defaults_file), Loader=yaml.FullLoader)


def dict_update_recursive(d: dict, u: dict) -> dict:
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = dict_update_recursive(d.get(k, {}), v)
        else:
            d[k] = v
    return d
