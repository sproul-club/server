import mongoengine as mongo
import mongoengine_goodjson as gj

from models.user import NewBaseUser, USER_ROLES
from models.metadata import Major, Minor, Tag

class StudentKanbanBoard(gj.EmbeddedDocument):
    interested_clubs  = mongo.ListField(mongo.StringField(), required=True)
    applied_clubs     = mongo.ListField(mongo.StringField(), required=True)
    interviewed_clubs = mongo.ListField(mongo.StringField(), required=True)

    meta = {'auto_create_index': False}


class NewStudentUser(NewBaseUser):
    role = mongo.StringField(default='student', choices=USER_ROLES)
    has_usable_password = mongo.BooleanField(default=False)

    majors = mongo.ListField(mongo.ReferenceField(Major), required=True, max_length=3)
    minors = mongo.ListField(mongo.ReferenceField(Minor), required=True, max_length=3)
    interests = mongo.ListField(mongo.ReferenceField(Tag), required=True)

    favorited_clubs = mongo.ListField(mongo.StringField(), default=[])
    visited_clubs = mongo.ListField(mongo.StringField(), default=[])

    club_board = mongo.EmbeddedDocumentField(StudentKanbanBoard)

    meta = {'auto_create_index': False}
