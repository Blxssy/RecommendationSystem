import re
import time

from prepare import data, df

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

start_time = time.time()
print("Second model started")


first_column = data.columns[0]
data = data[[first_column, "overview", "keywords", "all_genres"]].fillna("")
data["combined_features"] = data["overview"] + data["keywords"] + data["all_genres"]

# TF-IDF vector
tfidf_vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf_vectorizer.fit_transform(data["combined_features"])
#print(tfidf_matrix.shape)

# calculating Cosine Similarity
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
cosine_sim_df = pd.DataFrame(cosine_sim, index=data.index, columns=data.index)
#print(cosine_sim_df)

end_time = time.time()  # Засекаем время окончания выполнения
elapsed_time = end_time - start_time

print(f"Finish preparing. Execution time: {elapsed_time:.2f} seconds\n")

def normalize_title(movie_title):
    return re.sub(r'\s+', '', movie_title).lower()

def get_movies(movie_title, cosine_sim=cosine_sim_df, num_recommendations=5):
    normalized_title = normalize_title(movie_title)
    matching_titles = {normalize_title(title): title for title in df.index}
    if normalized_title not in matching_titles:
        return ["The movie was not found"]

    original_title = matching_titles[normalized_title]
    # получаем список похожих фильмов, сортируем по убыванию схожести
    similar_movies = cosine_sim[original_title].sort_values(ascending=False)
    # убираем сам фильм из списка рекомендаций
    similar_movies = similar_movies.iloc[1:]

    base_name = re.sub(r'[:\-—\d]', '', original_title).strip().lower()
    # попытка отсортировать сиквелы
    filtered_movies = [
        movie for movie in similar_movies.index
        if base_name not in movie.lower()
    ]
    return [df.loc[movie, first_column] for movie in filtered_movies[:num_recommendations]]