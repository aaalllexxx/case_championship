import asyncio
import datetime
import json
import os.path

import random

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aioschedule
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
)

from database import User
from helpers import get_user
from settings import *

TASKS = [
    "Берпи (10б)",
    "10 подтягиваний на высокой перекладине (7б)",
    "10 Берпи (7б)",
    "15 подтягиваний на высокой перекладине (10б)",
    "15 приседаний (9б)",
    "10 приседаний (7б)",
    "3 минут планки на локтях (6б)",
    "5 минут планки на локтях (10б)",
    "10 отжиманий на брусьях (10б)",
    "10 отжиманий в упоре лежа (7б)",
    "15 отжиманий в упоре лежа (10б)",
    "15 отжиманий на брусьях (12б)"
]

async def add_tasks():
    users = session.query(User).all()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Смотреть", callback_data="tasks")]])
    for user in users:
        my_simple_tasks = random.choices(TASKS, k=3)
        user.tasks = json.dumps(my_simple_tasks)
        session.commit()
        await bot.send_message(user.id, "Ежедневные задания обновлены.", reply_markup=keyboard)

async def add_tasks_to(user_id):
    user = get_user(user_id)
    my_simple_tasks = random.choices(TASKS, k=3)
    user.tasks = json.dumps(my_simple_tasks)
    session.commit()


async def run_tick():
    print("start ticking")
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


class States(StatesGroup):
    editing_name = State()
    editing_age = State()
    editing_bio = State()
    editing_tags = State()


def check_match(user1: str, user2: str) -> bool:
    tags1 = json.loads(user1 or "[]")
    tags2 = json.loads(user2 or "[]")
    for tag in tags1:
        if tag in tags2:
            return True
    return False


def get_tags_keyboard(user_id):
    user = get_user(user_id)
    if user:
        tags = json.loads(user.tags or "[]")
        keys = []
        for tag in available_tags:
            if tag in tags:
                keys.append([InlineKeyboardButton(text=f"{tag}✅", callback_data=tag)])
            else:
                keys.append([InlineKeyboardButton(text=f"{tag}❌", callback_data=tag)])
        keys.append([InlineKeyboardButton(text="Готово", callback_data="готово")])
        return InlineKeyboardMarkup(inline_keyboard=keys)


@dp.message(States.editing_name)
async def set_name(message: Message, state: FSMContext):
    user = get_user(message.chat.id)
    if user:
        user.name = message.text
        session.commit()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Продолжить", callback_data="edit")]
            ]
        )
        await message.answer("Имя установлено.", reply_markup=keyboard)
        await state.clear()


@dp.message(States.editing_age)
async def set_age(message: Message, state: FSMContext):
    user = get_user(message.chat.id)
    if user:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Продолжить", callback_data="edit")]
            ]
        )
        user.age = message.text
        session.commit()
        await message.answer("Возраст установлен.", reply_markup=keyboard)
        await state.clear()


@dp.callback_query(lambda x: 'set_score' in x.data)
async def set_score(query: CallbackQuery):
    user = get_user(query.message.chat.id)
    if user:
        ind = int(query.data.split('_')[2])
        my_simple_tasks = json.loads(user.tasks or "[]")
        try:
            new_score = my_simple_tasks[ind].split('(')[-1].strip('б)')
        except IndexError:
            new_score = 0
        user.score += int(new_score)
        session.commit()
        await query.answer()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="В меню", callback_data="menu")]
            ])
        try:
            my_simple_tasks.pop(int(ind))
            user.tasks = json.dumps(my_simple_tasks)
            session.commit()
        except IndexError:
            pass
        await query.message.edit_text(f"Вам начислено {new_score} баллов.", reply_markup=keyboard)


@dp.message(States.editing_bio)
async def set_bio(message: Message, state: FSMContext):
    user = get_user(message.chat.id)
    if user:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Продолжить", callback_data="edit")]
            ]
        )
        user.desription = message.text
        session.commit()
        await message.answer("Описание установлено.", reply_markup=keyboard)
        await state.clear()


