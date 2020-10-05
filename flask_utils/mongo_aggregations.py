from models import PreVerifiedEmail, Club, Tag

def fetch_aggregated_rso_list():
    # This pipeline will fill in the 'registered' and 'confirmed' fields into the RSO list
    return list(PreVerifiedEmail.objects.aggregate([
        {
            '$lookup': {
                'from': 'user',
                'localField': 'email',
                'foreignField': '_id',
                'as': 'matching'
            }
        }, {
            '$unwind': {
                'path': '$matching',
                'preserveNullAndEmptyArrays': True
            }
        }, {
            '$project': {
                '_id': 0,
                'email': 1,
                'registered': {
                    '$cond': [
                        { '$ifNull': [ '$matching.registered_on', False] },
                        True,
                        False
                    ]
                },
                'confirmed': {
                    '$ifNull': [ '$matching.confirmed', False ]
                }
            }
        }, {
            '$sort': {
                'email': 1
            }
        }
    ]))


def fetch_aggregated_club_list():
    # This pipeline will attach the 'confirmed' field with the list of clubs registered
    return list(Club.objects.aggregate([
        {
            '$lookup': {
                'from': 'user',
                'localField': 'owner',
                'foreignField': '_id',
                'as': 'user'
            }
        }, {
            '$unwind': {
                'path': '$user',
                'preserveNullAndEmptyArrays': True
            }
        }, {
            '$project': {
                'name': 1,
                'owner': 1,
                'confirmed': '$user.confirmed'
            }
        }, {
            '$sort': {
                'name': 1
            }
        }
    ]))


def fetch_aggregated_tag_list():
    # This pipeline will associate the tags with the number of clubs that have said tag
    return list(Tag.objects.aggregate([
        {
            '$lookup': {
                'from': 'club',
                'localField': '_id',
                'foreignField': 'tags',
                'as': 'associated_clubs'
            }
        }, {
            '$project': {
                'name': 1,
                'num_clubs': { '$size': '$associated_clubs' }
            }
        }
    ]))
