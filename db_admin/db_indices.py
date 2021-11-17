"""
This file contains all of the DB index configurations and is used by 'manage_indices.py'
"""

import pymongo
from app_config import CurrentConfig
to_seconds = lambda dt_obj: round(dt_obj.total_seconds())


ALL_INDICES = [
    {
        'collection': 'access_jti',
        'key': 'expiry_time',
        'name': 'token-expiry',
        'extra': {
            'expireAfterSeconds': to_seconds(CurrentConfig.JWT_ACCESS_TOKEN_EXPIRES)
        }
    },
    {
        'collection': 'refresh_jti',
        'key': 'expiry_time',
        'name': 'token-expiry',
        'extra': {
            'expireAfterSeconds': to_seconds(CurrentConfig.JWT_REFRESH_TOKEN_EXPIRES)
        }
    },
    {
        'collection': 'confirm_email_token',
        'key': 'expiry_time',
        'name': 'token-expiry',
        'extra': {
            'expireAfterSeconds': to_seconds(CurrentConfig.CONFIRM_EMAIL_EXPIRY)
        }
    },
    {
        'collection': 'reset_password_token',
        'key': 'expiry_time',
        'name': 'token-expiry',
        'extra': {
            'expireAfterSeconds': to_seconds(CurrentConfig.RESET_PASSWORD_EXPIRY)
        }
    },
    {
        'collection': 'pre_verified_email',
        'key': 'email',
        'name': 'rso-email',
        'extra': {
            'unique': True
        }
    },
    {
        'collection': 'future_user',
        'key': 'org_name',
        'name': 'org-name'
    },
    {
        'collection': 'future_user',
        'key': 'org_email',
        'name': 'org-email',
        'extra': {
            'unique': True
        }
    },
    {
        'collection': 'tag',
        'key': 'name',
        'name': 'tag-name'
    },
    {
        'collection': 'new_base_user',
        'key': [
            ('email', pymongo.ASCENDING),
            ('role', pymongo.ASCENDING),
        ],
        'name': 'user-email-and-role',
        'extra': {
            'unique': True
        }
    },
    {
        'collection': 'new_base_user',
        'key': 'club.link_name',
        'name': 'club-link-name'
    },
    {
        'collection': 'new_base_user',
        'key': 'club.name',
        'name': 'club-name'
    }
]
