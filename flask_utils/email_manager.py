from itsdangerous import URLSafeTimedSerializer
from flask import Flask
from flask_mail import Mail
from flask_json import JsonError

VALID_SALT_TYPES = ['confirm', 'reset']

class EmailVerifier:
    def __init__(self, app=None):
        if isinstance(app, Flask):
            self.init_app(app)

    def init_app(self, app):
        if isinstance(app, Flask):
            secret_key = app.config['SECRET_KEY']
            self.serializer = URLSafeTimedSerializer(secret_key)
            self.pass_salts = {
                'confirm': app.config['CONFIRM_EMAIL_SALT'],
                'reset': app.config['RESET_PASSWORD_SALT'],
            }

    def generate_token(self, email, salt_type):
        if salt_type not in VALID_SALT_TYPES:
            raise JsonError(status='error', reason='Invalid salt type provided', status_=500)

        return self.serializer.dumps(email, salt=self.pass_salts[salt_type])

    def confirm_token(self, token, salt_type, expiration=3600):
        try:
            email = self.serializer.loads(token, salt=self.pass_salts[salt_type], max_age=expiration)
        except:
            return None
        return email


class EmailSender:
    def __init__(self, app=None):
        if isinstance(app, Flask):
            self.init_app(app)

    def init_app(self, app):
        if isinstance(app, Flask):
            self.mail = Mail()
            self.mail.init_app(app)
            self.sender = app.config['MAIL_DEFAULT_SENDER']

    def send(self, recipients, subject, body):
        self.mail.send_message(
            subject=subject,
            recipients=recipients,
            html=body,
            sender=self.sender
        )
        