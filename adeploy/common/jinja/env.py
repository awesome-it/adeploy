from inspect import getmembers, isfunction, getfile
from logging import Logger
from pathlib import Path
from typing import List

import jinja2

import adeploy.common.jinja.globals as globals
import adeploy.common.jinja.filters as filters


def create(pathes: List[str or Path] = None, log: Logger = None, deployment=None, templates_dir=None) -> jinja2.Environment:
    env = jinja2.Environment(
        # This is to load macros from template dir and the parent dir
        loader=jinja2.FileSystemLoader([str(p) for p in pathes]),
        autoescape=jinja2.select_autoescape(['json']),
        # Add support for expressions statements, see https://stackoverflow.com/a/39858522/381166
        extensions=['jinja2.ext.do'],
    )

    # Register filters from common.filters
    for name, func in [f for f in getmembers(filters) if isfunction(f[1])]:
        if log:
            log.debug(f'Registering filter "{name}" from "{getfile(func)}"')
        env.filters[name] = func

    register_globals(env, deployment, log, templates_dir)

    return env


def register_globals(env: jinja2.Environment, deployment=None, log: Logger = None, templates_dir=None):
    for name, func_creator in [f for f in getmembers(globals) if isfunction(f[1])]:

        if '__' not in name:
            continue

        if log:
            log.debug(f'Registering global function "{name}" ' +
                      (f'for deployment "{str(deployment)}" ' if deployment else '') +
                      f'from "{getfile(func_creator)}"')

        env.globals.update(
            {name.split('__')[1]: func_creator(deployment, log=log, env=env, templates_dir=templates_dir)})
