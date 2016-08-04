import sys


def to_int_or_maxint(param):
    try:
        return int(param)

    except:
        return sys.maxint