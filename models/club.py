import mongoengine as mongo
import mongoengine_goodjson as gj

from models.relaxed_url_field import RelaxedURLField
from models.user import User

class Event(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(null=True)
    event_start = mongo.DateTimeField(required=True)
    event_end   = mongo.DateTimeField(required=True)
    description = mongo.StringField(required=True, max_length=1000)

class Resource(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(required=True)

class SocialMediaLinks(gj.EmbeddedDocument):
    contact_email = mongo.EmailField(required=True)
    website     = RelaxedURLField(null=True)
    facebook    = RelaxedURLField(null=True)
    instagram   = RelaxedURLField(null=True)
    linkedin    = RelaxedURLField(null=True)
    twitter     = RelaxedURLField(null=True)
    youtube     = RelaxedURLField(null=True)
    github      = RelaxedURLField(null=True)
    behance     = RelaxedURLField(null=True)
    medium      = RelaxedURLField(null=True)
    gcalendar   = RelaxedURLField(null=True)
    discord     = RelaxedURLField(null=True)

class Tag(gj.Document):
    id   = mongo.IntField(required=True, primary_key=True)
    name = mongo.StringField(required=True)

    meta = {'auto_create_index': False}

class Club(gj.Document):
    id    = mongo.StringField(required=True, primary_key=True)
    name  = mongo.StringField(required=True, max_length=100)
    owner = mongo.ReferenceField(User, required=True)

    tags         = mongo.ListField(mongo.ReferenceField(Tag), required=True, max_length=3)
    app_required = mongo.BooleanField(required=True)
    new_members  = mongo.BooleanField(required=True)

    logo_url   = RelaxedURLField(null=True, default=None)
    banner_url = RelaxedURLField(null=True, default=None)

    about_us     = mongo.StringField(default='', max_length=1500)
    get_involved = mongo.StringField(default='', max_length=1000)

    resources = mongo.EmbeddedDocumentListField(Resource, default=[])
    events    = mongo.EmbeddedDocumentListField(Event, default=[])

    social_media_links = mongo.EmbeddedDocumentField(SocialMediaLinks)

    meta = {'auto_create_index': False}
