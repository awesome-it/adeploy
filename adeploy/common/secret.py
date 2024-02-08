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
                return result.stdout.decode("utf-8")
            except UnicodeDecodeError:
                return result.stdout

        if self.use_pass:
            return gopass_get(data, log, use_cat=self.use_gopass_cat)

        return data

    def __init__(self, deployment, name: str = None, use_pass: bool = True, use_gopass_cat: bool = True,
                 custom_cmd: bool = False):

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


class GenericSecret(Secret):
    type: str = "generic"
    data: dict = None

    def __init__(self, deployment, data: dict, name: str = None, use_pass: bool = True, use_gopass_cat: bool = True,
                 custom_cmd: bool = False):
        self.data = data
        super().__init__(deployment, name, use_pass, use_gopass_cat, custom_cmd)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:

        args = []
        temp_files = []
        for k, v in self.data.items():
            data = self.get_value(v, log, dry_run=dry_run)
            fd = tempfile.NamedTemporaryFile(delete=False, mode='wb' if isinstance(data, (bytes, bytearray)) else 'w')
            fd.write(data)
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
                pass

        return result


_DUMMY_DATA_CRT = """
-----BEGIN CERTIFICATE-----
MIIEDTCCAfUCFAGFXSSH5VQqWAOkjXbbsFU+89CQMA0GCSqGSIb3DQEBCwUAMEMx
CzAJBgNVBAYTAkRFMQswCQYDVQQIDAJCVzESMBAGA1UEBwwJS2FybHNydWhlMRMw
EQYDVQQKDApEdW1teSBJbmMuMB4XDTIxMDEwNzExNTExMloXDTIyMDUyMjExNTEx
MlowQzELMAkGA1UEBhMCREUxCzAJBgNVBAgMAkJXMRIwEAYDVQQHDAlLYXJsc3J1
aGUxEzARBgNVBAoMCkR1bW15IEluYy4wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
ggEKAoIBAQDXtmzy3L2FNlvPu/u8wu6arC7GnXkhIkOtuS3HydrSrfzcO/YjUafr
o9Yw9SfYK1gfHcTYCCCKr1DOLOVmyU5ZkVUtJpljmg97l4ljvoNX6P4STWbOmCRE
mPuOOlBruqabc478QUTz840RVRpUOEg3BDTgZ/AgetqJUcVJW+FBk3kIlO8AaEKx
n9jZPhlZovuWJZdxk4qjsM1xnTs4Xlj/QyJzYsxuD7tXbNvWflQh1AKLkZ5aOj9x
4XhV2hizB82Lszn5lX6SReAKeR9BH6SfEjGHlNoC3DKRC82fJVUAhdLFcbl2if3r
GneeIQ/ghkOXc+eXPU6vN4xqBFyBp/J/AgMBAAEwDQYJKoZIhvcNAQELBQADggIB
AIJ2ta5YPwqYlCb4N3AkqLURC0a3BxRqeElLsGQRVekLGzUn/rp+vGJ3B38reC/7
lW6LKXFU8D96hWPggzYJjVBIkrv5EZo12DfXv0z7UPOgy2piaRvrfpmkiwCgEZPQ
R+d34rPY3rYcs7YIa7kbO0wAKSwdeUMhz1fhQuiJKgIKr0vFRrLHOdM5G0czPL7d
Qc3QGfJ8Y8nJjg8DcbRNKNWuL5BWmCXD/WWFS9N3EUzVsnOQu4/4d0zXxw1LVIH8
nClhhu92PgeFd067hWNH6iRTI79a/8mI3M5J+2OE71IIDqj5JNDKvD0bMf8oLuQj
znNXTwH/V9z3iemsJXbqzzRLf8Uqt81V28L6fPdAShUnLCCXS1rz6RHYpkBqbUso
hEY2wbvYl6SPvrsqCJ5PMzqH0EZcbx86V1Fd+CqbBlKMS1/rMBUQ+12/gxsJ0WcY
IKFHyhNFgeUNpZt3uo2KmiotrCFS+IOd/Jdcjbn9O3JvhTQFXmdXaP2Pdqm6rVeu
KxcQayRbw5HSQp9T08xJFuUfF2i5Vk6xgMlwWx9qNzHslKJjmcT5bYkDCv/L7cS6
6IWEggQai1pEs++U8rTHZHKBSL3Q63LgLMVSEgEsXLNPS+VQkU+2tLIsqFFR6FiP
YZFF4v0S0UKute95q56ftVLEQhDJGrofWy3sZKlla52b
-----END CERTIFICATE-----
"""

