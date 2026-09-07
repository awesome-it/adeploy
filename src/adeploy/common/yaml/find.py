def find(d, tags: str | list):
    if not d:
        return []

    if isinstance(tags, str):
        tags = [tags]

    for tag in tags:
        if tag in d:
            yield d[tag]

    for v in d.values():
        if isinstance(v, dict):
            yield from find(v, tags)
