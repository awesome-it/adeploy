import os
import subprocess
import re

from logging import Logger
from pathlib import Path
from typing import Union
from packaging.version import parse as parse_version

from adeploy.common import colors
from adeploy.common.args import get_args
from adeploy.common.errors import InputError
from adeploy.common.logging import get_logger


def gopass_get_version():
    result = subprocess.run(['gopass', 'version'], capture_output=True, text=True)
    result.check_returncode()
    version_match = re.match(r"gopass ([^ ]*)", result.stdout.strip())

    if not version_match:
        raise InputError('Could not determine gopass version')

    return version_match.group(1)


def gopass_get_repos() -> [str]:
    repos = [""]

    if os.getenv('ADEPLOY_GOPASS_REPOS', False):
        repos += os.getenv('ADEPLOY_GOPASS_REPOS', '').split(',')
    else:
        repos += get_args().gopass_repo

    return repos


def gopass_get(path: Union[Path, str], log: Logger = None) -> str:

    if not log:
        log = get_logger()

    if not path:
        log.debug('Empty path, skipping call to gopass')
        return ""

    # Check GoPass version
    gopass_required_version = '1.10.0'
    gopass_version = gopass_get_version()
    if parse_version(gopass_version) < parse_version(gopass_required_version):
        raise InputError(f'Found gopass version {gopass_version} but version {gopass_required_version}+ is required.')

    result = gopass_try_repos(path, True, log)
    if not result:
        result = gopass_try_repos(path, False, log)

    # Trigger error on last run (if any)
    result.check_returncode()

    return result.stdout.lstrip()


def gopass_try_repos(path: Union[Path, str], explicit_pass = True, log: Logger = None) -> subprocess.CompletedProcess:

    result = None
    for repo in [Path(r) for r in gopass_get_repos()]:

        repo_path = repo.joinpath(path)
        cmd = ['gopass', 'show'] + (['--password'] if explicit_pass else []) + [str(repo_path)]
        log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Stop on success
        if not result.returncode and len(result.stdout.strip()) > 0:
            break

    return result