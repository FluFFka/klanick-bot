#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import random
import time

import telegram
import telegram.ext

import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


def bot_command(command_handler):
    def wrapper(update: telegram.Update, context: telegram.ext.CallbackContext):
        logger.info(
            "Handling a command with function %s" % command_handler.__name__)
        command_handler(update, context)

    return wrapper


@bot_command
def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text('Я говорю тебе... Привеееееет)')


@bot_command
def help_command(update: telegram.Update,
                 context: telegram.ext.CallbackContext):
    update.message.reply_text("Эээээээто секрет!")


def initialize_sheets_service():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'creds.json',
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive',
         'https://spreadsheets.google.com/feeds'])

    return gspread.authorize(creds)


ANSWERS_UPDATE_TIME = 5
last_answers_update = None
answers = []


def get_answers(service):
    global last_answers_update, answers

    now = time.time()
    since_last_update = now - last_answers_update \
        if last_answers_update is not None else ANSWERS_UPDATE_TIME

    if since_last_update >= ANSWERS_UPDATE_TIME:
        logging.info("Updating answers from google spreadsheet")
        last_answers_update = now
        answers = service.open('Кланик бот').sheet1.col_values(1)
    return answers


def get_todd_etot_sticker_set(bot):
    return bot.getStickerSet("ToddEtot")


def make_message_handler(*reply_functions):
    def handle(update: telegram.Update, context: telegram.ext.CallbackContext):
        message = update.message.text

        logging.info("Message: %s" % message)
        replies = [reply
                   for f in reply_functions
                   for reply in f(update, context, message)]
        logging.info("Replies: %s" % replies)

        for reply in replies:
            update.message.__getattribute__(reply[0])(*reply[1:])

    return handle


def random_message_from_gspread(*args):
    return [("reply_text", random.choice(get_answers(gsheets_service)))]


random_message_handler = make_message_handler(random_message_from_gspread)


def random_todd_etot_sticker(update, context, message):
    return [("reply_sticker",
             random.choice(get_todd_etot_sticker_set(context.bot).stickers))]


random_sticker_handler = make_message_handler(random_todd_etot_sticker)


def random_reply(*reply_functions_and_probas):
    reply_functions = [pair[0] for pair in reply_functions_and_probas]
    probas = [pair[1] for pair in reply_functions_and_probas]
    return make_message_handler(
        lambda update, context, message:
        random.choices(reply_functions, probas)[0](update, context, message)
    )


klan_message_handler = random_reply(
    (random_message_from_gspread, 95),
    (random_todd_etot_sticker, 5),
)


def main():
    logging.info("Starting bot")

    logging.info("Initializing gsheets_service...")
    global gsheets_service
    gsheets_service = initialize_sheets_service()

    logging.info("Initializing bot...")
    with open("bot_token.txt") as f:
        updater = telegram.ext.Updater(f.read(), use_context=True)

    dp: telegram.ext.Dispatcher = updater.dispatcher

    dp.add_handler(telegram.ext.CommandHandler("start", start))
    dp.add_handler(telegram.ext.CommandHandler("help", help_command))
    dp.add_handler(telegram.ext.CommandHandler("klan", klan_message_handler))
    dp.add_handler(
        telegram.ext.CommandHandler("random", random_message_handler))
    dp.add_handler(
        telegram.ext.CommandHandler("sticker", random_sticker_handler))

    dp.add_handler(telegram.ext.MessageHandler(
        telegram.ext.Filters.all & ~telegram.ext.Filters.command,
        klan_message_handler))

    updater.start_polling()

    logging.info("Initializing done!")
    updater.idle()


if __name__ == '__main__':
    main()
