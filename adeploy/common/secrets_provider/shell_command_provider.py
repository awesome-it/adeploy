import subprocess
from logging import Logger

from adeploy.common import colors
from adeploy.common.errors import EmptySecretError
from adeploy.common.logging import get_logger
from adeploy.common.secrets_provider import SecretsProvider


class ShellCommandSecretProvider(SecretsProvider):
    REQUIRED_GOPASS_VERSION = '1.10.0'
    def __init__(self, command: str, logger: Logger):
        if not command:
            raise ValueError('Command cannot be empty')
        self.command = command
        if not logger:
            self.log = get_logger()
        else:
            self.log = logger

    def get_value(self):
        self.log.debug(f'... executing command "{colors.bold(self.command)}"')
        result = subprocess.run(self.command, shell=True, capture_output=True)
        result.check_returncode()

        try:
            result = result.stdout.decode("utf-8")
        except UnicodeDecodeError:
            result = result.stdout
        if not result:
            raise EmptySecretError(f'Cannot create secret: Command "{colors.bold(self.command)}" returned empty result')

        return result