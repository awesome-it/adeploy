import textwrap

import adeploy.common.colors as colors
import adeploy.common.secret as secret
import adeploy.common.errors as errors


def create__get_version(deployment, **kwargs):
    def get_version(package):
        if not deployment:
            raise errors.RenderError('get_version() or version() cannot be used here')
        return deployment.config.get('versions', {}).get(package, 'latest')

    return get_version


# Alias for get_version()
def create__version(deployment, **kwargs):
    return create__get_version(deployment, **kwargs)


def create__get_url(deployment, **kwargs):
    def get_url():
        if not deployment:
            raise errors.RenderError('get_url() cannot be used here')
        ingress = deployment.config.get('ingress', {}).items()
        server_name, props = next(iter(ingress))
        if props.get('external', False):
            return f'https://{server_name}'
        else:
            return f'http://{server_name}'

    return get_url


def create__create_generic_secret(deployment, **create_kwargs):
    log = create_kwargs.get('log', None)

    def create_secret(name: str = None, use_pass=True, custom_cmd=False, data=None, **kwargs):
        if not deployment:
            raise errors.RenderError('create_secret() cannot be used here')
        s = secret.GenericSecret(deployment, data or kwargs, name, use_pass, custom_cmd)
        if secret.Secret.register(s) and log:
            log.info(f'Registered generic secret "{colors.bold(s.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return s.name

    return create_secret


# Alias for create_generic_secret()
def create__create_secret(deployment, **kwargs):
    return create__create_generic_secret(deployment, **kwargs)


def create__create_tls_secret(deployment, **kwargs):
    log = kwargs.get('log')

    def create_tls_secret(cert_data: str, key_data: str, name: str, use_pass: bool = True, custom_cmd=False):
        if not deployment:
            raise errors.RenderError('create_tls_secret() cannot be used here')
        s = secret.TlsSecret(deployment, name, cert_data, key_data, use_pass, custom_cmd)
        if secret.Secret.register(s) and log:
            log.info(f'Registering TLS secret "{colors.bold(s.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return s.name

    return create_tls_secret


def create__create_docker_registry_secret(deployment, **kwargs):
    log = kwargs.get('log')

    def create_docker_registry_secret(server: str, username: str, password: str, email: str = None, name: str = None,
                                      use_pass: bool = True, custom_cmd=False):
        if not deployment:
            raise errors.RenderError('create_docker_registry_secret() cannot be used here')
        s = secret.DockerRegistrySecret(deployment, server, username, password, email, name, use_pass, custom_cmd)
        if secret.Secret.register(s) and log:
            log.info(f'Registering docker registry secret "{colors.bold(s.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return s.name

    return create_docker_registry_secret


def create__include_file(deployment, **kwargs):
    env = kwargs.get('env')
    values = {}
    if deployment:
        values = deployment.get_template_values()

    def include_file(path: str, direct: bool = False, render: bool = True, indent: int = 4):
        prefix = '|\n' if not direct else ''
        if render:
            data = env.get_template(path).render(**values)
        else:
            data, _, _ = env.loader.get_source(env, path)
        return f'{prefix}{textwrap.indent(data, indent * " ")}'

    return include_file
