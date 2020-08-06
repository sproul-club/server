from itsdangerous import URLSafeTimedSerializer
from flask import Flask
from flask_mail import Mail

class EmailVerifier:
    def __init__(self, app=None):
        if isinstance(app, Flask):
            self.init_app(app)

    def init_app(self, app):
        if isinstance(app, Flask):
            secret_key = app.config['SECRET_KEY']
            self.serializer = URLSafeTimedSerializer(secret_key)
            self.pass_salt = app.config['SECURITY_PASSWORD_SALT']

    def generate_token(self, email):
        return self.serializer.dumps(email, salt=self.pass_salt)

    def confirm_token(self, token, expiration=3600):
        try:
            email = self.serializer.loads(token, salt=self.pass_salt, max_age=expiration)
        except:
            return None
        return email

class EmailSender:
    def __init__(self, app, mail_inst):
        if isinstance(app, Flask):
            self.init_app(app, mail_inst)

    def init_app(self, app, mail_inst):
        if isinstance(app, Flask):
            self.mail = mail_inst
            self.sender = app.config['MAIL_DEFAULT_SENDER']

    def send(self, recipients, subject, body):
        self.mail.send_message(
            subject=subject,
            recipients=recipients,
            html=body,
            sender=self.sender
        )
        