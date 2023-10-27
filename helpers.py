from settings import *
from database import *


def get_user(user_id) -> User:
    return session.query(User).filter_by(id=user_id).first()