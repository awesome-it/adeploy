import secrets
import string

from adeploy.common.secrets_provider.provider import SecretsProvider


class RandomSecretProvider(SecretsProvider):
    """
    A secret provider that provides a random secret.
    The secret is generated once and stored in memory.
    During a run of adeploy, the same secret will be returned for the same name.
    """

    __named_passwords = {}

    def __init__(self, name: str, length: int = 32, log=None):
        super().__init__(log)
        if not name:
            raise ValueError('Name cannot be empty')
        self.name = name
        if not self.name in RandomSecretProvider.__named_passwords:
            self.__named_passwords[self.name] = RandomSecretProvider.get_random_string(length)

    def _get_value(self, log) -> str:
        return RandomSecretProvider.__named_passwords[self.name]

    def get_id(self):
        return self.name

    @classmethod
    def get_random_string(cls, length: int):
        """
        Generate a random password as described in the best practices.
        https://docs.python.org/3/library/secrets.html#recipes-and-best-practices
        """
        if not isinstance(length, int):
            raise ValueError('create_random_string() requires an integer as length')
        if length < 16:
            raise ValueError('create_random_string() requires a length of at least 16 characters')


        alphabet = string.ascii_letters + string.digits
        while True:
            password = ''.join(secrets.choice(alphabet) for i in range(length))
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and sum(c.isdigit() for c in password) >= 3):
                return password

