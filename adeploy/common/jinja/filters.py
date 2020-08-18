import base64
import hashlib

import yaml as _yaml


def yaml(obj, flow_style):
    """Returns yaml for object"""
    return _yaml.safe_dump(obj, default_flow_style=flow_style)


def quote(string):
    return '"' + str(string).replace('"', '\\"') + '"'


def base64_encode(string):
    return str(base64.b64encode(string.encode('utf-8')), 'utf-8')


def sha256sum(string: str):
    hash = hashlib.sha256()
    hash.update(string.encode('utf-8'))
    return hash.hexdigest()