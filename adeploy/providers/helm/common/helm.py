import subprocess
from logging import Logger
from pathlib import Path

import yaml

from adeploy.common.helpers import run_command
from adeploy.common.deployment import Deployment
from adeploy.common import colors


def helm_repo_add(log, repo, url):
    log.debug(f'Adding helm repo "{colors.bold(repo)}" from {colors.blue(url)} ...')
    return helm(log, ['repo', 'add', repo, url, '--force-update'])


def helm_repo_pull(log, repo, name, version, dest):
    log.debug(f'Pulling chart "{colors.bold(name)}" from helm repo {colors.bold(repo)} to "{colors.bold(dest)}" ...')
    return helm(log,
                ['pull', f'{repo}/{name}'] +
                (['--version', version] if version else []) +
                ['--untar', '--untardir', dest])


def helm_template(log, deployment: Deployment, chart_path, values_path, skip_validate: bool = False):
    args = ['template'] + (['--validate'] if not skip_validate else []) + [deployment.release, chart_path, '-n',
                                                                           deployment.namespace, '-f', values_path]

    chart_version, old_app_version = helm_prepare_chart(log, deployment, chart_path)

    if chart_version:
        args += ['--version', chart_version]

    result = helm(log, args)

    if old_app_version:
        helm_update_app_version(chart_path, old_app_version)

    return result


def helm_install(log, deployment: Deployment, chart_path, values_path, dry_run=True) -> subprocess.CompletedProcess:
    args = ['upgrade', '--install', deployment.release, chart_path, '-n', deployment.namespace, '-f', values_path, '-o',
            'json']

    chart_version, old_app_version = helm_prepare_chart(log, deployment, chart_path)

    if chart_version:
        args += ['--version', chart_version]

    if dry_run:
        args.append('--dry-run')

    result = helm(log, args)

    if old_app_version:
        helm_update_app_version(chart_path, old_app_version)

    return result


def helm(log, args) -> subprocess.CompletedProcess:
    return run_command(log, ['helm'] + args)


def helm_prepare_chart(log: Logger, deployment: Deployment, chart_path: Path) -> (str, str):
    chart = deployment.config.get('_chart', {})
    chart_version = chart.get('version', None)
    app_version = chart.get('appVersion', None)

    old_app_version = None

    if app_version:
        log.debug(f'Using app version {colors.bold(app_version)} from defaults ...')
        old_app_version = helm_update_app_version(chart_path, app_version)

    if chart_version:
        log.debug(f'Using chart version {colors.bold(chart_version)} from defaults ...')

    return chart_version, old_app_version


def helm_update_app_version(chart_path: Path, app_version: str) -> str:
    with open(str(chart_path.joinpath('Chart.yaml')), 'r+') as fd:
        chart = yaml.load(fd.read(), Loader=yaml.FullLoader)
        old_version = chart.get('appVersion', None)
        chart['appVersion'] = app_version

        fd.seek(0)
        yaml.dump(chart, fd)
        fd.truncate()

    return old_version
