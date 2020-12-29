import json
import textwrap

import jinja2

import adeploy.common.colors as colors
import adeploy.common.secret as secret
import adeploy.common.errors as errors


def create__get_version(deployment, **kwargs):
    def get_version(package: str):
        if not deployment:
            raise errors.RenderError('get_version() or version() cannot be used here')
        return deployment.config.get('versions', {}).get(package, 'latest')

    return get_version


# Alias for get_version()
def create__version(deployment, **kwargs):
    return create__get_version(deployment, **kwargs)


def create__create_generic_secret(deployment, **create_kwargs):
    log = create_kwargs.get('log', None)

    def create_secret(name: str = None, use_pass: bool = True, custom_cmd: bool = False, as_ref: bool = False,
                      data: dict = None, **kwargs):
        if not deployment:
            raise errors.RenderError('create_secret() cannot be used here')
        s = secret.GenericSecret(deployment, data or kwargs, name, use_pass, custom_cmd)
        if secret.Secret.register(s) and log:
            log.info(f'Registered generic secret "{colors.bold(s.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')

        if not as_ref:
            return s.name

        keys = (data or kwargs).keys()
        if len(keys) == 0:
            raise errors.RenderError(
                'You must specify at least a secret key if using create_secret() with key_ref = True')

        return json.dumps({'name': s.name, 'key': list(keys)[0]})

    return create_secret


# Alias for create_generic_secret()
def create__create_secret(deployment, **kwargs):
    return create__create_generic_secret(deployment, **kwargs)


def create__create_tls_secret(deployment, **kwargs):
    log = kwargs.get('log')

    def create_tls_secret(cert_data: str, key_data: str, name: str, use_pass: bool = True, custom_cmd: bool = False):
        if not deployment:
            raise errors.RenderError('create_tls_secret() cannot be used here')
        s = secret.TlsSecret(deployment, name, cert_data, key_data, use_pass, custom_cmd)
        if secret.Secret.register(s) and log:
            log.info(f'Registering TLS secret "{colors.bold(s.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return s.name

    return create_tls_secret


def create__create_docker_registry_secret(deployment, **kwargs):
    log = kwargs.get('log')

    def create_docker_registry_secret(server: str, username: str, password: str, email: str = None, name: str = None,
                                      use_pass: bool = True, custom_cmd: bool = False):
        if not deployment:
            raise errors.RenderError('create_docker_registry_secret() cannot be used here')
        s = secret.DockerRegistrySecret(deployment, server, username, password, email, name, use_pass, custom_cmd)
        if secret.Secret.register(s) and log:
            log.info(f'Registering docker registry secret "{colors.bold(s.name)}" '
                     f'for deployment "{colors.blue(deployment)} ...')
        return s.name

    return create_docker_registry_secret


def create__include_file(deployment, **kwargs):
    env = kwargs.get('env')
    log = kwargs.get('log', None)
    values = {}
    if deployment:
        values = deployment.get_template_values()

    def include_file(path: str, direct: bool = False, render: bool = True, indent: int = 4):
        prefix = '|\n' if not direct else ''
        if render:
            try:
                data = env.get_template(path).render(**values)

            except jinja2.exceptions.TemplateNotFound as e:
                log and log.debug(f'Used Jinja variables: {json.dumps(values)}')
                raise errors.RenderError(f'Jinja template error: Template "{e}" not found in "{path}"')
            except jinja2.exceptions.TemplateError as e:
                log and log.debug(f'Used Jinja variables: {json.dumps(values)}')
                raise errors.RenderError(f'Jinja template error in "{colors.bold(path)}": {e}')
        else:
            data, _, _ = env.loader.get_source(env, path)
        return f'{prefix}{textwrap.indent(data, indent * " ")}'

    return include_file


# See https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/#labels
def create__create_labels(deployment, **kwargs):
    default_instance = deployment.release if deployment else None
    default_part_of = deployment.name if deployment else None

    def create_labels(name: str = None,
                      instance: str = default_instance,
                      version: str = None,
                      component: str = None,
                      part_of: str = default_part_of,
                      managed_by: str = 'adeploy',
                      labels: dict = None, **kwargs):

        if labels is None:
            labels = kwargs

        if name:
            labels['app.kubernetes.io/name'] = name
        if instance:
            labels['app.kubernetes.io/instance'] = instance
        if version:
            labels['app.kubernetes.io/version'] = version
        if component:
            labels['app.kubernetes.io/component'] = component
        if part_of:
            labels['app.kubernetes.io/part-of'] = part_of
        if managed_by:
            labels['app.kubernetes.io/managed-by'] = managed_by

        return json.dumps(labels)

    return create_labels
