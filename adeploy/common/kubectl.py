import json
import os
import string
import subprocess
import tempfile
import random
from logging import Logger
from pathlib import Path
from typing import Optional

import yaml

from adeploy.common import colors
from adeploy.common.errors import TestError
from adeploy.common.helpers import dict_update_recursive

# See kubectl_init()
KUBECONF = None


def kubectl_add_default_context(log: Logger):
    kubectl(log, ['config', 'set-cluster', 'default',
                  f'--server=https://{os.getenv("KUBERNETES_SERVICE_HOST")}:{os.getenv("KUBERNETES_SERVICE_PORT_HTTPS")}',
                  '--certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'])

    kubectl(log, ['config', 'set-context', 'default', '--cluster=deploy'])

    with open('/var/run/secrets/kubernetes.io/serviceaccount/token') as fd:
        kubectl(log, ['config', 'set-credentials', 'default', f'--token={fd.read()}'])

    kubectl(log, ['config', 'set-context', 'default', '--user=default'])
    kubectl(log, ['config', 'use-context', 'default'])


def kubectl_set_default_namespace(log: Logger, namespace: str) -> subprocess.CompletedProcess:
    return kubectl(log, ['config', 'set-context', '--current', f'--namespace={namespace}'])


def kubectl_get_default_namespace(log: Logger) -> str:
    config = json.loads(kubectl(log, ['config', 'view', '-o', 'json']).stdout)
    contexts = config.get('contexts', [])
    for c in contexts or []:
        if c.get('name') == config.get('current-context'):
            return c.get('context').get('namespace', 'default')
    return 'default'


def kubectl_set_fake_namespace(log: Logger) -> (str, str):
    if os.getenv('CI'):
        kubectl_add_default_context(log)

    default_ns = kubectl_get_default_namespace(log)
    namespaces = kubectl_get_namespaces(log)
    fake_ns = None
    while fake_ns is None or fake_ns in namespaces:
        fake_ns = ''.join(random.choices(string.ascii_lowercase, k=32))
    kubectl_set_default_namespace(log, fake_ns)
    return default_ns, fake_ns


def kubectl_get_namespaces(log: Logger):
    return [n.get('metadata').get('name') for n in
            json.loads(kubectl(log, ['get', 'namespace', '-o', 'json']).stdout).get('items', [])]


def kubectl_apply(log, manifest_path, namespace=None, dry_run=None, output=None) -> subprocess.CompletedProcess:
    args = ['apply', '-f', str(manifest_path)]
    if dry_run:
        args.append(f'--dry-run={dry_run}')
    if output:
        args += ['-o', output]
    return kubectl(log, args, namespace)


def kubectl_get_secret(log, name, namespace) -> subprocess.CompletedProcess:
    return kubectl(log, ['get', 'secret', name, '-o', 'json'], namespace)


def kubectl_delete_secret(log, name, namespace) -> subprocess.CompletedProcess:
    return kubectl(log, ['delete', 'secret', name, '-o', 'name'], namespace)


def kubectl_create_secret(log, name, namespace, type, args, labels: dict = None,
                          dry_run: bool = None, output: str = None) -> subprocess.CompletedProcess:
    # Get manifest for secret
    result = kubectl(log, ['create', 'secret', type, name] + args + ['--dry-run=client', '-o', 'json'], namespace)
    manifest = json.loads(result.stdout)

    # Add labels
    manifest = dict_update_recursive(manifest, {
        'metadata': {
            'labels': labels
        }
    })

    fd = tempfile.NamedTemporaryFile(delete=False, mode='w')
    yaml.dump(manifest, fd)
    fd.close()

    # Apply manifest
    args = []
    if dry_run:
        args.append(f'--dry-run={dry_run}')

    if output:
        args += ['-o', output]

    try:
        result = kubectl(log, ['apply', '-f', fd.name] + args, namespace)
    finally:
        os.remove(fd.name)

    return result


def kubectl(log: Logger, args: list, namespace: str = None) -> subprocess.CompletedProcess:
    cmd = ['kubectl', '--kubeconfig', str(KUBECONF)]
    if namespace:
        cmd += ['-n', namespace]
    cmd += args

    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()
    return result


def kubectl_init(args):
    global KUBECONF

    # Create temporary kube config to not change users kubeconf
    KUBECONF = args.adeploy_dir.joinpath('kubeconf')
    KUBECONF.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(['kubectl', 'config', 'view', '--raw'], capture_output=True, text=True)
    result.check_returncode()

    with open(str(KUBECONF), 'w') as fd:
        fd.write(result.stdout)


def parse_kubectrl_apply(log, stdout, manifests: dict = None, fake_ns: str = None, default_ns: str = None,
                         deployment_ns: str = None, prefix='...'):
    # If there is no fake_ns, we need to determine by comparing existing namespaces
    namespaces = kubectl_get_namespaces(log)

    for line in stdout.split('\n'):
        token = line.split(' ')
        if len(token) >= 2:
            resource, resource_name = token[0].split('/')
            status = token[1]
            namespace = None
            namespace_description = ''
            found = False

            if manifests:
                for item in manifests.get('items', [manifests]):
                    metadata = item.get('metadata', {})
                    item_resource_name = item.get('kind').lower()
                    if '/' in item.get('apiVersion'):
                        item_resource_name += '.' + item.get('apiVersion').split('/')[0].lower()

                    if item_resource_name == resource and metadata.get('name', None) == resource_name:
                        found = True
                        namespace = metadata.get('namespace', None)

                        # If the helm templates does not contain a namespace (which is seen as best practise, see
                        # https://github.com/helm/helm/issues/5465. This displays the real namespace that would be used
                        # for helm install/upgrade.
                        if (namespace == 'default' or namespace not in namespaces) \
                                and deployment_ns and deployment_ns != namespace:
                            namespace = deployment_ns

                        # No namespace needed for cluster resources
                        if 'cluster' in item_resource_name.lower():
                            namespace_description = ''

                        elif fake_ns and namespace == fake_ns:
                            raise TestError(f'No namespace specified for '
                                            f'resource {colors.bold(resource)}/{colors.bold(resource_name)} ')
                        else:
                            namespace_description = f'namespace: {colors.bold(namespace or default_ns)} '

                        break

                if not found:
                    log.warning(f'Could not find metadata for resource: {colors.bold(resource)}, '
                                f'name: {colors.bold(resource_name)}, ignore ...')

            log.info(f'{prefix} {namespace_description}'
                     f'resource: {colors.bold(resource)}, '
                     f'name: {colors.bold(resource_name)}: '
                     f'{colors.gray(status) if status == "unchanged" else colors.green(status)}')


def kubectl_get_current_api_server_url(log: Logger) -> Optional[str]:
    args = ['config', 'view', '--minify', '--output', 'jsonpath="{.clusters[*].cluster.server}"']
    try:
        return json.loads(kubectl(log=log, args=args).stdout)
    except subprocess.CalledProcessError as e:
        log.error(f'Could not get current api server url: {e.stderr}')
        return None
