"""
This file contains the setup process for the Flask app, by initializing and attaching the necessary middleware.
"""

import os

from dotenv import load_dotenv
load_dotenv()

import pymongo
import mongoengine as mongo
# import walrus

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_json import FlaskJSON
from flask_cors import CORS
from flask_talisman import Talisman
from scout_apm.flask import ScoutApm
from flask_compress import Compress

from app_config import CurrentConfig
from flask_utils import EmailVerifier, EmailSender, ImageManager, PasswordEnforcer

from recommenders import ClubRecommender

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


# Setup the sentry SDK
sentry_sdk.init(
    dsn=os.getenv('SENTRY_URL'),
    integrations=[FlaskIntegration()]
)

app = Flask('app', template_folder='templates')
app.config.from_object(CurrentConfig)

# Create the uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True)


class FlaskExtensions(object):
    """
    This is a convenience class that allows you to easily access useful libraries that were initialized
    with the Flask application object.

    Example:

    from init_app import flask_exts

    ...

    @user_blueprint.route('/password-strength', methods=['POST'])
    @validate_json(schema={
        'password': {'type': 'string', 'empty': False}
    }, require_all=True)
    def is_password_strong_enough():
        json = g.clean_json
        password = json['password']

        is_strong = flask_exts.password_checker.check(password)
        return {'strong': is_strong}
    """

    def __init__(self, app):
        self.cors = CORS(app)
        self.talisman = Talisman(app)
        self.jwt = JWTManager(app)
        self.email_sender = EmailSender(app)
        self.email_verifier = EmailVerifier(app)
        self.json = FlaskJSON(app)
        self.img_manager = ImageManager(app)
        self.password_checker = PasswordEnforcer()
        self.scout_apm = ScoutApm(app)
        self.compressor = Compress(app)

        self.pymongo_db = pymongo.MongoClient(os.getenv('MONGO_URI'))[app.config['DATABASE_NAME']]

        self.mongo = mongo
        self.mongo.connect(host=os.getenv('MONGO_URI'))

        self.club_recommender = ClubRecommender(self.pymongo_db, f'ml-models/club-model-{CurrentConfig.MODE}.pkl')
        self.club_recommender.train_or_load_model(force_train=True)

        # redis_url = urlparse.urlparse(os.environ.get('REDIS_URI'))
        # self.redis = walrus.Database(host=redis_url.hostname, port=redis_url.port, password=redis_url.password, db=0, decode_responses=True)

flask_exts = FlaskExtensions(app)
