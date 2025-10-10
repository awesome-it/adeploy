import glob
import hashlib
import json
import shutil
import subprocess
import warnings

from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from pickle import dump, load
from typing import Union

from adeploy.common import colors
from adeploy.common.errors import RenderError
from adeploy.common.secrets_provider.gopass_provider import GopassSecretProvider
from adeploy.common.kubectl import parse_kubectrl_apply, kubectl_get_secret, \
    kubectl_delete_secret, kubectl
from adeploy.common.secrets_provider.provider import SecretsProvider
from adeploy.common.secrets_provider.shell_command_provider import ShellCommandSecretProvider


class Secret(ABC):
    type: str = None
    name: str = None
    deployment = None
    use_pass: bool = True           # Deprecated
    use_gopass_cat: bool = True     # Deprecated
    custom_cmd: bool = False        # Deprecated

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
            secrets.append(Secret.load(Path(secret)))
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

    def __deprecated_get_value(self, data: Union[Path, str], log: Logger = None, dry_run: Union[bool, str] = False) -> str:

        if dry_run:
            warnings.warn('Using deprecated value retrieval', FutureWarning)
            return '*****'

        if self.custom_cmd:
            warnings.warn('The use of custom commands in create_secret is deprecated.'
                          'Please use value_from_shell_command() instead.',
                          FutureWarning)
            return ShellCommandSecretProvider(command=data, log=log).get_value()

        if self.use_pass:
            warnings.warn('The use of gopass in create_secret() is deprecated.'
                          'Please use from_gopass() instead.',
                          FutureWarning)
            return GopassSecretProvider(path=data, log=log, use_show=not self.use_gopass_cat).get_value()
        # A plaintext secret
        warnings.warn('The use of plaintext in create_secret() is deprecated.'
                      'Please use from_plaintext() instead.',
                      FutureWarning)
        return data

    def get_value(self, data: Union[Path, str, SecretsProvider], log: Logger = None, dry_run: Union[bool, str] = False) -> str:
        if not isinstance(data, SecretsProvider):
            return self.__deprecated_get_value(data, log, dry_run)
        if dry_run:
            return '*****'
        return data.get_value(log=log)

    @abstractmethod
    def _is_legacy_secret(self) -> bool:
        pass

    def __init__(self, deployment, name: str = None, use_pass: bool = True, use_gopass_cat: bool = True,
                 custom_cmd: bool = False):
        self.is_legacy = self._is_legacy_secret()
        self.name = name if name else self._gen_name()
        self.deployment = deployment

        # Remove this in the future
        self.use_pass = use_pass
        self.custom_cmd = custom_cmd
        self.use_gopass_cat = use_gopass_cat
        if self.is_legacy:
            if use_pass:
                warnings.warn('The use of gopass in create_secret() is deprecated.'
                              'Please use from_gopass() instead.',
                              FutureWarning)
            if custom_cmd:
                warnings.warn('The use of custom commands in create_secret is deprecated.'
                              'Please use value_from_shell_command() instead.',
                              FutureWarning)
            if not use_pass and not custom_cmd:
                warnings.warn('The use of plaintext in create_secret() is deprecated.'
                              'Please use from_plaintext() instead.',
                              FutureWarning)


    def __repr__(self):
        return f'{self.deployment.name}/{self.name}'

    def _gen_name(self):
        # This is a little hard to understand...
        # Secret generation gets updated, but the secret names should not change between versions of adeploy
        # This is why we use a hash of the object's dictionary to generate the secret name
        # But.... SecretsProvider objects are not hashable, so we need to convert them to their id
        obj_dict = {}
        for key, val in self.__dict__.items():
            if isinstance(val, str):
                obj_dict[key] = val
            elif isinstance(val, dict):
                obj_dict[key] = {}
                for sub_key, sub_val in val.items():
                    if isinstance(sub_val, SecretsProvider):
                        obj_dict[key].update({sub_key: sub_val.get_id()})
                    else:
                        obj_dict[key].update({sub_key: sub_val})  # Keep it as is
            else:
                if isinstance(val, SecretsProvider):
                    obj_dict[key] = val.get_id()
                else:
                    obj_dict[key] = val
        return f'{Secret._name_prefix}{hashlib.sha1(json.dumps(obj_dict).encode()).hexdigest()}'

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
