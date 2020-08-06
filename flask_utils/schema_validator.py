from flask import request, g
from flask_json import JsonError

from cerberus import Validator
from decorator import decorator

@decorator
def validate_json(func, schema={}, allow_unknown=False, require_all=False, *args, **kw):
    if not request.is_json and request.method != 'OPTIONS':
        raise JsonError(
            status='error',
            reason='Expected JSON in body'
        )
    else:
        json = request.get_json()
        validator = Validator(schema, allow_unknown=allow_unknown, require_all=require_all)

        if not validator.validate(json):
            raise JsonError(
                status='error',
                reason='A validation error occurred when parsing the JSON body.',
                data=[{'field': v_error[0], 'errors': v_error[1]} for v_error in validator.errors.items()]
            )

        g.clean_json = validator.normalized(json)
    
        return func(*args, **kw)
        