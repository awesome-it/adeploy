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
from adeploy.common.secrets_provider.provider import SecretsProvider



class GopassSecretProvider(SecretsProvider):
    """
    A secret provider that provides a secret from gopass.
    The secret is retrieved from gopass using the path.
    The path is searched in the gopass repositories in the order they are defined
    in the environment variable ADEPLOY_GOPASS_REPOS or the command line argument --gopass-repo.
    """
    REQUIRED_GOPASS_VERSION = '1.10.0'
    def __init__(self, path: str, log: Logger, use_cat: bool = True):
        """
        Initialize the GopassSecretProvider.
        :param path: The path to the secret in gopass.
        :param log: The logger to use.
        :param use_cat: Use the gopass cat command instead of show.
        """
        super().__init__(log)
        if not path:
            raise ValueError('Path cannot be empty')
        self.path = path
        self.use_cat = use_cat

        # Check GoPass version
        gopass_version = self.gopass_get_version()
        if parse_version(gopass_version) < parse_version(GopassSecretProvider.REQUIRED_GOPASS_VERSION):
            raise InputError(
                f'Found gopass version {gopass_version} but version {GopassSecretProvider.REQUIRED_GOPASS_VERSION}+ is required.')

    def get_id(self):
        return self.path

    def _get_value(self, log: Logger = None) -> str:
        if not log:
            log = self.log
        result = self.gopass_try_repos(log)
        if result is None:
            raise InputError(f'Cannot find gopass value for {self.path} in repos {self.gopass_get_repos()}.')

        result.check_returncode()

        if isinstance(result.stdout, (bytes, bytearray)):
            return result.stdout.lstrip()
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

    def gopass_try_repos(self, log: Logger) -> subprocess.CompletedProcess:
        result = None
        for repo in [Path(r) for r in GopassSecretProvider.gopass_get_repos()]:
            secret_path = repo.joinpath(self.path)
            result = self.gopass_try(repo_path=secret_path, use_cat=self.use_cat, log=log)

            # Stop on success
            if result and result.returncode == 0 and len(result.stdout.strip()) > 0:
                break

        # Return the last possible result
        return result

    def gopass_try(self,
                   repo_path: Union[Path, str],
                   log: Logger,
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
        log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
        result = subprocess.run(cmd, capture_output=True)
        log.debug(f'... command exited with return code {colors.bold(result.returncode)}')

        # Stop on success
        if result.returncode == 0 and len(result.stdout.strip()) > 0:

            try:
                # Properly handle meta data
                result.stdout = result.stdout.decode('utf-8')
                if result.stdout.startswith('GOPASS-SECRET-1.0'):
                    return self.gopass_try(repo_path=repo_path, log=log, explicit_pass=explicit_pass,
                                           use_cat=False, skip_parsing=False)
                if result.stdout.startswith('Password: '):
                    return self.gopass_try(repo_path=repo_path, log=log, explicit_pass=True,
                                           use_cat=False, skip_parsing=skip_parsing)

            except UnicodeDecodeError:
                log.debug('Decoding failed ... assuming binary data')
                pass

            return result
