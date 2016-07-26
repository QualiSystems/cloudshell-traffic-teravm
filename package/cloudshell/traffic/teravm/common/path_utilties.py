import re


def combine_path(*args):
    path_parts = []
    for path in args:
        path_parts.extend(re.split('/|\\\\', path))
    combined_path = '/'.join(path_parts)
    return combined_path
