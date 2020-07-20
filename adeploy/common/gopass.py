import subprocess
from logging import Logger
from pathlib import Path

from adeploy.common import colors
from adeploy.common.args import get_args
from adeploy.common.logging import get_logger


def gopass_get(path: Path, log: Logger = None):
    prefix = Path(get_args().gopass_prefix)
    path = prefix.joinpath(path)

    cmd = ['gopass', str(path)]

    if not log:
        log = get_logger()

    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()

    lines = result.stdout.split('\n')
    if len(lines) > 1 and lines[1] == '--':
        return lines[0]

    return result.stdout