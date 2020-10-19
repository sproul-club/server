import os
import json
import datetime
import dateutil

from passlib.hash import pbkdf2_sha512 as hash_manager

from init_app import flask_exts
from flask import Blueprint, request, g
from flask_json import as_json, JsonError
from flask_csv import send_csv
from flask_utils import validate_json, id_creator
from flask_utils import mongo_aggregations
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user

from models import *

monitor_blueprint = Blueprint('monitor', __name__, url_prefix='/api/monitor')


@as_json
@monitor_blueprint.route('/login', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False},
    'password': {'type': 'string', 'empty': False}
}, require_all=True)
def login():
    json = g.clean_json
    email = json['email']
    password = json['password']

    user = OfficerUser.objects(email=email).first()
    if user is None:
        raise JsonError(status='error', reason='The user does not exist.')

    if not user.confirmed:
        raise JsonError(status='error', reason='The user has not confirmed their email.')

    if not hash_manager.verify(password, user.password):
        raise JsonError(status='error', reason='The password is incorrect.')

    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)

    access_jti = get_jti(encoded_token=access_token)
    refresh_jti = get_jti(encoded_token=refresh_token)

    AccessJTI(owner=user, token_id=access_jti).save()
    RefreshJTI(owner=user, token_id=refresh_jti).save()

    return {
        'access': access_token,
        'access_expires_in': int(CurrentConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()),
        'refresh': refresh_token,
        'refresh_expires_in': int(CurrentConfig.JWT_REFRESH_TOKEN_EXPIRES.total_seconds())
    }


@as_json
@monitor_blueprint.route('/overview/stats/sign-up', methods=['GET'])
def fetch_sign_up_stats():
    one_day_ago = datetime.datetime.now() - datetime.timedelta(weeks=1)
    officer_users = OfficerUser.objects
    student_users = StudentUser.objects

    # Officer stats
    num_registered_clubs = len(officer_users)
    recent_num_registered_clubs = len(officer_users.filter(registered_on__gte=one_day_ago))

    num_confirmed_clubs = len(officer_users.filter(confirmed=True))
    recent_num_confirmed_clubs = len(officer_users.filter(confirmed=True, registered_on__gte=one_day_ago))

    num_clubs_rso_list = len(PreVerifiedEmail.objects)

    # Student stats
    num_students_signed_up = len(student_users)
    recent_num_students_signed_up = len(student_users.filter(registered_on__gte=one_day_ago))

    num_confirmed_students = len(student_users.filter(confirmed=True))
    recent_num_confirmed_students = len(student_users.filter(confirmed=True, registered_on__gte=one_day_ago))

    return {
        'main': {
            'clubs_registered': num_registered_clubs,
            'clubs_confirmed': num_confirmed_clubs,
            'clubs_rso_list': num_clubs_rso_list,
            'students_signed_up': num_students_signed_up,
            'students_confirmed': num_confirmed_students,
        },
        'changed': {
            'clubs_registered': recent_num_registered_clubs,
            'clubs_confirmed': recent_num_confirmed_clubs,
            'students_signed_up': recent_num_students_signed_up,
            'students_confirmed': recent_num_confirmed_students
        }
    }


@as_json
@monitor_blueprint.route('/overview/stats/activity', methods=['GET'])
def fetch_activity_stats():
    # HACK: I should probably be using aggregations here!
    officer_users = [jti.owner.role == 'officer' for jti in AccessJTI.objects]
    student_users = [jti.owner.role == 'student' for jti in AccessJTI.objects]

    num_active_admins = len(officer_users)
    num_active_users = len(student_users)
    num_catalog_searches = 'N/A'

    return {
        'active_admins': num_active_admins,
        'active_users': num_active_users,
        'catalog_searches': num_catalog_searches
    }


@as_json
@monitor_blueprint.route('/rso/list', methods=['GET'])
def list_rso_users():
    rso_list = mongo_aggregations.fetch_aggregated_rso_list()
    return json.dumps(rso_list)


@monitor_blueprint.route('/rso/download', methods=['GET'])
def download_rso_users():
    rso_list = mongo_aggregations.fetch_aggregated_rso_list()
    for rso_email in rso_list:
        rso_email['registered'] = 'Yes' if rso_email['registered'] else 'No'
        rso_email['confirmed']  = 'Yes' if rso_email['confirmed'] else 'No'

    return send_csv(rso_list, 'rso_emails.csv', ['email', 'registered', 'confirmed'], cache_timeout=0)


