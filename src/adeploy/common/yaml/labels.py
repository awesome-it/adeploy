from typing import Union
from adeploy.common.helpers import dict_update_recursive


def update_labels(log, doc, deployment):

    # Skip if no default labels configuration was found
    default_labels = deployment.config.get('_labels', False)
    if default_labels:
        for label in find_labels(doc):
            dict_update_recursive(label, default_labels)


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