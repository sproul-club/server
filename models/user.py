import datetime
import mongoengine as mongo
import mongoengine_goodjson as gj

from models.metadata import Major, Minor, Tag
USER_ROLES = ['student', 'officer', 'admin']


class NewBaseUser(gj.Document):
    email    = mongo.EmailField(required=True)
    password = mongo.StringField(required=True)

    registered_on = mongo.DateTimeField(default=datetime.datetime.utcnow)
    confirmed     = mongo.BooleanField(default=False)
    confirmed_on  = mongo.DateTimeField(default=None)

    has_usable_password = mongo.BooleanField(required=True)

    role = mongo.StringField(required=True, choices=USER_ROLES)

    meta = {'auto_create_index': False, 'allow_inheritance': True}


class PreVerifiedEmail(gj.Document):
    email = mongo.EmailField(unique=True)

    meta = {'auto_create_index': False}


class AccessJTI(gj.Document):
    owner = mongo.ReferenceField(NewBaseUser, required=True)
    token_id = mongo.StringField(required=True)
    expired = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'access_jti', 'auto_create_index': False}


class RefreshJTI(gj.Document):
    owner = mongo.ReferenceField(NewBaseUser, required=True)
    token_id = mongo.StringField(required=True)
    expired = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.now)

    meta = {'collection': 'refresh_jti', 'auto_create_index': False}


class ConfirmEmailToken(gj.Document):
    token = mongo.StringField(required=True)
    used = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.utcnow)

    meta = {'auto_create_index': False}


class ResetPasswordToken(gj.Document):
    token = mongo.StringField(required=True)
    used = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.utcnow)

    meta = {'auto_create_index': False}
