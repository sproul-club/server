import mongoengine as mongo
import mongoengine_goodjson as gj

from models.user import NewBaseUser, USER_ROLES


class NewAdminUser(NewBaseUser):
    role = mongo.StringField(default='admin', choices=USER_ROLES)
    has_usable_password = mongo.BooleanField(default=True)

    super_admin = mongo.BooleanField(default=False)

    meta = {'auto_create_index': False}
