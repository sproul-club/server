from decorator import decorator

from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims

@decorator
def role_required(func, roles=[], *args, **kw):
    verify_jwt_in_request()
    claims = get_jwt_claims()

    user_roles = set(claims['role'])
    required_roles = set(roles)

    matched_roles = user_roles.intersection(required_roles)
    has_perms = len(matched_roles) > 0

    if has_perms:
        return func(*args, **kw)
    else:
        return {'status': 'error', 'reason': 'You are not allowed to access this endpoint!'}, 401