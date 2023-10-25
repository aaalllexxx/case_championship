from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    link = Column(String(100))
    age = Column(Integer)
    tags = Column(String(512))
    desription = Column(String(256))
    declines = Column(String(2 ** 13))
    watched = Column(String(2 ** 15))

    def __repr__(self):
        return f"User({self.id}, {self.name})"
