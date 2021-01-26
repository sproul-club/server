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
    def __init__(self, mongo_database, model_file_loc, debug = False):
        self.db = mongo_database
        self.model_file_loc = model_file_loc
        self.debug = debug

    def _fetch_list_of_club_tags(self):
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
        # Step 1: Fetch data
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
        # Step 2: Clean data
        
        """
        Description:
        Cleans club dataframe descriptions into another column containing a lists of significant words in each description.
        
        Input:
        table - club dataframe
        
        Output:
        cleaned_table - table with a new column: "cleaned descriptions"
        
        """
        
        def clean_description(description):
            """
            Description:
            Clean single description into lists of significant words.

            Input:
            description - string of club description 

            Output:
            new_description - list of significant words in description
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
        # Step 2: Train model vectors from table

        MIN_WORD_COUNT = 20
        VECTOR_SIZE = 100
        CONTEXT_WINDOW_SIZE = 10
        
        """
        Description:
        Uses cleaned table to create another column containing vectors using gensim's word2vec.
        
        Input:
        table - cleaned table
        
        Output:
        vectorized_table - table with a new_column: "vector sum"
        
        Run word2vec model
        """
        
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
        # Step 4: Generate cosine distance table from vectors

        """
        Description:
        Uses a vectorized table to create a pivot table containing distances between each club.
        
        Input:
        table - table with vectorized descriptions
        
        Output:
        distance_table - table containing all distances between each club
        
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
        list_of_club_tags = self._fetch_list_of_club_tags()
        self.club_tags_list = list_of_club_tags

        if not force_train and self.model_file_loc and os.path.exists(self.model_file_loc):
            self.distance_table = pd.read_pickle(self.model_file_loc)
        else:
            clubs_table = self._fetch_data()
            cleaned_table = self._clean_data(clubs_table)
            vectorized_table = self._train_model_vectors(cleaned_table)
            distance_table = self._generate_dist_table(vectorized_table)
            self.distance_table = distance_table

            os.makedirs(os.path.dirname(self.model_file_loc), exist_ok=True)
            self.distance_table.to_pickle(self.model_file_loc)

    def _count_tags(self, a, b, num_tags):
        """
        Description:
        Returns if club A and B contain at least k tags in common.

        Input:
        a - list of club tags for club A
        b - list of club tags for club B
        num_tags - minimum number of tags required to match

        Output:
        matching_tags - # of matching tags

        """
        matching_tags = len(set(a).intersection(set(b))) >= num_tags
        return matching_tags

    def _filter_by_tag(self, club_tags, k):
        """
        Description:
        Return boolean list that contains max amount of matching tags that satisfies matching k amount of clubs.

        Output:
        filtered_clubs - list of booleans based off of clubs filtered by tags

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
        Recommends club based off of k-nearest neighbors, prioritizing matching tags.
        
        Input:
        club_name - string of club name we want to create recommendations for
        k - represents how many neighbors
        
        Output:
        recommendations - k recommendations based off of closest distances
        
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
        sorted_club_distances = club_distances.sort_values(ascending = True, na_position = 'last')
        recommendations = sorted_club_distances.keys()[1: k + 1]
        
        return list(recommendations)
