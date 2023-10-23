import dotenv as de
from aiogram import Bot, Dispatcher
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from database import Base

env = de.dotenv_values(".env")
token = env.get("TOKEN")
bot = Bot(token)
dp = Dispatcher()
engine = create_engine("sqlite:///db")
Session = sessionmaker(engine)
session = Session()

# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

available_tags = ["Туризм", "Волейбол", "Бег", "Футбол", "Тренажёрный зал", "Баскетбол", "Яхтинг"]
