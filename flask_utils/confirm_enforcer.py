from decorator import decorator

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


@decorator
def confirmed_account_required(func, *args, **kw):
    """
    This decorator checks if the user account has been confirmed via email, and otherwise returns
    a 401 Unauthorized error. This is useful for incentivizing accounts to confirm their emails by
    unlocking said protected features.

    NOTE: This only works if a JWT token is present (enforced via jwt_required).

    Example:

    @app.route('/my_profile', methods=['GET'])
    @jwt_required
    @confirmed_account_required
    def fetch_profile():
        user = get_current_user()

        return {
            'name': user.name,
            'email': user.email
        }
    """
    
    # verify_jwt_in_request()
    identity = get_jwt_identity()

    if identity['confirmed']:
        return func(*args, **kw)
    else:
        return {'status': 'error', 'reason': 'You are not allowed to access this endpoint!'}, 401
