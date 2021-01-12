import dateutil

from passlib.hash import pbkdf2_sha512 as hash_manager
from slugify import slugify

from init_app import flask_exts
from flask import Blueprint, request, g, make_response
from flask_json import as_json, JsonError
from flask_utils import validate_json, query_to_objects, role_required
from flask_jwt_extended import jwt_required, get_current_user

from models import *

from flask_jwt_extended import (
    jwt_required, jwt_refresh_token_required,
    create_access_token, create_refresh_token,
    get_raw_jwt, get_jti, get_current_user
)

student_blueprint = Blueprint('student', __name__, url_prefix='/api/student')

_fetch_resources_list = lambda user: [query_to_objects(res) for res in user.club.resources]
_fetch_event_list = lambda user: [query_to_objects(event) for event in user.club.events]
_fetch_recruiting_events_list = lambda user: [query_to_objects(r_event) for r_event in user.club.recruiting_events]


PSEUDO_PASSWORD_PREFIX = 'UNUSABLE_PASSWORD'

from authomatic.extras.flask import FlaskAuthomatic
from authomatic.providers import oauth2

from app_config import CurrentConfig


fa = FlaskAuthomatic(
    config={
        'google': {
            'class_': oauth2.Google,
            'consumer_key': CurrentConfig.GOOGLE_OAUTH_CLIENT_ID,
            'consumer_secret': CurrentConfig.GOOGLE_OAUTH_CLIENT_SECRET,
            'scope': [
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/userinfo.email'
            ],
        }
    },
    secret=CurrentConfig.SECRET_KEY,
    debug=True,
)


@student_blueprint.route('/glogin', methods=['GET', 'POST'])
@fa.login('google')
def glogin():
    if fa.result is not None:
        google_user = fa.result.user
        login_error = fa.result.error

        if login_error is not None:
            raise JsonError(status='error', reason=f'Login failed: {login_error.message}')
        elif google_user is not None:
            if not (google_user.name and google_user.id):
                google_user.update()

            student_email = google_user.email
            student_name = google_user.name

            # Check if email is already registered
            potential_user = NewStudentUser.objects(email=student_email).first()
            if potential_user is None:
                new_user = NewStudentUser(
                    email=student_email,
                    full_name=student_name,
                    password=hash_manager.hash(PSEUDO_PASSWORD_PREFIX + student_email),

                    majors=[],
                    minors=[],
                    interests=[],
                    club_board=StudentKanbanBoard(),
                )

                new_user.save()
            
            access_token = create_access_token(identity=potential_user)
            refresh_token = create_refresh_token(identity=potential_user)

            access_jti = get_jti(encoded_token=access_token)
            refresh_jti = get_jti(encoded_token=refresh_token)

            AccessJTI(owner=potential_user, token_id=access_jti).save()
            RefreshJTI(owner=potential_user, token_id=refresh_jti).save()

            return {
                'access': access_token,
                'access_expires_in': int(CurrentConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()),
                'refresh': refresh_token,
                'refresh_expires_in': int(CurrentConfig.JWT_REFRESH_TOKEN_EXPIRES.total_seconds())
            }
    else:
        return fa.response


@student_blueprint.route('/finish-register', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False},
    'majors': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'minors': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'interests': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
}, require_all=True)
def finish_register():
    json = g.clean_json

    student_email = json['email']
    student_majors = json['majors']
    student_minors = json['minors']
    student_interests = json['interests']

    # Check if email is already registered
    potential_user = NewStudentUser.objects(email=student_email).first()
    if potential_user is None:
        raise JsonError(status='error', reason='The student account for this email does not exist', status_=404)

    potential_user.update(
        majors=Major.objects.filter(id__in=student_majors),
        minors=Minor.objects.filter(id__in=student_minors),
        interests=Tag.objects.filter(id__in=student_interests),
    )

    potential_user.save()

    return {'status': 'success'}


@student_blueprint.route('/profile', methods=['GET'])
@jwt_required
@role_required(roles=['student'])
def fetch_profile():
    user = get_current_user()
    user_obj = query_to_objects(user)

    return user_obj


@student_blueprint.route('/profile', methods=['POST'])
@jwt_required
@role_required(roles=['student'])
@validate_json(schema={
    'majors': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'minors': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'interests': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'favorited_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
    'visited_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
    'club_board': {
        'type': 'dict',
        'schema': {
            'interested_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
            'applied_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
            'interviewed_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
        }
    },
})
def edit_profile():
    user = get_current_user()
    json = g.clean_json

    for key in json.keys():
        user[key] = json[key]

    user.save()

    return {'status': 'success'}

