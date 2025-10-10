import os
import subprocess
import tempfile
from logging import Logger

from adeploy.common.kubectl import kubectl_create_secret
from adeploy.common.secrets.secret import Secret
from adeploy.common.secrets_provider.provider import SecretsProvider


class GenericSecret(Secret):
    type: str = "generic"
    data: dict = None

    def __init__(self, deployment, data: dict, name: str = None, use_pass: bool = True, use_gopass_cat: bool = True,
                 custom_cmd: bool = False):
        self.data = data
        super().__init__(deployment, name, use_pass, use_gopass_cat, custom_cmd)

    def _is_legacy_secret(self) -> bool:
        return not all([isinstance(d, SecretsProvider) for d in self.data.values()])

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
