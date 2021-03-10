from contextlib import contextmanager
import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, Updater
from typing import Callable


questions = [
    "Как дела в целом?",
    "Как дела в индивидуальной работе?",
    "Как дела в команде?",
    "Как оцениваешь движение к своим рабочим целям?",
    "Как оцениваешь нагрузку на работе?",
    "Как ты относишься к нашей компании?",
    "Твои комментарии:",
]

reply_markup = ReplyKeyboardMarkup([
    ["Хорошо", "Плохо"]
], one_time_keyboard=True)

DB_FILE = "smdd_feedback.db"


Base = declarative_base()


@contextmanager
def db_session(db_file):
    engine = create_engine(f"sqlite:///{db_file}", echo=True, convert_unicode=True)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    session = scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=True,
            bind=engine
        )
    )
    yield session
    session.commit()
    session.close()
    connection.close()


class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
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


class Response(Base):
    id = Column(Integer, primary_key=True)
    question = Column(Integer)
    user = Column(Integer, ForeignKey("users.id"))
    answer = Column(String)
    datetime = Column(DateTime)

    __tablename__ = "responses"

    def __init__(self, question, user, answer, datetime):
        self.question = question
        self.user = user
        self.answer = answer
        self.datetime = datetime

    def __repr__(self):
        return f"Question: {self.id}\n" \
               f"User: {self.user}\n" \
               f"Answer: {self.answer}"


def get_response(question: int) -> Callable:
    def response(update, context) -> int:
        chat_id = update.effective_chat.id

        with db_session(DB_FILE) as db:
            user = db.query(User).filter_by(chat_id=chat_id)

            if user.count() == 0:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="Вы не зарегистрированы :("
                )
            else:
                assert user.count() == 1
                user = user.first()
                current_response = Response(
                    question=question,
                    user=user.id,
                    answer=update.message.text,
                    datetime=datetime.datetime.now()
                )
                db.add(current_response)

        if question == len(questions):
            context.bot.send_message(
                chat_id=chat_id,
                text="Ваш ответ очень важен для нас!"
            )

            return ConversationHandler.END
        elif question == len(questions) - 1:
            context.bot.send_message(
                chat_id=chat_id,
                text=questions[question]
            )
            return question + 1
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text=questions[question],
                reply_markup=reply_markup
            )
            return question + 1
    return response


def start(update, context):
    user = User(
        update.message.chat.username,
        update.message.chat.first_name,
        update.message.chat.last_name,
        update.message.chat_id
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=repr(user)
    )

    with db_session(DB_FILE) as db:
        try:
            db.add(user)
            db.commit()
        except IntegrityError:
            # User already exists
            db.rollback()

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=questions[0],
            reply_markup=reply_markup
        )

    return 1


def cancel(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.chat_id,
        text="Что-то пошло не так"
    )


if __name__ == "__main__":
    token = open("token", "r").read().strip()
    open("pid", "w").write(str(os.getpid()))
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            **{
                i: [MessageHandler(Filters.regex("Хорошо|Плохо"), get_response(i))] for i in range(1, 7)
            },
            **{
                7: [MessageHandler(Filters.text, get_response(7))]
            }
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
