import subprocess
import sys
from logging import Logger

from adeploy.common import colors
from adeploy.common.secrets_provider.provider import SecretsProvider


class ShellCommandSecretProvider(SecretsProvider):
    """
    A secret provider that provides a secret from a shell command.
    The secret is retrieved from the command output. 
    The command is executed upon first value access and the result is stored in memory.
    A ShellCommandSecretProvider object will return the same value for subsequent calls to get_value().
    """
    def __init__(self, command: str, log: Logger, ltrim: bool = False, rtrim: bool = False):
        self.__value = None
        if not command:
            raise ValueError('Command cannot be empty')
        self.command = command
        super().__init__(name=command, log=log, ltrim=ltrim, rtrim=rtrim)

    def get_id(self):
        return self.command

    def _get_value(self, log: Logger) -> str:
        if self.__value:
            return self.__value
        
        log.debug(f'... executing command "{colors.bold(self.command)}"')
        result = subprocess.run(self.command, shell=True, capture_output=True)
        result.check_returncode()

        try:
            result = result.stdout.decode("utf-8")
        except UnicodeDecodeError:
            result = result.stdout
        if not result:
            log.error(f'Command "{colors.bold(self.command)}" returned empty result')
            sys.exit(1)
        self.__value = result
        return self.__value
