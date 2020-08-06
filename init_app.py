from dotenv import load_dotenv
load_dotenv()

import os
import datetime

from flask import Flask
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_json import FlaskJSON
from flask_cors import CORS

from flask_utils import EmailVerifier, EmailSender, ImageManager

app = Flask('app', template_folder='templates')

# Configuration object for Flask app
class FlaskConfig(object):
    # Flask settings
    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY')
    FLASK_SECRET = os.getenv('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.getenv('PASSWORD_SALT')
    JSON_ADD_STATUS = False
    CORS_HEADERS = '*' # TODO: [Security] - Tweak headers "specifically"
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Max upload size if 16 MB

    # JWT settings
    JWT_SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=15)

    # Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = f'"sproul.club" <{os.getenv("MAIL_USERNAME")}>'

    # AWS S3 settings
    S3_REGION     = os.getenv('S3_REGION_TEST')
    S3_BUCKET     = os.getenv('S3_BUCKET_TEST')
    S3_ACCESS_KEY = os.getenv('S3_KEY_TEST')
    S3_SECRET_KEY = os.getenv('S3_SECRET_TEST')

app.config.from_object(__name__ + '.FlaskConfig')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True)

# Flask extension libraries
class FlaskExtensions(object):
    def __init__(self, app):
        self.cors = CORS(app)
        self.jwt = JWTManager(app)
        self.mail = Mail(app)
        self.email_verifier = EmailVerifier(app)
        self.email_sender = EmailSender(app, self.mail)
        self.json = FlaskJSON(app)
        self.img_manager = ImageManager(app)

flask_exts = FlaskExtensions(app)
