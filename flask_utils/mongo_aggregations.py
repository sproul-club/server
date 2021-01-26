from models import PreVerifiedEmail, Tag, NewBaseUser, AccessJTI

def fetch_aggregated_rso_list():
    # This pipeline will fill in the 'registered' and 'confirmed' fields into the RSO list
    return list(PreVerifiedEmail.objects.aggregate([
        {
            '$lookup': {
                'from': 'new_base_user',
                'localField': 'email',
                'foreignField': 'email',
                'as': 'user'
            }
        }, {
            '$unwind': {
                'path': '$user',
                'preserveNullAndEmptyArrays': True
            }
        }, {
            '$match': {
                'user.role': 'officer'
            }
        }, {
            '$project': {
                '_id': 0,
                'email': 1,
                'registered': {
                    '$cond': [
                        { '$ifNull': [ '$user.registered_on', False] },
                        True,
                        False
                    ]
                },
                'confirmed': {
                    '$ifNull': [ '$user.confirmed', False ]
                }
            }
        }, {
            '$sort': {
                'email': 1
            }
        }
    ]))


def fetch_aggregated_tag_list():
    # This pipeline will associate the tags with the number of clubs that have said tag
    return list(Tag.objects.aggregate([
        {
            '$lookup': {
                'from': 'new_base_user',
                'localField': '_id',
                'foreignField': 'club.tags',
                'as': 'associated_clubs'
            }
        }, {
            '$project': {
                'name': 1,
                'num_clubs': { '$size': '$associated_clubs' }
            }
        }, {
            '$sort': {
                'name': 1
            }
        }
    ]))


def fetch_aggregated_social_media_usage():
    # This pipeline will count up the number of various social media links from all clubs available
    return list(NewBaseUser.objects.aggregate([
        {
            '$match': {
                'confirmed': True,
                'role': 'officer'
            }
        }, {
            '$replaceRoot': {
                'newRoot': '$club.social_media_links'
            }
        }, {
            '$group': {
                '_id': 1,
                'website': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$website', '']}, 1, 0]
                    }
                },
                'facebook': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$facebook', '']}, 1, 0]
                    }
                },
                'instagram': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$instagram', '']}, 1, 0]
                    }
                },
                'linkedin': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$linkedin', '']}, 1, 0]
                    }
                },
                'twitter': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$twitter', '']}, 1, 0]
                    }
                },
                'youtube': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$youtube', '']}, 1, 0]
                    }
                },
                'github': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$github', '']}, 1, 0]
                    }
                },
                'behance': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$behance', '']}, 1, 0]
                    }
                },
                'medium': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$medium', '']}, 1, 0]
                    }
                },
                'gcalendar': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$gcalendar', '']}, 1, 0]
                    }
                },
                'discord': {
                    '$sum': {
                        '$cond': [{ '$ne': ['$discord', '']}, 1, 0]
                    }
                }
            }
        }, {
            '$project': {
                '_id': 0
            }
        }
    ]));


def fetch_aggregated_club_requirement_stats():
    # This pipeline will count up the number of club requirements various social media links from all clubs available
    return list(NewBaseUser.objects.aggregate([
        {
            '$match': {
                'confirmed': True,
                'role': 'officer'
            }
        }, {
            '$group': {
                '_id': 1,
                'app_required': {
                    '$sum': {
                        '$cond': ['$club.app_required', 1, 0]
                    }
                },
                'no_app_required': {
                    '$sum': {
                        '$cond': ['$club.app_required', 0, 1]
                    }
                },
                'new_members': {
                    '$sum': {
                        '$cond': ['$club.new_members', 1, 0]
                    }
                },
                'no_new_members': {
                    '$sum': {
                        '$cond': ['$club.new_members', 0, 1]
                    }
                }
            }
        }, {
            '$project': {
                '_id': 0
            }
        }
    ]));

def fetch_aggregated_picture_stats():
    # This pipeline will count up the number of clubs having logo/banner pictures from all clubs available
    return list(NewBaseUser.objects.aggregate([
        {
            '$match': {
                'confirmed': True,
                'role': 'officer'
            }
        }, {
            '$group': {
                '_id': 1,
                'logo_pic': {
                    '$sum': {
                        '$cond': ['$club.logo_url', 1, 0]
                    }
                },
                'no_logo_pic': {
                    '$sum': {
                        '$cond': ['$club.logo_url', 0, 1]
                    }
                },
                'banner_pic': {
                    '$sum': {
                        '$cond': ['$club.banner_url', 1, 0]
                    }
                },
                'no_banner_pic': {
                    '$sum': {
                        '$cond': ['$club.banner_url', 0, 1]
                    }
                }
            }
        }, {
            '$project': {
                '_id': 0
            }
        }
    ]))

def fetch_active_users_stats():
    active_stats = list(AccessJTI.objects.aggregate([
        {
            '$lookup': {
                'from': 'new_base_user',
                'localField': 'owner',
                'foreignField': '_id',
                'as': 'user'
            }
        }, {
            '$unwind': {
                'path': '$user',
                'preserveNullAndEmptyArrays': False
            }
        }, {
            '$match': {
                'user.confirmed': True
            }
        }, {
            '$project': {
                '_id': 0,
                'email': '$user.email',
                'role': '$user.role'
            }
        }, {
            '$group': {
                '_id': 0,
                'uniqueUser': {
                    '$addToSet': {
                        'email': '$email',
                        'role': '$role'
                    }
                }
            }
        }, {
            '$project': {
                '_id': 0
            }
        }, {
            '$unwind': {
                'path': '$uniqueUser',
                'preserveNullAndEmptyArrays': False
            }
        }, {
            '$group': {
                '_id': 1,
                'student': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$uniqueUser.role', 'student'
                                ]
                            }, 1, 0
                        ]
                    }
                },
                'officer': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$uniqueUser.role', 'officer'
                                ]
                            }, 1, 0
                        ]
                    }
                },
                'admin': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$uniqueUser.role', 'admin'
                                ]
                            }, 1, 0
                        ]
                    }
                }
            }
        }, {
            '$project': {
                '_id': 0
            }
        }
    ]))

    if len(active_stats) > 0:
        return active_stats[0]
    else:
        return {
            'student': 0,
            'officer': 0,
            'admin': 0,
        }
