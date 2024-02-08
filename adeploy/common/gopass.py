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

    gopass_repos = get_args().gopass_repo
    if gopass_repos and len(gopass_repos) > 0:
        repos += [r[0] for r in gopass_repos]

    elif os.getenv('ADEPLOY_GOPASS_REPOS', False):
        repos += os.getenv('ADEPLOY_GOPASS_REPOS', '').split(',')

    return repos


def gopass_get(path: Union[Path, str], log: Logger = None, use_cat: bool = True) -> str:
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

    result = gopass_try_repos(path, log=log, use_cat=use_cat)
    if result is None:
        raise InputError(f'Cannot find gopass value, did you specify a gopass repo?')

    result.check_returncode()

    if isinstance(result.stdout, (bytes, bytearray)):
        return result.stdout.lstrip();

    else:

        num_lines = len(result.stdout.strip().split("\n"))

        # Strip front/back for single line, strip front for multi-line
        return result.stdout.strip() if num_lines <= 1 else result.stdout.lstrip()


def gopass_try_repos(path: Union[Path, str], log: Logger = None, use_cat: bool = True) -> subprocess.CompletedProcess:
    result = None
    for repo in [Path(r) for r in gopass_get_repos()]:
        result = gopass_try(repo.joinpath(path), use_cat=use_cat, log=log)

        # Stop on success
        if result and result.returncode == 0 and len(result.stdout.strip()) > 0:
            break

    # Return the last possible result
    return result


def gopass_try(repo_path: Union[Path, str], explicit_pass=False, skip_parsing=True, use_cat: bool = True,
               log: Logger = None) -> subprocess.CompletedProcess:
    cmd = ['gopass', 'cat' if use_cat else 'show'] + (['-n'] if not use_cat and skip_parsing else []) + (
        ['--password'] if not use_cat and explicit_pass else []) + [str(repo_path)]
    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True)
    log.debug(f'... command returned {colors.bold(result.returncode)}')

    # Stop on success
    if result.returncode == 0 and len(result.stdout.strip()) > 0:

        try:
            # Properly handle meta data
            result.stdout = result.stdout.decode('utf-8')
            if result.stdout.startswith('GOPASS-SECRET-1.0'):
                return gopass_try(repo_path, explicit_pass=explicit_pass, use_cat=False, skip_parsing=False, log=log)
            if result.stdout.startswith('Password: '):
                return gopass_try(repo_path, explicit_pass=True, use_cat=False, skip_parsing=skip_parsing, log=log)

        except UnicodeDecodeError:
            log.debug('Decoding failed ... assuming binary data')
            pass

        return result
