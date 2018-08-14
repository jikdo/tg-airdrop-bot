#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright(c) 2018
# Kofi Amanfo <expl00ra@protonmail.com>

# This program is the sole property of www.airdropking.io

"""
This module is the engine of a telegram bounty and referral bot
designed to enhance visibilty for ICOs
"""

import logging
import json
from datetime import date
import re
import os

from telegram.ext import (
    Updater,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    messagequeue as mq
)
from telegram.ext.dispatcher import run_async

from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.utils.request import Request

import shortuuid
import psycopg2

from db import (
    create_table,
    add_task_column,
    is_user,
    add_new_user,
    get_total_rewards,
    get_user_referral_reward_and_referred_no,
    set_referredby_code,
    set_user_wallet_address,
    get_users_telegram_id,
)

from tasks import (
    ask_facebook_name,
    ask_twitter_username,
    receive_facebook_name,
    receive_twitter_username,
    reward_telegram_group,
    reward_telegram_channel,
    receive_email_address,
    ask_email_address,
    ask_verification_question,
    receive_verification_answer,
    set_user_task_reward
)

from menu import (
    menu_markup,
    menu_relayer
)


# log data
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# get config
with open(r'config.json', 'r') as file:
    config = json.loads(file.read())

# create a spam beater bot instance
class MQBot(bot.Bot):
    '''A subclass of Bot which delegates send method handling to MQ'''

    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(MQBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).send_message(*args, **kwargs)


# setup
request = Request(con_pool_size=8)
q = mq.MessageQueue()
tfb_bot = MQBot(os.environ["TG_ACCESS_TOKEN"], request=request, mqueue=q)
updater = Updater(bot=tfb_bot)
dispatcher = updater.dispatcher

# create users table
create_table()


def start(bot, update, args=None):
    "Register user"
    telegram_id = update.message.from_user.id
    telegram_username = update.message.from_user.username
    if telegram_username is None:
        telegram_username = 'n/a'
    chat_id = update.message.chat_id

    total = get_total_rewards()
    if total is None:
        total = 0

    print('total >>>>>> ' + str(total))
    if total >= config['rewards']['cap']:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Bounty completed.\nAllocated tokens finished. Visit our community for more info {}".format(
                config['social']['telegram_group']),
            disable_web_page_preview=True
        )
        print('airdrop shared ::: ' + str(total))
    else:
        if not is_user(telegram_id):
            # add new user
            add_new_user(telegram_id, chat_id, telegram_username)
            print("new user added")

            # award referer
            if args:
                referredby_code = args[0]
                print('new user referred by >> ' + referredby_code)

                set_referredby_code(referredby_code, telegram_id)

            bot.send_message(
                chat_id=update.message.chat_id,
                text=config['messages']['start_msg'].format(
                    config['ICO_name']),
                disable_web_page_preview=True,
                reply_markup=menu_markup,
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                chat_id=update.message.chat_id,
                text="You are already in the campaign",
                reply_markup=menu_markup
            )


def ask_eth_address(bot, update):
    """ ask eth address """
    bot.send_message(
        chat_id=update.message.chat_id,
        text='- Enter your ethereum wallet address.'
    )
    return "receive_eth_address"


def receive_eth_address(bot, update):
    """ receive eth address """
    telegram_id = update.message.from_user.id
    eth_address = update.message.text

    if eth_address.lower() == "skip":
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Process skipped"
        )
        return ConversationHandler.END

    pattern = re.compile(r"^0x[a-fA-F0-9]{40}$")
    match = pattern.match(eth_address)
    if not match:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Invalid ethereum address.\nSend me a valid one or stop by typing 'skip'",
        )
        return "receive_eth_address"

    # update db
    set_user_wallet_address(eth_address, telegram_id)
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Wallet address saved",
        disable_web_page_preview=True,
        parse_mode="Markdown"
    )

    bot.send_message(
        chat_id=update.message.chat_id,
        text="Complete a task to earn {} tokens".format(config['ticker']),
    )
    return ConversationHandler.END

@run_async
def send_blast(bot, update, args):
    """ send message to all participants """

    message = " ".join(args)
    delivered = 0
    failed = 0

    receivers = get_users_telegram_id()

    for chat_id in receivers:
        try:
            promise = bot.send_message(
                chat_id=chat_id[0],
                text=message,
                disable_web_page_preview=True,
                )
            promise.result()
            delivered += 1
            print('messages delivered = ' + delivered)
        except:
            failed += 1
    bot.send_message(
        chat_id=update.message.chat_id,
        text=config['messages']['report_msg'].format(delivered, failed)
    )

def cancel(bot, update):
    pass


reg_convo_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start, pass_args=True),
        CommandHandler('Wallet', ask_eth_address),
        CallbackQueryHandler(
            pattern="telegram_channel_reward",
            callback=reward_telegram_channel,
        ),
        CallbackQueryHandler(
            pattern="telegram_group_reward",
            callback=reward_telegram_group,
        ),
        CallbackQueryHandler(
            pattern='twitter',
            callback=ask_twitter_username,
        ),
        CallbackQueryHandler(
            pattern='facebook',
            callback=ask_facebook_name,
        ),
        CallbackQueryHandler(
            pattern='email',
            callback=ask_email_address,
        ),
        CallbackQueryHandler(
            pattern='verification',
            callback=ask_verification_question,
        ),
    ],
    states={
        'receive_eth_address': [
            MessageHandler(Filters.text, receive_eth_address)
        ],
        'receive_twitter_username': [
            MessageHandler(Filters.text, receive_twitter_username)
        ],
        'receive_facebook_name': [
            MessageHandler(Filters.text, receive_facebook_name)
        ],
        'receive_email_address': [
            MessageHandler(Filters.text, receive_email_address)
        ],
        'receive_verification_answer': [
            MessageHandler(Filters.text, receive_verification_answer)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# register handlers
menu_relayer_handler = MessageHandler(Filters.text, menu_relayer)
send_blast_handler = CommandHandler('blast', send_blast, pass_args=True)

handlers = [
    reg_convo_handler,
    menu_relayer_handler,
    send_blast_handler,
]

for handler in handlers:
    dispatcher.add_handler(handler)


def main():
    updater.start_polling()
    print("airdropkingbot started :::: running {} campaign".format(
        config['ICO_name'])
    )
    updater.idle()


if __name__ == '__main__':
    main()
