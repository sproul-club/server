import re
from mongoengine import StringField

class RelaxedURLField(StringField):
    """
    This class is a more lenient version of mongoengine's 'URLField', which allows adding the
    protocol and the 'www' part to be optional.

    Modified from sources:
    * https://stackoverflow.com/a/3809435
    * http://regexr.com/3e6m0
    """

    _URL_REGEX = re.compile(r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-z]{1,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)', re.IGNORECASE)

    def __init__(self, url_regex=None, **kwargs):
        self.url_regex = url_regex or self._URL_REGEX
        super().__init__(**kwargs)

    def validate(self, value):
        """
        Overriden function from 'StringField' that gets executed upon a document trying to be
        saved onto the database.
        """

        if not self.null and value is None:
            self.error('Field cannot be null')

        if self.required and not value:
            self.error('Field is required and cannot be empty')


        if not self.null and not self.url_regex.match(value):
            # Only check full URL
            self.error("Invalid URL: {}".format(value))
