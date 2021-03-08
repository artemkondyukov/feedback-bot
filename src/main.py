from telegram.ext import CommandHandler, Updater
import os


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


token = open("token", "r").read()
print(token)
open("pid", "w").write(str(os.getpid()))
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()
