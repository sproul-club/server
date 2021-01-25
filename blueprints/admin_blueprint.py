import datetime
import dateutil.parser

from passlib.hash import pbkdf2_sha512 as hash_manager
from slugify import slugify

from utils import datetime_or_null, random_slugify, pst_right_now

from init_app import flask_exts
from flask import Blueprint, request, g
from flask_json import as_json, JsonError
from flask_utils import validate_json, query_to_objects, role_required
from flask_jwt_extended import jwt_required, get_current_user

from models import *

admin_blueprint = Blueprint('admin', __name__, url_prefix='/api/admin')

_fetch_resources_list = lambda user: [query_to_objects(res) for res in user.club.resources]
_fetch_event_list = lambda user: [query_to_objects(event) for event in user.club.events]
_fetch_recruiting_events_list = lambda user: [query_to_objects(r_event) for r_event in user.club.recruiting_events]
_fetch_gallery_pics_list = lambda user: [query_to_objects(gallery_pic) for gallery_pic in user.club.gallery_pics]


@admin_blueprint.route('/profile', methods=['GET'])
@jwt_required
@role_required(roles=['officer'])
def fetch_profile():
    user = get_current_user()

    club_obj = query_to_objects(user.club)
    club_obj['owner'] = user.email
    club_obj['confirmed'] = user.confirmed

    return club_obj


@admin_blueprint.route('/profile', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'is_reactivating': {'type': 'boolean', 'default': False},
    'name': {'type': 'string', 'empty': False, 'maxlength': 70},
    'tags': {'type': 'list', 'schema': {'type': 'integer'}, 'empty': False, 'maxlength': 3},
    'app_required': {'type': 'boolean'},
    'new_members': {'type': 'boolean'},
    'num_users': {'type': 'integer'},
    'about_us': {'type': 'string', 'maxlength': 750},
    'get_involved': {'type': 'string', 'maxlength': 500},
    'apply_link': {'type': 'string', 'nullable': True, 'empty': False},
    'apply_deadline_start': {'type': 'datetime', 'nullable': True, 'coerce': datetime_or_null},
    'apply_deadline_end': {'type': 'datetime', 'nullable': True, 'coerce': datetime_or_null},
    'recruiting_start': {'type': 'datetime', 'nullable': True, 'coerce': datetime_or_null},
    'recruiting_end': {'type': 'datetime', 'nullable': True, 'coerce': datetime_or_null},
    'social_media_links': {
        'type': 'dict',
        'schema': {
            'contact_email': {'type': 'string', 'empty': False},
            'website': {'type': 'string', 'nullable': True, 'empty': False},
            'facebook': {'type': 'string', 'nullable': True, 'empty': False},
            'instagram': {'type': 'string', 'nullable': True, 'empty': False},
            'linkedin': {'type': 'string', 'nullable': True, 'empty': False},
            'twitter': {'type': 'string', 'nullable': True, 'empty': False},
            'youtube': {'type': 'string', 'nullable': True, 'empty': False},
            'github': {'type': 'string', 'nullable': True, 'empty': False},
            'behance': {'type': 'string', 'nullable': True, 'empty': False},
            'medium': {'type': 'string', 'nullable': True, 'empty': False},
            'gcalendar': {'type': 'string', 'nullable': True, 'empty': False},
            'discord': {'type': 'string', 'nullable': True, 'empty': False}
        }
    }
})
def edit_profile():
    user = get_current_user()
    json = g.clean_json

    for key in json.keys():
        if key == 'is_reactivating':
            continue
        if key == 'tags':
            user.club['tags'] = Tag.objects.filter(id__in=json['tags'])
        elif key == 'num_users':
            user.club['num_users'] = NumUsersTag.objects.filter(id=json['num_users']).first()
        elif key == 'social_media_links':
            user.update(club__social_media_links=json['social_media_links'])
        else:
            user.club[key] = json[key]

    user.club.last_updated = pst_right_now()

    if json['is_reactivating'] and not user.club.reactivated:
        user.club.reactivated = True
        user.club.reactivated_last = user.club.last_updated
        
    user.save()

    return {'status': 'success'}


