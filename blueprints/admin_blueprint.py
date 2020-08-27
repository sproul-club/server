import os
import json
import datetime
import dateutil

from passlib.hash import pbkdf2_sha512 as hash_manager

from init_app import flask_exts
from flask import Blueprint, request, g
from flask_json import as_json, JsonError
from flask_utils import validate_json, id_creator
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user

from models import *

admin_blueprint = Blueprint('admin', __name__, url_prefix='/api/admin')

_get_list_resources = lambda club: json.dumps([json.loads(resource.to_json()) for resource in club.resources])
_get_list_events    = lambda club: json.dumps([json.loads(event.to_json()) for event in club.events])


@as_json
@admin_blueprint.route('/profile', methods=['GET'])
@jwt_required
def fetch_profile():
    club = current_user['club']
    return club.to_json()


@as_json
@admin_blueprint.route('/profile', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 100},
    'tags': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'app_required': {'type': 'boolean'},
    'new_members': {'type': 'boolean'},
    'about_us': {'type': 'string', 'maxlength': 750},
    'get_involved': {'type': 'string', 'maxlength': 500},
    'social_media_links': {
        'type': 'dict',
        'schema': {
            'contact_email': {'type': 'string', 'empty': False},
            'website': {'type': 'string', 'nullable': True, 'empty': True},
            'facebook': {'type': 'string', 'nullable': True, 'empty': True},
            'instagram': {'type': 'string', 'nullable': True, 'empty': True},
            'linkedin': {'type': 'string', 'nullable': True, 'empty': True},
            'twitter': {'type': 'string', 'nullable': True, 'empty': True},
            'youtube': {'type': 'string', 'nullable': True, 'empty': True},
            'github': {'type': 'string', 'nullable': True, 'empty': True},
            'behance': {'type': 'string', 'nullable': True, 'empty': True},
            'medium': {'type': 'string', 'nullable': True, 'empty': True},
            'gcalendar': {'type': 'string', 'nullable': True, 'empty': True}
        }
    }
})
@jwt_required
def edit_profile():
    json = g.clean_json
    json['tags'] = Tag.objects.filter(id__in=json['tags'])

    club = current_user['club']
    club.update(**json)
    return {'status': 'success'}


@as_json
@admin_blueprint.route('/upload-logo', methods=['POST'])
@jwt_required
def upload_logo():
    club = current_user['club']
    logo_file = request.files.get('logo', None)

    if logo_file is not None:
        logo_url = flask_exts.img_manager.upload_img_asset_s3(club.id, logo_file, 'logo', 1.0)
        club.update(logo_url=logo_url)
        return {'status': 'success', 'logo-url': club.logo_url}
    else:
        raise JsonError(status='error', reason='A logo was not provided for uploading.')


@as_json
@admin_blueprint.route('/upload-banner', methods=['POST'])
@jwt_required
def upload_banner():
    club = current_user['club']
    banner_file = request.files.get('banner', None)

    if banner_file is not None:
        banner_url = flask_exts.img_manager.upload_img_asset_s3(club.id, banner_file, 'banner', 8 / 3)
        club.update(banner_url=banner_url)
        return {'status': 'success', 'banner-url': club.banner_url}
    else:
        raise JsonError(status='error', reason='A banner was not provided for uploading.')


@as_json
@admin_blueprint.route('/resources', methods=['GET'])
@jwt_required
def get_resources():
    club = current_user['club']
    return _get_list_resources(club)


@as_json
@admin_blueprint.route('/resources', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 100},
    'link': {'type': 'string', 'empty': False}
}, require_all=True)
@jwt_required
def add_resource():
    json = g.clean_json
    club = current_user['club']

    res_name = json['name']
    res_link = json['link']

    new_resource_id = id_creator(res_name)
    for resource in club.resources:
        if resource.id == new_resource_id:
            raise JsonError(status='error', reason='Resource already exists under that name')

    resource = Resource(
        id=id_creator(res_name),
        name=res_name,
        link=res_link
    )

    club.resources += [resource]
    club.save()

    return _get_list_resources(club)


