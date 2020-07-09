import subprocess

from adeploy.common import colors


def kubectl_apply(log, manifest_path, namespace=None, dry_run=None) -> subprocess.CompletedProcess:
    args = ['apply', '-f', str(manifest_path)]
    if dry_run:
        args.append(f'--dry-run={dry_run}')

    return kubectl(log, namespace, args)


def kubectl(log, namespace, args) -> subprocess.CompletedProcess:
    cmd = ['kubectl', '-n', namespace]
    cmd.extend(args)
    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()
    return result


def parse_kubectrl_apply(log, stdout, prefix='...'):
    for line in stdout.split('\n'):
        token = line.split(' ')
        if len(token) > 3:
            resource, resource_name = token[0].split('/')
            status = token[1]

            log.info(f'{prefix} {resource}/{colors.bold(resource_name)}: '
                     f'{colors.gray(status) if status == "unchanged" else colors.green(status)}')