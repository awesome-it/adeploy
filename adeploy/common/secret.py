import shutil
from logging import Logger
from pathlib import Path

from adeploy.common import colors, kubectl_apply, parse_kubectrl_apply
from adeploy.common.jinja import env as jinja_env


class Secret:
    type: str = None
    name: str = None
    deployment = None

    def __init__(self, name: str, deployment):
        self.name = name
        self.deployment = deployment

    def get_path(self, build_dir):
        return build_dir \
            .joinpath(self.deployment.namespace) \
            .joinpath(self.name) \
            .joinpath(self.deployment.release) \
            .joinpath('secrets') \
            .joinpath(self.name + '.yml')

    def render(self, build_dir: Path, log: Logger = None):
        env = jinja_env.create([Path(__file__).parent.joinpath('jinja/templates/secrets')])
        jinja_env.register_globals(env, self.deployment)

        values = {
            'secret': self.__dict__,
            'deployment': self.deployment.__dict__,
        }

        secret_build_path = self.get_path(build_dir)
        log.info(f'Rendering secret "{colors.bold(self.name)}" in "{colors.bold(secret_build_path)}" ...')

        if secret_build_path.parent.exists():
            shutil.rmtree(secret_build_path.parent)
        secret_build_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(secret_build_path), 'w') as fd:
            fd.write(env.get_template(f'{self.type}.yml').render(**values))

    def test(self, build_dir: Path, log: Logger = None):
        secret_build_path = self.get_path(build_dir)

        log.info(f'Testing secret for deployment "{colors.blue(self.deployment)}" in "{secret_build_path}" ...')
        result = kubectl_apply(log, self.get_path(build_dir), namespace=self.deployment.namespace, dry_run='server')
        parse_kubectrl_apply(log, result.stdout)

    def deploy(self, build_dir: Path, log: Logger = None):
        secret_build_path = self.get_path(build_dir)

        log.info(f'Creating secret for deployment "{colors.blue(self.deployment)}" in "{secret_build_path}" ...')
        result = kubectl_apply(log, self.get_path(build_dir), namespace=self.deployment.namespace)
        parse_kubectrl_apply(log, result.stdout)


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


def get_secrets():
    return __secrets.values()

