import copy
from typing import Union

from ruamel.yaml import YAML, StringIO
from ruamel.yaml.scanner import ScannerError
from adeploy.common.helpers import dict_update_recursive


def update(log, data, deployment):
    # Skip if no default labels configuration was found
    default_labels = deployment.config.get('_labels', False)
    if not default_labels:
        return data

    processed_data = []

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True

    for doc in data.split("---\n"):
        doc = doc.strip()
        if len(doc) > 0:
            try:
                doc = yaml.load(doc)
                for label in find_labels(doc):
                    dict_update_recursive(label, default_labels)

                stream = StringIO()
                yaml.dump(doc, stream)
                doc = stream.getvalue()

            except ScannerError as e:
                log.error(f'...... Scanner error: {e}')
                log.error(f'......         data: {doc}')
                pass

        processed_data.append(doc)

    return "---\n".join(processed_data)


def find_labels(doc: Union[list,dict], kind=None, labels=None):

    if labels is None:
        labels = []

    if kind is None:
        kind = doc.get('kind')

    if isinstance(doc, list):
        for elem in doc:
            find_labels(elem, kind, labels)

    elif isinstance(doc, dict):
        for k in doc:
            v = doc[k]

            if k == 'metadata':

                # Create labels if they do not exist
                if not 'labels' in v:
                    v['labels'] = {}

                labels.append(v.get('labels'))

            # Selectors in services
            elif kind.lower() == 'service' and k == 'spec' and v.get('selector', False):
                labels.append(v.get('selector'))

            # Match labels in deployments/statefulsets/daemonsets
            elif kind.lower() in ['deployment', 'statefulset', 'daemonset'] and k == 'selector':
                labels.append(v.get('matchLabels'))


            else:
                find_labels(v, kind, labels)

    return labels