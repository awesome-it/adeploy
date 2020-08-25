import re


class JinjaDict(dict):

    delimiter = None
    dict: dict = None

    def __init__(self, dict, delimiter: str = None):
        super().__init__(dict)
        if delimiter:
            self.delimiter = re.compile(delimiter)
        else:
            self.delimiter = re.compile('\.|:')

    def get(self, key, default=None):
        return super().get(key) or self.get_path(key) or default

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