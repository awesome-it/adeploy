import os
import subprocess
import re

from pathlib import Path
from typing import Union
from logging import Logger
from packaging.version import parse as parse_version

from adeploy.common import colors
from adeploy.common.args import get_args
from adeploy.common.errors import InputError
from adeploy.common.logging import get_logger
from adeploy.common.secrets_provider import SecretsProvider



class GopassSecretProvider(SecretsProvider):
    REQUIRED_GOPASS_VERSION = '1.10.0'
    def __init__(self, path: str, logger: Logger, use_cat: bool = True):
        if not path:
            raise ValueError('Path cannot be empty')
        self.path = path
        if not logger:
            self.log = get_logger()
        else:
            self.log = logger

        # Check GoPass version
        gopass_version = self.gopass_get_version()
        if parse_version(gopass_version) < parse_version(GopassSecretProvider.REQUIRED_GOPASS_VERSION):
            raise InputError(
                f'Found gopass version {gopass_version} but version {GopassSecretProvider.REQUIRED_GOPASS_VERSION}+ is required.')

    def get_value(self):
        result = self.gopass_try_repos()
        if result is None:
            raise InputError(f'Cannot find gopass value, did you specify a gopass repo?')

        result.check_returncode()

        if isinstance(result.stdout, (bytes, bytearray)):
            return result.stdout.lstrip();

        else:

            num_lines = len(result.stdout.strip().split("\n"))

            # Strip front/back for single line, strip front for multi-line
            return result.stdout.strip() if num_lines <= 1 else result.stdout.lstrip()

    @staticmethod
    def gopass_get_version():
        result = subprocess.run(['gopass', 'version'], capture_output=True, text=True)
        result.check_returncode()
        version_match = re.match(r"gopass ([^ ]*)", result.stdout.strip())

        if not version_match:
            raise InputError('Could not determine gopass version')

        return version_match.group(1)

    @staticmethod
    def gopass_get_repos() -> [str]:
        repos = [""]

        gopass_repos = get_args().gopass_repo
        if gopass_repos and len(gopass_repos) > 0:
            repos += [r[0] for r in gopass_repos]

        elif os.getenv('ADEPLOY_GOPASS_REPOS', False):
            repos += os.getenv('ADEPLOY_GOPASS_REPOS', '').split(',')

        return repos

    def gopass_try_repos(self) -> subprocess.CompletedProcess:
        result = None
        for repo in [Path(r) for r in GopassSecretProvider.gopass_get_repos()]:
            secret_path = repo.joinpath(self.path)
            result = self.gopass_try(secret_path)

            # Stop on success
            if result and result.returncode == 0 and len(result.stdout.strip()) > 0:
                break

        # Return the last possible result
        return result

    def gopass_try(self,
                   repo_path: Union[Path, str],
                   explicit_pass=False,
                   skip_parsing=True,
                   use_cat: bool = True) -> subprocess.CompletedProcess:
        cmd = ([
                  'gopass',
                  'cat' if use_cat else 'show'
              ]
               + (['-n'] if not use_cat and skip_parsing else [])
               + (['--password'] if not use_cat and explicit_pass else [])
               + [str(repo_path)])
        self.log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
        result = subprocess.run(cmd, capture_output=True)
        self.log.debug(f'... command returned {colors.bold(result.returncode)}')

        # Stop on success
        if result.returncode == 0 and len(result.stdout.strip()) > 0:

            try:
                # Properly handle meta data
                result.stdout = result.stdout.decode('utf-8')
                if result.stdout.startswith('GOPASS-SECRET-1.0'):
                    return self.gopass_try(repo_path, explicit_pass=explicit_pass, use_cat=False, skip_parsing=False)
                if result.stdout.startswith('Password: '):
                    return self.gopass_try(repo_path, explicit_pass=True, use_cat=False, skip_parsing=skip_parsing)

            except UnicodeDecodeError:
                self.log.debug('Decoding failed ... assuming binary data')
                pass

            return result


def gopass_get(path: Union[Path, str], log: Logger = None, use_cat: bool = True) -> str:
    log.warning('gopass_get is deprecated, use GopassSecretProvider instead')
    provider = GopassSecretProvider(path, log, use_cat)
    return provider.get_value()