@admin_blueprint.route('/upload-logo', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
def upload_logo():
    user = get_current_user()

    logo_file = request.files.get('logo', None)

    if logo_file is not None:
        logo_url, _ = flask_exts.img_manager.upload_img_asset_s3(user.club.link_name, logo_file, 'logo', 1.0)

        user.club.last_updated = pst_right_now()
        user.club.logo_url = logo_url

        user.save()
        return {'status': 'success', 'logo-url': user.club.logo_url}
    else:
        raise JsonError(status='error', reason='A logo was not provided for uploading.')


@admin_blueprint.route('/upload-banner', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
def upload_banner():
    user = get_current_user()

    banner_file = request.files.get('banner', None)

    if banner_file is not None:
        banner_url, _ = flask_exts.img_manager.upload_img_asset_s3(user.club.link_name, banner_file, 'banner', 10 / 3)

        user.club.last_updated = pst_right_now()
        user.club.banner_url = banner_url

        user.save()
        return {'status': 'success', 'banner-url': user.club.banner_url}
    else:
        raise JsonError(status='error', reason='A banner was not provided for uploading.')


@admin_blueprint.route('/gallery-pics', methods=['GET'])
@jwt_required
@role_required(roles=['officer'])
@as_json
def get_gallery_pics():
    user = get_current_user()
    return _fetch_gallery_pics_list(user)


@admin_blueprint.route('/gallery-pics', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'caption': {'type': 'string', 'empty': True, 'maxlength': 50}
}, require_all=True)
def add_gallery_pic():
    user = get_current_user()
    json = g.clean_json

    gallery_pic_file = request.files.get('gallery', None)

    if gallery_pic_file is not None:
        gallery_pic_url, pic_id = flask_exts.img_manager.upload_img_asset_s3(user.club.link_name, gallery_pic_file, 'gallery', 16 / 9)

        captioned_pic = CaptionedPic(
            id      = pic_id,
            url     = gallery_pic_url,
            caption = json['caption']
        )

        user.club.gallery_pics += [captioned_pic]
        user.club.last_updated = pst_right_now()

        user.save()
        return _fetch_gallery_pics_list(user)
    else:
        raise JsonError(status='error', reason='A gallery picture was not provided for uploading.')


@admin_blueprint.route('/gallery-pics/<pic_id>', methods=['PUT'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'caption': {'type': 'string', 'empty': True, 'maxlength': 50}
})
def modify_gallery_pic(pic_id):
    user = get_current_user()
    json = g.clean_json

    captioned_pic = user.club.gallery_pics.filter(id=pic_id).first()
    if captioned_pic is None:
        raise JsonError(status='error', reason='Specified gallery picture does not exist.')

    if json.get('caption') is not None:
        captioned_pic.caption = json['caption']

    gallery_pic_file = request.files.get('gallery', None)

    if gallery_pic_file is not None:
        gallery_pic_url, new_pic_id = flask_exts.img_manager.upload_img_asset_s3(user.club.link_name, gallery_pic_file, 'gallery', 16 / 9)
        
        captioned_pic.id = new_pic_id
        captioned_pic.url = gallery_pic_url
    
    user.club.last_updated = pst_right_now()
    user.save()
    return _fetch_gallery_pics_list(user)


@admin_blueprint.route('/gallery-pics/<pic_id>', methods=['DELETE'])
@jwt_required
@role_required(roles=['officer'])
def remove_gallery_pic(pic_id):
    user = get_current_user()

    user.club.gallery_pics = [gallery_pic for gallery_pic in user.club.gallery_pics if gallery_pic.id != pic_id]
    user.club.last_updated = pst_right_now()
    user.save()

    return _fetch_gallery_pics_list(user)


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

    new_resource_id = random_slugify(res_name, max_length=100)
    for resource in club.resources:
        if resource.id == new_resource_id:
            raise JsonError(status='error', reason='Resource already exists under that name')

    resource = Resource(
        id=new_resource_id,
        name=res_name,
        link=res_link
    )

    club.resources += [resource]

    user.club.last_updated = pst_right_now()
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

            user.club.last_updated = pst_right_now()
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

    user.club.last_updated = pst_right_now()
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
    'link': {'type': 'string', 'default': None},
    'event_start': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'description': {'type': 'string', 'maxlength': 500, 'default': ''}
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

    new_event_id = random_slugify(event_name, max_length=100)
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

    user.club.last_updated = pst_right_now()
    user.save()

    return _fetch_event_list(user)


@admin_blueprint.route('/events/<event_id>', methods=['PUT'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'maxlength': 100},
    'link': {'type': 'string'},
    'event_start': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'coerce': dateutil.parser.parse},
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

            user.club.last_updated = pst_right_now()
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

    user.club.last_updated = pst_right_now()
    user.save()

    new_len = len(club.events)
    if new_len != prev_len:
        return _fetch_event_list(user)
    else:
        raise JsonError(status='error', reason='Requested event does not exist', status_=404)


@admin_blueprint.route('/recruiting-events', methods=['GET'])
@jwt_required
@role_required(roles=['officer'])
@as_json
def get_recruiting_events():
    user = get_current_user()
    return _fetch_recruiting_events_list(user)


@admin_blueprint.route('/recruiting-events', methods=['POST'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'required': True, 'maxlength': 100},
    'link': {'type': 'string', 'nullable': True, 'default': None},
    'virtual_link': {'type': 'string', 'nullable': True, 'default': None},
    'invite_only': {'type': 'boolean', 'required': True},
    'event_start': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'required': True, 'coerce': dateutil.parser.parse},
    'description': {'type': 'string', 'maxlength': 200, 'default': ''}
})
@as_json
def add_recruiting_event():
    user = get_current_user()
    club = user.club

    json = g.clean_json
    r_event_name = json['name']

    new_event_id = random_slugify(r_event_name, max_length=100)
    for r_event in club.recruiting_events:
        if r_event.id == new_event_id:
            raise JsonError(status='error', reason='Recruiting event already exists under that name')

    new_r_event = RecruitingEvent(
        id              = new_event_id,
        name            = r_event_name,
        link            = json['link'],
        virtual_link    = json['virtual_link'],
        event_start     = json['event_start'],
        event_end       = json['event_end'],
        description     = json['description'],
        invite_only     = json['invite_only'],
    )

    club.recruiting_events += [new_r_event]

    user.club.last_updated = pst_right_now()
    user.save()

    return _fetch_recruiting_events_list(user)


