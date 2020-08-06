__all__ = ['EmailVerifier', 'EmailSender', 'ImageManager' 'validate_json', 'id_creator']
from flask_utils.email import EmailVerifier, EmailSender
from flask_utils.image_manager import ImageManager
from flask_utils.schema_validator import validate_json

id_creator = lambda string: string.replace(' ', '-').lower()[:100]

# Modified from source: https://stackoverflow.com/a/55986782
def hyphen_to_underscore(dictionary):
    # for arrays, perform this method on every object
    if type(dictionary) is type([]):
        return [hyphen_to_underscore(item) for item in dictionary]

    # for sub-dictionaries traverse all the keys and replace hyphen with underscore
    elif type(dictionary) is type({}):
        return dict( (k.replace('-', '_'), hyphen_to_underscore(v)) for k, v in dictionary.items() )
        
    # otherwise, return the same object
    return dictionary
