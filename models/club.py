import mongoengine as mongo
import mongoengine_goodjson as gj

from models.relaxed_url_field import RelaxedURLField

class Event(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(null=True)
    event_start = mongo.DateTimeField(required=True)
    event_end   = mongo.DateTimeField(required=True)
    description = mongo.StringField(required=True, max_length=1000)

    meta = {'allow_inheritance': True}

class RecruitingEvent(Event):
    description = mongo.StringField(required=True, max_length=200)
    virtual_link = RelaxedURLField(null=True)

class Resource(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(required=True)

class SocialMediaLinks(gj.EmbeddedDocument):
    contact_email = mongo.EmailField(required=True)
    website     = RelaxedURLField(null=True, default='')
    facebook    = RelaxedURLField(null=True, default='')
    instagram   = RelaxedURLField(null=True, default='')
    linkedin    = RelaxedURLField(null=True, default='')
    twitter     = RelaxedURLField(null=True, default='')
    youtube     = RelaxedURLField(null=True, default='')
    github      = RelaxedURLField(null=True, default='')
    behance     = RelaxedURLField(null=True, default='')
    medium      = RelaxedURLField(null=True, default='')
    gcalendar   = RelaxedURLField(null=True, default='')
    discord     = RelaxedURLField(null=True, default='')

class Tag(gj.Document):
    id   = mongo.IntField(required=True, primary_key=True)
    name = mongo.StringField(required=True)

    meta = {'auto_create_index': False}

class NumUsersTag(gj.Document):
    id   = mongo.IntField(required=True, primary_key=True)
    value = mongo.StringField(required=True)

    meta = {'auto_create_index': False}

class NewClub(gj.EmbeddedDocument):
    name  = mongo.StringField(required=True, max_length=100)
    link_name = mongo.StringField(required=True)

    tags         = mongo.ListField(mongo.ReferenceField(Tag, required=True), required=True, max_length=3)
    app_required = mongo.BooleanField(required=True)
    new_members  = mongo.BooleanField(required=True)
    num_users    = mongo.ReferenceField(NumUsersTag, required=True)

    logo_url   = RelaxedURLField(null=True, default='')
    banner_url = RelaxedURLField(null=True, default='')

    about_us     = mongo.StringField(default='', max_length=1500)
    get_involved = mongo.StringField(default='', max_length=1000)

    apply_link = RelaxedURLField(null=True, default='')
    apply_deadline = mongo.DateTimeField(null=True)

    resources = mongo.EmbeddedDocumentListField(Resource, default=[])
    events    = mongo.EmbeddedDocumentListField(Event, default=[])
    recruiting_events = mongo.EmbeddedDocumentListField(RecruitingEvent, default=[])

    social_media_links = mongo.EmbeddedDocumentField(SocialMediaLinks)

    meta = {'auto_create_index': False}
