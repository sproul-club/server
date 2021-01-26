import json

from flask import request, g
from flask_json import JsonError

from cerberus import Validator
from decorator import decorator

@decorator
def validate_json(func, schema={}, allow_unknown=False, require_all=False, form_keys=None, *args, **kw):
    if not request.is_json and request.method != 'OPTIONS' and form_keys is None:
        raise JsonError(
            status='error',
            reason='Expected JSON in body'
        )
    else:
        if form_keys is not None:
            obj = {}
            for key in form_keys:
                obj[key] = request.form.get(key, None)

                if obj[key] is None and require_all:
                    raise JsonError(
                        status='error',
                        reason=f'A form field was missing during validation: "{key}"',
                    )
        else:
            obj = request.get_json()

        validator = Validator(schema, allow_unknown=allow_unknown, require_all=require_all)

        if not validator.validate(obj):
            raise JsonError(
                status='error',
                reason='A validation error occurred when parsing the JSON body.',
                data=[{'field': v_error[0], 'errors': v_error[1]} for v_error in validator.errors.items()]
            )

        g.clean_json = validator.normalized(obj)
    
        return func(*args, **kw)
        
