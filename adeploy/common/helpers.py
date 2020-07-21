import collections.abc
import os
import pkgutil
import subprocess
from collections import namedtuple

from adeploy import providers
from adeploy.common import colors


def get_submodules(pkg):
    modules = []
    for module_finder, name, ispkg in pkgutil.iter_modules([os.path.dirname(pkg.__file__)]):
        module = module_finder.find_module(name).load_module(name)
        class_name = list(filter(lambda m: module.__name__ == m.lower(), dir(module)))[0]
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
    # Convert possible Pathes to strings
    cmd = [str(c) for c in cmd]
    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()
    return result


def dict_update_recursive(d: dict, u: dict) -> dict:
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = dict_update_recursive(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k] = (d[k] if k in d else []) + v
        else:
            d[k] = v
    return d