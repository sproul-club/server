from flask import Blueprint, g
from flask_json import as_json, JsonError
from flask_utils import validate_json, query_to_objects, role_required

from models import Tag, NewOfficerUser

catalog_blueprint = Blueprint('catalog', __name__, url_prefix='/api/catalog')

CATALOG_VIEW_FIELDS = [
    'club.name', 'club.link_name', 'club.tags', 'club.app_status',
    'club.about_us', 'club.logo_url', 'club.banner_url'
]


@catalog_blueprint.route('/tags', methods=['GET'])
@as_json
def get_tags():
    return query_to_objects(Tag.objects.all())


@catalog_blueprint.route('/organizations', methods=['POST'])
@validate_json(schema={
    'limit': {'type': 'integer', 'default': 50},
    'skip': {'type': 'integer', 'default': 0}
})
def get_organizations():
    body = g.clean_json

    limit = body['limit']
    skip = body['skip']

    query = NewOfficerUser.objects \
        .filter(confirmed=True) \
        .only(*CATALOG_VIEW_FIELDS) \
        .order_by('club.name') \
        .limit(limit) \
        .skip(skip)

    results = [obj['club'] for obj in query_to_objects(query)]

    return {
        'results': results,
        'num_results': query.count()
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
    body = g.clean_json

    search_text = body['search']
    club_tags = body['tags']
    app_required = body['app_required']
    new_members = body['new_members']

    limit = body['limit']
    skip = body['skip']

    query = NewOfficerUser.objects \
        .filter(confirmed=True) \
        .only(*CATALOG_VIEW_FIELDS)

    if len(search_text) > 0:
        query = query.filter(club__name__icontains=search_text).order_by('club.name')

        # regex_search_query = re.compile(search_text, re.IGNORECASE)
        # query = query.filter(name=regex_search_query)
        # query = query.search_text(search_text) \
        #             .order_by('$text_score')
    else:
        query = query.order_by('club.name')

    for tag in club_tags:
        query = query.filter(club__tags=tag)

    if app_required is not None:
        query = query.filter(club__app_required=app_required)

    if new_members is not None:
        query = query.filter(club__new_members=new_members)

    query = query \
        .limit(limit) \
        .skip(skip)

    results = [obj['club'] for obj in query_to_objects(query)]

    return {
        'results': results,
        'num_results': query.count()
    }


@catalog_blueprint.route('/organizations/<org_link_name>', methods=['GET'])
def get_org_by_id(org_link_name):
    user = NewOfficerUser.objects(club__link_name=org_link_name).first()
    if user is None:
        raise JsonError(status='error', reason='The requested club does not exist!', status_=404)

    return query_to_objects(user.club)
