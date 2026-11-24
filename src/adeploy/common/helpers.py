import collections.abc
import importlib
import logging
import pkgutil
import subprocess
from collections import namedtuple
from pathlib import PosixPath

import yaml

import adeploy.common.jinja.env as jinja_env
from adeploy import providers
from adeploy.common import colors

_log = logging.getLogger(__name__)


def get_submodules(pkg):
    modules = []
    for _, name, ispkg in _iter_submodules(pkg):
        if ispkg:
            continue
        module = importlib.import_module(f"{pkg.__name__}.{name}")
        class_name = next(
            (m for m in dir(module) if m.lower() == name and m[0].isupper()),
            None,
        )
        if class_name is None:
            _log.debug(f'Skipping submodule "{name}" without matching step class')
            continue
        module.__name__ = name
        modules.append((module, class_name))

    return modules


def get_provider(name):
    return get_providers().get(name, None)


def get_providers() -> dict:
    found = {}
    for _, name, ispkg in _iter_submodules(providers):
        if ispkg:
            module = importlib.import_module(f"{providers.__name__}.{name}")
            found[name] = namedtuple("Provider", "renderer tester deployer watcher")(
                renderer=module.Renderer,
                tester=module.Tester,
                deployer=module.Deployer,
                watcher=module.Watcher,
            )
    return found


def _iter_submodules(pkg):
    """List direct submodules/packages of a package.

    Uses ``pkgutil.iter_modules`` over the package's ``__path__`` to discover
    candidates; each name is later resolved through ``importlib``.
    """
    return pkgutil.iter_modules(pkg.__path__)


def get_defaults(
    defaults_files: PosixPath | list[PosixPath],
    deployment=None,
    log=None,
    template_values=None,
):
    if type(defaults_files) is PosixPath:
        files = [defaults_files]
    else:
        files = defaults_files
    defaults = {}
    for file in files:
        _log.debug(f"Loading defaults from {file}")
        env = jinja_env.create([file.parent], deployment=deployment, log=log)
        # Make best to load defaults
        template_values_default = {
            "name": deployment.name if deployment else "undefined",
            "namespace": deployment.namespace if deployment else "undefined",
        }
        values = yaml.load(
            env.get_template(file.name).render(
                template_values if template_values else template_values_default
            ),
            Loader=yaml.FullLoader,
        )
        defaults.update(values)
    return defaults


def run_command(log, cmd) -> subprocess.CompletedProcess:
    # Convert possible Paths to strings
    cmd = [str(c) for c in cmd]
    log.debug(f"Executing command {colors.bold(' '.join(cmd))}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    result.check_returncode()
    return result


def dict_update_recursive(d: dict, u: dict) -> dict:
    if u is not None:
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                sub = {}
                if d and k in d and isinstance(d[k], collections.abc.Mapping):
                    sub = d[k]
                d[k] = dict_update_recursive(sub, v)
            # We don't merge lists! List will be overwritten completely.
            # elif isinstance(v, list):
            #    d[k] = (d[k] if k in d else []) + v
            else:
                d[k] = v
    return d
