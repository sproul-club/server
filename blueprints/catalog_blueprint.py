from flask import Blueprint, g, request
from flask_json import as_json, JsonError
from flask_utils import validate_json, query_to_objects, role_required

from models import Tag, NewOfficerUser

catalog_blueprint = Blueprint('catalog', __name__, url_prefix='/api/catalog')

CATALOG_VIEW_FIELDS = [
    'club.name', 'club.link_name', 'club.tags', 'club.app_required',
    'club.new_members', 'club.logo_url', 'club.banner_url', 'club.about_us'
]

def to_int_safe(s, default):
    try:
        return int(s)
    except ValueError:
        return default


@catalog_blueprint.route('/tags', methods=['GET'])
@as_json
def get_tags():
    return query_to_objects(Tag.objects.all())


@catalog_blueprint.route('/num-user-tags', methods=['GET'])
@as_json
def get_num_user_tags():
    return query_to_objects(NumUsersTag.objects.all())


@catalog_blueprint.route('/organizations', methods=['GET'])
def get_organizations():
    limit = to_int_safe( request.args.get('limit'), 50)
    skip = to_int_safe( request.args.get('skip'), 0)

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


@catalog_blueprint.route('/organizations/<org_link_name>', methods=['GET'])
def get_org_by_id(org_link_name):
    user = NewOfficerUser.objects(club__link_name=org_link_name).first()
    if user is None:
        raise JsonError(status='error', reason='The requested club does not exist!', status_=404)

    club_obj = query_to_objects(user.club)

    for event in club_obj['events']:
        del event['_cls']

    for r_event in club_obj['recruiting_events']:
        del r_event['_cls']

    return club_obj
