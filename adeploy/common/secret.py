from logging import Logger
from pathlib import Path

from adeploy.common import colors
from adeploy.common.jinja import env as jinja_env


class Secret:
    type: str = None
    name: str = None
    deployment = None

    def __init__(self, name: str, deployment):
        self.name = name
        self.deployment = deployment

    def render(self, path: Path):

        env = jinja_env.create([Path(__file__).parent.joinpath('jinja/templates/secrets')])
        jinja_env.register_globals(env, self.deployment)

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

    def __init__(self, name: str, deployment, data: dict):
        super().__init__(name, deployment)
        self.data = data


class TlsSecret(Secret):
    type: str = "tls"
    cert_data: str = None
    key_data: str = None

    def __init__(self, name: str, deployment, cert_data: str, key_data: str):
        super().__init__(name, deployment)
        self.cert_data = cert_data
        self.key_data = key_data


class DockerRegistrySecret(Secret):
    type: str = "docker-registry"
    server: str = None
    username: str = None
    password: str = None
    email: str = None

    def __init__(self, name: str, deployment, server: str, username: str, password: str, email: str = None):
        super().__init__(name, deployment)
        self.server = server
        self.username = username
        self.password = password
        self.email = email


__secrets = {}


def register_secret(s: Secret):
    __secrets[s.name] = s


def render_secrets(build_dir: Path, log: Logger):
    for secret in __secrets.values():
        secret_output_path = build_dir \
            .joinpath(secret.namespace) \
            .joinpath(secret.name) \
            .joinpath(secret.deployment.release) \
            .joinpath('secrets') \
            .joinpath(secret.name + '.yml')

        log.info(f'Rendering secret "{colors.bold(secret.name)}" '
                      f'in "{colors.bold(secret_output_path)}" ...')
        secret.render(secret_output_path)