@admin_blueprint.route('/recruiting-events/<r_event_id>', methods=['PUT'])
@jwt_required
@role_required(roles=['officer'])
@validate_json(schema={
    'name': {'type': 'string', 'maxlength': 100},
    'link': {'type': 'string', 'nullable': True},
    'virtual_link': {'type': 'string', 'nullable': True},
    'invite_only': {'type': 'boolean'},
    'event_start': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'event_end': {'type': 'datetime', 'coerce': dateutil.parser.parse},
    'description': {'type': 'string', 'maxlength': 200}
})
@as_json
def update_recruiting_event(r_event_id):
    user = get_current_user()
    club = user.club

    json = g.clean_json

    for (i, r_event) in enumerate(club.recruiting_events):
        if r_event.id == r_event_id:
            for key in json.keys():
                club.recruiting_events[i][key] = json[key]

            user.club.last_updated = pst_right_now()
            user.save()

            return _fetch_recruiting_events_list(user)

    raise JsonError(status='error', reason='Requested recruiting event does not exist', status_=404)


@admin_blueprint.route('/recruiting-events/<r_event_id>', methods=['DELETE'])
@jwt_required
@role_required(roles=['officer'])
@as_json
def delete_recruiting_event(r_event_id):
    user = get_current_user()
    club = user.club

    prev_len = len(club.recruiting_events)

    club.recruiting_events = [r_event for r_event in club.recruiting_events if r_event.id != r_event_id]

    user.club.last_updated = pst_right_now()
    user.save()

    new_len = len(club.recruiting_events)
    if new_len != prev_len:
        return _fetch_recruiting_events_list(user)
    else:
        raise JsonError(status='error', reason='Requested recruiting event does not exist', status_=404)



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
