import os

from flask import Flask
from werkzeug.utils import secure_filename
from flask_json import JsonError

from PIL import Image, UnidentifiedImageError
import boto3

def allowed_file(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

class ImageManager:
    def __init__(self, app=None):
        if isinstance(app, Flask):
            self.init_app(app)

    def init_app(self, app):
        if isinstance(app, Flask):
            self.upload_folder = app.config['UPLOAD_FOLDER']
            self.allowed_img_exts = app.config['ALLOWED_IMG_EXTENSIONS']

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=app.config['S3_ACCESS_KEY'],
                aws_secret_access_key=app.config['S3_SECRET_KEY']
            )
            self.bucket = app.config['S3_BUCKET']
            self.region = app.config['S3_REGION']
            self.public_url = f'https://{self.bucket}.s3-{self.region}.amazonaws.com'

    def get_s3_url(self, img_type, club_id):
        return f'{self.public_url}/{img_type}/{club_id}-{img_type}.png'
        
    def upload_img_asset_s3(self, club_id, flask_file, img_type, req_aspect_ratio, error_rate=0.05):
        if img_type not in ['logo', 'banner']:
            raise JsonError(status='error', reason='Invalid image type provided when trying to upload club image asset.', status_=500)

        if flask_file is not None and allowed_file(secure_filename(flask_file.filename), self.allowed_img_exts):
            try:
                pil_image = Image.open(flask_file)
            except UnidentifiedImageError as ex:
                raise JsonError(status='error', reason=f'The provided {img_type} is not an image.')

            img_aspect_ratio = pil_image.width / pil_image.height
            if abs(img_aspect_ratio - req_aspect_ratio) > error_rate:
                raise JsonError(status='error', reason=f'The provided {img_type} has a aspect ratio that deviates too far from the required ratio.')
            
            img_filename = f'{club_id}-{img_type}.png'
            img_file_location = os.path.join(self.upload_folder, img_filename)
            pil_image.save(img_file_location, 'PNG')

            s3_file_location = f'{img_type}/{img_filename}'

            try:
                self.s3_client.upload_file(img_file_location, self.bucket, s3_file_location, ExtraArgs={'ACL':'public-read'})

                if os.path.exists(img_file_location):
                    os.remove(img_file_location)
                
                return self.get_s3_url(img_type, club_id)
            except Exception as ex:
                raise JsonError(status='error', reason=f'Unable to upload {img_type} image: ' + str(ex))
