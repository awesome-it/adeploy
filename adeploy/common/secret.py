import glob
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from pickle import dump, load
from typing import Union

from adeploy.common import colors
from adeploy.common.errors import RenderError
from adeploy.common.gopass import gopass_get
from adeploy.common.kubectl import parse_kubectrl_apply, kubectl_create_secret, kubectl_get_secret, \
    kubectl_delete_secret, kubectl


class Secret(ABC):
    type: str = None
    name: str = None
    deployment = None
    use_pass: bool = True
    custom_cmd: bool = False

    _name_prefix = 'secret-'
    _secrets = {}

    @staticmethod
    def get_secret_dir(build_dir: Path, deployment_name: str):
        return build_dir.joinpath(deployment_name).joinpath('secrets')

    @staticmethod
    def clean_build_secrets(build_dir: Path):
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
        key = f'{s.deployment.namespace}.{s.name}'
        if key not in Secret._secrets:
            Secret._secrets[key] = s
            return True
        return False

    @staticmethod
    def get_registered():
        return Secret._secrets.values()

    @staticmethod
    def get_stored(build_dir: Path, deployment_name: str):
        secrets_dir = Secret.get_secret_dir(build_dir, deployment_name)
        secrets = []
        for secret in glob.glob(f'{secrets_dir}/*/*'):
            secrets.append(Secret.load(secret))
        return secrets

    @staticmethod
    def clean_all(secrets, log, dry_run: bool = True):
        deployments = {}
        for s in secrets:
            key = str(s.deployment)
            deployments[key] = deployments.get(key, []) + [s]

        for d, secrets in deployments.items():
            if len(secrets) > 0:
                log.info(f'Checking for orphaned secrets of deployment "{colors.blue(d)}" ...')
                d = secrets[0].deployment
                result = kubectl(log, ['get', 'secret', '-l',
                                       f'adeploy.name={d.name},adeploy.release={d.release}',
                                       '-o=jsonpath=\'{.items[*].metadata.name}\''], namespace=d.namespace)

                secrets_existing = [s for s in result.stdout.replace("'", '').split(' ') if len(s) > 0]
                secrets_created = [s.name for s in secrets]
                num_orphaned = 0
                for s in secrets_existing:
                    if s not in secrets_created:
                        num_orphaned += 1
                        if not dry_run:
                            log.info(f'... {colors.orange("delete")} orphaned secret "{colors.bold(d.name + "/" + s)}"')
                            kubectl_delete_secret(log, name=s, namespace=d.namespace)
                        else:
                            log.info(f'... found orphaned secret "{colors.bold(d.name + "/" + s)}", '
                                     f'{colors.orange("will be deleted without dry-run")}')

                if num_orphaned > 0:
                    log.info(f'Found {colors.bold(num_orphaned)} orphaned secrets.')
                else:
                    log.info(f'No orphaned secrets found.')

    def get_value(self, data: Union[Path, str], log: Logger = None, dry_run: Union[bool, str] = False) -> str:

        if dry_run:
            return '*****'

        if self.custom_cmd:
            result = subprocess.run(data, shell=True, capture_output=True, text=True)
            result.check_returncode()
            return result.stdout

        if self.use_pass:
            return gopass_get(data, log)

        return data

    def __init__(self, deployment, name: str = None, use_pass: bool = True, custom_cmd: bool = False):

        self.name = name if name else self.gen_name()
        self.deployment = deployment
        self.use_pass = use_pass
        self.custom_cmd = custom_cmd

    def __repr__(self):
        return f'{self.deployment.name}/{self.name}'

    def gen_name(self):
        return f'{Secret._name_prefix}{hashlib.sha1(json.dumps(self.__dict__).encode()).hexdigest()}'

    def get_path(self, build_dir):
        return Secret.get_secret_dir(build_dir, self.deployment.name).joinpath(self.deployment.namespace).joinpath(
            self.name)

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
            log.info(f'... secret already exists. '
                     f'{colors.orange("The secret will not be re-created unless --recreate-secrets was specified.")}')
            return

        # Test creating the secret using kubectl
        try:
            manifest = self.create(log, dry_run='client', output='json')
            result = self.create(log, dry_run='server')
            parse_kubectrl_apply(log, result.stdout,
                                 manifests=json.loads(manifest.stdout),
                                 deployment_ns=self.deployment.namespace)

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

    def __init__(self, deployment, data: dict, name: str = None, use_pass: bool = True, custom_cmd: bool = False):
        self.data = data
        super().__init__(deployment, name, use_pass, custom_cmd)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:

        args = []
        temp_files = []
        for k, v in self.data.items():

            fd = tempfile.NamedTemporaryFile(delete=False, mode='w')
            fd.write(self.get_value(v, log, dry_run=dry_run))
            fd.close()

            temp_files.append(fd.name)
            args.append(f'--from-file={k}={fd.name}')

        try:

            result = kubectl_create_secret(
                log=log, name=self.name,
                namespace=self.deployment.namespace,
                type=self.type, dry_run=dry_run,
                args=args, output=output,
                labels={
                    'adeploy.name': self.deployment.name,
                    'adeploy.release': self.deployment.release
                })

        finally:
            for f in temp_files:
                os.remove(f)

        return result


class TlsSecret(Secret):
    type: str = "tls"
    cert_data: str = None
    key_data: str = None

    def __init__(self, deployment, cert_data: str, key_data: str, name: str = None, use_pass: bool = True,
                 custom_cmd: bool = False):
        self.cert_data = cert_data
        self.key_data = key_data
        super().__init__(deployment, name, use_pass, custom_cmd)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:
        # TODO: Implement TLS secret generation.
        raise NotImplementedError()


class DockerRegistrySecret(Secret):
    type: str = "docker-registry"
    server: str = None
    username: str = None
    password: str = None
    email: str = None

    def __init__(self, deployment, server: str, username: str, password: str, email: str = None, name: str = None,
                 use_pass: bool = True, custom_cmd: bool = False):
        self.server = server
        self.username = username
        self.password = password
        self.email = email
        super().__init__(deployment, name, use_pass, custom_cmd)

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
