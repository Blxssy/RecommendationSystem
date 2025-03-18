import re
import time

from prepare import data, df

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

start_time = time.time()
print("Second model started")


first_column = data.columns[0]
data = data[[first_column, "overview", "all_genres"]].fillna("")
data["combined_features"] = data["overview"] + data["all_genres"]

# TF-IDF vector
tfidf_vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf_vectorizer.fit_transform(data["combined_features"])
#print(tfidf_matrix.shape)

end_time = time.time()  # Засекаем время окончания выполнения
elapsed_time = end_time - start_time

print(f"Finish preparing. Execution time: {elapsed_time:.2f} seconds\n")

def normalize_title(movie_title):
    return re.sub(r'\s+', '', movie_title).lower()

def get_movies(movie_title, num_recommendations=5):
    normalized_title = normalize_title(movie_title)
    matching_titles = {normalize_title(title): i for i, title in enumerate(df[first_column])}

    if normalized_title not in matching_titles:
        return ["The movie was not found"]

    idx = matching_titles[normalized_title]

    query_vector = tfidf_matrix[idx] # вектор конкретного фильма

    # вычисляем Cosine Similarity
    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    # получаем индексы 5 самых похожих фильмов
    similar_indices = cosine_similarities.argsort()[-(num_recommendations + 1):-1][::-1]

    return df.iloc[similar_indices][first_column].tolist()