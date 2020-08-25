import textwrap

from adeploy.common import colors
from adeploy.common.secret import Secret, GenericSecret, TlsSecret, DockerRegistrySecret


def create__get_version(deployment, **kwargs):
    def get_version(package):
        return deployment.config.get('versions', {}).get(package, 'latest')

    return get_version


# Alias for get_version()
def create__version(deployment, **kwargs):
    return create__get_version(deployment, **kwargs)


def create__get_url(deployment, **kwargs):
    def get_url():
        ingress = deployment.config.get('ingress', {}).items()
        server_name, props = next(iter(ingress))
        if props.get('external', False):
            return f'https://{server_name}'
        else:
            return f'http://{server_name}'

    return get_url


def create__create_generic_secret(deployment, **create_kwargs):
    log = create_kwargs.get('log', None)

    def create_secret(name: str = None, use_pass=True, data=None, **kwargs):
        secret = GenericSecret(deployment, data or kwargs, name, use_pass)
        if Secret.register(secret) and log:
            log.info(f'Registered generic secret "{colors.bold(secret.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return secret.name

    return create_secret


# Alias for create_generic_secret()
def create__create_secret(deployment, **kwargs):
    return create__create_generic_secret(deployment, **kwargs)


def create__create_tls_secret(deployment, **kwargs):
    log = kwargs.get('log')

    def create_tls_secret(cert_data: str, key_data: str, name: str, use_pass: bool = True):
        secret = TlsSecret(deployment, name, cert_data, key_data, use_pass)
        if Secret.register(secret) and log:
            log.info(f'Registering TLS secret "{colors.bold(secret.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return secret.name

    return create_tls_secret


def create__create_docker_registry_secret(deployment, **kwargs):
    log = kwargs.get('log')

    def create_docker_registry_secret(server: str, username: str, password: str, email: str = None, name: str = None,
                                      use_pass: bool = True):
        secret = DockerRegistrySecret(deployment, server, username, password, email, name, use_pass)
        if Secret.register(secret) and log:
            log.info(f'Registering docker registry secret "{colors.bold(secret.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return secret.name

    return create_docker_registry_secret


def create__include_file(deployment, **kwargs):
    env = kwargs.get('env')
    values = deployment.get_template_values()

    def include_file(path: str, direct: bool = False, indent: int = 4):
        prefix = '|\n' if not direct else ''
        return f'{prefix}{textwrap.indent(env.get_template(path).render(**values), indent * " ")}'

    return include_file
