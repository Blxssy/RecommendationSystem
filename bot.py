import asyncio
import logging
import os
import json
import time
import requests

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

from first_model import get_movies
from second_model import find_similar_movies
from prepare import main_df

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATA_FILE = "feedback.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

dp.include_router(router)

logging.basicConfig(level=logging.INFO)


class FeedbackManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = {"model_1": {"likes": 0, "dislikes": 0}, "model_2": {"likes": 0, "dislikes": 0}}
        self.load()

    def load(self):
        try:
            with open(self.file_path, "r") as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=4)


feedback_manager = FeedbackManager(DATA_FILE)


@router.callback_query(F.data.startswith("like_"))
async def handle_like(callback_query: CallbackQuery):
    # Ensure data is in the correct format
    try:
        model = callback_query.data.replace("like_", "")
        print(f"handle_like: {model}")
        # logging.info(f"Received like for model: {model}")

        # if model not in feedback_manager.data:
        #     logging.warning(f"Invalid model received: {model}")
        #     await callback_query.answer("Ошибка: неизвестная модель.", show_alert=True)
        #     return

        feedback_manager.data[model]["likes"] += 1
        feedback_manager.save()
        await callback_query.message.answer("Спасибо за отзыв! Хотите снова выбрать модель?",
                                            reply_markup=get_main_keyboard())
        await callback_query.answer()
    except IndexError:
        logging.error(f"Invalid callback data: {callback_query.data}")
        # await callback_query.answer("Ошибка: неверные данные.", show_alert=True)


@router.callback_query(F.data.startswith("dislike_"))
async def handle_dislike(callback_query: CallbackQuery):
    # Ensure data is in the correct format
    try:
        model = callback_query.data.replace("dislike_", "")
        # logging.info(f"Received dislike for model: {model}")

        # if model not in feedback_manager.data:
        #     logging.warning(f"Invalid model received: {model}")
        #     await callback_query.answer("Ошибка: неизвестная модель.", show_alert=True)
        #     return

        feedback_manager.data[model]["dislikes"] += 1
        feedback_manager.save()
        await callback_query.message.answer("Спасибо за отзыв! Хотите снова выбрать модель?",
                                            reply_markup=get_main_keyboard())
        await callback_query.answer()
        # await callback_query.answer("Спасибо за отзыв!", show_alert=True)
    except IndexError:
        logging.error(f"Invalid callback data: {callback_query.data}")
        # await callback_query.answer("Ошибка: неверные данные.", show_alert=True)


def search_trailer(movie_title):
    try:
        query = f"{movie_title} official trailer"
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}&maxResults=1&type=video"
        response = requests.get(url).json()
        if "items" in response and response["items"]:
            return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    except requests.RequestException:
        logging.error("Failed to fetch trailer from YouTube API")
    return None


class RecommendationState(StatesGroup):
    waiting_for_movie_title = State()
    waiting_for_movie_title_second = State()


def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Рекомендации (Модель 1)", callback_data="start_recommendation")],
        [InlineKeyboardButton(text="Рекомендации (Модель 2)", callback_data="start_recommendation_second")]
    ])


def get_feedback_keyboard(model):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👍 Да", callback_data=f"like_{model}"),
         InlineKeyboardButton(text="👎 Нет", callback_data=f"dislike_{model}")]
    ])


@router.message(F.text == "/start")
async def start_command(message: Message):
    await message.answer("Выберите способ рекомендации:", reply_markup=get_main_keyboard())


@router.callback_query(F.data == "start_recommendation")
async def ask_for_movie(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название фильма:")
    await state.set_state(RecommendationState.waiting_for_movie_title)
    await callback_query.answer()


@router.message(RecommendationState.waiting_for_movie_title)
async def process_movie_title(message: Message, state: FSMContext):
    await recommend_movies(message, "model_1")
    await state.clear()


@router.callback_query(F.data == "start_recommendation_second")
async def ask_for_movie_second(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название фильма:")
    await state.set_state(RecommendationState.waiting_for_movie_title_second)
    await callback_query.answer()


@router.message(RecommendationState.waiting_for_movie_title_second)
async def process_movie_title_second(message: Message, state: FSMContext):
    await recommend_movies(message, "model_2")
    await state.clear()


import time
from aiogram.types import Message


async def recommend_movies(message: Message, model: str):
    print(f"Recommending {model} movies for {message.text}")

    start_time = time.time()
    movie_title = message.text.strip()

    recommendations = get_movies(movie_title) if model == "model_1" else find_similar_movies(movie_title, top_n=5)
    # print(recommendations)
    if not recommendations:
        await message.answer("Фильм не найден в базе. Попробуйте другое название.")
        return
    if isinstance(recommendations, str):
        recommendations = [recommendations]

    for movie in recommendations:
        try:
            movie_data = main_df.loc[main_df['title'] == movie]

            if movie_data.empty:
                continue

            poster_path = movie_data['poster_path'].values[0] if 'poster_path' in movie_data else None
            rating = movie_data['vote_average'].values[0] if 'vote_average' in movie_data else "Нет данных"
            genres = movie_data['genres'].values[0] if 'genres' in movie_data else "Неизвестно"
            runtime = movie_data['runtime'].values[0] if 'runtime' in movie_data else "Не указано"
            overview = movie_data['overview'].values[0] if 'overview' in movie_data else "Описание отсутствует"

            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            movie_info = (
                f"🎬 <b>{movie}</b>\n"
                f"⭐️ Средний рейтинг: {rating}\n"
                f"🎭 Жанры: {genres}\n"
                f"⏳ Длительность: {runtime} минут\n\n"
                f"📖 {overview}"
            )

            if poster_url:
                await message.answer_photo(poster_url, caption=movie_info, parse_mode="HTML")
            else:
                await message.answer(movie_info, parse_mode="HTML")
        finally:
            continue

    await message.answer("Вам понравились рекомендации?", reply_markup=get_feedback_keyboard(model))
    print(f"Execution time: {time.time() - start_time:.2f} seconds")


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        feedback_manager.save()
        await bot.session.close()


if __name__ == "__main__":
    print("Bot started")
    asyncio.run(main())
