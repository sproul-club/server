DEV_MODE = False

from dotenv import load_dotenv
load_dotenv(dotenv_path='../.env.prod' if not DEV_MODE else '../.env.dev')

import os
import sys

# We need to import the current configuration for the token expiry TTL indices
sys.path.append('../')

from models import *

import pymongo
from pymongo import MongoClient
from db_indices import ALL_INDICES

def generate_db_indices(database_name):
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


def delete_db_indices(database_name):
    # Initialize the MongoDB Client and needed variables
    mongo_client = MongoClient(os.getenv('MONGO_URI'))
    db = mongo_client[database_name]
    all_collection_names = db.list_collection_names()

    # Delete all the indices (except for the default ones)
    for index in ALL_INDICES:
        col_name = index['collection']

        if col_name in all_collection_names:
            try:
                db[col_name].drop_index(index['name'])
            except pymongo.errors.OperationFailure:
                print(f"Ignoring index '{index['name']}' in collection '{col_name}' as it doesn't exist...")
        else:
            raise Exception(f"Collection '{col_name}' not found in database!")

def delete_all_db_indices(database_name):
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
