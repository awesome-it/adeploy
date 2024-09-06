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
from adeploy.common.errors import EmptySecretError, RenderError
from adeploy.common.gopass import gopass_get
from adeploy.common.kubectl import parse_kubectrl_apply, kubectl_create_secret, kubectl_get_secret, \
    kubectl_delete_secret, kubectl


class Secret(ABC):
    type: str = None
    name: str = None
    deployment = None
    use_pass: bool = True
    use_gopass_cat: bool = True
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
        key = f'{str(s.deployment)}/{s.name}'
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
        for secret in glob.glob(f'{secrets_dir}/*/*/*'):
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

                secrets_existing.sort()
                secrets_created.sort()

                num_orphaned = 0
                log.debug(f'... existing secrets: {colors.bold(", ".join(secrets_existing))}')
                log.debug(f'... created secrets: {colors.bold(", ".join(secrets_created))}')
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
            log.debug(f'... executing command "{colors.bold(data)}"')
            result = subprocess.run(data, shell=True, capture_output=True)
            result.check_returncode()

            try:
                result = result.stdout.decode("utf-8")
            except UnicodeDecodeError:
                result = result.stdout
            if not result:
                raise EmptySecretError(f'Cannot create secret: Command "{colors.bold(data)}" returned empty result')

            return result

        if self.use_pass:
            return gopass_get(data, log, use_cat=self.use_gopass_cat)

        return data

    def __init__(self, deployment, name: str = None, use_pass: bool = True, use_gopass_cat: bool = True,
                 custom_cmd: bool = False):

        self.name = name if name else self.gen_name()
        self.deployment = deployment
        self.use_pass = use_pass
        self.custom_cmd = custom_cmd
        self.use_gopass_cat = use_gopass_cat

    def __repr__(self):
        return f'{self.deployment.name}/{self.name}'

    def gen_name(self):
        return f'{Secret._name_prefix}{hashlib.sha1(json.dumps(self.__dict__).encode()).hexdigest()}'

    def get_path(self, build_dir):
        return Secret.get_secret_dir(build_dir, self.deployment.name).joinpath(self.deployment.namespace).joinpath(
            self.deployment.release).joinpath(
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