@dp.callback_query(States.editing_tags)
async def set_tags(query: CallbackQuery, state: FSMContext):
    user = get_user(query.message.chat.id)
    if user:
        tags: list = json.loads(user.tags or "[]")
        if (
                query.data not in tags
                and query.data.lower() != "другое"
                and query.data.lower() != "готово"
        ):
            tags.append(query.data)
        elif query.data.lower() != "готово":
            tags.remove(query.data)
        elif query.data.lower() == "готово":
            await state.clear()
            return await back_to_menu(query)

        user.tags = json.dumps(tags)
        session.commit()
        await query.answer()
        await query.message.edit_text(
            "Выберите увлечения:", reply_markup=get_tags_keyboard(user.id)
        )


@dp.message(Command("start"))
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мероприятия📰", callback_data="news")],
            [
                InlineKeyboardButton(
                    text="Найти друга для занятий😊", callback_data="find"
                )
            ],
            [InlineKeyboardButton(text="Профиль👤", callback_data="profile")],
            [InlineKeyboardButton(text="Ежедневные задания", callback_data="tasks")],
        ]
    )
    user = get_user(message.chat.id)
    if user:
        return await message.answer(f"Привет, {user.name}!", reply_markup=keyboard)
    user = User(
        id=message.chat.id,
        name=message.from_user.full_name,
        link=f"https://t.me/{message.from_user.username}",
    )
    session.add(user)
    session.commit()
    await add_tasks_to(user.id)
    await message.answer(f"Привет!", reply_markup=keyboard)


@dp.callback_query(F.data == "menu")
async def back_to_menu(query: CallbackQuery):
    await query.answer()
    message = query.message
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мероприятия📰", callback_data="news")],
            [
                InlineKeyboardButton(
                    text="Найти друга для занятий😊", callback_data="find"
                )
            ],
            [InlineKeyboardButton(text="Профиль👤", callback_data="profile")],
            [InlineKeyboardButton(text="Ежедневные задания", callback_data="tasks")],
        ]
    )
    user = get_user(message.chat.id)
    if user:
        return await message.edit_text(f"Привет, {user.name}!", reply_markup=keyboard)


@dp.callback_query(lambda x: "find" in x.data)
async def find(query: CallbackQuery):
    user = get_user(query.message.chat.id)
    await query.answer()
    if user:
        declines = json.loads(user.declines or "[]")
        index = 0
        if "_" in query.data:
            index = int(query.data.split("_")[1])
        matches = (
            session.query(User)
            .where(User.age <= user.age + 2)
            .where(user.age - 2 <= User.age)
            .where(user.id != User.id)
            .all()
        )
        match = []
        for matched_user in matches:
            if (
                    check_match(user.tags, matched_user.tags)
                    and matched_user.id not in declines
            ):
                match.append(matched_user)
        buttons = []
        if index > 0:
            buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"find_{index - 1}")
            )
        if index < len(match) - 1:
            buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"find_{index + 1}")
            )
        matched_user: User | bool = match[index] if match else False
        if matched_user:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    buttons,
                    [
                        InlineKeyboardButton(
                            text="Предложить позаниматься",
                            callback_data=f"ask_{match[index].id}",
                        )
                    ],
                    [InlineKeyboardButton(text="Назад", callback_data=f"menu")],
                ]
            )
            await query.message.edit_text(
                f"<b>{matched_user.name}</b>, <u>{matched_user.age}</u>\nОписание: <i>{matched_user.desription}</i>\nУвлечения: {', '.join(json.loads(matched_user.tags or '[]')) or None}",
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Назад", callback_data=f"menu")]
                ]
            )
            await query.message.answer(
                "Никого не нашлось.\n\n"
                "Если вы ещё не заполняли профиль - заполняйте и возвращайтесь сюда😃\n\n"
                "Если вы уже заполнили профиль - подождите появления новых пользователей😁",
                reply_markup=markup,
            )


