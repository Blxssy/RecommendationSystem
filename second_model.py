import re
import time

import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from prepare import main_df

# Загружаем данные
df = pd.read_csv("data/filtered_ratings.csv")

start_time = time.time()
print("Second model started")

reader = Reader(rating_scale=(0, 5))
data = Dataset.load_from_df(df[['userId', 'tmdbId', 'rating']], reader)

trainset, testset = train_test_split(data, test_size=0.2)

# Обучаем ALS (SVD в Surprise)
model = SVD(n_factors=100, n_epochs=30, verbose=True)
model.fit(trainset)

def normalize_title(title):
    if not isinstance(title, str):  # Проверка, что это строка
        return ''
    return re.sub(r'\s+', '', title).lower()

movie_id_to_title = dict(zip(df['tmdbId'], df['title']))
title_to_movie_id = {normalize_title(title): movie_id for movie_id, title in movie_id_to_title.items()}

available_movie_ids = set(trainset.all_items())

movie_factors = {}
for movieId in df["tmdbId"].unique():
    if movieId in available_movie_ids:
        try:
            inner_id = trainset.to_inner_iid(movieId)
            movie_factors[movieId] = model.qi[inner_id]
        except ValueError:
            print(f"Фильм с ID {movieId} не найден в trainset.")

end_time = time.time() 
elapsed_time = end_time - start_time

print(f"Finish preparing second model. Execution time: {elapsed_time:.2f} seconds\n")

# Функция поиска похожих фильмов
def find_similar_movies(movie_name, top_n=5):
    normalized_name = normalize_title(movie_name)

    if normalized_name not in title_to_movie_id:
        return "Фильм не найден в базе!"

    movie_id = title_to_movie_id[normalized_name]
    if movie_id not in movie_factors:
        return "Фильм не найден в обученной модели!"

    target_vector = movie_factors[movie_id].reshape(1, -1)

    # Косинусное сходство
    similarities = {
        mid: cosine_similarity(target_vector, vector.reshape(1, -1))[0][0]
        for mid, vector in movie_factors.items()
    }

    # Убираем исходный фильм
    similarities.pop(movie_id, None)

    valid_titles = set(main_df['title'])

    # Отбираем N уникальных фильмов
    unique_titles = set()
    similar_movies = []

    for movie, _ in sorted(similarities.items(), key=lambda x: -x[1]):
        title = movie_id_to_title[movie]

        if title in valid_titles and title not in unique_titles:
            similar_movies.append(title)
            unique_titles.add(title)

        if len(similar_movies) == top_n:
            break

    return similar_movies
