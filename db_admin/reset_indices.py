"""
This file is a CLI script to reset the database indices depending on the database specified,
either the dev (development) or prod (production) database.

To use it, first specify what database to reset the respsective indices by setting 'DEV_MODE'
to true or false.
- If DEV_MODE is true, then the *development* database's indices will be reset
- If DEV_MODE is false, then the *production* database's indices will be reset

Then run the command 'python db_admin/reset_indices.py' from the root of the project.
"""

DEV_MODE = True

from dotenv import load_dotenv
load_dotenv(dotenv_path='../.env.prod' if not DEV_MODE else '../.env.dev')

import os
import sys

# NOTE: We need to import the current configuration for the token expiry TTL indices
sys.path.append('../')

from models import *

import pymongo
from pymongo import MongoClient
from db_indices import ALL_INDICES

def generate_db_indices(database_name):
    """
    A utility function to generate the database indices for each collection via the config object
    'ALL_INDICES', if that collection exists and the index doesn't already exist in said database.
    """

    # Initialize the MongoDB Client and needed variables
    mongo_client = MongoClient(os.getenv('MONGO_URI'))
    db = mongo_client[database_name]
    all_collection_names = db.list_collection_names()

    # Generate all the indices (except for the default ones)
    for index in ALL_INDICES:
        col_name = index['collection']

        if col_name in all_collection_names:
            try:
                db[col_name].create_index(index['key'], name=index['name'], **index.get('extra', {}))
            except pymongo.errors.OperationFailure:
                print(f"Ignoring index '{index['name']}' in collection '{col_name}' as it already exist...")
        else:
            raise Exception(f"Collection '{col_name}' not found in database!")


def delete_all_db_indices(database_name):
    """
    A utility function to delete ALL database indices for ALL collections. This differs from 'delete_db_indices'
    in that it deletes all indices regardless of if it was in the config object 'ALL_INDICES' or not.
    """
    
    # Initialize the MongoDB Client and needed variables
    mongo_client = MongoClient(os.getenv('MONGO_URI'))
    db = mongo_client[database_name]
    all_collection_names = db.list_collection_names()

    # Delete all the indices (except for the default ones)
    for col_name in all_collection_names:
        db[col_name].drop_indexes()


if __name__ == '__main__':
    DATABASE_NAME = 'production-db' if not DEV_MODE else 'develop-db'

    print(f'Using database: {DATABASE_NAME}')

    print('Deleting all indices...')
    delete_all_db_indices(DATABASE_NAME)

    print('Generating indices...')
    generate_db_indices(DATABASE_NAME)
