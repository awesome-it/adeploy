import json


class HelmOutput:

    info: dict = None
    status: str = None
    first_deployed: str = None
    last_deployed: str = None
    description: str = None
    chart: dict = None
    chart_version: str = None
    app_version: str = None

    def __init__(self, stdout):

        result = json.loads(stdout)
        self.info = result.get('info')
        self.status = self.info.get('status')
        self.first_deployed = self.info.get('first_deployed')
        self.last_deployed = self.info.get('last_deployed')
        self.description = self.info.get('description')

        self.chart = result.get('chart')
        self.chart_version = self.chart.get('metadata').get('version')
        self.app_version = self.chart.get('metadata').get('appVersion')