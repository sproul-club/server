from decorator import decorator

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

@decorator
def confirmed_account_required(func, *args, **kw):
    # verify_jwt_in_request()
    identity = get_jwt_identity()

    if identity['confirmed']:
        return func(*args, **kw)
    else:
        return {'status': 'error', 'reason': 'You are not allowed to access this endpoint!'}, 401