@as_json
@monitor_blueprint.route('/rso', methods=['POST'])
@validate_json(schema={
    'email': {'type': 'string', 'empty': False}
}, require_all=True)
def add_rso_user():
    email = g.clean_json['email']

    rso_email = PreVerifiedEmail.objects(email=email).first()
    if rso_email is None:
        PreVerifiedEmail(email=email).save()
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='Specified RSO Email already exists!')


@as_json
@monitor_blueprint.route('/rso/<email>', methods=['DELETE'])
def remove_rso_user(email):
    rso_email = PreVerifiedEmail.objects(email=email).first()
    if rso_email is None:
        raise JsonError(status='error', reason='Specified RSO Email does not exist!')

    user = User.objects(email=email).first()
    if user is not None:
        raise JsonError(status='error', reason='A club already exists with that email! Please delete it first')

    rso_email.delete()
    return {'status': 'success'}


@as_json
@monitor_blueprint.route('/club/list', methods=['GET'])
def list_clubs():
    club_list = mongo_aggregations.fetch_aggregated_club_list()
    return json.dumps(club_list)


@monitor_blueprint.route('/club/download', methods=['GET'])
def download_clubs():
    club_list = mongo_aggregations.fetch_aggregated_club_list()
    for club in club_list:
        del club['_id']
        club['confirmed'] = 'Yes' if club['confirmed'] else 'No'

    return send_csv(club_list, 'clubs.csv', ['name', 'owner', 'confirmed'], cache_timeout=0)


@as_json
@monitor_blueprint.route('/club/<email>', methods=['DELETE'])
def delete_club(email):
    user = User.objects(email=email).first()
    if user is None:
        raise JsonError(status='error', reason='The user does not exist!')

    club = Club.objects(owner=user).first()

    # NOTE: Each club may have an associated user, unless it's a student account
    if club is not None:
        club.delete()

    user.delete()
    return {'status': 'success'}


@as_json
@monitor_blueprint.route('/tags/list', methods=['GET'])
def list_tags_with_usage():
    # This pipeline will associate the tags with the number of clubs that have said tag
    tags_with_usage = mongo_aggregations.fetch_aggregated_tag_list()
    return json.dumps(tags_with_usage)


@monitor_blueprint.route('/tags/download', methods=['GET'])
def download_tags_with_usage():
    tags_with_usage = mongo_aggregations.fetch_aggregated_tag_list()
    return send_csv(tags_with_usage, 'tags.csv', ['name', 'num_clubs'], cache_timeout=0)


@as_json
@monitor_blueprint.route('/tags', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False}
}, require_all=True)
def add_tag():
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


@as_json
@monitor_blueprint.route('/tags/<tag_id>', methods=['PUT'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False}
}, require_all=True)
def edit_tag(tag_id):
    new_tag_name = g.clean_json['name']

    old_tag = Tag.objects(id=tag_id).first()
    if old_tag is None:
        raise JsonError(status='error', reason='Old tag does not exist!')

    new_tag = Tag.objects(name=new_tag_name).first()
    if new_tag is not None:
        raise JsonError(status='error', reason='New tag already exists!')

    old_tag.update(name=new_tag_name)
    return {'status': 'success'}


@as_json
@monitor_blueprint.route('/tags/<tag_id>', methods=['DELETE'])
def remove_tag(tag_id):
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


@as_json
@monitor_blueprint.route('/more-stats/social-media', methods=['GET'])
def fetch_social_media_stats():
    smedia_stats = mongo_aggregations.fetch_aggregated_social_media_usage()
    return json.dumps(smedia_stats)


@as_json
@monitor_blueprint.route('/more-stats/club-reqs', methods=['GET'])
def fetch_club_req_stats():
    club_req_stats = mongo_aggregations.fetch_aggregated_club_requirement_stats()
    return json.dumps(club_req_stats)


@as_json
@monitor_blueprint.route('/more-stats/pic-stats', methods=['GET'])
def fetch_picture_stats():
    pic_stats = mongo_aggregations.fetch_aggregated_picture_stats()
    return json.dumps(pic_stats)
