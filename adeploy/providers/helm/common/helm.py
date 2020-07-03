import subprocess
from adeploy.common import run_command, colors


def helm_repo_add(log, repo, url):
    log.info(f'Adding helm repo "{colors.bold(repo)}" from {colors.blue(url)} ...')
    return helm(log, ['repo', 'add', repo, url])


def helm_repo_pull(log, repo, name, dest):
    log.info(f'Pulling chart "{colors.bold(name)}" from helm repo {colors.bold(repo)} to "{colors.bold(dest)}" ...')
    return helm(log, ['pull', f'{repo}/{name}', '--untar', '--untardir', dest])


def helm_template(log, name, chart_path):
    return helm(log, ['template', f'{name}', chart_path])


def helm(log, args) -> subprocess.CompletedProcess:
    cmd = ['helm']
    cmd.extend(args)
    return run_command(log, cmd)