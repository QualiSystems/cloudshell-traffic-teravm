import sys


def to_int_or_maxint(param):
    try:
        return int(param)

    except:
        return sys.maxint


def _to_lower_and_underscore(arg):
    """
    :type arg: str
    :rtype: str
    """
    return arg.lower().replace(' ', '_')


def lowercase_and_underscores(dictionary):
    """
    :type dictionary: dict
    :rtype: dict
    """
    return {_to_lower_and_underscore(k): v for k, v in dictionary.iteritems()}