_DUMMY_DATA_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA17Zs8ty9hTZbz7v7vMLumqwuxp15ISJDrbktx8na0q383Dv2
I1Gn66PWMPUn2CtYHx3E2Aggiq9QzizlZslOWZFVLSaZY5oPe5eJY76DV+j+Ek1m
zpgkRJj7jjpQa7qmm3OO/EFE8/ONEVUaVDhINwQ04GfwIHraiVHFSVvhQZN5CJTv
AGhCsZ/Y2T4ZWaL7liWXcZOKo7DNcZ07OF5Y/0Mic2LMbg+7V2zb1n5UIdQCi5Ge
Wjo/ceF4VdoYswfNi7M5+ZV+kkXgCnkfQR+knxIxh5TaAtwykQvNnyVVAIXSxXG5
don96xp3niEP4IZDl3Pnlz1OrzeMagRcgafyfwIDAQABAoIBAF0/RLVvapWtO97+
2gFtGovOJqJA7F3AXBU62Wll/qvX/liNqwb1g2s/dZXQRBsUEZHR4oeoa7jHtFyL
19ao6q+ZPYK5DtGZhVvd08xETK6xzzLGNszTw8nLf+Kpnp4TH3ZPa93rsQzrmW2G
pk0Fz2HI9bqT8592vAVkTa46g5M+izV/A4OuuY+hdUXaBq8r04EfuLFiSkh7HOA2
Ht2GYtVmGnWzThlReDdTWHKTjkXXWwR871omiz3zK24gZC6VKcGSsPFbxYxKYw4S
dIR5Rrl+r7v6U0dbNFdNxnBfuspZDQkyeQO+3g2X0kcnW/uH/ReHChk7X5ZR2o6+
NQ3o7uECgYEA+H3BKbcVfCozi1t2UjzkUefcIA3PLSsPMRku5L+1U2161MYxJXan
N/BdDLRbGInOkFduscCaK+pwvew6hBeNtix5KtNcvkn17guGTfCfew03vlTG89Ur
ArnNdJPAdGFKZy9kR4llNFtrCy+MDrC9EwnsFzoZaGnjrbqD6b4uFkkCgYEA3jsb
QdZXsrfUpXm9CanMNhRCnlOQpN6aXo+ZFo0ktUrbTJNspLOjtKS/dbp0VeCDqH7Z
dce/cBxyNzqna9g1CErtVfnPgWgs0V7YxP+gibEIuR2j/sdAanbOdkRJEjHbg5D/
IShL+IcxNHOzLQFEWX3uvcz6nTABwfHNuqNAoocCgYEAqBgBjCOCkCzIE3Q6lSUF
2nY7DR/qTwa6zx7W/vzEP3xmw/qSEmKyeX/KoiZ7HR1Ts4bBpdLBOAXuYDul1edN
ALgS+yphqYPErlPzdVPZvlbRp5oXv6gq4TwpRLwSS2fo+eYwMsg5wvI4diei2ekq
7e8fWxL9Twmab9IlHAB/kqkCgYBKT+OGeYFr7tL53qKbB5+U+eNpBDKbHyDpvAUK
KHp88SIyEh5DWRrF/k1TtdzPFruP7ZMUMo5OlASReVig1HSvaDbDCD0eXdKW1KuR
/JUXVg6/sCy1trVQpJfXrm/s2KU58pON5+a3naWTj5j71K+haV4bM98eDv6Xdx8/
aPXlIwKBgQDz9TGYW2nM3GWVQSds/y78He/9p8wsbKgvjSyU0JfulK88eYGNsNho
lnUqJtp1zChmcVqRN2f8m9XX59Kgt90RnlCQ0Vl010ovo+y8bCmbsjHzI2SlZ012
4jzbJHDRq1er3/Euz59jAoELTecROcMno/Sm+VTLLc6E2ufzXB5JGw==
-----END RSA PRIVATE KEY-----
"""


class TlsSecret(Secret):
    type: str = "tls"
    cert: str = None
    key: str = None

    def __init__(self, deployment, cert: str, key: str, name: str = None, use_pass: bool = True,
                 use_gopass_cat: bool = True, custom_cmd: bool = False):
        self.cert = cert
        self.key = key
        super().__init__(deployment, name, use_pass, use_gopass_cat, custom_cmd)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:

        cert_data = _DUMMY_DATA_CRT if dry_run else self.get_value(self.cert, log, dry_run=False)
        cert = tempfile.NamedTemporaryFile(delete=False,
                                           mode='wb' if isinstance(cert_data, (bytes, bytearray)) else 'w')
        cert.write(cert_data)
        cert.close()

        key_data = _DUMMY_DATA_KEY if dry_run else self.get_value(self.key, log, dry_run=False)
        key = tempfile.NamedTemporaryFile(delete=False, mode='wb' if isinstance(key_data, (bytes, bytearray)) else 'w')
        key.write(key_data)
        key.close()

        args = [
            f'--cert={cert.name}',
            f'--key={key.name}',
        ]

        try:

            result = kubectl_create_secret(
                log=log,
                name=self.name,
                namespace=self.deployment.namespace,
                type=self.type,
                args=args,
                output=output,
                labels={
                    'adeploy.name': self.deployment.name,
                    'adeploy.release': self.deployment.release
                })

        finally:
            os.remove(cert.name)
            os.remove(key.name)

        return result


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
