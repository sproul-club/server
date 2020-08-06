import os
import json
import datetime
import dateutil

from init_app import app, flask_exts
from flask import Blueprint, request, g
from flask_json import as_json, JsonError
from flask_utils import validate_json, id_creator, hyphen_to_underscore
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user

from models import *

admin_blueprint = Blueprint('admin', __name__, url_prefix='/api/admin')


@as_json
@admin_blueprint.route('/profile', methods=['GET'])
@jwt_required
def fetch_profile():
    club = current_user['club']
    return club.to_json()


@as_json
@admin_blueprint.route('/profile', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string'},
    'tags': {'type': 'list', 'schema': {'type': 'integer'}},
    'app-required': {'type': 'boolean'},
    'new-members': {'type': 'boolean'},
    'about-us': {'type': 'string'},
    'get-involved': {'type': 'string'},
    'social-media-links': {
        'type': 'dict',
        'schema': {
            'contact-email': {'type': 'string', 'nullable': True},
            'website': {'type': 'string', 'nullable': True},
            'facebook': {'type': 'string', 'nullable': True},
            'instagram': {'type': 'string', 'nullable': True},
            'linkedin': {'type': 'string', 'nullable': True},
            'twitter': {'type': 'string', 'nullable': True},
            'youtube': {'type': 'string', 'nullable': True},
            'github': {'type': 'string', 'nullable': True},
            'behance': {'type': 'string', 'nullable': True},
            'medium': {'type': 'string', 'nullable': True},
            'gcalendar': {'type': 'string', 'nullable': True}
        }
    }
})
@jwt_required
def edit_profile():
    json = g.clean_json
    json['tags'] = Tag.objects.filter(id__in=json['tags'])
    json = hyphen_to_underscore(json)

    club = current_user['club']
    club.update(**json)
    return {'status': 'success'}


@as_json
@admin_blueprint.route('/upload-images', methods=['POST'])
@jwt_required
def upload_logo():
    club = current_user['club']
    club_id = club.id

    response = {}

    logo_file = request.files.get('logo', None)
    if logo_file is not None:
        logo_url = flask_exts.img_manager.upload_img_asset_s3(club.id, logo_file, 'logo', 1.0)
        club.logo_url = logo_url
        response['logo-url'] = club.logo_url

    banner_file = request.files.get('banner', None)
    if banner_file is not None:
        banner_url = flask_exts.img_manager.upload_img_asset_s3(club.id, banner_file, 'banner', 16 / 9)
        club.banner_url = banner_url
        response['banner-url'] = club.banner_url

    club.save()
    response['status'] = 'success'
    return response


@as_json
@admin_blueprint.route('/resources', methods=['GET'])
@jwt_required
def get_resources():
    club = current_user['club']
    return json.dumps([json.loads(resource.to_json()) for resource in club.resources])


@as_json
@admin_blueprint.route('/resources', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string'},
    'link': {'type': 'string'}
}, require_all=True)
@jwt_required
def add_resource():
    json = g.clean_json

    res_name = json['name']
    res_link = json['link']

    new_resource_id = id_creator(res_name)
    for resource in current_user['club'].resources:
        if resource.id == new_resource_id:
            raise JsonError(status='error', reason='Resource already exists under that name')

    resource = Resource(
        id=id_creator(res_name),
        name=res_name,
        link=res_link
    )

    current_user['club'].resources += [resource]
    current_user['club'].save()

    return {'status': 'success'}


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
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='Requested resource does not exist', status_=404)


@as_json
@admin_blueprint.route('/events', methods=['GET'])
@jwt_required
def get_events():
    club = current_user['club']
    return json.dumps([json.loads(event.to_json()) for event in club.events])


@as_json
@admin_blueprint.route('/events', methods=['POST'])
@validate_json(schema={
    'name': {'type': 'string'},
    'link': {'type': 'string'},
    'event-start': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'event-end': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'description': {'type': 'string'}
}, require_all=True)
@jwt_required
def add_event():
    json = g.clean_json
    event_name        = json['name']
    event_link        = json['link']
    event_start       = json['event-start']
    event_end         = json['event-end']
    event_description = json['description']

    new_event_id = id_creator(event_name)
    for event in current_user['club'].events:
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

    current_user['club'].events += [event]
    current_user['club'].save()

    return {'status': 'success'}


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
        return {'status': 'success'}
    else:
        raise JsonError(status='error', reason='Requested event does not exist', status_=404)
