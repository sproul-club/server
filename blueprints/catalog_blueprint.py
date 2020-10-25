import re
import json as json_module

from flask import Blueprint, request, g
from flask_json import as_json, JsonError
from flask_utils import validate_json

from models import *

catalog_blueprint = Blueprint('catalog', __name__, url_prefix='/api/catalog')

@catalog_blueprint.route('/tags', methods=['GET'])
@as_json
def get_tags():
    return Tag.objects.to_json()


@catalog_blueprint.route('/organizations', methods=['POST'])
@validate_json(schema={
    'limit': {'type': 'integer', 'default': 50},
    'skip': {'type': 'integer', 'default': 0}
})
def get_organizations():
    json = g.clean_json

    limit = json['limit']
    skip = json['skip']

    confirmed_users = User.objects(confirmed=True)

    query = Club.objects \
        .filter(owner__in=confirmed_users) \
        .only('id', 'name', 'tags', 'app_required',
              'new_members', 'logo_url', 'banner_url') \
        .order_by('name')

    num_clubs = len(query)

    query = query \
        .limit(limit) \
        .skip(skip) \

    return {
        'results': json_module.loads(query.to_json()),
        'num_results': num_clubs
    }


@catalog_blueprint.route('/search', methods=['POST'])
@validate_json(schema={
    'search': {'type': 'string', 'default': ''},
    'tags': {'type': 'list', 'schema': {'type': 'integer'}, 'default': []},
    'app_required': {'type': 'boolean', 'nullable': True, 'default': None},
    'new_members': {'type': 'boolean', 'nullable': True, 'default': None},
    'limit': {'type': 'integer', 'default': 50},
    'skip': {'type': 'integer', 'default': 0}
})
def search_orgs():
    json = g.clean_json

    search_text = json['search']
    club_tags = json['tags']
    app_required = json['app_required']
    new_members = json['new_members']

    limit = json['limit']
    skip = json['skip']

    confirmed_users = User.objects(confirmed=True)

    query = Club.objects \
        .filter(owner__in=confirmed_users) \
        .only('id', 'name', 'tags', 'app_required',
              'new_members', 'logo_url', 'banner_url')

    if len(search_text) > 0:
        query = query.filter(name__icontains=search_text).order_by('name')

        # regex_search_query = re.compile(search_text, re.IGNORECASE)
        # query = query.filter(name=regex_search_query)
        # query = query.search_text(search_text) \
        #             .order_by('$text_score')
    else:
        query = query.order_by('name')

    for tag in club_tags:
        query = query.filter(tags=tag)

    if app_required is not None:
        query = query.filter(app_required=app_required)

    if new_members is not None:
        query = query.filter(new_members=new_members)

    num_clubs = len(query)

    query = query \
        .limit(limit) \
        .skip(skip) \

    return {
        'results': json_module.loads(query.to_json()),
        'num_results': num_clubs
    }


@catalog_blueprint.route('/organizations/<org_id>', methods=['GET'])
def get_org_by_id(org_id):
    club = Club.objects(id=org_id).first()
    if club is None:
        raise JsonError(status='error', reason='The requested club does not exist!', status_=404)

    return club.to_json()
