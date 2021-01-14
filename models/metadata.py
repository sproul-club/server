import mongoengine as mongo
import mongoengine_goodjson as gj

class Tag(gj.Document):
    id   = mongo.IntField(required=True, primary_key=True)
    name = mongo.StringField(required=True)

    meta = {'auto_create_index': False}

class NumUsersTag(gj.Document):
    id    = mongo.IntField(required=True, primary_key=True)
    value = mongo.StringField(required=True)

    meta = {'auto_create_index': False}

class Major(gj.Document):
    id    = mongo.IntField(required=True, primary_key=True)
    major = mongo.StringField(required=True)

    meta = {'auto_create_index': False}

class Minor(gj.Document):
    id    = mongo.IntField(required=True, primary_key=True)
    minor = mongo.StringField(required=True)

    meta = {'auto_create_index': False}

class StudentYear(gj.Document):
    id    = mongo.IntField(required=True, primary_key=True)
    year  = mongo.StringField(required=True)

    meta = {'auto_create_index': False}
