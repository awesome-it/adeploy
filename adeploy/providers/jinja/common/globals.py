def create__get_version(deployment):
    def get_version(package):
        return deployment.config.get('versions', {}).get(package, 'latest')


def create__get_url(deployment):
    def get_url():
        ingress = deployment.config.get('ingress', {}).items()
        server_name, props = next(iter(ingress))
        if props.get('external', False):
            return f'https://{server_name}'
        else:
            return f'http://{server_name}'
    return get_url


__secrets = []


def get_secrets():
    return __secrets


def create__create_secret(delpoyment):
    def create_secret(name, value):
        __secrets.append({
            'name': name,
            'value': value,
            'deployment': delpoyment.__dict__,
        })
        return f'secret_{name}'
    return create_secret