import json

from flask import request, g
from flask_json import JsonError

from cerberus import Validator
from decorator import decorator

"""
This decorator checks the form data or JSON submitted for a POST/PUT endpoint against a provided schema,
by checking if those fields exist and have the correct data type. This is provided by the 'cerberus' library.

If the 'coerce' modifier is provided with a conversion, assuming that the field is valid, it'll attempt
to convert the string field via the provided function.

Example:

@app.route('/club/info', methods=['PUT'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'required': True, 'maxlength': 100},
    'tags': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'num_attendees': {'type': 'integer', 'default': None},
    'description': {'type': 'string', 'maxlength': 500, 'default': ''}
    'start_time': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse}
})
def update_club_information():
    user = get_current_user()
    club = user.club

    # Fetch the validated and processed JSON
    json = g.clean_json

    club.name          = json['name']
    club.tags          = json['tags']
    club.num_attendees = json['num_attendees']
    club.description   = json['event_end']
    club.start_time    = json['start_time']

    user.save()

    return {'status': 'success'}
"""

@decorator
def validate_json(func, schema={}, allow_unknown=False, require_all=False, form_keys=None, *args, **kw):
    if not request.is_json and request.method != 'OPTIONS' and form_keys is None:
        raise JsonError(
            status='error',
            reason='Expected JSON in body'
        )
    else:
        # When processing form data, make sure none of the fields are non-existent.
        if form_keys is not None:
            obj = {}
            for key in form_keys:
                obj[key] = request.form.get(key, None)

                if obj[key] is None and require_all:
                    raise JsonError(
                        status='error',
                        reason=f'A form field was missing during validation: "{key}"',
                    )
        # Otherwise, process the submitted JSON as-is.
        else:
            obj = request.get_json()

        validator = Validator(schema, allow_unknown=allow_unknown, require_all=require_all)

        if not validator.validate(obj):
            raise JsonError(
                status='error',
                reason='A validation error occurred when parsing the JSON body.',
                data=[{'field': v_error[0], 'errors': v_error[1]} for v_error in validator.errors.items()]
            )

        # Store the validated and processed JSON into the global storage object 'g' (provided by Flask).
        g.clean_json = validator.normalized(obj)
    
        return func(*args, **kw)
        
