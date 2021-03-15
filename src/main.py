from contextlib import contextmanager
import csv
import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
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
], one_time_keyboard=False, resize_keyboard=True)

DB_FILE = "/data/smdd_feedback.db"
PASSWORD = open("db_password", "r").read().strip()


Base = declarative_base()


@contextmanager
def db_session():
    engine = create_engine(
        f"sqlite:///{DB_FILE}",
        echo=True,
        convert_unicode=True
    )
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


class Response(Base):
    id = Column(Integer, primary_key=True)
    question = Column(Integer)
    user = Column(Integer, ForeignKey("users.id"))
    answer = Column(String(127))
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


def get_data(update, context) -> None:
    chat_id = update.effective_chat.id

    def make_row(pair):
        response: Response
        user: User
        response, user = pair
        return (
            user.first_name,
            user.last_name,
            questions[response.question - 1],
            response.answer,
            str(response.datetime),
            str(user.chat_id),
            user.username
        )

    with db_session() as db:
        answers = db.query(Response, User).filter(User.id == Response.user).all()
        processed_answers = [
            make_row(p) for p in answers
        ]

    timestamp = str(int(datetime.datetime.now().timestamp()))
    filename = f"/tmp/{timestamp}.csv"

    with open(filename, "w", newline='') as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=',',
            quotechar='|',
            quoting=csv.QUOTE_MINIMAL
        )
        for answer in processed_answers:
            csv_writer.writerow(answer)

    context.bot.send_document(chat_id, open(filename, "rb"))


def get_response(question: int) -> Callable:
    def response(update, context) -> int:
        chat_id = update.effective_chat.id

        with db_session() as db:
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
                text=questions[question],
                reply_markup=ReplyKeyboardRemove()
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

    with db_session() as db:
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


def schedule(update, context):
    with db_session() as db:
        users = db.query(User).all()
        chat_ids = [user.chat_id for user in users]

    for chat_id in chat_ids:
        context.bot.send_message(
            chat_id,
            "Отправьте боту /start"
        )


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
        entry_points=[CommandHandler("start", start)],
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
    get_data_handler = CommandHandler("get_data", get_data)
    schedule_handler = CommandHandler("schedule", schedule)

    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(get_data_handler)
    dispatcher.add_handler(schedule_handler)
    updater.start_polling()
