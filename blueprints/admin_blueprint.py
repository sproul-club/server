import dateutil

from passlib.hash import pbkdf2_sha512 as hash_manager
from slugify import slugify

from init_app import flask_exts
from flask import Blueprint, request, g
from flask_json import as_json, JsonError
from flask_utils import validate_json, query_to_objects
from flask_jwt_extended import jwt_required, get_current_user

from models import *

admin_blueprint = Blueprint('admin', __name__, url_prefix='/api/admin')

_fetch_resources_list = lambda user: [query_to_objects(res) for res in user.club.resources]
_fetch_event_list = lambda user: [query_to_objects(event) for event in user.club.events]


@admin_blueprint.route('/profile', methods=['GET'])
@jwt_required
@role_required(roles=['officer'])
def fetch_profile():
    user = get_current_user()

    club_obj = query_to_objects(user.club)
    club_obj['owner'] = user.email

    return club_obj


@admin_blueprint.route('/profile', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
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
            'gcalendar': {'type': 'string', 'nullable': True, 'empty': True},
            'discord': {'type': 'string', 'nullable': True, 'empty': True}
        }
    }
})
def edit_profile():
    user = get_current_user()
    json = g.clean_json

    for key in json.keys():
        if key == 'tags':
            user.club['tags'] = Tag.objects.filter(id__in=json['tags'])
        elif key == 'social_media_links':
            user.update(club__social_media_links=json['social_media_links'])
        else:
            user.club[key] = json[key]

    user.save()
    return {'status': 'success'}


@admin_blueprint.route('/upload-logo', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
def upload_logo():
    user = get_current_user()
    club = user.club

    logo_file = request.files.get('logo', None)

    if logo_file is not None:
        logo_url = flask_exts.img_manager.upload_img_asset_s3(club.link_name, logo_file, 'logo', 1.0)
        user.update(club__logo_url=logo_url)
        return {'status': 'success', 'logo-url': club.logo_url}
    else:
        raise JsonError(status='error', reason='A logo was not provided for uploading.')


@admin_blueprint.route('/upload-banner', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
def upload_banner():
    user = get_current_user()
    club = user.club

    banner_file = request.files.get('banner', None)

    if banner_file is not None:
        banner_url = flask_exts.img_manager.upload_img_asset_s3(club.link_name, banner_file, 'banner', 8 / 3)
        user.update(club__banner_url=banner_url)
        return {'status': 'success', 'banner-url': club.banner_url}
    else:
        raise JsonError(status='error', reason='A banner was not provided for uploading.')


@admin_blueprint.route('/resources', methods=['GET'])
@jwt_required
@role_required(roles=['officer'])
@as_json
def get_resources():
    user = get_current_user()
    return _fetch_resources_list(user)


@admin_blueprint.route('/resources', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 100},
    'link': {'type': 'string', 'empty': False}
}, require_all=True)
@as_json
def add_resource():
    user = get_current_user()
    club = user.club

    json = g.clean_json

    res_name = json['name']
    res_link = json['link']

    new_resource_id = slugify(res_name, max_length=100)
    for resource in club.resources:
        if resource.id == new_resource_id:
            raise JsonError(status='error', reason='Resource already exists under that name')

    resource = Resource(
        id=new_resource_id,
        name=res_name,
        link=res_link
    )

    club.resources += [resource]
    user.save()

    return _fetch_resources_list(user)


@admin_blueprint.route('/resources/<resource_id>', methods=['PUT'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'empty': False, 'maxlength': 100},
    'link': {'type': 'string', 'empty': False}
})
@as_json
def update_resource(resource_id):
    user = get_current_user()
    club = user.club

    json = g.clean_json

    for (i, resource) in enumerate(club.resources):
        if resource.id == resource_id:
            for key in json.keys():
                if json.get(key) is not None:
                    club.resources[i][key] = json[key]
            user.save()

            return _fetch_resources_list(user)

    raise JsonError(status='error', reason='Requested resource does not exist', status_=404)


@admin_blueprint.route('/resources/<resource_id>', methods=['DELETE'])
@jwt_required
@role_required(roles=['officer'])
@as_json
def delete_resource(resource_id):
    user = get_current_user()
    club = user.club

    prev_len = len(club.resources)

    club.resources = [resource for resource in club.resources if resource.id != resource_id]
    user.save()

    new_len = len(club.resources)
    if new_len != prev_len:
        return _fetch_resources_list(user)
    else:
        raise JsonError(status='error', reason='Requested resource does not exist', status_=404)


@admin_blueprint.route('/events', methods=['GET'])
@jwt_required
@role_required(roles=['officer'])
@as_json
def get_events():
    user = get_current_user()
    return _fetch_event_list(user)


@admin_blueprint.route('/events', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'required': True, 'maxlength': 100},
    'link': {'type': 'string'},
    'event_start': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'description': {'type': 'string', 'maxlength': 500}
})
@as_json
def add_event():
    user = get_current_user()
    club = user.club

    json = g.clean_json

    event_name        = json['name']
    event_link        = json['link']
    event_start       = json['event_start']
    event_end         = json['event_end']
    event_description = json['description']

    new_event_id = slugify(event_name, max_length=100)
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
    user.save()

    return _fetch_event_list(user)


@admin_blueprint.route('/events/<event_id>', methods=['PUT'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'required': True, 'maxlength': 100},
    'link': {'type': 'string'},
    'event_start': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'description': {'type': 'string', 'maxlength': 500}
})
@as_json
def update_event(event_id):
    user = get_current_user()
    club = user.club

    json = g.clean_json

    for (i, event) in enumerate(club.events):
        if event.id == event_id:
            for key in json.keys():
                if json.get(key) is not None:
                    club.events[i][key] = json[key]
            user.save()

            return _fetch_event_list(user)

    raise JsonError(status='error', reason='Requested event does not exist', status_=404)


@admin_blueprint.route('/events/<event_id>', methods=['DELETE'])
@jwt_required
@role_required(roles=['officer'])
@as_json
def delete_event(event_id):
    user = get_current_user()
    club = user.club

    prev_len = len(club.events)

    club.events = [event for event in club.events if event.id != event_id]
    user.save()

    new_len = len(club.events)
    if new_len != prev_len:
        return _fetch_event_list(user)
    else:
        raise JsonError(status='error', reason='Requested event does not exist', status_=404)


@admin_blueprint.route('/change-password', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'old_password': {'type': 'string', 'empty': False},
    'new_password': {'type': 'string', 'empty': False}
}, require_all=True)
def change_password():
    user = get_current_user()
    club = user.club

    json = g.clean_json

    old_password = json['old_password']
    new_password = json['new_password']

    if not hash_manager.verify(old_password, user.password):
        raise JsonError(status='error', reason='The old password is incorrect.')

    # Check if the password is the same
    if old_password == new_password:
        raise JsonError(status='error', reason='The old and new passwords are identical.')

    # Check if the password is strong enough
    is_password_strong = flask_exts.password_checker.check(new_password)
    if not is_password_strong:
        raise JsonError(status='error', reason='The new password is not strong enough')

    # Only set the new password if the old password is verified
    user.password = hash_manager.hash(new_password)
    user.save()

    return {'status': 'success'}
