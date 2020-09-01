import datetime
import mongoengine as mongo
import mongoengine_goodjson as gj

class User(gj.Document):
    email    = mongo.EmailField(primary_key=True)
    password = mongo.StringField(required=True)

    registered_on = mongo.DateTimeField(default=datetime.datetime.utcnow)
    confirmed     = mongo.BooleanField(default=False)
    confirmed_on  = mongo.DateTimeField(default=None)

    meta = {'auto_create_index': False}

class PreVerifiedEmail(gj.Document):
    email = mongo.EmailField(unique=True)

    meta = {'auto_create_index': False}

class AccessJTI(gj.Document):
    owner = mongo.ReferenceField(User, required=True)
    token_id = mongo.StringField(required=True)
    expired = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.utcnow)

    meta = {'auto_create_index': False}

class RefreshJTI(gj.Document):
    owner = mongo.ReferenceField(User, required=True)
    token_id = mongo.StringField(required=True)
    expired = mongo.BooleanField(default=False)
    expiry_time = mongo.DateTimeField(default=datetime.datetime.now)

    meta = {'auto_create_index': False}

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
