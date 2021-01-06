import datetime

from passlib.hash import pbkdf2_sha512 as hash_manager

from flask import render_template, Blueprint, url_for, redirect, g
from flask_json import JsonError

from flask_jwt_extended import (
    jwt_required, jwt_refresh_token_required,
    create_access_token, create_refresh_token,
    get_raw_jwt, get_jti, get_current_user
)

from flask_utils import validate_json, role_required

from slugify import slugify

from init_app import flask_exts
from app_config import CurrentConfig
from models import *

LOGIN_CONFIRMED_EXT = '?confirmed=true'
LOGIN_URL = 'https://www.sproul.club/signin'
RECOVER_URL = 'https://www.sproul.club/resetpassword'

user_blueprint = Blueprint('user', __name__, url_prefix='/api/user')


@user_blueprint.route('/email-exists', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False}
}, require_all=True)
def does_email_exist():
    json = g.clean_json
    email = json['email']

    return {'exists': PreVerifiedEmail.objects(email=email).first() is not None}


@user_blueprint.route('/password-strength', methods=['POST'])
@validate_json(schema={
    'password': {'type': 'string', 'empty': False}
}, require_all=True)
def is_password_strong_enough():
    json = g.clean_json
    password = json['password']

    return {'strong': flask_exts.password_checker.check(password)}


@user_blueprint.route('/register', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 100},
    'email': {'type': 'string', 'empty': False},
    'password': {'type': 'string', 'empty': False},
    'tags': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'app_required': {'type': 'boolean'},
    'new_members': {'type': 'boolean'},
    'num_users': {'type': 'integer'},
}, require_all=True)
def register():
    json = g.clean_json

    club_name = json['name']
    club_email = json['email']
    club_password = json['password']
    club_tag_ids = json['tags']
    app_required = json['app_required']
    new_members = json['new_members']
    num_users_id = json['num_users']

    # Check if email is part of pre-verified list of emails
    email_exists = PreVerifiedEmail.objects(email=club_email).first() is not None
    if not email_exists:
        raise JsonError(status='error', reason='The provided email is not part of the RSO list!', status_=404)

    # Check if email is already registered
    potential_user = NewOfficerUser.objects(email=club_email).first()
    if potential_user is not None:
        raise JsonError(status='error', reason='A club under that email already exists!', status_=401)

    # Check if the password is strong enough
    is_password_strong = flask_exts.password_checker.check(club_password)
    if not is_password_strong:
        raise JsonError(status='error', reason='The password is not strong enough')

    new_club = NewClub(
        name=club_name,
        link_name=slugify(club_name, max_length=100),

        tags=Tag.objects.filter(id__in=club_tag_ids),
        app_required=app_required,
        new_members=new_members,
        num_users=NumUsersTag.objects.filter(id=num_users_id).first(),

        social_media_links=SocialMediaLinks(contact_email=club_email)
    )

    new_user = NewOfficerUser(
        email=club_email,
        password=hash_manager.hash(club_password),
        club=new_club
    )

    new_user.save()

    verification_token = flask_exts.email_verifier.generate_token(club_email, 'confirm-email')
    confirm_url = CurrentConfig.BASE_URL + url_for('user.confirm_email', token=verification_token)
    html = render_template('confirm-email.html', confirm_url=confirm_url)

    flask_exts.email_sender.send(
        subject='Please confirm your email',
        recipients=[club_email],
        body=html
    )

    return {'status': 'success'}


@user_blueprint.route('/resend-confirm', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False}
}, require_all=True)
def resend_confirm_email():
    json = g.clean_json
    club_email = json['email']

    # Check if email is already registered
    potential_user = NewOfficerUser.objects(email=club_email).first()
    if potential_user is None:
        raise JsonError(status='error', reason='No club under that email exists!', status_=404)

    if potential_user.confirmed:
        raise JsonError(status='error', reason='The user is already confirmed.')

    verification_token = flask_exts.email_verifier.generate_token(club_email, 'confirm-email')
    confirm_url = CurrentConfig.BASE_URL + url_for('user.confirm_email', token=verification_token)
    html = render_template('confirm-email.html', confirm_url=confirm_url)

    flask_exts.email_sender.send(
        subject='Please confirm your email',
        recipients=[club_email],
        body=html
    )

    return {'status': 'success'}


