import dateutil

from passlib.hash import pbkdf2_sha512 as hash_manager
from slugify import slugify

from init_app import flask_exts
from flask import Blueprint, request, g, make_response
from flask_json import as_json, JsonError
from flask_utils import validate_json, query_to_objects, query_to_objects_full, role_required
from flask_jwt_extended import jwt_required, get_current_user

from models import *

from flask_jwt_extended import (
    jwt_required, jwt_refresh_token_required,
    create_access_token, create_refresh_token,
    get_raw_jwt, get_jti, get_current_user
)

from authomatic.extras.flask import FlaskAuthomatic
from authomatic.providers import oauth2

from app_config import CurrentConfig

PSEUDO_PASSWORD_PREFIX = 'UNUSABLE_PASSWORD'
_fetch_fav_clubs_list = lambda user: [query_to_objects(club) for club in user.favorited_clubs]

student_blueprint = Blueprint('student', __name__, url_prefix='/api/student')


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


@student_blueprint.route('/login', methods=['GET'])
@fa.login('google')
def login():
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
                'profile': {
                    'name': student_name,
                    'email': student_email,
                },
                'token': {
                    'access': access_token,
                    'access_expires_in': int(CurrentConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()),
                    'refresh': refresh_token,
                    'refresh_expires_in': int(CurrentConfig.JWT_REFRESH_TOKEN_EXPIRES.total_seconds())
                }
            }
    else:
        return fa.response


@student_blueprint.route('/finish-register', methods=['POST'])
@jwt_required
@role_required(roles=['student'])
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
    if potential_user is not None:
        raise JsonError(status='error', reason='The student account for this email already exists!', status_=404)

    potential_user.majors = Major.objects.filter(id__in=student_majors)
    potential_user.minors = Minor.objects.filter(id__in=student_minors)
    potential_user.interests = Tag.objects.filter(id__in=student_interests)

    potential_user.save()

    return {'status': 'success'}

# TODO: Refactor to not be duplicated here
@student_blueprint.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
@role_required(roles=['student'])
def refresh():
    user = get_current_user()
    access_token = create_access_token(identity=user)
    access_jti = get_jti(access_token)

    AccessJTI(owner=user, token_id=access_jti).save()

    return {
        'access': access_token,
        'access_expires_in': int(CurrentConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    }

# TODO: Refactor to not be duplicated here
@student_blueprint.route('/revoke-access', methods=['DELETE'])
@jwt_required
@role_required(roles=['student'])
def revoke_access():
    jti = get_raw_jwt()['jti']

    access_jti = AccessJTI.objects(token_id=jti).first()
    if access_jti is None:
        raise JsonError(status='error', reason='Access token does not exist!', status_=404)

    access_jti.expired = True
    access_jti.save()

    return {
        'status': 'success',
        'message': 'Access token revoked!'
    }

# TODO: Refactor to not be duplicated here
@student_blueprint.route('/revoke-refresh', methods=['DELETE'])
@jwt_refresh_token_required
@role_required(roles=['student'])
def revoke_refresh():
    jti = get_raw_jwt()['jti']

    refresh_jti = RefreshJTI.objects(token_id=jti).first()
    if refresh_jti is None:
        raise JsonError(status='error', reason='Refresh token does not exist!', status_=404)

    refresh_jti.expired = True
    refresh_jti.save()

    return {
        'status': 'success',
        'message': 'Refresh token revoked!'
    }


@student_blueprint.route('/profile', methods=['GET'])
@jwt_required
@role_required(roles=['student'])
def fetch_profile():
    user = get_current_user()

    user_obj = query_to_objects(user)
    accepted_keys = [
        'full_name', 'email',
        'majors', 'minors', 'interests',
        'club_board', 'favorited_clubs',
    ]

    user_obj = {k: v for (k, v) in user_obj.items() if k in accepted_keys}
    return user_obj


@student_blueprint.route('/profile', methods=['POST'])
@jwt_required
@role_required(roles=['student'])
@validate_json(schema={
    'majors': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'minors': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'interests': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
})
def edit_profile():
    user = get_current_user()
    json = g.clean_json

    user.majors = Major.objects.filter(id__in=json['majors'])
    user.minors = Minor.objects.filter(id__in=json['minors'])
    user.interests = Tag.objects.filter(id__in=json['interests'])

    user.save()

    return {'status': 'success'}


@student_blueprint.route('/favorite-clubs', methods=['POST'])
@jwt_required
@role_required(roles=['student'])
@validate_json(schema={
    'clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
})
def add_favorite_clubs():
    user = get_current_user()
    json = g.clean_json

    for club in json['clubs']:
        if club not in user.favorited_clubs:
            user.favorited_clubs += [club]

    user.save()

    return _fetch_fav_clubs_list(user)


@student_blueprint.route('/favorite-clubs', methods=['DELETE'])
@jwt_required
@role_required(roles=['student'])
@validate_json(schema={
    'clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
})
def remove_favorite_clubs():
    user = get_current_user()
    json = g.clean_json

    for club in user.favorited_clubs:
        if club in json['clubs']:
            user.favorited_clubs.remove(club)

    user.save()

    return _fetch_fav_clubs_list(user)



@student_blueprint.route('/club-board', methods=['PUT'])
@jwt_required
@role_required(roles=['student'])
@validate_json(schema={
    'interested_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
    'applied_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
    'interviewed_clubs': {'type': 'list', 'schema': {'type': 'string'}, 'empty': False},
})
def update_club_board():
    user = get_current_user()
    json = g.clean_json

    user.club_board.interested_clubs  = json['interested_clubs']
    user.club_board.applied_clubs     = json['applied_clubs']
    user.club_board.interviewed_clubs = json['interviewed_clubs']

    user.save()

    return query_to_objects(user.club_board)
