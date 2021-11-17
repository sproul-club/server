from flask import Blueprint, g, request
from flask_json import as_json, JsonError
from flask_utils import validate_json, query_to_objects, role_required
from flask_jwt_extended import jwt_optional, get_current_user
from init_app import flask_exts

from models import *

from app_config import CurrentConfig

catalog_blueprint = Blueprint('catalog', __name__, url_prefix='/api/catalog')

CATALOG_VIEW_FIELDS = [
    'club.name', 'club.link_name', 'club.about_us',
    'club.tags', 'club.app_required', 'club.new_members', 'club.num_users',
    'club.logo_url', 'club.banner_url', 'club.last_updated', 'club.apply_deadline_end', 'club.recruiting_end'
]

def to_int_safe(s, default):
    """
    A safe string to integer function that returns a default if it fails.
    """

    try:
        return int(s)
    except ValueError:
        return default


def _random_generic_club_recommendations(size):
    """
    Generates random clubs recommendations, intended for testing purposes only.
    """

    random_recommended_users = NewOfficerUser.objects \
        .filter(confirmed=True) \
        .filter(club__reactivated=True) \
        .aggregate([{ '$sample': {'size': size} }])

    random_recommended_clubs = []
    for user in random_recommended_users:
        random_recommended_clubs += [{
            'link_name': user['club']['link_name'],
            'name':      user['club']['name'],
            'logo_url':  user['club']['logo_url'],
            'about_us':  user['club']['about_us'],
        }]

    return random_recommended_clubs


def _fetch_recommended_club_info(link_names):
    """
    Given a set of clubs' link names, fetch the relevant club information for the club view page.
    """

    random_recommended_users = NewOfficerUser.objects \
        .filter(club__link_name__in=link_names)

    random_recommended_clubs = []
    for user in random_recommended_users:
        random_recommended_clubs += [{
            'link_name': user['club']['link_name'],
            'name':      user['club']['name'],
            'logo_url':  user['club']['logo_url'],
            'about_us':  user['club']['about_us'],
        }]

    return random_recommended_clubs


@catalog_blueprint.route('/tags', methods=['GET'])
@as_json
def get_tags():
    """
    GET endpoint that fetches the set of club tags.
    """

    return query_to_objects(Tag.objects.all())


@catalog_blueprint.route('/num-user-tags', methods=['GET'])
@as_json
def get_num_user_tags():
    """
    GET endpoint that fetches the set of "# of users" tags.
    """

    return query_to_objects(NumUsersTag.objects.all())


@catalog_blueprint.route('/organizations', methods=['GET'])
def get_organizations():
    """
    GET endpoint that fetches the list of organizations without filters, sorted alphabetically.
    """

    limit = to_int_safe( request.args.get('limit'), 50)
    skip = to_int_safe( request.args.get('skip'), 0)

    query = NewOfficerUser.objects \
        .filter(confirmed=True) \
        .filter(club__reactivated=True) \
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
@jwt_optional
def get_org_by_id(org_link_name):
    """
    GET endpoint that fetches all information of the requested club organization, including
    its similarly recommended clubs.
    """

    user = NewOfficerUser.objects(
        club__link_name=org_link_name,
        confirmed=True,
        club__reactivated=True,
    ).first()

    if user is None:
        raise JsonError(status='error', reason='The requested club does not exist!', status_=404)

    club_obj = query_to_objects(user.club)

    for event in club_obj['events']:
        del event['_cls']


    current_user = get_current_user()

    if current_user and current_user.role == 'student':
        # Save the club as part of the student's visiting history of clubs
        current_user.visited_clubs += [org_link_name]
        current_user.save()

    if CurrentConfig.DEBUG:
        club_obj['recommended_clubs'] = _random_generic_club_recommendations(3)
    else:
        recommended_club_link_names = flask_exts.club_recommender.recommend(org_link_name)
        club_obj['recommended_clubs'] = _fetch_recommended_club_info(recommended_club_link_names)


    return club_obj
