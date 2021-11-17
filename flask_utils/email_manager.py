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


class EmailVerifier:
    """
    This class is for handling the verification of temporary email links via email tokens, mainly
    for email confirmations and password resetting. Using a specified salt and an equivalent MongoDB
    class to represent the tokens, it'll handle when tokens are either valid, expired or used.

    Example for email confirmation:

    app = Flask(__name__)

    email_verifier = EmailVerifier(app)

    ...

    # NOTE: For password resets, switch from 'confirm-email' to 'reset-password'
    email_token = email_verifier.generate_token('test@gmail.com', 'confirm-email')

    ...

    possible_email = email_verifier.confirm_token(email_token)
    if possible_email is not None:
        print('Email is verified!')
    else:
        print('Email is NOT verified!')

    ...

    email_verifier.revoke_token(email_token)
    another_possible_email = email_verifier.confirm_token(email_token)

    print(another_possible_email) # will print None
    """

    def __init__(self, app=None):
        """
        A convenience constructor for initializing the email verifier.
        """

        if isinstance(app, Flask):
            self.init_app(app)


    def init_app(self, app):
        """
        Initialize the email verifier by pulling any required settings from the Flask config.
        """

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


    def generate_token(self, email, token_type):
        """
        This will generate a temporary token based on the type and the given email and save it to the database.
        """

        if token_type not in self.token_salts:
            raise JsonError(status='error', reason='Invalid token type provided', status_=500)

        # Generate a token given one of the allowed token salts
        token = self.serializer.dumps(email, salt=self.token_salts[token_type])
        
        # Save the token to MongoDB to allow blacklisting tokens after first use
        MongoEmailToken = TokenTypes[token_type]
        MongoEmailToken(token=token).save()

        return token


    def confirm_token(self, token, token_type):
        """
        This will verify the given email token, if it exists.
        """

        if token_type not in self.token_salts:
            raise JsonError(status='error', reason='Invalid token type provided', status_=500)

        # First check if the token exists or is used already
        MongoEmailToken = TokenTypes[token_type]
        email_token = MongoEmailToken.objects(token=token).first()
        if email_token is None or email_token.used:
            return None

        # Then try to decrypt the token and fetch the email originally encoded into the token, given a maximum age
        try:
            email = self.serializer.loads(token, salt=self.token_salts[token_type], max_age=self.expiry_durations[token_type])
        except:
            return None

        return email


    def revoke_token(self, token, token_type):
        """
        This will revoke the given email token, if it exists.
        """

        if token_type not in self.token_salts:
            raise JsonError(status='error', reason='Invalid token type provided', status_=500)

        # First check if the token exists or is used already
        MongoEmailToken = TokenTypes[token_type]
        email_token = MongoEmailToken.objects(token=token).first()
        if email_token is not None and not email_token.used:
            email_token.used = True
            email_token.save()


class EmailSender:
    """
    This class is for sending emails in a convenient manner, using the Mail SMTP
    server settings as specified in the Flask config object.

    Example for email confirmation:

    app = Flask(__name__)

    email_sender = EmailSender(app)

    ...

    recipients = ['tom_cruise@gmail.com']
    subject    = 'message from generic fan girl #34193'
    body       = 'HIIII OMG I'M YOUR BIGGEST FAN CAN I HAVE YOUR DIGITAL AUTOGRAPH'

    email_sender.send(recipients, subject, body)
    """

    def __init__(self, app=None):
        """
        A convenience constructor for initializing the email sender
        """

        if isinstance(app, Flask):
            self.init_app(app)


    def init_app(self, app):
        """
        Initialize the email sender by pulling any required settings from the Flask config
        """

        if isinstance(app, Flask):
            self.mail = Mail()
            self.mail.init_app(app)
            self.sender = app.config['MAIL_DEFAULT_SENDER']


    def send(self, recipients, subject, body):
        """
        A simple method to send an HTML email to a list of recipients with a subject
        """

        try:
            self.mail.send_message(
                subject=subject,
                recipients=recipients,
                html=body,
                sender=self.sender
            )
        except smtplib.SMTPAuthenticationError as ex:
            raise JsonError(status='error', reason='The GMail login failed. Please see the logs', status_=500)
