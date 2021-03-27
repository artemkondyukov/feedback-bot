from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import List, Tuple

from response import Response
from user import User
from src import Base


class FeedbackBotDatabase:
    def __init__(self, db_file):
        self.db_file = db_file

    @contextmanager
    def db_session(self):
        engine = create_engine(
            f"sqlite:///{self.db_file}",
            convert_unicode=True
        )
        Base.metadata.create_all(engine)
        connection = engine.connect()
        session = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=True,
                bind=engine,
                expire_on_commit=False
            )
        )
        yield session
        session.commit()
        session.close()
        connection.close()

    def add_user(self, user: User):
        with self.db_session() as db:
            try:
                db.add(user)
                db.commit()
            except IntegrityError:
                # User already exists
                db.rollback()

    def add_response(self, response: Response):
        with self.db_session() as db:
            db.add(response)

    def get_users(self, chat_id=None) -> List[User]:
        with self.db_session() as db:
            users = db.query(User).filter_by(chat_id=chat_id).all()
        return users

    def get_user_response_pairs(self) -> List[Tuple[Response, User]]:
        with self.db_session() as db:
            answers = db.query(Response, User).filter(User.id == Response.user).all()
        return answers
