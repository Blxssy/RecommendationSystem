import asyncio
import logging
import os

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

    try:
        recommendations = get_movies(movie_title)
        if not recommendations:
            await message.answer("Фильм не найден в базе. Попробуйте другое название.")
            return

        media = []  # Список для фотографий

        for movie in recommendations:
            poster_path = main_df.loc[main_df['title'] == movie, 'poster_path'].values
            poster_path = poster_path[0] if len(poster_path) > 0 else None

            # Формируем полный URL постера
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None


            if poster_url:
                media.append(InputMediaPhoto(media=poster_url))

        if media:
            await bot.send_media_group(message.chat.id, media)
        else:
            await message.answer("Постеры не найдены.")

        response = "Похожие фильмы:\n" + "\n".join(recommendations)
    except KeyError as e:
        logging.error(f"Фильм не найден в базе: {e}")
        response = "Произошла ошибка. Попробуйте позже."
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        response = "Произошла ошибка. Попробуйте позже."

    await message.answer(response)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())