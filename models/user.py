import datetime
import mongoengine as mongo
import mongoengine_goodjson as gj

from init_app import app

class FutureUser(gj.Document):
    org_name = mongo.StringField(min_length=1)
    org_email = mongo.EmailField()

    poc_name = mongo.StringField(min_length=1)
    poc_email = mongo.EmailField()

class User(gj.Document):
    email    = mongo.EmailField(primary_key=True)
    password = mongo.StringField(max_length=256)

    registered_on = mongo.DateTimeField(default=datetime.datetime.now)
    confirmed     = mongo.BooleanField(default=False)
    confirmed_on  = mongo.DateTimeField(default=None)

class PreVerifiedEmail(gj.Document):
    email = mongo.EmailField(unique=True)

class AccessJTI(gj.Document):
    owner = mongo.ReferenceField(User, required=True)
    token_id = mongo.StringField(required=True, min_length=1)
    expired = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.now)

    meta = {
        'collection': 'access-jti',
        'indexes': [
            {
                'fields': ['expiry_time'],
                'expireAfterSeconds': int(app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
            }
        ]
    }

class RefreshJTI(gj.Document):
    owner = mongo.ReferenceField(User, required=True)
    token_id = mongo.StringField(required=True, min_length=1)
    expired = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.now)

    meta = {
        'collection': 'refresh-jti',
        'indexes': [
            {
                'fields': ['expiry_time'],
                'expireAfterSeconds': int(app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds())
            }
        ]
    }
