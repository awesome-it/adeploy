import subprocess
from adeploy.common.helpers import run_command
from adeploy.common.deployment import Deployment
from adeploy.common import colors


def helm_repo_add(log, repo, url):
    log.debug(f'Adding helm repo "{colors.bold(repo)}" from {colors.blue(url)} ...')
    return helm(log, ['repo', 'add', repo, url])


def helm_repo_pull(log, repo, name, dest):
    log.debug(f'Pulling chart "{colors.bold(name)}" from helm repo {colors.bold(repo)} to "{colors.bold(dest)}" ...')
    return helm(log, ['pull', f'{repo}/{name}', '--untar', '--untardir', dest])


def helm_template(log, deployment: Deployment, chart_path, values_path):
    return helm(log, ['template', deployment.release, chart_path, '-n', deployment.namespace, '-f', values_path])


def helm_install(log, deployment: Deployment, chart_path, values_path, dry_run=True) -> subprocess.CompletedProcess:
    args = ['upgrade', '--install', deployment.release, chart_path, '-n', deployment.namespace, '-f', values_path, '-o', 'json']
    if dry_run:
        args.append('--dry-run')
    return helm(log, args)


def helm(log, args) -> subprocess.CompletedProcess:
    cmd = ['helm']
    cmd.extend(args)
    return run_command(log, cmd)