@dp.callback_query(F.data == "profile")
async def profile(query: CallbackQuery):
    await query.answer()
    text = ""
    user = get_user(query.message.chat.id)
    markup = None
    if user:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Изменить", callback_data=f"edit")],
                [InlineKeyboardButton(text="Назад", callback_data=f"menu")],
            ]
        )
        text = (
            f"Имя: <b>{user.name}</b>\n"
            f"Возраст: <b>{user.age}</b>\n"
            f"Описание: <b>{user.desription}</b>\n"
            f"Увлечения: <b>{', '.join(json.loads(user.tags or '[]')) if json.loads(user.tags or '[]') else None}</b>\n".replace(
                "None", "Нет данных"
            )
        )
        text += f"Баллы: <b>{user.score}</b>"
    if text:
        return await query.message.edit_text(
            text, reply_markup=markup, parse_mode="HTML"
        )


@dp.callback_query(lambda x: "tasks" in x.data)
async def tasks(query: CallbackQuery):
    await query.answer()
    user = get_user(query.message.chat.id)
    index = 0
    if "_" in query.data:
        index = int(query.data.split("_")[1])
    buttons = []
    my_simple_tasks = json.loads(user.tasks or "[]")
    if index > 0:
        buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"tasks_{index - 1}")
        )
    if index < len(my_simple_tasks) - 1:
        buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"tasks_{index + 1}")
        )
    if not my_simple_tasks:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="В меню", callback_data="menu")]
            ]
        )
        return await query.message.edit_text("На сегодня заданий больше нет.", reply_markup=keyboard)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [
                InlineKeyboardButton(
                    text="Выполнил",
                    callback_data=f"set_score_{index}",
                ),
                InlineKeyboardButton(text="Назад", callback_data=f"menu")
            ],
            [InlineKeyboardButton(text="Как делать?", callback_data=f"work_{index}")]
        ]
    )
    await query.message.edit_text(f"<b>{my_simple_tasks[index]}</b>", parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query(lambda q: "edit" in q.data)
async def edit_profile(query: CallbackQuery, state: FSMContext):
    await query.answer()
    user = get_user(query.message.chat.id)
    if not user:
        return await query.message.answer("Сначала пропишите /start")
    if "_" not in query.data:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Имя", callback_data="edit_name")],
                [InlineKeyboardButton(text="Возраст", callback_data="edit_age")],
                [InlineKeyboardButton(text="Описание", callback_data="edit_bio")],
                [InlineKeyboardButton(text="Увлечения", callback_data="edit_tags")],
                [InlineKeyboardButton(text="Назад", callback_data="profile")],
            ]
        )
        return query.message.edit_text("Что вы хотите изменить?", reply_markup=keyboard)
    if "_" in query.data:
        messages = {
            "name": "Введите имя:",
            "age": "Введите возраст:",
            "bio": "Введите описание:",
            "tags": "Выберите увлечения:",
        }
        data = query.data.split("_")[1]
        keyboard = get_tags_keyboard(user.id) if data == "tags" else None
        await query.message.edit_text(messages[data], reply_markup=keyboard)
        await state.set_state(getattr(States, f"editing_{data}"))


