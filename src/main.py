from telegram.ext import Updater

from feedback_bot import FeedbackBot

if __name__ == "__main__":
    token = open("token", "r").read().strip()
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    feedback_bot = FeedbackBot("data/config")

    for handler in feedback_bot.handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
