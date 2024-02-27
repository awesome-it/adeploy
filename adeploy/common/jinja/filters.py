import base64
import hashlib
from pathlib import Path
from typing import Union

import yaml as _yaml
import adeploy.common.jinja.dict as jinja_dict


def yaml(obj: Union[jinja_dict.JinjaDict, dict], flow_style: bool):
    """ Converts given object into YAML formatted string

    This filter is using [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation) to convert the given object into a
    YAML formatted string.

    Args:
        obj: The object to convert into the YAML formatted string.
        flow_style: By default, PyYAML chooses the style of a collection depending on whether it has nested collections.
            If a collection has nested collections, it will be assigned the block style. Otherwise it will have the flow
            style. Set `True` or `False` to explicitly define the flow style to use.

    Returns:
        str: YAML representation of the given data.

    !!!example "Example: Using the `yaml()` filter with `flow_style=False`"

        ```{.yaml title="templates/ingress.yml" hl_lines="5"}
        --8<-- "examples/jinja/002-secrets-ingress/templates/ingress.yml:example-filter-yaml"
        ```

        Will result in the following:

        ```{.yaml title="build/jinja/playground/002-secrets-ingress/prod/ingress.yml" hl_lines="5-7"}
        --8<-- "examples/jinja/002-secrets-ingress/build/jinja/playground/002-secrets-ingress/prod/ingress.yml:example-filter-yaml"
        ```
    """
    if isinstance(obj, jinja_dict.JinjaDict):
        obj = obj.get_dict()
    return _yaml.safe_dump(obj, default_flow_style=flow_style)


def quote(string: str):
    """ Quotes the given string

    This filter add quotations `"..."` around the given string and escapes any quotations inside the string.

    Args:
        string: The string to be quoted.

    Returns:
        str: String with quotations.

    !!!example "Example: Quote a property value"

        ```{.yaml title="templates/deployment.yml" hl_lines="7"}
        metadata:
          name: my-deployment
          namespace: playground
          labels:
            app.kubernetes.io/instance: prod
            app.kubernetes.io/component: nginx
            app.kubernetes.io/version: {{ version('nginx') | quote }}
        ```

    """
    return '"' + str(string).replace('"', '\\"') + '"'


def base64_encode(string: str):
    """ Returns base64-encoded string

    The given UTF-8 string is encoded to base64 using [base64.b64encode](https://docs.python.org/3/library/base64.html).

    Args:
        string: UTF-8 string to be encoded.

    Returns:
        str: Base64-encoded string.

    """
    return str(base64.b64encode(string.encode('utf-8')), 'utf-8')


def sha256sum(string: str):
    """ Creates a SHA256 hash

    Creates a SHA256 hash from the given string using [hashlib.sha256](https://docs.python.org/3/library/hashlib.html#hashlib.sha256).

    Args:
        string: UTF-8 string to be hashed.

    Returns:
        str: Hex representation of SHA265 as string.

    !!!example "Example: Use a SHA265 hash of a config map to trigger a re-creation of k8s API objects on changes"
        ```{.yaml title="template/nginx/deployment.yml" hl_lines="7-9"}
        --8<-- "examples/jinja/003-include/templates/nginx/deployment.yml:example-sha256"
        ```
    """
    hash = hashlib.sha256()
    hash.update(string.encode('utf-8'))
    return hash.hexdigest()


def basename(path: str):
    """ Returns the basename of the given path using [pathlib.Path](https://docs.python.org/3/library/pathlib.html#basic-use).

    Args:
        path: The path to get the basename from.

    Returns:
        str: The basename from the path.
    """
    return Path(path).name