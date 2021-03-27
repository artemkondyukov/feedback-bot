import configparser
import csv
from datetime import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters
from typing import Callable, Tuple

from database import FeedbackBotDatabase
from response import Response
from user import User


class FeedbackBot:
    def __init__(self, config_file):
        self.handlers = []

        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.questions = open(self.config["DEFAULT"]["QuestionsFile"]).readlines()

        self.database = FeedbackBotDatabase(self.config["DEFAULT"]["DatabaseFile"])
        self.temp_dir = self.config["DEFAULT"]["TempDir"]

        self.reply_markup = ReplyKeyboardMarkup([
            ["Хорошо", "Плохо"]
        ], one_time_keyboard=False, resize_keyboard=True)

        self.conversation_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                **{
                    i: [MessageHandler(Filters.regex("Хорошо|Плохо"), self.get_response(i))] for i in range(1, 7)
                },
                **{
                    7: [MessageHandler(Filters.text, self.get_response(7))]
                }
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        self.get_data_handler = CommandHandler("get_data", self.get_data)
        self.schedule_handler = CommandHandler("schedule", self.schedule)
        self.handlers = [
            self.conversation_handler,
            self.get_data_handler,
            self.schedule_handler
        ]

    def get_response(self, question: int) -> Callable:
        def response(update, context) -> int:
            chat_id = update.effective_chat.id

            user = self.database.get_users(chat_id=chat_id)
            if len(user) == 0:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="Вы не зарегистрированы :("
                )
            else:
                assert len(user) == 1
                user = user[0]
                current_response = Response(
                    question=question,
                    user=user.id,
                    answer=update.message.text,
                    current_datetime=datetime.now()
                )
                self.database.add_response(current_response)

            if question == len(self.questions):
                context.bot.send_message(
                    chat_id=chat_id,
                    text="Ваш ответ очень важен для нас!"
                )

                return ConversationHandler.END

            elif question == len(self.questions) - 1:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=self.questions[question],
                    reply_markup=ReplyKeyboardRemove()
                )
                return question + 1
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=self.questions[question],
                    reply_markup=self.reply_markup
                )
                return question + 1

        return response

    def get_data(self, update, context) -> None:
        chat_id = update.effective_chat.id

        def make_row(pair: Tuple[Response, User]):
            response, user = pair
            return (
                user.first_name,
                user.last_name,
                self.questions[response.question - 1],
                response.answer,
                str(response.datetime),
                str(user.chat_id),
                user.username
            )

        processed_answers = [
            make_row(p) for p in self.database.get_user_response_pairs()
        ]

        timestamp = str(int(datetime.now().timestamp()))
        filename = f"{self.temp_dir}/{timestamp}.csv"

        with open(filename, "w", newline='') as csv_file:
            csv_writer = csv.writer(
                csv_file,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL
            )
            for answer in processed_answers:
                csv_writer.writerow(answer)

        context.bot.send_document(chat_id, open(filename, "rb"))

    def start(self, update, context):
        user = User(
            update.message.chat.username,
            update.message.chat.first_name,
            update.message.chat.last_name,
            update.message.chat_id
        )

        self.database.add_user(user)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.questions[0],
            reply_markup=self.reply_markup
        )

        return 1

    def schedule(self, update, context):
        users = self.database.get_users()
        chat_ids = [user.chat_id for user in users]

        for chat_id in chat_ids:
            context.bot.send_message(
                chat_id,
                "Отправьте боту /start"
            )

    @staticmethod
    def cancel(update, context):
        context.bot.send_message(
            chat_id=update.effective_chat.chat_id,
            text="Что-то пошло не так"
        )
