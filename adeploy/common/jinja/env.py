from inspect import getmembers, isfunction, getfile
from logging import Logger
from typing import List

import jinja2

from . import globals
from . import filters
from .. import Deployment


def create(pathes: List[str] = None, log: Logger = None):
    env = jinja2.Environment(
        # This is to load macros from template dir and the parent dir
        loader=jinja2.FileSystemLoader(pathes),
        autoescape=jinja2.select_autoescape(['json']),
        # Add support for expressions statements, see https://stackoverflow.com/a/39858522/381166
        extensions=['jinja2.ext.do'],
    )

    # Register filters from common.filters
    for name, func in [f for f in getmembers(filters) if isfunction(f[1])]:
        if log:
            log.debug(f'Registering filter "{name}" from "{getfile(func)}"')
        env.filters[name] = func

    return env


def register_globals(env: jinja2.Environment, deployment: Deployment, log: Logger = None):
    for name, func_creator in [f for f in getmembers(globals) if isfunction(f[1])]:

        if '__' not in name:
            continue

        if log:
            log.debug(f'Registering global function "{name}" '
                      f'for deployment "{str(deployment)}" '
                      f'from "{getfile(func_creator)}"')

        env.globals.update({name.split('__')[1]: func_creator(deployment)})
