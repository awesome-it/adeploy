import json
from adeploy.common import colors
from adeploy.common.yaml.find import find


def update_resources(log, doc, deployment):

    default_resource = deployment.config.get('_resources', False)
    if default_resource:

        for containers in find(doc, ['containers', 'initContainers']):
            for container in containers:

                doc_name = doc.get('metadata').get('name')
                container_name = container.get('name')
                resources = container.get('resources', {})

                log.debug(f'...... Updating limits and requests for {colors.blue(doc_name + "/" + container_name)} ...')
                for type in ['limits', 'requests']:

                    r = {}

                    # These are defaults and can be overwritten by the manifest
                    r.update(default_resource.get(type, {}))
                    r.update(default_resource.get(doc_name, {}).get(type, {}))

                    # Add resources from the manifest
                    r.update(resources.get(type, {}))

                    # The following explicitly overwrites the values from the doc
                    r.update(default_resource.get(doc_name, {}).get(container_name, {}).get(type, {}))

                    resources[type] = r
                    log.debug(f'......... Setting {type}: {json.dumps(r)}')