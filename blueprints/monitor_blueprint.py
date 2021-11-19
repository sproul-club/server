import datetime

from passlib.hash import pbkdf2_sha512 as hash_manager

from utils import pst_right_now, array_diff

from flask import Blueprint, g
from flask_json import as_json, JsonError
from flask_csv import send_csv
from flask_utils import validate_json, query_to_objects, role_required, mongo_aggregations, confirmed_account_required
from flask_jwt_extended import jwt_required, jwt_refresh_token_required, get_jwt_identity, create_access_token, create_refresh_token, get_jti

from app_config import CurrentConfig

from models import *

monitor_blueprint = Blueprint('monitor', __name__, url_prefix='/api/monitor')


def _fetch_clubs():
    """
    Utility function to fetch the entire list of clubs by name, email, confirmation
    and reactivation status.
    """
    club_list_query = NewOfficerUser.objects.scalar('club.name', 'email', 'confirmed', 'club.reactivated')
    raw_club_list = query_to_objects(club_list_query)
    club_list = []

    for club in raw_club_list:
        del club['id']
        del club['_cls']
        club_list.append({
            'name': club['club']['name'],
            'email': club['email'],
            'confirmed': club['confirmed'],
            'reactivated': club['club']['reactivated'],
        })

    return club_list


@monitor_blueprint.route('/login', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False},
    'password': {'type': 'string', 'empty': False}
}, require_all=True)
def login():
    """
    POST endpoint that logs in an existing admin user.
    """

    json = g.clean_json
    email = json['email']
    password = json['password']

    potential_user = NewAdminUser.objects(email=email).first()
    if potential_user is None:
        raise JsonError(status='error', reason='The user does not exist.')

    if not potential_user.confirmed:
        raise JsonError(status='error', reason='The user has not confirmed their email.')

    if not hash_manager.verify(password, potential_user.password):
        raise JsonError(status='error', reason='The password is incorrect.')

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


