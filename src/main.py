from telegram.ext import CommandHandler, Updater
import os


class User:
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


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=repr(
            User(
                update.message.chat.username,
                update.message.chat.first_name,
                update.message.chat.last_name,
                update.message.chat_id
            )
        )
    )


token = open("token", "r").read().strip()
open("pid", "w").write(str(os.getpid()))
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()
