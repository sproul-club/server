from dotenv import load_dotenv
load_dotenv()

from flask import request
from flask_json import JsonError

from init_app import app, flask_exts
from blueprints import user_blueprint, catalog_blueprint, admin_blueprint

@flask_exts.json.invalid_json_error
def handler(e):
    raise JsonError(status='error', reason='Expected JSON in body')

# Hotfix for full CORS support
@app.before_request
def before_request_func():
    if not request.is_json:
        if request.method == 'OPTIONS':
            return 'OK'

@app.errorhandler(flask_exts.mongo.errors.ValidationError)
def handle_mongo_validation_error(ex):
    return {
        'status': 'error',
        'reason': 'A validation error occurred within MongoDB. Please contact the backend dev about this!',
        'data': [{'field': v_error[0], 'error': v_error[1]} for v_error in ex.to_dict().items()]
    }, 500

app.register_blueprint(user_blueprint)
app.register_blueprint(catalog_blueprint)
app.register_blueprint(admin_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
