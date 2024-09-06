from abc import ABC, abstractmethod


class SecretsProvider(ABC):

    @abstractmethod
    def get_value(self):
        pass