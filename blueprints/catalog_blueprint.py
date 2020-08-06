import re

from flask import Blueprint, request, g
from flask_json import as_json, JsonError
from flask_utils import validate_json
from init_app import flask_exts

import mongoengine as mongo
from models import Tag, Club

catalog_blueprint = Blueprint('catalog', __name__, url_prefix='/api/catalog')

@as_json
@catalog_blueprint.route('/tags', methods=['GET'])
def get_tags():
    return Tag.objects.to_json()


@as_json
@catalog_blueprint.route('/organizations', methods=['GET'])
@validate_json(schema={
    'limit': {'type': 'integer', 'default': 50},
    'skip': {'type': 'integer', 'default': 0}
})
def get_organizations():
    json = g.clean_json

    limit = json['limit']
    skip = json['skip']

    return Club \
        .objects[skip:skip + limit] \
        .only('id', 'name', 'tags', 'app_required',
              'new_members', 'logo_url', 'banner_url') \
        .order_by('name') \
        .to_json()


@as_json
@catalog_blueprint.route('/search', methods=['GET'])
@validate_json(schema={
    'search': {'type': 'string', 'default': ''},
    'tags': {'type': 'list', 'schema': {'type': 'integer'}, 'default': []},
    'app-required': {'type': 'boolean', 'nullable': True, 'default': None},
    'new-members': {'type': 'boolean', 'nullable': True, 'default': None},
    'limit': {'type': 'integer', 'default': 50},
    'skip': {'type': 'integer', 'default': 0}
})
def search_orgs():
    json = g.clean_json
    
    search_text = json['search']
    club_tags = json['tags']
    app_required = json['app-required']
    new_members = json['new-members']

    limit = json['limit']
    skip = json['skip']
    
    query = Club.objects \
        .only('id', 'name', 'tags', 'app_required',
              'new_members', 'logo_url', 'banner_url')

    if len(search_text) > 0:
        regex_search_query = re.compile(search_text, re.IGNORECASE)
        query = query.search_text(search_text) \
                    .order_by('$text_score')

    for tag in club_tags:
        query = query.filter(tags=tag)

    if app_required is not None:
        query = query.filter(app_required=app_required)

    if new_members is not None:
        query = query.filter(new_members=new_members)

    return query \
        .limit(limit) \
        .skip(skip) \
        .to_json()


@as_json
@catalog_blueprint.route('/organizations/<org_id>', methods=['GET'])
def get_org_by_id(org_id):
    club = Club.objects(id=org_id).first()
    if club is None:
        raise JsonError(status='error', reason='The requested club does not exist!', status_=404)

    return club.to_json()
    