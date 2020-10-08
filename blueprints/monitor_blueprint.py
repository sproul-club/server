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


# @as_json
# @monitor_blueprint.route('/login', methods=['POST'])
# def login_monitor_dashboard():
#     pass


@as_json
@monitor_blueprint.route('/overview/stats/sign-up', methods=['GET'])
def fetch_sign_up_stats():
    one_day_ago = datetime.datetime.now() - datetime.timedelta(weeks=1)

    num_registered_clubs = len(User.objects)
    recent_num_registered_clubs = len(User.objects(registered_on__gte=one_day_ago))

    num_confirmed_clubs = len(User.objects(confirmed=True))
    recent_num_confirmed_clubs = len(User.objects(confirmed=True, registered_on__gte=one_day_ago))

    num_clubs_rso_list = len(PreVerifiedEmail.objects)

    return {
        'main': {
            'clubs_registered': num_registered_clubs,
            'clubs_confirmed': num_confirmed_clubs,
            'clubs_rso_list': num_clubs_rso_list
        },
        'changed': {
            'clubs_registered': recent_num_registered_clubs,
            'clubs_confirmed': recent_num_confirmed_clubs
        }
    }


@as_json
@monitor_blueprint.route('/overview/stats/activity', methods=['GET'])
def fetch_activity_stats():
    num_active_admins = len(AccessJTI.objects)
    num_active_users = 'N/A'
    num_catalog_searches = 'N/A'

    return {
        'active_admins': num_active_admins,
        'active_users': num_active_users,
        'catalog_searches': num_catalog_searches
    }


@as_json
@monitor_blueprint.route('/overview/stats/performance', methods=['GET'])
def fetch_performance_stats():
    uptime_percent = 'N/A'
    num_api_calls = 'N/A'
    amt_data_stored = 'N/A'

    return {
        'uptime_percent': uptime_percent,
        'api_calls': num_api_calls,
        'data_stored': amt_data_stored
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
def add_rso_user():
    email = g.clean_json['email']

    rso_email = PreVerifiedEmail.objects(email=email).first()
    if rso_email is None:
        PreVerifiedEmail(email=email).save()
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='RSO Email already exists!')


@as_json
@monitor_blueprint.route('/rso/<email>', methods=['DELETE'])
def remove_rso_user(email):
    rso_email = PreVerifiedEmail.objects(email=email).first()
    if rso_email is None:
        raise JsonError(status='error', reason='RSO Email does not exist!')

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

    # NOTE: Each club should always have an associated user, so there really shouldn't be
    # a case where there's a club without it's owner
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
def add_tag():
    tag_name = g.clean_json['name']

    tag = Tag.objects(name=tag_name).first()
    if tag is None:
        Tag(name=tag_name).save()
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='Tag already exists!')


@as_json
@monitor_blueprint.route('/tags/<tag_id>', methods=['PUT'])
def edit_tag(tag_id):
    new_tag_name = g.clean_json['tag_name']

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
    tag = Tag.objects(id=tag_id).first()
    if tag is not None:
        tag.delete()
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='Tag does not exist!')
