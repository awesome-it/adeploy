import glob
import hashlib
import json
import shutil
import subprocess
from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from pickle import dump, load, dumps

from adeploy.common import colors
from adeploy.common.kubectl import parse_kubectrl_apply, kubectl_create_secret, kubectl_get_secret, \
    kubectl_delete_secret
from adeploy.common.errors import RenderError
from adeploy.common.gopass import gopass_get


class Secret(ABC):
    type: str = None
    name: str = None
    deployment = None
    use_pass: bool = True

    _name_prefix = 'secret-'
    _secrets = {}

    @staticmethod
    def get_secret_path(build_dir: Path, deployment_name: str, name: str):
        return build_dir.joinpath(deployment_name).joinpath('secrets').joinpath(name)

    @staticmethod
    def clean_all(build_dir: Path):
        for secret in Secret.get_registered():
            secrets_dir = secret.get_path(build_dir).parent
            if secrets_dir.exists():
                shutil.rmtree(secrets_dir)

    @staticmethod
    def load(path: Path):
        with open(str(path), 'rb') as fd:
            return load(fd)

    @staticmethod
    def register(s):
        if s.name not in Secret._secrets:
            Secret._secrets[s.name] = s
            return True
        return False

    @staticmethod
    def get_registered():
        return Secret._secrets.values()

    @staticmethod
    def get_stored(build_dir: Path, name: str):
        secrets_dir = Secret.get_secret_path(build_dir, name, '.')
        secrets = []
        for secret in glob.glob(f'{secrets_dir}/*'):
            secrets.append(Secret.load(secret))
        return secrets

    def __init__(self, deployment, name: str = None, use_pass: bool = True):

        self.name = name if name else self.gen_name()
        self.deployment = deployment
        self.use_pass = use_pass

    def __repr__(self):
        return f'{self.deployment.name}/{self.name}'

    def gen_name(self):
        return f'{Secret._name_prefix}{hashlib.sha1(dumps(self)).hexdigest()}'

    def get_path(self, build_dir):
        return Secret.get_secret_path(build_dir, self.deployment.name, self.name)

    def store(self, build_dir: Path):
        output_path = self.get_path(build_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(output_path), 'wb') as fd:
            dump(self, fd)

    def exists(self, log: Logger):
        try:
            kubectl_get_secret(log, self.name, self.deployment.namespace)
            return True
        except subprocess.CalledProcessError:
            pass
        return False

    def test(self, log: Logger):
        log.info(f'Testing secret "{colors.bold(self)}" for deployment "{colors.blue(self.deployment)}" ...')

        # Test whether this secret is already deployed
        if self.exists(log):
            log.info(f'... Secret already exists. '
                     f'{colors.orange("The secret will not be re-created unless --recreate-secrets was specified.")}')
            return

        # Test creating the secret using kubectl
        try:
            manifest = self.create(log, dry_run='client', output='json')
            result = self.create(log, dry_run='server')
            parse_kubectrl_apply(log, result.stdout, manifests=json.loads(manifest.stdout))

        except subprocess.CalledProcessError as e:
            raise RenderError(
                f'Error while creating (dry-run) secret "{colors.bold(self.name)}": {e}\n{e.stderr.strip()}')

    def deploy(self, log: Logger, recreate=False):

        if self.exists(log):
            if recreate:
                kubectl_delete_secret(log, self.name, self.deployment.namespace)
                log.info(f'... remove existing secret "{colors.bold(self)}" in order to re-create ...')
            else:
                log.info(f'... skip re-creating existing secret "{colors.bold(self)}"')
                return

        # Creating the secret using kubectl
        try:
            log.info(f'... creating secret "{colors.bold(self)}" ...')
            self.create(log)
        except subprocess.CalledProcessError as e:
            raise RenderError(f'Error while creating secret "{colors.bold(self.name)}": {e}\n{e.stderr.strip()}')

    @abstractmethod
    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:
        pass


class GenericSecret(Secret):
    type: str = "generic"
    data: dict = None

    def __init__(self, deployment, data: dict, name: str = None, use_pass: bool = True):
        self.data = data
        super().__init__(deployment, name, use_pass)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:

        args = []
        for k, v in self.data.items():
            if dry_run:
                value = '*****'
            elif self.use_pass:
                value = gopass_get(v, log)
            else:
                value = v
            args.append(f'--from-literal={k}={value}')

        return kubectl_create_secret(
            log=log, name=self.name,
            namespace=self.deployment.namespace,
            type=self.type, dry_run=dry_run,
            args=args, output=output)


class TlsSecret(Secret):
    type: str = "tls"
    cert_data: str = None
    key_data: str = None

    def __init__(self, deployment, cert_data: str, key_data: str, name: str = None, use_pass: bool = True):
        self.cert_data = cert_data
        self.key_data = key_data
        super().__init__(deployment, name, use_pass)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:
        raise NotImplementedError()


class DockerRegistrySecret(Secret):
    type: str = "docker-registry"
    server: str = None
    username: str = None
    password: str = None
    email: str = None

    def __init__(self, deployment, server: str, username: str, password: str, email: str = None, name: str = None,
                 use_pass: bool = True):
        self.server = server
        self.username = username
        self.password = password
        self.email = email
        super().__init__(deployment, name, use_pass)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:
        raise NotImplementedError()
