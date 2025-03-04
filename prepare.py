import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder

main_df  = pd.read_csv('./data/TMDB_movie_dataset_v11.csv', sep=',', nrows=10000)
pd.set_option('display.max_columns', None)

# -------------------------------------------------------------------------------------------------------------
# Prepare dataset
df = main_df[main_df['vote_average']!=0]
df.reset_index(inplace=True)
df = df.drop( ['index','id' , 'vote_count' , 'status' , 'release_date', 'revenue' , 'backdrop_path',
              'budget','homepage','imdb_id','original_title',
              'tagline' , 'production_companies','production_countries' ,'spoken_languages', 'poster_path'], axis=1)
df['org_title']=df['title']
df['genres'] = df['genres'].fillna('unknown')
df = df.drop_duplicates()

dff= df.copy()
# -------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------------------
# Encoding
dff['all_genres'] = df['genres']
genre_l = dff['genres'].apply(lambda x: x.split(','))
genre_l = pd.DataFrame(genre_l)

genre_l['genres'] = genre_l['genres'].apply(lambda x :[ y.strip().lower().replace(' ','') for y in x] )

MLB = MultiLabelBinarizer()

genre_encoded = MLB.fit_transform(genre_l['genres'])

genre_encoded_df = pd.DataFrame(genre_encoded, columns=MLB.classes_)
genre_encoded_df=genre_encoded_df.reset_index()

mod_df = dff.drop(['genres'],axis=1)
mod_df=mod_df.reset_index()

df = pd.concat([mod_df,genre_encoded_df],axis=1).drop('index',axis=1)

df['title'] = df['title'].apply(lambda x :x.strip().lower().replace(' ','') )
df['original_language'] = df['original_language'].apply(lambda x :x.strip().lower().replace(' ','') )

df.loc[~( (df['original_language']=='en')|(df['original_language']=='fr')|(df['original_language']=='es')|(df['original_language']=='de')|(df['original_language']=='ja')),'original_language'] = 'else'

# One-Hot Encoding
encoder = OneHotEncoder(sparse_output=False)

df['adult'] = df['adult'].astype('str')
adult_enc = encoder.fit_transform(df[['adult']])
adult_enc_df = pd.DataFrame(adult_enc,columns=encoder.get_feature_names_out())

adult_enc_df = adult_enc_df.drop('adult_True',axis=1)

lang_enc = encoder.fit_transform(df[['original_language']])
lang_enc_df = pd.DataFrame(lang_enc,columns=encoder.get_feature_names_out())

mod_df = df.drop(['adult','original_language'],axis=1)

df = pd.concat([mod_df,adult_enc_df,lang_enc_df],axis=1)
# -------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------------------
# Normalization
from sklearn.preprocessing import StandardScaler

SC = StandardScaler()

ignore_cols = ['title', 'org_title', 'action',
       'adventure', 'animation', 'comedy', 'crime', 'documentary', 'drama',
       'family', 'fantasy', 'history', 'horror', 'music', 'mystery', 'romance',
       'sciencefiction', 'thriller', 'tvmovie', 'unknown', 'war', 'western',
       'adult_False', 'original_language_de', 'original_language_else',
       'original_language_en', 'original_language_es', 'original_language_fr',
       'original_language_ja', 'all_genres', 'overview', 'keywords']

df_norm = SC.fit_transform(df.drop(ignore_cols, axis=1))
df_norm_df = pd.DataFrame(df_norm, columns=[x for x in df.columns if x not in ignore_cols])

df = pd.concat([df[ignore_cols],df_norm_df],axis=1)

df = df.drop_duplicates(subset=['title'])

df=df.set_index(['title'])
data=df