from sqlalchemy import Column, Integer, String

from src import Base


class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String(127), unique=True)
    first_name = Column(String(127))
    last_name = Column(String(127))
    chat_id = Column(Integer, unique=True)

    __tablename__ = 'users'

    def __init__(self, username, first_name, last_name, chat_id):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.chat_id = chat_id

    def __repr__(self):
        return f"Username: {self.username}\n" \
               f"Fist name: {self.first_name}\n" \
               f"Last name: {self.last_name}\n" \
               f"Chat id: {self.chat_id}"
