import asyncio
import logging
import os
import time

from aiogram import Bot, Dispatcher, Router
from aiogram import F
from aiogram.types import Message, InputMediaPhoto
from dotenv import load_dotenv

from second_model import get_movies
from prepare import main_df

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

dp.include_router(router)


@router.message(F.text == "/start")
async def start_command(message: Message):
    await message.answer("Привет! Отправь мне название фильма, и я найду 5 похожих.")


@router.message(F.text)
async def recommend_movies(message: Message):
    movie_title = message.text.strip()

    print(movie_title)

    try:
        recommendations = get_movies(movie_title)
        if not recommendations:
            await message.answer("Фильм не найден в базе. Попробуйте другое название.")
            return

        for movie in recommendations:
            # Получаем данные о фильме
            movie_data = main_df.loc[main_df['title'] == movie]

            if movie_data.empty:
                continue  # Пропускаем, если данных нет

            # Извлекаем нужные поля
            poster_path = movie_data['poster_path'].values[0] if 'poster_path' in movie_data else None
            rating = movie_data['vote_average'].values[0] if 'vote_average' in movie_data else "Нет данных"
            genres = movie_data['genres'].values[0] if 'genres' in movie_data else "Неизвестно"
            runtime = movie_data['runtime'].values[0] if 'runtime' in movie_data else "Не указано"
            overview = movie_data['overview'].values[0] if 'overview' in movie_data else "Описание отсутствует"

            # Формируем полный URL постера
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            # Формируем текст сообщения
            movie_info = (
                f"🎬 <b>{movie}</b>\n"
                f"⭐️ Средний рейтинг: {rating}\n"
                f"🎭 Жанры: {genres}\n"
                f"⏳ Длительность: {runtime} минут\n\n"
                f"📖 {overview}"
            )

            # Отправляем сообщение с фото и информацией о фильме
            if poster_url:
                await message.answer_photo(poster_url, caption=movie_info, parse_mode="HTML")
            else:
                await message.answer(movie_info, parse_mode="HTML")

    except KeyError as e:
        logging.error(f"Фильм не найден в базе: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Bot started")
    asyncio.run(main())