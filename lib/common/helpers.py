import os
import pkgutil
import sys

from .. import common
from .. import providers


def get_submodules(pkg):
    pkgpath = os.path.dirname(pkg.__file__)
    modules = []
    prefix = pkgpath.split("adeploy")[1][1:].replace("/", ".")
    for modname in [name for _, name, _ in pkgutil.iter_modules([pkgpath])]:
        if f'{prefix}.{modname}' in sys.modules:
            module = sys.modules[f'{prefix}.{modname}']
            class_name = modname.title()
            modules.append((modname, module, getattr(module, class_name) if hasattr(module, class_name) else None))

    return modules


def get_provider(name):
    for (module_name, module, _) in common.get_submodules(providers):
        if name.lower() == module_name.lower():
            return module
    return None