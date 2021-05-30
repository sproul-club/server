import datetime

import mongoengine as mongo
import mongoengine_goodjson as gj

from models.relaxed_url_field import RelaxedURLField

from models.user import NewBaseUser, USER_ROLES
from models.metadata import Tag, NumUsersTag

from utils import pst_right_now

# TODO: Decouple embedded 'NewClub' from 'NewOfficerUser'
# TODO: Decouple embedded 'Event' from 'NewOfficerUser'
# TODO: Decouple embedded 'RecruitingEvent' from 'NewOfficerUser'

GALLERY_MEDIA_TYPES = [
    'picture',
    #'video',
]


class Event(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(null=True, default=None) # TODO: remove "link" in favor of "links", make mongo migration script for existing events with only one "link"
    links = mongo.ListField(RelaxedURLField, default=[], max_length=10)
    location = mongo.StringField(required=True, default='', max_length=1000)
    event_start = mongo.DateTimeField(required=True)
    event_end   = mongo.DateTimeField(required=True)
    description = mongo.StringField(required=True, max_length=1000)
    tags = mongo.ListField(mongo.ReferenceField(Tag), max_length=100)
    meta = {'auto_create_index': False, 'allow_inheritance': True}


class RecruitingEvent(Event):
    description = mongo.StringField(required=True, max_length=200)
    virtual_link = RelaxedURLField(null=True, default=None)
    link = RelaxedURLField(required=False)
    invite_only = mongo.BooleanField(required=True)

    meta = {'auto_create_index': False}


class Resource(gj.EmbeddedDocument):
    id   = mongo.StringField(required=True, max_length=100)
    name = mongo.StringField(required=True, max_length=100)
    link = RelaxedURLField(required=True)

    meta = {'auto_create_index': False}


class SocialMediaLinks(gj.EmbeddedDocument):
    contact_email = mongo.EmailField(required=True)
    website     = RelaxedURLField(null=True, default=None)
    facebook    = RelaxedURLField(null=True, default=None)
    instagram   = RelaxedURLField(null=True, default=None)
    linkedin    = RelaxedURLField(null=True, default=None)
    twitter     = RelaxedURLField(null=True, default=None)
    youtube     = RelaxedURLField(null=True, default=None)
    github      = RelaxedURLField(null=True, default=None)
    behance     = RelaxedURLField(null=True, default=None)
    medium      = RelaxedURLField(null=True, default=None)
    gcalendar   = RelaxedURLField(null=True, default=None)
    discord     = RelaxedURLField(null=True, default=None)

    meta = {'auto_create_index': False}


class GalleryMedia(gj.EmbeddedDocument):
    id      = mongo.StringField(required=True, max_length=100)
    type    = mongo.StringField(required=True, choices=GALLERY_MEDIA_TYPES)
    url     = RelaxedURLField(null=True, default=None)
    caption = mongo.StringField(required=True, max_length=50)
    
    meta = {'auto_create_index': False, 'allow_inheritance': True}

class GalleryPic(GalleryMedia):
    type    = mongo.StringField(default='picture', choices=GALLERY_MEDIA_TYPES)
    
    meta = {'auto_create_index': False}


class GalleryVideo(GalleryMedia):
    type    = mongo.StringField(default='video', choices=GALLERY_MEDIA_TYPES)
    
    meta = {'auto_create_index': False}


class NewClub(gj.EmbeddedDocument):
    name  = mongo.StringField(required=True, max_length=100)
    link_name = mongo.StringField(required=True)

    tags         = mongo.ListField(mongo.ReferenceField(Tag), required=True, max_length=3)
    app_required = mongo.BooleanField(required=True)
    new_members  = mongo.BooleanField(required=True)
    num_users    = mongo.ReferenceField(NumUsersTag, required=True)

    logo_url   = RelaxedURLField(null=True, default=None)
    banner_url = RelaxedURLField(null=True, default=None)

    gallery_media = mongo.EmbeddedDocumentListField(GalleryMedia, default=[], max_length=5)

    about_us     = mongo.StringField(default='', max_length=1500)
    get_involved = mongo.StringField(default='', max_length=1000)

    apply_link = RelaxedURLField(null=True, default=None)
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
    reactivated_last = mongo.DateTimeField(null=True, default=pst_right_now)

    meta = {'auto_create_index': False}


class NewOfficerUser(NewBaseUser):
    role = mongo.StringField(default='officer', choices=USER_ROLES)
    has_usable_password = mongo.BooleanField(default=True)

    club = mongo.EmbeddedDocumentField(NewClub, required=True)

    meta = {'auto_create_index': False}
