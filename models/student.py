import datetime

import mongoengine as mongo
import mongoengine_goodjson as gj

from models.user import NewBaseUser, USER_ROLES
from models.metadata import Major, Minor, Tag

class StudentKanbanBoard(gj.EmbeddedDocument):
    interested_clubs  = mongo.ListField(mongo.StringField(), default=[])
    applied_clubs     = mongo.ListField(mongo.StringField(), default=[])
    interviewed_clubs = mongo.ListField(mongo.StringField(), default=[])

    meta = {'auto_create_index': False}


class NewStudentUser(NewBaseUser):
    role = mongo.StringField(default='student', choices=USER_ROLES)
    has_usable_password = mongo.BooleanField(default=False)

    full_name = mongo.StringField(max_length=100)

    majors = mongo.ListField(mongo.ReferenceField(Major), max_length=3)
    minors = mongo.ListField(mongo.ReferenceField(Minor), max_length=3)
    interests = mongo.ListField(mongo.ReferenceField(Tag))

    favorited_clubs = mongo.ListField(mongo.StringField(), default=[])
    bookmarked_clubs = mongo.ListField(mongo.StringField(), default=[])
    visited_clubs = mongo.ListField(mongo.StringField(), default=[])

    club_board = mongo.EmbeddedDocumentField(StudentKanbanBoard)

    meta = {'auto_create_index': False}