@user_blueprint.route('/confirm/<token>', methods=['GET'])
def confirm_email(token):
    club_email = flask_exts.email_verifier.confirm_token(token, 'confirm-email')
    if club_email is None:
        raise JsonError(status='error', reason='The confirmation link is invalid.', status_=404)

    potential_user = NewOfficerUser.objects(email=club_email).first()
    if potential_user is None:
        raise JsonError(status='error', reason='The user matching the email does not exist.', status_=404)

    # First, revoke the given email token
    flask_exts.email_verifier.revoke_token(token, 'confirm-email')

    if potential_user.confirmed:
        return redirect(LOGIN_URL + LOGIN_CONFIRMED_EXT)

    confirmed_on = datetime.datetime.now()
    if confirmed_on - potential_user.registered_on > CurrentConfig.CONFIRM_EMAIL_EXPIRY:
        # Delete the user with the associated club here
        # HACK: This was supposed to simulate the auto-deletion of the user and club after the first confirmation email expires,
        # but MongoDB TTL doesn't support deleting referenced or back-referenced documents (user -> club).
        potential_user.delete()

        raise JsonError(status='error', reason='The account associated with the email has expired. Please re-register the club again.')

    # Then, set the user and club to 'confirmed' if it's not done already
    potential_user.confirmed = True
    potential_user.confirmed_on = datetime.datetime.now()
    potential_user.save()

    return redirect(LOGIN_URL + LOGIN_CONFIRMED_EXT)


@user_blueprint.route('/login', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False},
    'password': {'type': 'string', 'empty': False}
}, require_all=True)
def login():
    json = g.clean_json
    email = json['email']
    password = json['password']

    potential_user = NewOfficerUser.objects(email=email).first()
    if potential_user is None:
        raise JsonError(status='error', reason='The user does not exist.')

    if not potential_user.confirmed:
        raise JsonError(status='error', reason='The user has not confirmed their email.')

    if not hash_manager.verify(password, potential_user.password):
        raise JsonError(status='error', reason='The password is incorrect.')

    if potential_user.role == 'student':
        raise JsonError(status='error', reason='Student sign-in is not supported!')

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


@user_blueprint.route('/request-reset', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False}
}, require_all=True)
def request_reset_password():
    json = g.clean_json
    club_email = json['email']

    potential_user = NewOfficerUser.objects(email=club_email).first()
    if potential_user is None:
        raise JsonError(status='error', reason='The user does not exist.')

    recover_token = flask_exts.email_verifier.generate_token(club_email, 'reset-password')
    html = render_template('reset-password.html', reset_pass_url=f'{RECOVER_URL}?token={recover_token}')

    flask_exts.email_sender.send(
        subject='Reset your password',
        recipients=[club_email],
        body=html
    )

    return {'status': 'success'}


@user_blueprint.route('/confirm-reset', methods=['POST'])
@validate_json(schema={
    'token': {'type': 'string'},
    'password': {'type': 'string'}
}, require_all=True)
def confirm_reset_password():
    json = g.clean_json

    token = json['token']
    club_password = json['password']

    club_email = flask_exts.email_verifier.confirm_token(token, 'reset-password')
    if club_email is None:
        raise JsonError(status='error', reason='The recovery token is invalid!', status_=404)

    potential_user = NewOfficerUser.objects(email=club_email).first()
    if potential_user is None:
        raise JsonError(status='error', reason='The user matching the email does not exist!', status_=404)

    # Check if the password is strong enough
    is_password_strong = flask_exts.password_checker.check(club_password)
    if not is_password_strong:
        raise JsonError(status='error', reason='The password is not strong enough')

    # First, revoke the given email token
    flask_exts.email_verifier.revoke_token(token, 'reset-password')

    # Next, delete all access and refresh tokens from the user
    AccessJTI.objects(owner=potential_user).delete()
    RefreshJTI.objects(owner=potential_user).delete()

    # Finally, set the new password
    potential_user.password = hash_manager.hash(club_password)
    potential_user.save()

    return {'status': 'success'}


@user_blueprint.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    user = get_current_user()
    access_token = create_access_token(identity=user)
    access_jti = get_jti(access_token)

    AccessJTI(owner=user, token_id=access_jti).save()

    return {
        'access': access_token,
        'access_expires_in': int(CurrentConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    }


@user_blueprint.route('/revoke-access', methods=['DELETE'])
@jwt_required
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


@user_blueprint.route('/revoke-refresh', methods=['DELETE'])
@jwt_refresh_token_required
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
