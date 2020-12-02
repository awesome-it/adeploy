import os
import subprocess
from logging import Logger
from pathlib import Path
from typing import Union

from adeploy.common import colors
from adeploy.common.args import get_args
from adeploy.common.logging import get_logger


def gopass_get_repos():
    repos = get_args().gopass_repo
    if repos is None or len(repos) == 0:
        repos = os.getenv('ADEPLOY_GOPASS_REPOS', '').split(',')
    return repos


def gopass_get(path: Union[Path, str], log: Logger = None) -> str:

    if not log:
        log = get_logger()

    if not path:
        log.debug('Empty path, skipping call to gopass')
        return ""

    result = None
    for repo in [Path(r) for r in gopass_get_repos()]:

        repo_path = repo.joinpath(path)
        cmd = ['gopass', 'show', '--password', str(repo_path)]

        log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Stop on success
        if not result.returncode:
            break

    # Trigger error on last run (if any)
    result.check_returncode()

    lines = result.stdout.split('\n')
    if len(lines) > 1:
        return lines[-1]

    return result.stdout
