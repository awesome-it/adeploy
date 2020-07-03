import base64

import yaml as _yaml


def yaml(obj, flow_style):
    """Returns yaml for object"""
    return _yaml.safe_dump(obj, default_flow_style=flow_style)


def quote(string):
    return '"' + str(string).replace('"', '\\"') + '"'


def base64_encode(string):
    return str(base64.b64encode(string.encode('utf-8')), 'utf-8')