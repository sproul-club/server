from dotenv import load_dotenv
load_dotenv()

from utils import pst_right_now
from flask import request
from flask_json import JsonError

import datetime

import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from init_app import app, flask_exts
from blueprints import *

from models import *

@flask_exts.json.invalid_json_error
def handler(e):
    """
    This is an error handler for when a POST request doesn't receive a JSON body.
    """

    raise JsonError(status='error', reason='Expected JSON in body')


@app.before_request
def before_request_func():
    """
    HACK: This is a pre-request hook for allowing OPTIONS requests to go through, as part of fully supporting CORS.

    NOTE: If you plan to remove it, test this in development AND production before confirming to remove it!
    """

    if not request.is_json:
        if request.method == 'OPTIONS':
            return 'OK'


@app.errorhandler(flask_exts.mongo.errors.ValidationError)
def handle_mongo_validation_error(ex):
    """
    This is an error handler for when the app tries to save an invalid MongoDB document per docment's specification.
    These validation errors are meant for the developer and therefore should not appear to the user. They should
    ideally be properly handled and return 4XX errors instead.
    """

    return {
        'status': 'error',
        'reason': 'A validation error occurred within MongoDB. Please contact the dev team about this!',
        'data': [{'field': v_error[0], 'error': v_error[1]} for v_error in ex.to_dict().items()]
    }, 500


"""
These next few handlers are part of implementing JWT-based authentication support, as part of the
'flask_jwt_extended' library.

Documentation for 'flask_jwt_extended' handlers: https://darksun-flask-jwt-extended.readthedocs.io/en/latest/api

Implemented handlers:
* user_identity_loader
* user_loader_callback_loader
* user_loader_error_loader
* token_in_blacklist_loader
* expired_token_loader
* unauthorized_loader
* invalid_token_loader
* revoked_token_loader
"""

@flask_exts.jwt.user_identity_loader
def user_identity_lookup(user):
    """
    This function is triggered after 'user_loader_callback' and is used to return a plain JSON object back to the user.
    """

    return {
        'email': user.email,
        'role': user.role,
        'confirmed': user.confirmed,
    }


@flask_exts.jwt.user_loader_callback_loader
def user_loader_callback(identity):
    """
    Given the decrypted identity object, find the corresponding user on the database and return it
    if it exists. Otherwise return None.
    """

    return NewBaseUser.objects(
        email=identity['email'],
        role=identity['role'],
        confirmed=identity['confirmed'],
    ).first()


@flask_exts.jwt.user_loader_error_loader
def custom_user_loader_error(identity):
    """
    If 'user_loader_callback' returns None, notify that the user couldn't be found.
    """

    return {'status': 'error', 'reason': 'User not found'}, 404


@flask_exts.jwt.token_in_blacklist_loader
def is_token_in_blacklist(decrypted_token):
    """
    This is called to check if given decrypted JWT is in the blocklist. If it is, return true and
    return false otherwise.
    """

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
    """
    Custom handler for when the given JWT has expired.
    """

    return {'status': 'error', 'reason': 'Token has expired'}, 401


@flask_exts.jwt.unauthorized_loader
@flask_exts.jwt.invalid_token_loader
def unauth_or_invalid_jwt_handler(reason):
    """
    Custom generic handler for when the given JWT is invalid.
    """

    return {'status': 'error', 'reason': reason}, 401


@flask_exts.jwt.revoked_token_loader
def revoked_jwt_handler():
    """
    Custom handler for when the given JWT has been revoked.
    """

    return {'status': 'error', 'reason': 'Token has been revoked'}, 401


# Load the Flask blueprints
app.register_blueprint(user_blueprint)
app.register_blueprint(catalog_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(monitor_blueprint)
app.register_blueprint(student_blueprint)


def setup_background_jobs():
    """
    Setups a series of background jobs that run per a set schedule. These jobs range from updating if
    application and recruitement deadlines have passed and for retraining the similar clubs recommendation
    model if club descriptions have possibly changed.
    """
    scheduler = BackgroundScheduler()

    def update_apply_required_or_recruiting_statuses():
        """
        Update if a club is open for applying or recruiting.
        """
        right_now_dt = pst_right_now()

        for officer_user in NewOfficerUser.objects:
            if officer_user.club.app_required and officer_user.club.apply_deadline_start and officer_user.club.apply_deadline_end:
                apply_deadline_in_range = officer_user.club.apply_deadline_start < right_now_dt and officer_user.club.apply_deadline_end > right_now_dt
                officer_user.club.new_members = apply_deadline_in_range
                officer_user.save()
            elif not officer_user.club.app_required and officer_user.club.recruiting_start and officer_user.club.recruiting_end:
                recruiting_period_in_range = officer_user.club.recruiting_start < right_now_dt and officer_user.club.recruiting_end > right_now_dt
                officer_user.club.new_members = recruiting_period_in_range
                officer_user.save()

    def retrain_club_recommender_model():
        """
        Retrain the similar clubs recommender model.
        """
        flask_exts.club_recommender.train_or_load_model(force_train=True)


    job = scheduler.add_job(update_apply_required_or_recruiting_statuses, 'cron', minute='*/1')
    job = scheduler.add_job(retrain_club_recommender_model, 'cron', hour='*/4')
    scheduler.start()

    # Register a shutdown handler to gracefully terminate and running jobs.
    atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    setup_background_jobs()
    app.run(load_dotenv=False, use_reloader=False)
