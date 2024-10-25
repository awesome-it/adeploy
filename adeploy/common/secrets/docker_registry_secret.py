import subprocess
from logging import Logger
from typing import Union

from adeploy.common.kubectl import kubectl_create_secret
from adeploy.common.secrets.secret import Secret
from adeploy.common.secrets_provider.provider import SecretsProvider


class DockerRegistrySecret(Secret):
    type: str = "docker-registry"
    server: str = None
    username: str = None
    password: str = None
    email: str = None

    def __init__(self, deployment, server: str, username: str, password: Union[SecretsProvider, str], email: str = None, name: str = None,
                 use_pass: bool = True, use_gopass_cat: bool = True, custom_cmd: bool = False):
        self.server = server
        self.username = username
        self.password = password
        self.email = email
        super().__init__(deployment, name, use_pass, use_gopass_cat, custom_cmd)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:
        args = [f'--docker-server={self.server}',
                f'--docker-username={self.username}']

        if self.email:
            args.append(f'--docker-email={self.email}')

        args.append(f'--docker-password={self.get_value(self.password, log, dry_run=dry_run)}')

        return kubectl_create_secret(
            log=log, name=self.name,
            namespace=self.deployment.namespace,
            type=self.type, dry_run=dry_run,
            args=args, output=output,
            labels={
                'adeploy.name': self.deployment.name,
                'adeploy.release': self.deployment.release
            })
