__all__ = [
    'user_blueprint', 'catalog_blueprint', 'admin_blueprint',
    'monitor_blueprint', 'student_blueprint'
]

from blueprints.user_blueprint import user_blueprint
from blueprints.catalog_blueprint import catalog_blueprint
from blueprints.admin_blueprint import admin_blueprint
from blueprints.monitor_blueprint import monitor_blueprint
from blueprints.student_blueprint import student_blueprint
