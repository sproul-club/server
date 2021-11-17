import os.path
import json, re

import pymongo

import numpy as np
import pandas as pd
import scipy

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

import gensim


class ClubRecommender:
    """
    This class contains the similar clubs recommender system. It's mostly extracted from the Jupyter Notebooks
    and optimized for use with backend.
    """

    def __init__(self, mongo_database, model_file_loc, debug = False):
        self.db = mongo_database
        self.model_file_loc = model_file_loc
        self.debug = debug

    ######################
    ### TRAINING STEPS ###
    ######################

    def _fetch_list_of_club_tags(self):
        """
        Utility method to fetch the list of club tags as a 2D array, with each entry in the outer
        array being a list of club tags itself (i.e a numeric list of tag IDs).
        """

        list_of_tags = []

        for user in self.db['new_base_user'].find({
            'role': 'officer',
            'confirmed': True,
            'club.reactivated': True
        }):
            club_tags = user['club']['tags']
            list_of_tags += [club_tags]

        return list_of_tags


    def _fetch_data(self):
        """
        Fetches all the raw data from the database specified and stores it in a pandas DataFrame.

        Input: Nothing

        Output: A DataFrame with all the needed *raw* club data for training the model (still needs processing)
        """

        club_info_db = []

        for user in self.db['new_base_user'].find({
            'role': 'officer',
            'confirmed': True,
            'club.reactivated': True
        }):
            club_name = user['club']['name'].strip()
            club_link_name = user['club']['link_name'].strip()
            club_description = user['club']['about_us'].strip()
            club_tags = user['club']['tags']
            
            club_info_db += [{
                'name': club_name,
                'link_name': club_link_name,
                'description': club_description,
                'tags': club_tags,
            }]
            
        club_db_df = pd.DataFrame(club_info_db)
        club_db_df = club_db_df.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False)
        club_db_df = club_db_df.reset_index(drop = True)

        for (i, row) in club_db_df.iterrows():
            row['description'] = row['description'] if len(row['description']) != 0 else row['name']

        return club_db_df


    def _clean_data(self, table):
        """
        Cleans club dataframe descriptions into another column containing a lists of significant words in each description.

        Input:
        * table - The raw DataFrame containing all the club data

        Output: A copy of the input DataFrame with a new column containing a list of the significant words
        from each club's original description.
        """
        
        def clean_description(description):
            """
            Clean single description into lists of significant words.

            Input:
            * description - The club description string

            Output: A list of significant words from input description.
            """
            
            try: 
                # Remove punctuation
                new_description = re.sub("[^a-zA-Z]", " ", description)

                # Tokenize into words (all lower case)
                new_description = new_description.lower().split()

                # Remove stopwords
                eng_stopwords = set(stopwords.words("english"))
                new_description = [w for w in new_description if not w in eng_stopwords]

                # Remove "uc" and "berkeley"
                uc_berkeley = ['uc', 'berkeley', 'also', 'providing', 'various', 'well', 'provide', 'one']
                new_description = [w for w in new_description if not w in uc_berkeley]
            except TypeError:
                return [""]

            return new_description
        
        clean_descriptions = []
        
        for i in np.arange(len(table)):
            clean_descriptions += [clean_description(table['description'][i])]
            
        cleaned_table = table.drop(['description'], axis=1)
        cleaned_table['clean_description'] = clean_descriptions
        
        return cleaned_table


    def _train_model_vectors(self, table, yield_model = False):
        """
        Uses the cleaned descriptions to create another column containing word-embedding vectors
        via gensim's word2vec algorithm.

        Input:
        * table - Processed DataFrame with *all* required data for training the model.

        Output: A copy of the input table with a new column containing a word-embedding vector of
        size VECTOR_SIZE for each club.
        """

        MIN_WORD_COUNT = 20
        VECTOR_SIZE = 100
        CONTEXT_WINDOW_SIZE = 10
        
        list_vectors = []
        
        model = gensim.models.Word2Vec(
            table['clean_description'],
            min_count=MIN_WORD_COUNT,
            size=VECTOR_SIZE,
            window=CONTEXT_WINDOW_SIZE,
            compute_loss=True,
            sample=1e-3 / 2,
            workers=1,
            seed=42
        )
        
        for i in range(len(table)):
            ith_description = table['clean_description'][i]    
            
            ith_vector_list = []
            for ith_description_word in ith_description:
                if ith_description_word in model:
                    ith_vector_list += [model[ith_description_word]]
            
            if len(ith_vector_list) == 0:
                description_sum_vector = [1e-6] * VECTOR_SIZE
            else:
                description_sum_vector = sum(np.array(ith_vector_list))
                
            list_vectors += [description_sum_vector]
            
        vectorized_table = table.copy()
        vectorized_table['vector_sum'] = list_vectors
        
        if yield_model:
            return vectorized_table, model
        else:
            return vectorized_table


    def _generate_dist_table(self, table):
        """
        Uses a vectorized table to create a 2D distance table containing distances between each club.

        Input:
        * table - DataFrame with word-embedding vectors from descriptions

        Output:
        * A 2D table of cosine distance between each and every club based on their descriptions. If two clubs
        are very similar, their distance will be close to 1, and otherwise the distance will be close to 0.
        """
            
        dict = table[['link_name','vector_sum']].set_index('link_name')['vector_sum'].to_dict()
        distance_list = []
        
        for club_1 in dict:
            vector_1 = dict[club_1]
            distance_dictionary = {}
            
            for club_2 in dict:
                vector_2 = dict[club_2]
                
                cosine_sim = 1 - scipy.spatial.distance.cosine(vector_1, vector_2)
                distance_dictionary[club_2] = cosine_sim
                
            distance_list += [distance_dictionary]
            
        distance_table = pd.DataFrame(data=distance_list)
        distance_table.index = table['link_name']
        
        return distance_table


    def train_or_load_model(self, force_train = False):
        """
        A convenient function to either load a previously trained model or train a new model from scratch.

        Note that the so-called model is actually a distance table that 'models' the relationships between
        each of the clubs via its descriptions.
        """

        list_of_club_tags = self._fetch_list_of_club_tags()
        self.club_tags_list = list_of_club_tags

        # Search for the model given the file location and load it...otherwise generate a new one.
        if not force_train and self.model_file_loc and os.path.exists(self.model_file_loc):
            self.distance_table = pd.read_pickle(self.model_file_loc)
        else:
            # Step 1: Fetch raw data
            clubs_table = self._fetch_data()

            # Step 2: Clean raw data
            cleaned_table = self._clean_data(clubs_table)

            # Step 3: Train model vectors from table
            vectorized_table = self._train_model_vectors(cleaned_table)

            # Step 4: Generate distance table from vectors
            distance_table = self._generate_dist_table(vectorized_table)
            self.distance_table = distance_table

            # Step 5: Save distance table as pickle file
            os.makedirs(os.path.dirname(self.model_file_loc), exist_ok=True)
            self.distance_table.to_pickle(self.model_file_loc)


    ###################
    ### INFERENCING ###
    ###################

    def _count_tags(self, a, b, num_tags):
        """
        Returns if club A and B contain at least k tags in common.

        Input:
        * a - list of club tags for club A
        * b - list of club tags for club B
        * num_tags - minimum number of tags required to match

        Output: The number of matching tags from the set intersection between 'a' and 'b'
        """

        matching_tags = len(set(a).intersection(set(b))) >= num_tags
        return matching_tags


    def _filter_by_tag(self, club_tags, k):
        """
        Returns boolean list that contains max amount of matching tags that satisfies matching 'k' amount of clubs.

        Input:
        * club_tags - A 2D list of club tags, with each outer array entry being a list of club tags itself
        * k - The num

        Output: - A list of booleans based off of clubs filtered by tags
        """

        filtered_clubs = []

        num_of_tags = len(club_tags)
        while (np.count_nonzero(filtered_clubs) - 1 < k):
            if num_of_tags == 0:
                return [True] * len(self.club_tags_list)

            filtered_clubs = []
            for other_club_tags in self.club_tags_list:
                if self._count_tags(club_tags, other_club_tags, num_of_tags):
                    filtered_clubs += [True]
                else:
                    filtered_clubs += [False]
            num_of_tags -= 1

        else:
            return filtered_clubs


    def recommend(self, club_link_name, k = 3):
        """
        Description:
        Given a club's link name, recommend up to 'k' similar clubs, prioritizing first by matching tags and
        then by description.
        
        Input:
        club_link_name - The link name of the club, which is typically the ID of the club when it was first created
        k - Number of similar clubs to recommend
        
        Output: 'k' recommended clubs based on tags and description
        """

        try:
            club_info = self.db['new_base_user'].find({
                'role': 'officer',
                'confirmed': True,
                'club.reactivated': True,
                'club.link_name': club_link_name,
            })[0]['club']
        except IndexError:
            return None
        
        target_club_name = club_info['link_name'].strip()
        target_club_tags = club_info['tags']

        filtered_clubs = self._filter_by_tag(target_club_tags, k)
        
        filtered_distances = self.distance_table[filtered_clubs]
        club_distances = filtered_distances[target_club_name] 
        sorted_club_distances = club_distances.sort_values(ascending = False, na_position = 'last')
        recommendations = sorted_club_distances.keys()[1: k + 1]
        
        return list(recommendations)
