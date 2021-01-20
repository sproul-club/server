__all__ = [
    'EmailVerifier', 'EmailSender', 'ImageManager', 'PasswordEnforcer',
    'validate_json', 'mongo_aggregations',
    'role_required', 'confirmed_account_required',
    'query_to_objects', 'query_to_objects_full', 'get_random_bits',
    'datetime_or_null', 'slugify', 'random_slugify'
]

import json

from slugify import slugify
import dateutil.parser

from flask_utils.email_manager import EmailVerifier, EmailSender
from flask_utils.image_manager import ImageManager
from flask_utils.password_enforcer import PasswordEnforcer
from flask_utils.schema_validator import validate_json
from flask_utils.role_enforcer import role_required
from flask_utils.confirm_enforcer import confirmed_account_required
from flask_utils import mongo_aggregations

query_to_objects = lambda query: json.loads(query.to_json())
query_to_objects_full = lambda query: json.loads(query.to_json(follow_reference=True))

get_random_bits = lambda num_bits: os.urandom(num_bits).hex()

def datetime_or_null(dt_obj):
    try:
        return dateutil.parser.parse(dt_obj)
    except:
        return None

random_slugify = lambda string, bits=16, max_length=0: f'{slugify(string, max_length=max_length)}-{os.urandom(bits).hex()}'
