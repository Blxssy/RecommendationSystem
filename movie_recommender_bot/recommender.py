import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

data = pd.read_csv('data/TMDB_movie_dataset_v11.csv', sep=',', nrows=10000)

data = data[data['vote_average'] != 0].reset_index(drop=True)

drop_cols = ['id', 'vote_count', 'status', 'release_date', 'revenue', 'backdrop_path',
             'budget', 'homepage', 'imdb_id', 'original_title', 'overview', 'poster_path',
             'tagline', 'production_companies', 'production_countries', 'spoken_languages', 'keywords']
data = data.drop(columns=drop_cols)

data['genres'] = data['genres'].fillna('unknown')

data['genres'] = data['genres'].apply(lambda x: x.split(', ') if isinstance(x, str) else [])

mlb = MultiLabelBinarizer()
genre_encoded = pd.DataFrame(mlb.fit_transform(data['genres']), columns=mlb.classes_)

data_encoded = pd.concat([data.drop(columns=['genres']), genre_encoded], axis=1)

print(data_encoded.head())
