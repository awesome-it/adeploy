import subprocess
from logging import Logger

from adeploy.common import colors


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


def kubectl_create_secret(log, name, namespace, type, args, dry_run: bool = None,
                          output: str = None) -> subprocess.CompletedProcess:
    args = ['create', 'secret', type, name] + args
    if dry_run:
        args.append(f'--dry-run={dry_run}')
    if output:
        args += ['-o', output]
    return kubectl(log, args, namespace)


def kubectl(log: Logger, args: list, namespace: str = None) -> subprocess.CompletedProcess:
    cmd = ['kubectl']
    if namespace:
        cmd += ['-n', namespace]
    cmd += args

    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()
    return result


def parse_kubectrl_apply(log, stdout, manifests: dict = None, deployment=None, prefix='...'):
    for line in stdout.split('\n'):
        token = line.split(' ')
        if len(token) > 3:
            resource, resource_name = token[0].split('/')
            status = token[1]
            namespace = None

            found = False
            if manifests:
                for item in manifests.get('items', [manifests]):
                    metadata = item.get('metadata', {})
                    item_resource_name = item.get('kind').lower()
                    if '/' in item.get('apiVersion'):
                        item_resource_name += '.' + item.get('apiVersion').split('/')[0].lower()

                    if item_resource_name == resource and metadata.get('name', None) == resource_name:
                        namespace = metadata.get('namespace', None)

                        # If the helm templates does not contain a namespace (which is seen as best practise, see
                        # https://github.com/helm/helm/issues/5465. This "fakes" the real namespace that would be used
                        # for helm install/upgrade.
                        if namespace == 'default' and deployment and deployment.namespace != namespace:
                            namespace = deployment.namespace

                        found = True

                if not found:
                    log.warning(f'Could not find metadata for resource: {colors.bold(resource)}, '
                                f'name: {colors.bold(resource_name)}, ignore ...')

            namespace_description = ''
            if manifests:
                namespace_description = f'namespace: {colors.bold(namespace) if namespace else colors.orange("all")}, '

            log.info(f'{prefix} {namespace_description}'
                     f'resource: {colors.bold(resource)}, '
                     f'name: {colors.bold(resource_name)}: '
                     f'{colors.gray(status) if status == "unchanged" else colors.green(status)}')
