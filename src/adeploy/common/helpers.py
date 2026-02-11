import collections.abc
import logging
import os
import pkgutil
import subprocess
from pathlib import PosixPath

import yaml

from collections import namedtuple
from adeploy import providers

import adeploy.common.colors as colors
import adeploy.common.jinja.env as jinja_env


def get_submodules(pkg):
    modules = []
    for module_finder, name, ispkg in pkgutil.iter_modules([os.path.dirname(pkg.__file__)]):
        module_spec = module_finder.find_spec(name)
        module = module_spec.loader.load_module()
        class_name = list(filter(lambda m: module.__name__ == m.lower(), dir(module)))[0]
        modules.append((module, class_name))

    return modules


def get_provider(name):
    return get_providers().get(name, None)


def get_providers() -> dict:
    found = {}
    for module_finder, name, ispkg in pkgutil.iter_modules([os.path.dirname(providers.__file__)]):
        if ispkg:
            module_spec = module_finder.find_spec(name)
            module = module_spec.loader.load_module()
            found[name] = namedtuple('Provider', 'renderer tester deployer watcher')(
                    renderer=getattr(module, 'Renderer'),
                    tester=getattr(module, 'Tester'),
                    deployer=getattr(module, 'Deployer'),
                    watcher=getattr(module, 'Watcher')
                )
    return found


def get_defaults(defaults_files: PosixPath | list[PosixPath], deployment=None, log=None, template_values=None):
    if type(defaults_files) is PosixPath:
        files = [defaults_files]
    else:
        files = defaults_files
    defaults = {}
    for file in files:
        logging.debug(f'Loading defaults from {file}')
        env = jinja_env.create([file.parent], deployment=deployment, log=log)
        # Make best to load defaults
        template_values_default = {
            'name': deployment.name if deployment else 'undefined',
            'namespace': deployment.namespace if deployment else 'undefined',
        }
        values = yaml.load(env.get_template(file.name).render(template_values if template_values else template_values_default), Loader=yaml.FullLoader)
        defaults.update(values)
    return defaults


def run_command(log, cmd) -> subprocess.CompletedProcess:
    # Convert possible Paths to strings
    cmd = [str(c) for c in cmd]
    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()
    return result


def dict_update_recursive(d: dict, u: dict) -> dict:
    if u is not None:
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                sub = {}
                if d and k in d and d[k] and len(d[k]) > 0:
                    sub = d[k]
                d[k] = dict_update_recursive(sub, v)
            # We don't merge lists! List will be overwritten completely.
            #elif isinstance(v, list):
            #    d[k] = (d[k] if k in d else []) + v
            else:
                d[k] = v
    return d