from ruamel.yaml import YAML, StringIO
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.parser import ParserError
from adeploy.common.yaml.labels import update_labels
from adeploy.common.yaml.probes import update_probes
from adeploy.common.yaml.resources import update_resources


def update(log, data, deployment):

    processed_data = []

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True

    for doc in data.split("---\n"):
        doc = doc.strip()
        if len(doc) > 0:
            try:
                doc = yaml.load(doc)

                update_probes(log, doc, deployment)
                update_labels(log, doc, deployment)
                update_resources(log, doc, deployment)

                stream = StringIO()
                yaml.dump(doc, stream)
                doc = stream.getvalue()

            except DuplicateKeyError as e:
                log.error(f'...... Constructor error: {e}')
                log.error(f'......              data: {doc}')
                pass

            except ScannerError as e:
                log.error(f'...... Scanner error: {e}')
                log.error(f'......         data: {doc}')
                pass
            
            except ParserError as e:
                log.error(f'...... Parser error: {e}')
                log.error(f'......         data: {doc}')
                pass
            
        processed_data.append(doc)

    return "---\n".join(processed_data)