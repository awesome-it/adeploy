import sys
from abc import ABC, abstractmethod
from typing import final

from adeploy.common import colors
from adeploy.common.logging import get_logger

class SecretsProvider(ABC):
    """
    Abstract class for a secret provider.
    A secret provider is an object that can provide a secret value.
    It stores the information needed to retrieve the secret value - e.g. from a password manager.
    It provides the ability to reference a secret without the need of actually decrypting it.
    """

    __created_secrets = {}

    def __init__(self, name, log, ltrim: bool = False, rtrim: bool = False):
        if not log:
            self.log = get_logger()
        else:
            self.log = log
        self.ltrim = ltrim
        self.rtrim = rtrim
        if not name:
            name = self.get_id()
        if not name in self.__created_secrets:
            self.__created_secrets[name] = self
        else:
            self.log.error(f'Secret "{colors.bold(name)}" of tye {self.__class__} already exists')
            self.log.error(f'Reference the existing secret instead of creating a new one')
            sys.exit(1)

    def __str__(self):
        """
        Return the secret value.
        This is used by Jinja to render the object.
        """
        return self.get_value()

    @final
    def get_value(self, log=None) -> str:
        """
        Return the secret value.
        This is used by Jinja to render the object.
        """
        if not log:
            log = self.log
        value = self._get_value(log)
        if self.ltrim:
            value = value.lstrip()
        else:
            if value != value.lstrip():
                self.log.warning(f'"{colors.bold(self.get_id())}" returned leading whitespace')
        if self.rtrim:
            value = value.rstrip()
        else:
            if value != value.rstrip():
                self.log.warning(f'"{colors.bold(self.get_id())}" returned trailing whitespace')
        return value

    @abstractmethod
    def _get_value(self, log) -> str:
        """
        Return the secret value.
        Used to generate the k8s secret API object and by __str__ to render the object.
        """
        pass

    @abstractmethod
    def get_id(self) -> str:
        """
        Return the identifier of the secret.
        This is used to create the k8s secrets name and to reference it from deployments.
        The identifier must be unique for each secret and must not depend on the secret value.
        """
        pass