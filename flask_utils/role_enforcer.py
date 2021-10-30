from decorator import decorator

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


@decorator
def role_required(func, roles=[], *args, **kw):
    """
    This decorator checks if the user account has the necessary role(s) to access a particular endpoint,
    and otherwise returns a 401 Unauthorized error. This is necessary to implement multiple account types
    by restricting specific endpoints to specific ones. For example, a student account shouldn't be editing
    a club logo...since they don't have one to begin with.

    The logic for checking against a set of required roles is that it checks if a user has *at least* one
    of the required roles.

    NOTE: This only works if a JWT token is present (enforced via jwt_required).

    Example:

    @app.route('/club-name', methods=['POST'])
    @jwt_required
    @role_required(roles=['officer'])
    def edit_club_name():
        user = get_current_user()

        user.club.name = request.get_json()['name']
        user.save()

        return {'status': 'success'}

    This endpoint would throw a 401 Unauthorized error if a student account tried using this endpoint.
    """

    # verify_jwt_in_request()
    identity = get_jwt_identity()

    user_roles = set([identity['role']])
    required_roles = set(roles)

    # Check if the user's role has ANY common roles to the required roles. In other words, if a user's
    # roles are mutually exclusive to the required roles, then the user isn't allowed to access that endpoint.
    matched_roles = user_roles.intersection(required_roles)
    has_perms = len(matched_roles) > 0

    if has_perms:
        return func(*args, **kw)
    else:
        return {'status': 'error', 'reason': 'You are not allowed to access this endpoint!'}, 401
