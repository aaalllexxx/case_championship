import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import User
from helpers import get_user
from settings import *


@dp.message(Command("start"))
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Новости📰", callback_data="news")],
                                                     [InlineKeyboardButton(text="Найти друга для занятий😊",
                                                                           callback_data="find")],
                                                     [InlineKeyboardButton(text="Профиль👤", callback_data="profile")]])
    user = get_user(message.chat.id)
    if user:
        return await message.answer(f"Привет, {user.name}!", reply_markup=keyboard)
    user = User(id=message.chat.id, name=message.from_user.full_name, link=f"https://t.me/{message.from_user.username}")
    session.add(user)
    session.commit()
    await message.answer(f"Привет!", reply_markup=keyboard)


@dp.callback_query(F.data == "menu")
async def back_to_menu(query: CallbackQuery):
    await query.answer()
    message = query.message
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Новости📰", callback_data="news")],
                                                     [InlineKeyboardButton(text="Найти друга для занятий😊",
                                                                           callback_data="find")],
                                                     [InlineKeyboardButton(text="Профиль👤", callback_data="profile")]])
    user = get_user(message.chat.id)
    if user:
        return await message.edit_text(f"Привет, {user.name}!", reply_markup=keyboard)


@dp.callback_query(F.data == "profile")
async def profile(query: CallbackQuery):
    await query.answer()
    text = ""
    user = get_user(query.message.chat.id)
    markup = None
    if user:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit_{user.id}")],
            [InlineKeyboardButton(text="Назад", callback_data=f"menu")]
        ])
        text = f"Имя: <b>{user.name}</b>\n" \
               f"Возраст: <b>{user.age}</b>\n" \
               f"Описание: <b>{user.desription}</b>\n" \
               f"Увлечения: <b>{', '.join(user.tags) if user.tags else None}</b>".replace("None", "Нет данных")
    if text:
        return await query.message.edit_text(text, reply_markup=markup, parse_mode="HTML")


async def run():
    print("started")
    await dp.start_polling(bot)
    print("end")


if __name__ == "__main__":
    print("starting bot...")
    asyncio.run(run())
