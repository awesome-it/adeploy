from adeploy.common.secrets_provider.provider import SecretsProvider

class PlaintextSecretProvider(SecretsProvider):
    """
    A secret provider that provides a secret from plain text.
    As a plaintext secret is not secret this if for testing purposes only.
    """

    __named_passwords = {}

    def __init__(self, plaintext_secret: str, log=None):
        if not plaintext_secret:
            raise ValueError('Plaintext secret cannot be empty')
        super().__init__(name=plaintext_secret, log=log)
        self.name = plaintext_secret
        self.plaintext = plaintext_secret
        log.warning(f'Plaintext secret "{self.name}" created. Don\'t use this in production!')

    def _get_value(self, log) -> str:
        log.warning(f'Plaintext secret "{self.name}" value rendered. Don\'t use this in production!')
        return self.plaintext

    def get_id(self):
        return self.name

