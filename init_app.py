from dotenv import load_dotenv
load_dotenv()

import os

import mongoengine as mongo
# import walrus

from flask import Flask
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_json import FlaskJSON
from flask_cors import CORS
from flask_talisman import Talisman
from scout_apm.flask import ScoutApm

from app_config import CurrentConfig
from flask_utils import EmailVerifier, EmailSender, ImageManager, PasswordEnforcer

# Setup Sentry SDK
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_URL'),
    integrations=[FlaskIntegration()]
)

app = Flask('app', template_folder='templates')
app.config.from_object(CurrentConfig)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True)

# Flask extension libraries
class FlaskExtensions(object):
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

        self.mongo = mongo
        self.mongo.connect(host=os.getenv('MONGO_URI'))

        # redis_url = urlparse.urlparse(os.environ.get('REDIS_URI'))
        # self.redis = walrus.Database(host=redis_url.hostname, port=redis_url.port, password=redis_url.password, db=0, decode_responses=True)

flask_exts = FlaskExtensions(app)