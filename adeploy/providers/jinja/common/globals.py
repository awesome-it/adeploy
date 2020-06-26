def create_get_version(deployment):
    def get_version(package):
        return deployment.config.get('versions', {}).get(package, 'latest')


def create_get_url(deployment):
    def get_url():
        ingress = deployment.config.get('ingress', {}).items()
        server_name, props = next(iter(ingress))
        if props.get('external', False):
            return f'https://{server_name}'
        else:
            return f'http://{server_name}'
    return get_url