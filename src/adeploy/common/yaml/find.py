from typing import Union


def find(d, tags: Union[str,list]):

    if not d:
        return []

    if isinstance(tags, str):
        tags = [tags]

    for tag in tags:
        if tag in d:
            yield d[tag]

    for k, v in d.items():
        if isinstance(v, dict):
            for i in find(v, tags):
                yield i