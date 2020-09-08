import base64
import hashlib

import yaml as _yaml
import adeploy.common.jinja.dict as jinja_dict


def yaml(obj, flow_style):
    """Returns yaml for object"""
    if isinstance(obj, jinja_dict.JinjaDict):
        obj = obj.get_dict()
    return _yaml.safe_dump(obj, default_flow_style=flow_style)


def quote(string):
    return '"' + str(string).replace('"', '\\"') + '"'


def base64_encode(string):
    return str(base64.b64encode(string.encode('utf-8')), 'utf-8')


def sha256sum(string: str):
    hash = hashlib.sha256()
    hash.update(string.encode('utf-8'))
    return hash.hexdigest()