# TODO: Refactor to not be duplicated here from User API
@monitor_blueprint.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
@role_required(roles=['admin'])
@confirmed_account_required
def refresh():
    """
    POST endpoint that fetches a new access token given a valid refresh token.
    """

    user = get_current_user()
    access_token = create_access_token(identity=user)
    access_jti = get_jti(access_token)

    AccessJTI(owner=user, token_id=access_jti).save()

    return {
        'access': access_token,
        'access_expires_in': int(CurrentConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    }

# TODO: Refactor to not be duplicated here from User API
@monitor_blueprint.route('/revoke-access', methods=['DELETE'])
@jwt_required
@role_required(roles=['admin'])
@confirmed_account_required
def revoke_access():
    """
    DELETE endpoint that revokes an issued access token, preventing further use of it.
    """

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

# TODO: Refactor to not be duplicated here from User API
@monitor_blueprint.route('/revoke-refresh', methods=['DELETE'])
@jwt_refresh_token_required
@role_required(roles=['admin'])
@confirmed_account_required
def revoke_refresh():
    """
    DELETE endpoint that revokes an issued refresh token, preventing further use of it.
    """

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


@monitor_blueprint.route('/overview/stats/sign-up', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
def fetch_sign_up_stats():
    """
    GET endpoint that fetches the sign up statistics for all user account types.
    """

    time_delta = pst_right_now() - datetime.timedelta(weeks=1)
    history_deltas = [pst_right_now() - datetime.timedelta(weeks=delay) for delay in range(11)]

    # Officer stats
    num_registered_clubs = NewOfficerUser.objects.count()
    recent_num_registered_clubs = NewOfficerUser.objects.filter(registered_on__gte=time_delta).count()
    num_registered_clubs_history = reversed(array_diff([NewOfficerUser.objects.filter(registered_on__gte=hist_delta).count() for hist_delta in history_deltas]))

    num_confirmed_clubs = NewOfficerUser.objects.filter(confirmed=True).count()
    recent_num_confirmed_clubs = NewOfficerUser.objects.filter(confirmed=True, registered_on__gte=time_delta).count()
    num_confirmed_clubs_history = reversed(array_diff([NewOfficerUser.objects.filter(confirmed=True, registered_on__gte=hist_delta).count() for hist_delta in history_deltas]))

    num_reactivated_clubs = NewOfficerUser.objects.filter(confirmed=True, club__reactivated=True).count()
    recent_num_reactivated_clubs = NewOfficerUser.objects.filter(
        confirmed=True, club__reactivated=True,
        club__reactivated_last__gte=time_delta
    ).count()
    num_reactivated_clubs_history = reversed(array_diff([NewOfficerUser.objects.filter(
        confirmed=True, club__reactivated=True,
        club__reactivated_last__gte=hist_delta
    ).count() for hist_delta in history_deltas]))

    num_clubs_rso_list = PreVerifiedEmail.objects.count()

    # Student stats
    num_students_signed_up = NewStudentUser.objects.count()
    recent_num_students_signed_up = NewStudentUser.objects.filter(registered_on__gte=time_delta).count()

    num_confirmed_students = NewStudentUser.objects.filter(confirmed=True).count()
    recent_num_confirmed_students = NewStudentUser.objects.filter(confirmed=True, registered_on__gte=time_delta).count()

    return {
        'club_admin': {
            'main': {
                'clubs_registered': num_registered_clubs,
                'clubs_confirmed': num_confirmed_clubs,
                'clubs_reactivated': num_reactivated_clubs,
                'clubs_rso_list': num_clubs_rso_list,
            },
            'changed': {
                'clubs_registered': recent_num_registered_clubs,
                'clubs_confirmed': recent_num_confirmed_clubs,
                'clubs_reactivated': recent_num_reactivated_clubs,
            },
            'history': {
                'clubs_registered': num_registered_clubs_history,
                'clubs_confirmed': num_confirmed_clubs_history,
                'clubs_reactivated': num_reactivated_clubs_history,
            }
        },
        'student': {
            'main': {
                'students_signed_up': num_students_signed_up,
                'students_confirmed': num_confirmed_students,
            },
            'changed': {
                'students_signed_up': recent_num_students_signed_up,
                'students_confirmed': recent_num_confirmed_students
            }
        }
    }


@monitor_blueprint.route('/overview/stats/activity', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
def fetch_activity_stats():
    """
    GET endpoint that fetches the number of active users and recent catalog searches (WIP).
    """

    active_user_stats = mongo_aggregations.fetch_active_users_stats()

    return {
        'active_club_admins': active_user_stats['officer'],
        'active_students': active_user_stats['student'],
        'catalog_searches': 'N/A'
    }


@monitor_blueprint.route('/more-stats/social-media', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
@as_json
def fetch_social_media_stats():
    """
    GET endpoint that fetches the aggregated usage of social media links across all clubs.
    """

    smedia_stats = mongo_aggregations.fetch_aggregated_social_media_usage()
    return smedia_stats


@monitor_blueprint.route('/more-stats/club-reqs', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
@as_json
def fetch_club_req_stats():
    """
    GET endpoint that fetches aggregated statistics for club application statuses.
    """

    club_req_stats = mongo_aggregations.fetch_aggregated_club_requirement_stats()
    return club_req_stats


@monitor_blueprint.route('/more-stats/pic-stats', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
@as_json
def fetch_picture_stats():
    """
    GET endpoint that fetches the aggregated usage of logo / banner pictures for clubs.
    """

    pic_stats = mongo_aggregations.fetch_aggregated_picture_stats()
    return pic_stats


@monitor_blueprint.route('/rso/list', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
@as_json
def list_rso_users():
    """
    GET endpoint that fetches the list of RSO emails scraped from CalLink.
    """

    rso_list = mongo_aggregations.fetch_aggregated_rso_list()
    return rso_list


@monitor_blueprint.route('/rso/download', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
def download_rso_users():
    """
    GET endpoint that downloads a CSV file of the list of RSO emails scraped from CalLink.
    """

    rso_list = mongo_aggregations.fetch_aggregated_rso_list()
    for rso_email in rso_list:
        rso_email['registered'] = 'Yes' if rso_email['registered'] else 'No'
        rso_email['confirmed']  = 'Yes' if rso_email['confirmed'] else 'No'

    return send_csv(rso_list, 'rso_emails.csv', ['email', 'registered', 'confirmed'], cache_timeout=0)


@monitor_blueprint.route('/rso', methods=['POST'])
@jwt_required
@role_required(roles=['admin'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False}
}, require_all=True)
def add_rso_user():
    """
    POST endpoint that adds a new RSO email.
    """

    email = g.clean_json['email']

    rso_email = PreVerifiedEmail.objects(email=email).first()
    if rso_email is None:
        PreVerifiedEmail(email=email).save()
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='Specified RSO Email already exists!')


@monitor_blueprint.route('/rso/<email>', methods=['DELETE'])
@jwt_required
@role_required(roles=['admin'])
def remove_rso_user(email):
    """
    DELETE endpoint that removes an existing RSO email.
    """

    rso_email = PreVerifiedEmail.objects(email=email).first()
    if rso_email is None:
        raise JsonError(status='error', reason='Specified RSO Email does not exist!')

    user = NewOfficerUser.objects(email=email).first()
    if user is not None:
        raise JsonError(status='error', reason='A club already exists with that email! Please delete it first')

    rso_email.delete()
    return {'status': 'success'}


@monitor_blueprint.route('/club/list', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
@as_json
def list_clubs():
    """
    GET endpoint that fetches the list of clubs with relevent info (abridged).
    """

    club_list = _fetch_clubs()
    return club_list


@monitor_blueprint.route('/club/download', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
def download_clubs():
    """
    GET endpoint that downloads a CSV file of the list of clubs with relevent info (abridged).
    """

    club_list = _fetch_clubs()
    for club in club_list:
        club['confirmed'] = 'Yes' if club['confirmed'] else 'No'
        club['reactivated'] = 'Yes' if club['reactivated'] else 'No'

    return send_csv(club_list, 'clubs.csv', ['name', 'email', 'confirmed', 'reactivated'], cache_timeout=0)


@monitor_blueprint.route('/club/<email>', methods=['DELETE'])
@jwt_required
@role_required(roles=['admin'])
def delete_club(email):
    """
    DELETE endpoint that removes an existing officer user and thus, their respective club.
    """

    user = NewOfficerUser.objects(email=email).first()
    if user is None:
        raise JsonError(status='error', reason='The user does not exist!')

    user.delete()
    return {'status': 'success'}


@monitor_blueprint.route('/tags/list', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
@as_json
def list_tags_with_usage():
    """
    GET endpoint that fetches the list of club tags with usage statistics per tag.
    """

    tags_with_usage = mongo_aggregations.fetch_aggregated_tag_list()
    return tags_with_usage


@monitor_blueprint.route('/tags/download', methods=['GET'])
@jwt_required
@role_required(roles=['admin'])
def download_tags_with_usage():
    """
    GET endpoint that downloads a CSV file of the list of club tags with usage statistics per tag.
    """

    tags_with_usage = mongo_aggregations.fetch_aggregated_tag_list()
    return send_csv(tags_with_usage, 'tags.csv', ['_id', 'name', 'num_clubs'], cache_timeout=0)


@monitor_blueprint.route('/tags', methods=['POST'])
@jwt_required
@role_required(roles=['admin'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False}
}, require_all=True)
def add_tag():
    """
    POST endpoint that adds a new club tag.
    """

    tag_name = g.clean_json['name']

    # Auto-determine new tag ID by filling in nearest
    # missing number starting from 0
    # Ex. [1, 2, 3] => [0, 1, 2, 3]
    # Ex. [0, 1, 5, 6] => [0, 1, 2, 5, 6]
    # Ex. [0, 1, 2] => [0, 1, 2, 3]
    all_tag_ids = [tag.id for tag in Tag.objects]

    new_tag_id = None
    for (i, tag_id) in enumerate(sorted(all_tag_ids)):
        if tag_id != i:
            # we found a tag id to fill in
            new_tag_id = i
            break

    if new_tag_id is None:
        new_tag_id = i + 1

    tag = Tag.objects(name=tag_name).first()
    if tag is None:
        Tag(id=new_tag_id, name=tag_name).save()
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='Specified tag already exists!')


@monitor_blueprint.route('/tags/<tag_id>', methods=['PUT'])
@jwt_required
@role_required(roles=['admin'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False}
}, require_all=True)
def edit_tag(tag_id):
    """
    PUT endpoint that edits an existing club tag.
    """

    new_tag_name = g.clean_json['name']

    old_tag = Tag.objects(id=tag_id).first()
    if old_tag is None:
        raise JsonError(status='error', reason='Old tag does not exist!')

    new_tag = Tag.objects(name=new_tag_name).first()
    if new_tag is not None:
        raise JsonError(status='error', reason='New tag already exists!')

    old_tag.name = new_tag_name
    old_tag.save()
    return {'status': 'success'}


@monitor_blueprint.route('/tags/<tag_id>', methods=['DELETE'])
@jwt_required
@role_required(roles=['admin'])
def remove_tag(tag_id):
    """
    DELETE endpoint that removes an existing club tag, if there are no clubs using said tag.
    """

    tags_with_usage = mongo_aggregations.fetch_aggregated_tag_list()

    selected_tag = None
    for tag in tags_with_usage:
        if tag['_id'] == int(tag_id):
            selected_tag = tag

    if selected_tag is None:
        raise JsonError(status='error', reason='Specified tag does not exist!')
    elif selected_tag['num_clubs'] > 0:
        raise JsonError(status='error', reason=f"At least {selected_tag['num_clubs']} clubs are using this tag!")
    else:
        tag = Tag.objects(id=int(tag_id)).first()
        tag.delete()
        return {'status': 'success'}
