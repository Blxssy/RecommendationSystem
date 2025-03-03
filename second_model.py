import re

from prepare import data, df

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

first_column = data.columns[0]
data = data[[first_column, "overview", "keywords"]].fillna("")
data["combined_features"] = data["overview"] + data["keywords"]

# TF-IDF vector
tfidf_vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf_vectorizer.fit_transform(data["combined_features"])
#print(tfidf_matrix.shape)

# calculating Cosine Similarity
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
cosine_sim_df = pd.DataFrame(cosine_sim, index=data.index, columns=data.index)
#print(cosine_sim_df)

def recommend_movies(movie_title, cosine_sim=cosine_sim_df, num_recommendations=5):
    if movie_title not in df.index:
        return ["The movie was not found"]

    # получаем список похожих фильмов, сортируем по убыванию схожести
    similar_movies = cosine_sim[movie_title].sort_values(ascending=False)
    # убираем сам фильм из списка рекомендаций
    similar_movies = similar_movies.iloc[1:]

    base_name = re.sub(r'[:\-—\d]', '', movie_title).strip().lower()
    # попытка отсортировать сиквелы
    filtered_movies = [
        movie for movie in similar_movies.index
        if base_name not in movie.lower()
    ]

    return filtered_movies[:num_recommendations]

movie = 'avatar'
recommendations = recommend_movies(movie)
print(f"Recommendations for '{movie}': {', '.join(recommendations)}")