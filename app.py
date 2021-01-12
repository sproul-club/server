from dotenv import load_dotenv
load_dotenv()

from flask import request
from flask_json import JsonError

from init_app import app, flask_exts
from blueprints import *

from models import *

@flask_exts.json.invalid_json_error
def handler(e):
    raise JsonError(status='error', reason='Expected JSON in body')


# Hotfix for full CORS support
@app.before_request
def before_request_func():
    if not request.is_json:
        if request.method == 'OPTIONS':
            return 'OK'


@app.errorhandler(flask_exts.mongo.errors.ValidationError)
def handle_mongo_validation_error(ex):
    return {
        'status': 'error',
        'reason': 'A validation error occurred within MongoDB. Please contact the backend dev about this!',
        'data': [{'field': v_error[0], 'error': v_error[1]} for v_error in ex.to_dict().items()]
    }, 500

# JWT custom handlers
@flask_exts.jwt.user_identity_loader
def user_identity_lookup(user):
    return {
        'email': user.email,
        'role': user.role,
    }


@flask_exts.jwt.user_loader_callback_loader
def user_loader_callback(identity):
    return NewBaseUser.objects(
        email=identity['email'],
        role=identity['role']
    ).first()


@flask_exts.jwt.user_loader_error_loader
def custom_user_loader_error(identity):
    return {'status': 'error', 'reason': 'User not found'}, 404


@flask_exts.jwt.token_in_blacklist_loader
def is_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    access_jti = AccessJTI.objects(token_id=jti).first()
    refresh_jti = RefreshJTI.objects(token_id=jti).first()

    if access_jti is not None:
        return access_jti.expired
    elif refresh_jti is not None:
        return refresh_jti.expired
    else:
        # If a token is not in the blacklist, it's already expired according to MongoDB
        # and thus is available for another user to take that same value
        return False


@flask_exts.jwt.expired_token_loader
def expired_jwt_handler(exp_token):
    return {'status': 'error', 'reason': 'Token has expired'}, 401


@flask_exts.jwt.unauthorized_loader
@flask_exts.jwt.invalid_token_loader
def unauth_or_invalid_jwt_handler(reason):
    return {'status': 'error', 'reason': reason}, 401


@flask_exts.jwt.revoked_token_loader
def revoked_jwt_handler():
    return {'status': 'error', 'reason': 'Token has been revoked'}, 401


app.register_blueprint(user_blueprint)
app.register_blueprint(catalog_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(monitor_blueprint)
app.register_blueprint(student_blueprint)

if __name__ == '__main__':
    app.run(load_dotenv=False, use_reloader=False)
