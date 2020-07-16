from logging import Logger

from adeploy.common import colors
from adeploy.common.secret import Secret, GenericSecret, TlsSecret, DockerRegistrySecret


def create__get_version(deployment, log: Logger = None):
    def get_version(package):
        return deployment.config.get('versions', {}).get(package, 'latest')

    return get_version


def create__get_url(deployment, log: Logger = None):
    def get_url():
        ingress = deployment.config.get('ingress', {}).items()
        server_name, props = next(iter(ingress))
        if props.get('external', False):
            return f'https://{server_name}'
        else:
            return f'http://{server_name}'

    return get_url


def create__create_generic_secret(deployment, log: Logger = None):
    def create_secret(name: str = None, use_pass=True, **data):
        secret = GenericSecret(deployment, data, name, use_pass)
        if Secret.register(secret) and log:
            log.info(f'Registered generic secret "{colors.bold(secret.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return secret.name

    return create_secret


# Alias for create_generic_secret()
def create__create_secret(deployment, log: Logger = None):
    return create__create_generic_secret(deployment, log)


def create__create_tls_secret(deployment, log: Logger = None):
    def create_tls_secret(cert_data: str, key_data: str, name: str, use_pass: bool = True):
        secret = TlsSecret(deployment, name, cert_data, key_data, use_pass)
        if Secret.register(secret) and log:
            log.info(f'Registering TLS secret "{colors.bold(secret.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return secret.name

    return create_tls_secret


def create__create_docker_registry_secret(deployment, log: Logger = None):
    def create_tls_secret(server: str, username: str, password: str, email: str = None, name: str = None, use_pass: bool = True):
        secret = DockerRegistrySecret(deployment, server, username, password, email, name, use_pass)
        if Secret.register(secret) and log:
            log.info(f'Registering docker registry secret "{colors.bold(secret.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return secret.name

    return create_tls_secret
