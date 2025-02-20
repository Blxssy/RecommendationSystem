import numpy as np
import pandas as pd

data = pd.read_csv('data/TMDB_movie_dataset_v11.csv', sep=',')
data = data[data['vote_average'] != 0]
data.reset_index(inplace=True)

data = data.drop( ['id' , 'vote_count' , 'status' , 'release_date', 'revenue' , 'backdrop_path',
              'budget','homepage','imdb_id','original_title' , 'overview','poster_path',
              'tagline' , 'production_companies','production_countries' ,'spoken_languages' ,'keywords'], axis=1)
data['genres'] = data['genres'].fillna('unknown')
data = data.drop_duplicates()

print(data.columns)