import base64
import hashlib
from pathlib import Path
from typing import Union

import yaml as _yaml
import adeploy.common.jinja.dict as jinja_dict


def yaml(obj: Union[jinja_dict.JinjaDict, dict], flow_style: bool):
    """Returns yaml for object"""
    if isinstance(obj, jinja_dict.JinjaDict):
        obj = obj.get_dict()
    return _yaml.safe_dump(obj, default_flow_style=flow_style)


def quote(string: str):
    return '"' + str(string).replace('"', '\\"') + '"'


def base64_encode(string: str):
    return str(base64.b64encode(string.encode('utf-8')), 'utf-8')


def sha256sum(string: str):
    hash = hashlib.sha256()
    hash.update(string.encode('utf-8'))
    return hash.hexdigest()


def basename(path: str):
    return Path(path).name