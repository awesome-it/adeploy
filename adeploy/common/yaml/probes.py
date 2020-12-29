import copy
from adeploy.common import colors
from adeploy.common.helpers import dict_update_recursive


def update_probes(log, doc, deployment):

    # Skip if no default probes configuration was found
    default_probes = deployment.config.get('_probes', False)
    if default_probes:
        for type in ['readiness', 'liveness', 'startup']:
            probe = find_probe(doc, f'{type}Probe')
            if probe:
                doc_name = doc.get('metadata', {}).get('name', None)
                default_probes = copy.deepcopy(default_probes)
                default_probe = dict_update_recursive(default_probes.get(type, None),
                                                      default_probes.get(doc_name, {}).get(type, None))
                if default_probe:
                    log.debug(f"...... Updating {colors.bold(type)} probe "
                              f"for \"{colors.bold(doc_name)}\": {str(default_probe)}")

                    for k, v in default_probe.items():
                        probe[to_camel_case(k)] = v


def find_probe(doc, probe):
    if isinstance(doc, list):
        for elem in doc:
            x = find_probe(elem, probe)
            if x is not None:
                return x
    elif isinstance(doc, dict):
        for k in doc:
            v = doc[k]
            if k == probe:
                return v
            x = find_probe(v, probe)
            if x is not None:
                return x
    return None


def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])
