import mongoengine as mongo
import mongoengine_goodjson as gj

from models.user import NewBaseUser, USER_ROLES

class NewAdminUser(NewBaseUser):
    role = mongo.StringField(default='admin', choices=USER_ROLES)
    super_admin = mongo.BooleanField(default=False)

    meta = {'auto_create_index': False}
