from itsdangerous import URLSafeTimedSerializer
from flask import Flask
from flask_mail import Mail
from flask_json import JsonError

import smtplib

from models import ConfirmEmailToken, ResetPasswordToken

TokenTypes = {
    'confirm-email': ConfirmEmailToken,
    'reset-password': ResetPasswordToken
}

"""
This class is for handling the verification of temporary email links via email tokens, mainly
for email confirmation and password resetting. Using a specified salt and an equivalent MongoDB
class to represent the tokens, it'll handle when tokens are either valid, expired or used.
"""
class EmailVerifier:
    # A convenience constructor for initializing the email verifier
    def __init__(self, app=None):
        if isinstance(app, Flask):
            self.init_app(app)

    # Initialize the email verifier by pulling any required settings from the Flask config
    def init_app(self, app):
        if isinstance(app, Flask):
            self.serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

            self.token_salts = {
                'confirm-email': app.config['CONFIRM_EMAIL_SALT'],
                'reset-password': app.config['RESET_PASSWORD_SALT'],
            }

            self.expiry_durations = {
                'confirm-email': int(app.config['CONFIRM_EMAIL_EXPIRY'].total_seconds()),
                'reset-password': int(app.config['CONFIRM_EMAIL_EXPIRY'].total_seconds())
            }

    # This will generate a temporary token based on the type and the given email and save it to the database.
    def generate_token(self, email, token_type):
        if token_type not in self.token_salts:
            raise JsonError(status='error', reason='Invalid token type provided', status_=500)

        # Generate a token given one of the allowed token salts
        token = self.serializer.dumps(email, salt=self.token_salts[token_type])
        
        # Save the token to MongoDB to allow blacklisting tokens after first use
        MongoEmailToken = TokenTypes[token_type]
        MongoEmailToken(token=token).save()

        return token

    # This will generate a temporary token based on the type and the given email and save it to the database.
    def confirm_token(self, token, token_type):
        if token_type not in self.token_salts:
            raise JsonError(status='error', reason='Invalid token type provided', status_=500)

        # First check if the token exists or is used already
        MongoEmailToken = TokenTypes[token_type]
        email_token = MongoEmailToken.objects(token=token).first()
        if email_token is None or email_token.used:
            return None

        # Then try to decrypt the token and fetch the email originally encoded into the token, given a maximum age.
        try:
            email = self.serializer.loads(token, salt=self.token_salts[token_type], max_age=self.expiry_durations[token_type])
        except:
            return None

        email_token.used = True
        email_token.save()

        return email


"""
This class is for sending emails in a convenient manner, using the Mail SMTP
server settings as specified in the Flask config object.
"""
class EmailSender:
    # A convenience constructor for initializing the email sender
    def __init__(self, app=None):
        if isinstance(app, Flask):
            self.init_app(app)

    # Initialize the email sender by pulling any required settings from the Flask config
    def init_app(self, app):
        if isinstance(app, Flask):
            self.mail = Mail()
            self.mail.init_app(app)
            self.sender = app.config['MAIL_DEFAULT_SENDER']

    # A simple method to send an HTML email to a list of recipients with a subject
    def send(self, recipients, subject, body):
        try:
            self.mail.send_message(
                subject=subject,
                recipients=recipients,
                html=body,
                sender=self.sender
            )
        except smtplib.SMTPAuthenticationError as ex:
            raise JsonError(status='error', reason='The GMail login failed. Please see the logs', status_=500)
