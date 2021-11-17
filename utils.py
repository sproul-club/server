__all__ = [
    'get_random_bits', 'try_parsing_datetime', 'random_slugify',
    'utc_right_now', 'pst_right_now', 'array_diff'
]

import os

from slugify import slugify
import dateutil.parser
import datetime
import pytz


PST = pytz.timezone('America/Los_Angeles')


def get_random_bits(num_bits):
    """
    Utility function to return a string of random characters, with each character ranging
    from 0 to F (hex range). All characters will be alphanumeric and lowercase.
    """

    return os.urandom(num_bits).hex()


def try_parsing_datetime(dt_str):
    """
    Given a datetime string, try to parse it into a datetime object or return None.
    """

    try:
        return dateutil.parser.parse(dt_str)
    except:
        return None


def random_slugify(string, bits=16, max_length=0):
    """
    Given a string, slufigy it by normalizing unconventional characters and whitespace to
    lowercase English alphanumeric characters and dashes, while appending a random bits
    string. This is useful for generating non-conflicting filenames for uploads.

    See https://github.com/un33k/python-slugify#how-to-use for examples on the 'slugify'
    function from the 'python-slugify' library.
    """

    return f'{slugify(string, max_length=max_length)}-{get_random_bits(bits)}'


def utc_right_now():
    """
    Returns a datetime object reflecting the time in UTC as of when this function was called.
    """

    return datetime.datetime.now(tz=pytz.utc).replace(tzinfo=None)


def pst_right_now():
    """
    Returns a datetime object reflecting the time in PST as of when this function was called.

    HACK: Right now, it formats as UTC but dates in PST
    """

    dt_obj = datetime.datetime.now(tz=pytz.utc) + datetime.datetime.now(tz=PST).utcoffset()
    dt_obj = dt_obj.replace(tzinfo=None)
    return dt_obj


def array_diff(arr):
    """
    Given an numeric array, calculate a discrete derivative between the elements. In other words,
    calculate the change between going from one element to the next subsequent element.

    Examples:
    array_diff([1, 2, 4, 7]) == [1, 2, 3]
    array_diff([1, 1, 0, 1]) == [0, -1, 1]

    Note that the array has to have at least 2 elements.

    Source: https://stackoverflow.com/a/2400875
    """

    return [j - i for i, j in zip(arr[:-1], arr[1:])]
