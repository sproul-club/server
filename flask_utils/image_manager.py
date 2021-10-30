import os

from flask import Flask
from werkzeug.utils import secure_filename
from flask_json import JsonError

from PIL import Image, UnidentifiedImageError
import boto3

from utils import get_random_bits

ALLOWED_IMG_TYPES = ['logo', 'banner', 'gallery']


def allowed_file(filename, allowed_exts):
    """
    Given a filename, check if its extension is allowed from the list of allowed extensions.
    """

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts


class ImageManager:
    """
    This class manages photo uploading for club logos and banners, although it can be expanded to support
    any category of photo uploads via 'ALLOWED_IMG_TYPES'. When a photo upload is successfully completed,
    an S3 link to that photo will be returned and can be stored and fetched for later use.

    NOTE/FIXME: Keep in mind that if a club decides to upload a new photo, the old photo will not be deleted.
    """

    def __init__(self, app=None):
        """
        A convenience constructor for initializing the image manager.
        """

        if isinstance(app, Flask):
            self.init_app(app)


    def init_app(self, app):
        """
        Initialize the image manager by pulling any required settings from the Flask config and
        initializing the S3 client.
        """

        if isinstance(app, Flask):
            self.upload_folder = app.config['UPLOAD_FOLDER']
            self.allowed_img_exts = app.config['ALLOWED_IMG_EXTENSIONS']

            self.bucket = app.config['S3_BUCKET']
            self.region = app.config['S3_REGION']
            self.public_url = f'https://{self.bucket}.s3-{self.region}.amazonaws.com'

            # Initialize the S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=app.config['S3_ACCESS_KEY'],
                aws_secret_access_key=app.config['S3_SECRET_KEY']
            )


    def get_s3_url(self, img_type, club_id):
        """
        Fetch the S3 public URL given the image type and club ID (a.k.a club link name).
        """

        return f'{self.public_url}/{img_type}/{club_id}-{img_type}.png'


    def upload_img_asset_s3(self, club_id, flask_file, img_type, req_aspect_ratio=None, error_rate=0.05, file_size_limit=None):
        """
        Given the club ID and the image, validate the image, upload the image to AWS S3 and return the S3 URL.
        """

        # Check if the image type is valid via 'ALLOWED_IMG_TYPES'
        if img_type not in ALLOWED_IMG_TYPES:
            raise JsonError(status='error', reason='Invalid image type provided when trying to upload club image asset.', status_=500)

        # Check if the file extension is valid
        if flask_file is not None and allowed_file(secure_filename(flask_file.filename), self.allowed_img_exts):
            # Check if the file is indeed an image
            try:
                pil_image = Image.open(flask_file)
            except UnidentifiedImageError as ex:
                raise JsonError(status='error', reason=f'The provided {img_type} is not an image.', data={'image_type': img_type})

            # Check if the file size is not greater than the specified limit, if applicable
            if file_size_limit is not None:
                flask_blob = flask_file.read()
                file_size = len(flask_blob)
                if file_size > file_size_limit:
                    raise JsonError(status='error', reason=f'The provided {img_type} is too large.', data={'image_type': img_type})

            # Check if the aspect ratio is within the % error rate (as a decimal), if specified
            # For example, if the requested aspect ratio is 1.0 and the error rate is 0.05, then
            # the allowed aspect ratios are 0.95 and 1.05.
            if req_aspect_ratio is not None:
                img_aspect_ratio = pil_image.width / pil_image.height
                if abs(img_aspect_ratio - req_aspect_ratio) > error_rate:
                    raise JsonError(status='error', reason=f'The provided {img_type}\'s aspect ratio deviates too far from the required ratio.', data={'image_type': img_type})
            
            # Generate the image file name and save it locally for uploading to S3
            random_bits = get_random_bits(16)
            img_filename = f'{club_id}-{img_type}-{random_bits}.png'
            img_file_location = os.path.join(self.upload_folder, img_filename)
            pil_image.save(img_file_location, 'PNG')

            # Upload said image to S3
            s3_file_location = f'{img_type}/{img_filename}'
            self.s3_client.upload_file(img_file_location, self.bucket, s3_file_location, ExtraArgs={'ACL':'public-read'})

            # Remove the local image
            if os.path.exists(img_file_location):
                os.remove(img_file_location)

            # Return the S3 image URL
            final_pic_url = f'{self.public_url}/{img_type}/{club_id}-{img_type}-{random_bits}.png'
            return final_pic_url, random_bits
