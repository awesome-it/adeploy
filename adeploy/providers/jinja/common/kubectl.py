import subprocess

from adeploy.common import colors


def kubectl_apply(log, manifest_path, namespace=None, dry_run=None):
    args = ['apply', '--output', 'json', '-f', str(manifest_path)]
    if dry_run:
        args.append(f'--dry-run={dry_run}')

    return kubectl(log, namespace, args)


def kubectl(log, namespace, args):
    cmd = ['kubectl', '-n', namespace]
    cmd.extend(args)
    log.debug(f'Executing command {colors.bold(" ".join(cmd))}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    result.check_returncode()
    return result