from dotenv import load_dotenv
load_dotenv()

import os

from flask import Flask
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_json import FlaskJSON
from flask_cors import CORS

from app_config import FlaskConfig
from flask_utils import EmailVerifier, EmailSender, ImageManager

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

app = Flask('app', template_folder='templates')
app.config.from_object(__name__ + '.FlaskConfig')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True)

# Flask extension libraries
class FlaskExtensions(object):
    def __init__(self, app):
        self.cors = CORS(app)
        self.jwt = JWTManager(app)
        self.email_sender = EmailSender(app)
        self.email_verifier = EmailVerifier(app)
        self.json = FlaskJSON(app)
        self.img_manager = ImageManager(app)

flask_exts = FlaskExtensions(app)

sentry_sdk.init(
    dsn=os.getenv('SENTRY_URL'),
    integrations=[FlaskIntegration()]
)