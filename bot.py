#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import random
import time

import telegram
import telegram.ext

import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def bot_command(command_handler):
    def wrapper(update: telegram.Update, context: telegram.ext.CallbackContext):
        logger.info("Handling a command with function %s" % command_handler.__name__)
        command_handler(update, context)
    return wrapper


@bot_command
def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text('Я говорю тебе... Привеееееет)')


@bot_command
def help_command(update: telegram.Update, context: telegram.ext.CallbackContext):
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
    since_last_update = now - last_answers_update if last_answers_update is not None else ANSWERS_UPDATE_TIME

    if since_last_update >= ANSWERS_UPDATE_TIME:
        logging.info("Updating answers from google spreadsheet")
        last_answers_update = now
        answers = service.open('Кланик бот').sheet1.col_values(1)
    return answers


def message_handler(update: telegram.Update, context: telegram.ext.CallbackContext):
    message = update.message.text

    logging.info("Message: %s" % message)
    answer = random.choice(get_answers(gsheets_service))
    logging.info("Answer: %s" % answer)

    update.message.reply_text(answer)


def main():
    logging.info("Starting bot")

    logging.info("Initializing gsheets_service...")
    global gsheets_service
    gsheets_service = initialize_sheets_service()

    logging.info("Initializing bot...")
    with open("bot_token.txt") as f:
        updater = telegram.ext.Updater(f.read(), use_context=True)

    dp = updater.dispatcher

    dp.add_handler(telegram.ext.CommandHandler("start", start))
    dp.add_handler(telegram.ext.CommandHandler("help", help_command))

    dp.add_handler(telegram.ext.MessageHandler(
        telegram.ext.Filters.text & ~telegram.ext.Filters.command,
        message_handler))

    updater.start_polling()

    logging.info("Initializing done!")
    updater.idle()


if __name__ == '__main__':
    main()
