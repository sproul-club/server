__all__ = [
    'get_random_bits', 'datetime_or_null', 'random_slugify', 'pst_right_now'
]

import os

from slugify import slugify
import dateutil.parser
import datetime
import pytz

PST = pytz.timezone('America/Los_Angeles')

get_random_bits = lambda num_bits: os.urandom(num_bits).hex()

def datetime_or_null(dt_obj):
    try:
        return dateutil.parser.parse(dt_obj)
    except:
        return None

random_slugify = lambda string, bits=16, max_length=0: f'{slugify(string, max_length=max_length)}-{os.urandom(bits).hex()}'

# HACK: Right now, it formats as UTC but dates in PST
def pst_right_now():
    dt_obj = datetime.datetime.now(tz=pytz.utc) + datetime.datetime.now(tz=PST).utcoffset()
    dt_obj = dt_obj.replace(tzinfo=None)
    return dt_obj
