from adeploy.common.secret import GenericSecret, TlsSecret, DockerRegistrySecret, register_secret


def create__get_version(deployment):
    def get_version(package):
        return deployment.config.get('versions', {}).get(package, 'latest')
    return get_version


def create__get_url(deployment):
    def get_url():
        ingress = deployment.config.get('ingress', {}).items()
        server_name, props = next(iter(ingress))
        if props.get('external', False):
            return f'https://{server_name}'
        else:
            return f'http://{server_name}'
    return get_url


def create__create_generic_secret(deployment):
    def create_secret(name: str, **data):
        secret = GenericSecret(name, deployment, data)
        register_secret(secret)
        return secret.name
    return create_secret


# Alias for create_generic_secret
def create__create_secret(deployment):
    return create__create_generic_secret(deployment)


def create__create_tls_secret(deployment):
    def create_tls_secret(name: str, cert_data: str, key_data: str):
        secret = TlsSecret(name, deployment, cert_data, key_data)
        register_secret(secret)
        return secret.name
    return create_tls_secret


def create__create_docker_registry_secret(deployment):
    def create_tls_secret(name: str, server: str, username: str, password: str, email: str = None):
        secret = DockerRegistrySecret(name, deployment, server, username, password, email)
        register_secret(secret)
        return secret.name
    return create_tls_secret