@dp.callback_query(lambda x: "ask" in x.data)
async def ask(query: CallbackQuery):
    await query.answer()
    data = query.data.split("_")[1]
    ask_user = get_user(data)
    user = get_user(query.message.chat.id)
    redirects = {1234567: "5237472052", 12345: "5237472052"}
    if ask_user:
        declines = json.loads(user.declines or "[]")
        if ask_user.id not in declines:
            declines.append(ask_user.id)
        user.declines = json.dumps(declines)
        session.commit()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Принять ✅", callback_data=f"answer_{user.id}"
                    ),
                    InlineKeyboardButton(
                        text="Отклонить ❌", callback_data=f"delete_decline_{user.id}"
                    ),
                ]
            ]
        )
        keyboard1 = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Продолжить", callback_data=f"find")]
            ]
        )
        await bot.send_message(
            redirects.get(ask_user.id) or ask_user.id,
            f"Приглашение:\n<b>{user.name}</b>, <u>{user.age}</u>\nОписание: <i>{user.desription}</i>\nУвлечения: {', '.join(json.loads(user.tags or '[]')) or None}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        await query.message.edit_text("Приглашение отправлено.", reply_markup=keyboard1)


@dp.callback_query(lambda x: "answer" in x.data)
async def answer(query: CallbackQuery):
    await query.answer()
    if "_" in query.data:
        data = query.data.split("_")
        user = get_user(query.message.chat.id)
        answer_user = get_user(data[1])

        declines = json.loads(answer_user.declines or "[]")
        if user.id not in declines:
            declines.append(user.id)
        answer_user.declines = json.dumps(declines)
        declines = json.loads(user.declines or "[]")
        if answer_user.id not in declines:
            declines.append(answer_user.id)
        user.declines = json.dumps(declines)
        session.commit()

        keyboard_user = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Открыть диалог", url=answer_user.link),
                    InlineKeyboardButton(text="Меню", callback_data="menu"),
                ]
            ]
        )
        keyboard_answer_user = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Открыть диалог", url=user.link),
                    InlineKeyboardButton(text="Меню", callback_data="menu"),
                ]
            ]
        )
        await query.message.answer(
            "Отлично! Теперь вы можете начать диалог, чтобы договориться о месте и времени занятий.",
            reply_markup=keyboard_user,
        )

        await bot.send_message(
            answer_user.id,
            f"Пользователь {user.name} согласился позаниматься! Теперь вы можете начать диалог, чтобы договориться о месте и времени занятий.",
            reply_markup=keyboard_answer_user,
        )
        await query.message.edit_text("Заявка принята.")


@dp.callback_query(lambda x: "delete" in x.data)
async def delete(query: CallbackQuery):
    await query.answer()
    if "_" in query.data:
        data = query.data.split("_")
        if data[1] == "decline":
            user = get_user(query.message.chat.id)
            decline_user = get_user(data[2])
            declines = json.loads(decline_user.declines or "[]")
            if decline_user.id not in declines:
                declines.append(user.id)
            decline_user.declines = json.dumps(declines)
            session.commit()
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="В меню", callback_data="menu")]
                ]
            )
            await query.message.answer("Заявка отклонена.", reply_markup=keyboard)
    await query.message.delete()


@dp.callback_query(lambda x: "news" in x.data)
async def display_news(query: CallbackQuery):
    await query.answer()
    index = 0
    if "_" in query.data:
        await query.message.delete()
        index = int(query.data.split("_")[1])
    if not os.path.exists("messages.json"):
        return await query.message.answer(
            "Пока что нет новостей. Как только они появятся - я вас оповещу😃"
        )
    news = json.loads(open("messages.json", encoding="utf-8").read() or "{}")
    if not news:
        return await query.message.answer(
            "Пока что нет новостей. Как только они появятся - я вас оповещу😃"
        )
    index = index % len(news)
    news = news[index]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"news_{index - 1}"),
                InlineKeyboardButton(text="➡️", callback_data=f"news_{index + 1}"),
            ],
            [InlineKeyboardButton(text="Закрыть❌", callback_data=f"delete")],
        ]
    )
    if news.get("files"):
        return await query.message.answer_photo(
            FSInputFile(news["files"], "rb"),
            caption=news["message"][:1024],
            reply_markup=keyboard,
        )
    else:
        return await query.message.answer(news["message"], reply_markup=keyboard)


async def on_startup():
    asyncio.create_task(run_tick())


async def run():
    print("started")
    await add_tasks()

    dp.startup.register(on_startup)
    await dp.start_polling(bot)
    print("end")


if __name__ == "__main__":
    print("starting bot...")
    aioschedule.every().day.at("10:00").do(add_tasks)
    asyncio.run(run())
