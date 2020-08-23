from dotenv import load_dotenv
load_dotenv()

import os
import json

from flask import request, g
from flask_json import as_json, JsonError, json_response
from flask_utils import validate_json

from init_app import app, flask_exts
from blueprints import user_blueprint, catalog_blueprint, admin_blueprint

import mongoengine as mongo
from models import FutureUser
mongo.connect(host=os.getenv('MONGO_URI'))

from oauth2client.service_account import ServiceAccountCredentials
import gspread

@flask_exts.json.invalid_json_error
def handler(e):
    raise JsonError(status='error', reason='Expected JSON in body')

# Hotfix for full CORS support
@app.before_request
def before_request_func():
    if not request.is_json:
        if request.method == 'OPTIONS':
            return 'OK'

@app.errorhandler(mongo.errors.ValidationError)
def handle_mongo_validation_error(ex):
    return {
        'status': 'error',
        'reason': 'A validation error occurred within MongoDB. Please contact the backend dev about this!',
        'data': [{'field': v_error[0], 'error': v_error[1]} for v_error in ex.to_dict().items()]
    }, 500


app.register_blueprint(user_blueprint)
app.register_blueprint(catalog_blueprint)
app.register_blueprint(admin_blueprint)

SPREADSHEET_ID = os.getenv('FUTURE_SIGN_UP_SHEET_ID')

json_creds = json.loads(os.getenv('GOOGLE_SHEETS_CREDS_JSON'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds, [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
])
gc = gspread.authorize(creds)

# gc = gspread.service_account(filename='credentials/sproul-club-gservice-account.json')
future_wks = gc.open_by_key(SPREADSHEET_ID).sheet1

@as_json
@app.route('/api/future-sign-up', methods=['POST'])
@validate_json(schema={
    'org-name': {'type': 'string', 'empty': False},
    'org-email': {'type': 'string', 'empty': False},
    'poc-name': {'type': 'string', 'empty': False},
    'poc-email': {'type': 'string', 'empty': False}
}, require_all=True)
def sign_up_future():
    json = g.clean_json

    # First check if the club email has been registered already
    org_email = json['org-email']
    future_user = FutureUser.objects(org_email=org_email).first()
    if future_user is not None:
        raise JsonError(status='error', reason='The organization email has already been registered!')

    # Save the new "future user"
    try:
        FutureUser(
            org_name=json['org-name'],
            org_email=org_email,
            poc_name=json['poc-name'],
            poc_email=json['poc-email'],
        ).save()
    except mongo.errors.ValidationError as ex:
        raise JsonError(status='error', reason='Both the organization email and POC email must be valid!')

    # Update the spreadsheet with the full list of new clubs
    club_infos = []
    for user in FutureUser.objects:
        club_infos += [[user['org_name'], user['org_email'], user['poc_name'], user['poc_email']]]

    future_wks.clear()
    future_wks.update('A1', [['Org Name', 'Org Email', 'POC Name', 'POC Email']])
    future_wks.format('A1:D1', {'textFormat': {'bold': True}})

    future_wks.update('A2', club_infos)

    return {'status': 'ok'}


if __name__ == '__main__':
    app.run(debug=True)
