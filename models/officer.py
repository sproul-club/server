import datetime

import mongoengine as mongo
import mongoengine_goodjson as gj

from models.relaxed_url_field import RelaxedURLField

from models.user import NewBaseUser, USER_ROLES
from models.metadata import Tag, NumUsersTag

# TODO: Decouple embedded 'NewClub' from 'NewOfficerUser'
# TODO: Decouple embedded 'Event' from 'NewOfficerUser'
# TODO: Decouple embedded 'RecruitingEvent' from 'NewOfficerUser'


class Event(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(null=True, default='')
    event_start = mongo.DateTimeField(required=True)
    event_end   = mongo.DateTimeField(required=True)
    description = mongo.StringField(required=True, max_length=1000)

    meta = {'auto_create_index': False, 'allow_inheritance': True}


class RecruitingEvent(Event):
    description = mongo.StringField(required=True, max_length=200)
    virtual_link = RelaxedURLField(null=True, default='')
    invite_only = mongo.BooleanField(required=True)

    meta = {'auto_create_index': False}


class Resource(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(required=True)

    meta = {'auto_create_index': False}


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

    meta = {'auto_create_index': False}


class CaptionedPic(gj.EmbeddedDocument):
    id      = mongo.StringField(required=True, max_length=100)
    url = RelaxedURLField(null=True, default='')
    caption = mongo.StringField(required=True, max_length=50)

    meta = {'auto_create_index': False}


class NewClub(gj.EmbeddedDocument):
    name  = mongo.StringField(required=True, max_length=100)
    link_name = mongo.StringField(required=True)

    tags         = mongo.ListField(mongo.ReferenceField(Tag), required=True, max_length=3)
    app_required = mongo.BooleanField(required=True)
    new_members  = mongo.BooleanField(required=True)
    num_users    = mongo.ReferenceField(NumUsersTag, required=True)

    logo_url   = RelaxedURLField(null=True, default='')
    banner_url = RelaxedURLField(null=True, default='')

    gallery_pics = mongo.EmbeddedDocumentListField(CaptionedPic, default=[], max_length=5)

    about_us     = mongo.StringField(default='', max_length=1500)
    get_involved = mongo.StringField(default='', max_length=1000)

    apply_link = RelaxedURLField(null=True, default='')
    apply_deadline_start = mongo.DateTimeField(null=True)
    apply_deadline_end = mongo.DateTimeField(null=True)

    recruiting_start = mongo.DateTimeField(null=True)
    recruiting_end = mongo.DateTimeField(null=True)

    resources = mongo.EmbeddedDocumentListField(Resource, default=[])
    events    = mongo.EmbeddedDocumentListField(Event, default=[])
    recruiting_events = mongo.EmbeddedDocumentListField(RecruitingEvent, default=[])

    social_media_links = mongo.EmbeddedDocumentField(SocialMediaLinks)

    last_updated = mongo.DateTimeField(null=True)

    reactivated = mongo.BooleanField(default=True)
    reactivated_last = mongo.DateTimeField(null=True, default=datetime.datetime.now)

    meta = {'auto_create_index': False}


class NewOfficerUser(NewBaseUser):
    role = mongo.StringField(default='officer', choices=USER_ROLES)
    has_usable_password = mongo.BooleanField(default=True)

    club = mongo.EmbeddedDocumentField(NewClub, required=True)

    meta = {'auto_create_index': False}
