from logging import Logger

from adeploy.common.deployment import Deployment
from adeploy.common.yaml.labels import update_labels
from adeploy.common.yaml.probes import update_probes
from adeploy.common.yaml.resources import update_resources
from ruamel.yaml.comments import CommentedMap


def update(log: Logger, data: CommentedMap, deployment: Deployment):
    update_probes(log, data, deployment)
    update_labels(log, data, deployment)
    update_resources(log, data, deployment)
    return data
