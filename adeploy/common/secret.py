from pathlib import Path

from adeploy.common import Deployment
from adeploy.common.jinja.env import create, register_globals


class Secret:
    type: str = None
    name: str = None
    deployment: Deployment = None

    def __init__(self, name: str, deployment: Deployment):
        self.name = name
        self.deployment = deployment

    def render(self, path: Path):

        env = create([Path(__file__).parent.joinpath('jinja/templates/secrets')])
        register_globals(env, self.deployment)

        values = {
            'secret': self.__dict__,
            'deployment': self.deployment.__dict__,
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(path), 'w') as fd:
            fd.write(env.get_template(f'{self.type}.yml').render(**values))


class GenericSecret(Secret):
    type: str = "generic"
    data: dict = None

    def __init__(self, name: str, deployment: Deployment, data: dict):
        super().__init__(name, deployment)
        self.data = data


class TlsSecret(Secret):
    type: str = "tls"
    cert_data: str = None
    key_data: str = None

    def __init__(self, name: str, deployment: Deployment, cert_data: str, key_data: str):
        super().__init__(name, deployment)
        self.cert_data = cert_data
        self.key_data = key_data


class DockerRegistrySecret(Secret):
    type: str = "docker-registry"
    server: str = None
    username: str = None
    password: str = None
    email: str = None

    def __init__(self, name: str, deployment: Deployment, server: str, username: str, password: str, email: str = None):
        super().__init__(name, deployment)
        self.server = server
        self.username = username
        self.password = password
        self.email = email