@as_json
@admin_blueprint.route('/resources/<resource_id>', methods=['PUT'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 100},
    'link': {'type': 'string', 'empty': False}
})
@jwt_required
def update_resource(resource_id):
    json = g.clean_json
    club = current_user['club']

    for (i, resource) in enumerate(club.resources):
        if resource.id == resource_id:
            for key in json.keys():
                if json.get(key) is not None:
                    club.resources[i][key] = json[key]
            club.save()

            return _get_list_resources(club)

    raise JsonError(status='error', reason='Requested resource does not exist', status_=404)


@as_json
@admin_blueprint.route('/resources/<resource_id>', methods=['DELETE'])
@jwt_required
def delete_resource(resource_id):
    club = current_user['club']
    prev_len = len(club.resources)

    club.resources = [resource for resource in club.resources if resource.id != resource_id]
    club.save()

    new_len = len(club.resources)
    if new_len != prev_len:
        return _get_list_resources(club)
    else:
        raise JsonError(status='error', reason='Requested resource does not exist', status_=404)


@as_json
@admin_blueprint.route('/events', methods=['GET'])
@jwt_required
def get_events():
    club = current_user['club']
    return _get_list_events(club)


@as_json
@admin_blueprint.route('/events', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 100},
    'link': {'type': 'string', 'empty': False},
    'event_start': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'description': {'type': 'string', 'maxlength': 1000}
}, require_all=True)
@jwt_required
def add_event():
    json = g.clean_json
    club = current_user['club']

    event_name        = json['name']
    event_link        = json['link']
    event_start       = json['event_start']
    event_end         = json['event_end']
    event_description = json['description']

    new_event_id = id_creator(event_name)
    for event in club.events:
        if event.id == new_event_id:
            raise JsonError(status='error', reason='Event already exists under that name')

    event = Event(
        id=new_event_id,
        name=event_name,
        link=event_link,
        event_start=event_start,
        event_end=event_end,
        description=event_description,
    )

    club.events += [event]
    club.save()

    return _get_list_events(club)


@as_json
@admin_blueprint.route('/events/<event_id>', methods=['PUT'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 60},
    'link': {'type': 'string', 'empty': False},
    'event_start': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'description': {'type': 'string', 'maxlength': 1000}
})
@jwt_required
def update_event(event_id):
    json = g.clean_json
    club = current_user['club']

    for (i, event) in enumerate(club.events):
        if event.id == event_id:
            for key in json.keys():
                if json.get(key) is not None:
                    club.events[i][key] = json[key]
            club.save()

            return _get_list_events(club)

    raise JsonError(status='error', reason='Requested event does not exist', status_=404)


@as_json
@admin_blueprint.route('/events/<event_id>', methods=['DELETE'])
@jwt_required
def delete_event(event_id):
    club = current_user['club']
    prev_len = len(club.events)

    club.events = [event for event in club.events if event.id != event_id]
    club.save()

    new_len = len(club.events)
    if new_len != prev_len:
        return _get_list_events(club)
    else:
        raise JsonError(status='error', reason='Requested event does not exist', status_=404)


@as_json
@admin_blueprint.route('/change-password', methods=['POST'])
@validate_json(schema={
    'old_password': {'type': 'string', 'empty': False},
    'new_password': {'type': 'string', 'empty': False}
}, require_all=True)
@jwt_required
def change_password():
    json = g.clean_json
    owner = current_user['user']

    old_password = json['old_password']
    new_password = json['new_password']

    if not hash_manager.verify(old_password, owner.password):
        raise JsonError(status='error', reason='The old password is incorrect.')

    # Check if the password is the same
    if old_password == new_password:
        raise JsonError(status='error', reason='The old and new passwords are identical.')

    # Check if the password is strong enough
    is_password_strong = flask_exts.password_checker.check(new_password)
    if not is_password_strong:
        raise JsonError(status='error', reason='The new password is not strong enough')

    # Only set the new password if the old password is verified
    owner.password = hash_manager.hash(new_password)
    owner.save()

    return {'status': 'success'}
