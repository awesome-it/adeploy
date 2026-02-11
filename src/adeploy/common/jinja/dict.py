import re


class JinjaDict(dict):

    delimiter = None

    def __init__(self, dict, delimiter: str = None):
        super().__init__(dict)
        if delimiter:
            self.delimiter = re.compile(delimiter)
        else:
            self.delimiter = re.compile('[.:]')

    def get(self, key, default=None):
        data = super().get(key)

        if data is None:
            data = self.get_path(key)\

        if data is None:
            data = default

        return JinjaDict(data) if isinstance(data, dict) else data

    def get_path(self, key):
        data = None
        for sub_key in re.split(self.delimiter, key):
            if not data:
                data = super().get(sub_key)
                continue

            if sub_key not in data:
                return None

            data = data.get(sub_key)

        return data

    def get_dict(self):
        obj = {}
        for n, v in self.items():
            obj[n] = v
        return obj