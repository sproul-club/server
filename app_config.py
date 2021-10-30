"""
This file houses the total backend application configuration. It's setup such that you can load multiple
configurations based on the environment files' names. For example, having a file called '.env.dev' will
load the development config and a file called '.env.prod' will load the production config.

You may add more configuration types as you see fit. Scroll down to see examples of how each configuration
type is implemented.
"""

import datetime
import os

"""
README: If you want to add a new configuration environment, add an entry to 'ALLOWED_MODES'
"""
ALLOWED_MODES = ['local', 'dev', 'staging', 'prod']

MODE = os.getenv('MODE')
if MODE not in ALLOWED_MODES:
    raise Exception(f'Invalid operating mode: "{MODE}"')

ENV_FILE = f'.env.{MODE}'

from dotenv import load_dotenv
load_dotenv(dotenv_path=ENV_FILE)

class BaseConfig(object):
    """
    Base configuration object to load the application.

    NOTE: You should only be changing this if you're adding new variables that affects *all* environments.
    """

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    FLASK_SECRET = os.getenv('SECRET_KEY')
    JSON_ADD_STATUS = False
    CORS_HEADERS = '*' # TODO: [Security] - Tweak headers "specifically"
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Max upload size if 16 MB

    # Email token settings
    CONFIRM_EMAIL_SALT = os.getenv('CONFIRM_EMAIL_SALT')
    RESET_PASSWORD_SALT = os.getenv('RESET_PASSWORD_SALT')
    CONFIRM_EMAIL_EXPIRY = datetime.timedelta(weeks=1)
    RESET_PASSWORD_EXPIRY = datetime.timedelta(minutes=30)

    # JWT settings
    JWT_SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=15)

    # Mail SMTP server settings
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL') == 'true'
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = f'"sproul.club" <{os.getenv("MAIL_SENDER")}>'

    # AWS S3 settings
    S3_REGION     = os.getenv('S3_REGION')
    S3_BUCKET     = os.getenv('S3_BUCKET')
    S3_ACCESS_KEY = os.getenv('S3_KEY')
    S3_SECRET_KEY = os.getenv('S3_SECRET')

    # Google OAuth key and secret
    GOOGLE_OAUTH_CLIENT_ID     = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

"""
README: If you want to add a new configuration environment, add a new class like the examples below.
"""

class LocalConfig(BaseConfig):
    DEBUG = True
    MODE = 'local'
    DATABASE_NAME = 'develop-db'
    FRONTEND_BASE_URL = 'http://localhost:3000'
    BACKEND_BASE_URL = 'http://localhost:5000'

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    MODE = 'dev'
    DATABASE_NAME = 'develop-db'
    FRONTEND_BASE_URL = 'http://localhost:3000'
    BACKEND_BASE_URL = 'https://sc-backend-dev.herokuapp.com'

class StagingConfig(BaseConfig):
    DEBUG = False
    MODE = 'staging'
    DATABASE_NAME = 'staging-db'
    FRONTEND_BASE_URL = 'http://localhost:3000'
    BACKEND_BASE_URL = 'https://sc-backend-staging.herokuapp.com'

class ProductionConfig(BaseConfig):
    DEBUG = False
    MODE = 'prod'
    DATABASE_NAME = 'production-db'
    FRONTEND_BASE_URL = 'https://www.sproul.club'
    BACKEND_BASE_URL = 'https://sc-backend-prod.herokuapp.com'

# Set the respective configuration class to load based on 'MODE'

"""
README: If you want to add a new configuration environment, add a new if statement clause to ensure that
CurrentConfig will have the right configuration variables loaded.
"""
if MODE == 'local':
    CurrentConfig = LocalConfig
elif MODE == 'dev':
    CurrentConfig = DevelopmentConfig
elif MODE == 'staging':
    CurrentConfig = StagingConfig
elif MODE == 'prod':
    CurrentConfig = ProductionConfig
else:
    raise Exception(f'Invalid operating mode: "{MODE}"')
