"""
The following functions are globally available in the `default.yml`, the namespace/release configuration or
in the Jinja templates in your `templates` folder.
"""
import os
import pathlib
import uuid
from logging import Logger

import shortuuid
import string
import json
import textwrap
import urllib.request
import jinja2

from typing import Union

import adeploy.common.colors as colors
import adeploy.common.secret as secret
import adeploy.common.errors as errors


class Handler(object):

    def __init__(self, env: jinja2.Environment, deployment=None, log: Logger = None, templates_dir: str = None):
        self.env = env
        self.deployment = deployment
        self.log = log
        self.templates_dir = templates_dir

    def uuid(self, short: bool = False, length: int = 8) -> str:
        """ Generates a UUIDv4 or a short UUID

        Args:
            short: Set `True` to return a ShortUUID(), otherwise a UUIDv4 is returned.
            length: Random string length if using ShortUUID().

        Returns:
            str: The generated UUID

        !!!Example

            You can use this Jinja function to create unique names i.e. for Jobs:

            ```{.jinja hl_lines="4"}
            apiVersion: batch/v1
            kind: Job
            metadata:
                name: {{ name }}-{{ release }}-my-job-{{ uuid() }}
                namespace: {{ namespace }}
                labels: {{ job.labels }}
            ```
        """
        return str(uuid.uuid4()) if not short else shortuuid.ShortUUID(
            alphabet=string.ascii_lowercase + string.digits).random(length)

    def version(self, package: str) -> str:
        """ Returns the version from the given package

        This returns the version from the dict in `versions` that can be specified in `defaults.yml` and in the
        namespace/release configuration.

        If `versions` is specified in both configurations, it will be merged while
        the namespace/release configuration takes precedence. See [Usage#variables](../usage.md#versions).

        Args:
            package: The package to retrieve the version from.

        Returns:
            str: The version or "latest" if no version was defined.

        !!!Example
            ```{.jinja hl_lines="4"}
            spec:
              containers:
                - name: main
                  image: {{ nginx.image }}:{{ version('nginx') }}
                  imagePullPolicy: Always
            ```

        """
        if not self.deployment:
            raise errors.RenderError('get_version() or version() cannot be used here!')

        return self.deployment.config.get('versions', {}).get(package, 'latest')

    def get_version(self, package: str):
        """ Alias for [version()](functions.md#adeploy.common.jinja.globals.Handler.version) """
        return self.version(package)

    def create_labels(self,
                      name: str = None,
                      instance: str = None,
                      version: str = None,
                      component: str = None,
                      part_of: str = None,
                      managed_by: str = 'adeploy',
                      labels: Union[dict, list] = None, **kwargs) -> str:
        """ Creates a dict of custom and common labels

        This can be used to create (and update) label objects ready to use in k8s manifests.

        Next to the specified custom labels, a set of standardised labels following best practise can be generated,
        see [Recommended Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/#labels).

        Args:
            name: Creates standard label `app.kubernetes.io/name`, the name of the application (e.g. "mysql").
            instance: Creates standard label `app.kubernetes.io/instance`, a unique name identifying
                the instance of an application (e.g. "mysql-abc").
            version: Creates standard label `app.kubernetes.io/version`, the current version of the application
                (e.g., a [SemVer 1.0](https://semver.org/spec/v1.0.0.html), revision hash, etc.)
            component: Creates standard label `app.kubernetes.io/component`, the component within the architecture
                (e.g. "database")
            part_of: Creates standard label `app.kubernetes.io/part-of`, the name of a higher level application
                this one is part of (e.g. "wordpress").
            managed_by: Creates standard label `app.kubernetes.io/managed-by`, the tool being used to manage the
                operation of an application (e.g. "adpeloy")
            labels: An optional dict or list with custom labels to use.
            **kwargs: Optionally, more labels can be specified as args.

        Returns:
            str: A string with a JSON object with the specified labels ready to add to k8s manifests

        You can `create_labels()` to create a global label object i.e. in your `defaults.yml` and use `create_labels()`
        a second time e.g. in your `templates/deployment.yml` to extend the labels with object related labels. See
        [Labels](labels.md) and [Nested Labels](labels.md#nested-labels) for more info.

        !!!example "Example: Nested Labels"
            --8<-- "docs/common/labels.md:nested_labels"
        """

        if instance is None and self.deployment:
            instance = self.deployment.release

        if part_of is None and self.deployment:
            part_of = self.deployment.name

        if labels is not None:
            if isinstance(labels, list):
                flat_labels = {}
                for l in labels:
                    flat_labels.update(l)
                labels = flat_labels
            else:
                # Make a copy to not specified labels dict.
                labels = labels.copy()

            labels.update(kwargs)
        else:
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

    def include_file(self, path: str, direct: bool = False, render: bool = True, indent: int = 4, skip=None,
                     escape=None) -> str:
        """ Include and optionally render arbitrary files into your manifest

        Reads the content of the specified file and returns the corresponding format to include the read content
        into your YAML manifest file or your config map.

        See [Includes](../includes.md) for details and examples.

        Args:
            path: The path to the file to include. This path must be relative to the project directory where
                `defaults.yml` is located.
            direct: Set `True` to skip adding YAML block formatting. This is useful if you include
                [YAML parts](../includes.md#include-yaml-parts) directly to a YAML document.
            render: Set `True` to render the content after reading using `adeploy`.
            indent: Indents the content block for the specified amount.
            skip: A list of characters to remove from the read file content.
                See [Skip & Escape](includes.md#skip-escape).
            escape: A list of characters to esdacpe from the read file content.
                See [Skip & Escape](includes.md#skip-escape).

        Returns:
            str: The (rendered) file content in the requested format to include it either into a YAML document or
                as a block string to use it as value i.e. in config maps.

        !!!example "Example: Include config files to config maps:"

            ```{.yaml title="templates/common/configmap.yml" hl_lines="11-14"}
            --8<-- "examples/jinja/003-include/templates/common/configmap.yml"
            ```

        !!!example "Example: Render and include YAML parts into YAML documents:"

            === "YAML Part (`__env.yml`)"

                ```{.yaml title="templates/common/__env.yml" hl_lines="11-14"}
                --8<-- "examples/jinja/003-include/templates/common/__env.yml"
                ```

            === "YAML Document (`deployment.yml`)"

                ```{.yaml title="templates/redis/deployment.yml" hl_lines="16"}
                --8<-- "examples/jinja/003-include/templates/redis/deployment.yml:template"
                ```

        !!!example "Example: Download and include CRDs from GitHub:"

            ```{.jinja title="templates/crds.yml"}
            {{ include_file('https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml', direct=True, render=False, indent=0) }}
            ```
        """

        if not skip:
            skip = []

        if not escape:
            escape = []

        tmp_path = None
        if path.startswith('http'):
            tmp_path, _ = urllib.request.urlretrieve(path)
            self.env.loader.searchpath.append(os.path.dirname(tmp_path))
            path = os.path.basename(tmp_path)

        if render:

            values = {}
            if self.deployment:
                values = self.deployment.get_template_values()

            try:
                data = self.env.get_template(path).render(**values)

            except jinja2.exceptions.TemplateNotFound as e:
                self.log and self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
                raise errors.RenderError(f'Jinja template error: Template "{path}" not found.')
            except jinja2.exceptions.TemplateError as e:
                self.log and self.log.debug(f'Used Jinja variables: {json.dumps(values)}')
                raise errors.RenderError(f'Jinja template error in "{colors.bold(path)}": {e}')
        else:
            data, _, _ = self.env.loader.get_source(self.env, path)

        # Clean temporary stuff
        if tmp_path is not None:
            self.env.loader.searchpath = filter(lambda p: p != os.path.dirname(path), self.env.loader.searchpath)
            os.remove(tmp_path)

        if direct:
            prefix = '\n'
        else:
            prefix = '|\n'

        for token in skip:
            replace = ''
            if type(token) is tuple:
                token, replace = token
            data = data.replace(token, replace)
            prefix = prefix.replace(token, replace)

        for token in escape:
            data = data.replace(token, f'\\{token}')
            prefix = prefix.replace(token, f'\\{token}')

        return f'{prefix}{textwrap.indent(data, indent * " ")}'

    def list_dir(self, dir: str, direct: bool = False, render: bool = True, indent: int = 4, skip=None, escape=None) -> dict:
        """ Include files from a directory

        This will include and optionally render all files from the given directory. Expect the `dir` arg, you can
        pass the same args to `list_dir()` as for [`include_file()`](functions.md#adeploy.common.jinja.global.Handler.include_file)
        to control how the files inside dir should be handled.

        See (Include Arbitrary Files)[includes.md#include-arbitrary-files] for details and examples.

        Args:
            dir: The path to the directory to include. This path must be relative to the project directory where
                `defaults.yml` is located.
            direct: See [`include_file()`](functions.md#adeploy.common.jinja.global.Handler.include_file)
            render: See [`include_file()`](functions.md#adeploy.common.jinja.global.Handler.include_file)
            indent: See [`include_file()`](functions.md#adeploy.common.jinja.global.Handler.include_file)
            skip: See [`include_file()`](functions.md#adeploy.common.jinja.global.Handler.include_file)
            escape: See [`include_file()`](functions.md#adeploy.common.jinja.global.Handler.include_file)

        Returns:
            dict: A dict with filename as key and the formatted content as value.

        !!!example "Example: Include all files form `files/conf.d` into a config map"
            --8<-- "docs/common/includes.md:example"
        """
        contents = {}
        for item in pathlib.Path(pathlib.Path(self.templates_dir) / dir).iterdir():
            if item.is_file():
                self.env.loader.searchpath.append(str(item.parent))
                contents[item.name] = self.include_file(
                    str(item.relative_to(self.templates_dir)), direct, render, indent, skip, escape)

        return contents

    def create_secret(self, name: str = None, use_pass: bool = True, use_gopass_cat: bool = True,
                      custom_cmd: bool = False, as_ref: bool = False,
                      data: dict = None, **kwargs):

        """ Create k8s secrets

        TODO: TBC

        Args:
            name:
            use_pass:
            use_gopass_cat:
            custom_cmd:
            as_ref:
            data:
            **kwargs:

        Returns:

        """

        if not self.deployment:
            raise errors.RenderError('create_secret() cannot be used here')

        s = secret.GenericSecret(self.deployment, data or kwargs, name, use_pass, use_gopass_cat, custom_cmd)
        if secret.Secret.register(s) and self.log:
            self.log.info(f'Registered generic secret "{colors.bold(s.name)}" '
                          f'for deployment "{colors.blue(self.deployment)} ...')

        if not as_ref:
            return s.name

        keys = (data or kwargs).keys()
        if len(keys) == 0:
            raise errors.RenderError(
                'You must specify at least a secret key if using create_secret() with key_ref = True')

        return json.dumps({'name': s.name, 'key': list(keys)[0]})

    def create_tls_secret(self, cert: str, key: str, name: str = None, use_pass: bool = True, use_gopass_cat: bool = True,
                          custom_cmd: bool = False):

        if not self.deployment:
            raise errors.RenderError('create_tls_secret() cannot be used here')

        s = secret.TlsSecret(deployment=self.deployment, name=name, cert=cert, key=key, use_pass=use_pass,
                             use_gopass_cat=use_gopass_cat,
                             custom_cmd=custom_cmd)

        if secret.Secret.register(s) and self.log:
            self.log.info(f'Registering TLS secret "{colors.bold(s.name)}" '
                          f'for deployment "{colors.blue(self.deployment)} ...')
        return s.name

    def create_docker_registry_secret(self, server: str, username: str, password: str, email: str = None, name: str = None,
                                      use_pass: bool = True, custom_cmd: bool = False):
        if not self.deployment:
            raise errors.RenderError('create_docker_registry_secret() cannot be used here')

        s = secret.DockerRegistrySecret(self.deployment, server, username, password, email, name, use_pass, custom_cmd)
        if secret.Secret.register(s) and self.log:
            self.log.info(f'Registering docker registry secret "{colors.bold(s.name)}" '
                     f'for deployment "{colors.blue(self.deployment)} ...')

        return s.name